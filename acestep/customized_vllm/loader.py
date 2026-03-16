"""Safetensors weight loader with packed-module support for Qwen3."""

import os
from glob import glob
import torch
from torch import nn
from safetensors import safe_open


def _default_weight_loader(param, loaded_weight):
    param.data.copy_(loaded_weight)


def _get_param(model, name):
    """Resolve parameter by name, trying with and without 'model.' prefix."""
    for candidate in (name, f"model.{name}", name.removeprefix("model.")):
        try:
            return model.get_parameter(candidate)
        except AttributeError:
            continue
    return None


def load_model(model: nn.Module, path: str):
    """Load safetensors weights into model.

    Handles packed-module mappings (e.g., separate q/k/v -> packed qkv_proj)
    defined in model.packed_modules_mapping.
    """
    mapping = getattr(model, "packed_modules_mapping", {})
    files = glob(os.path.join(path, "*.safetensors"))
    if not files:
        raise FileNotFoundError(f"No .safetensors files found in {path}")

    for filepath in files:
        with safe_open(filepath, "pt", "cpu") as f:
            for weight_name in f.keys():
                for src_key, (dst_key, shard_id) in mapping.items():
                    if src_key in weight_name:
                        param_name = weight_name.replace(src_key, dst_key)
                        param = _get_param(model, param_name)
                        if param is None:
                            continue
                        param.weight_loader(param, f.get_tensor(weight_name), shard_id)
                        break
                else:
                    param = _get_param(model, weight_name)
                    if param is None:
                        continue
                    loader = getattr(param, "weight_loader", _default_weight_loader)
                    loader(param, f.get_tensor(weight_name))
