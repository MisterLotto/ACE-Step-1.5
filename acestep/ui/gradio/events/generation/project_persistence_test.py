"""Unit tests for _save_project_impl in project_persistence."""

import importlib.util
import json
import os
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module():
    """Load project_persistence with gradio and i18n stubbed out."""
    gr_stub = types.SimpleNamespace(
        update=lambda **kw: kw,
        Info=lambda *a, **kw: None,
        Warning=lambda *a, **kw: None,
    )

    i18n = types.ModuleType("acestep.ui.gradio.i18n")
    i18n.t = lambda key, **_: key

    gen_info = types.ModuleType("acestep.ui.gradio.events.results.generation_info")
    gen_info.DEFAULT_RESULTS_DIR = "/tmp/gradio_outputs_stub"

    mocks = {
        "gradio": gr_stub,
        "acestep": types.ModuleType("acestep"),
        "acestep.ui": types.ModuleType("acestep.ui"),
        "acestep.ui.gradio": types.ModuleType("acestep.ui.gradio"),
        "acestep.ui.gradio.i18n": i18n,
        "acestep.ui.gradio.events": types.ModuleType("acestep.ui.gradio.events"),
        "acestep.ui.gradio.events.results": types.ModuleType("acestep.ui.gradio.events.results"),
        "acestep.ui.gradio.events.results.generation_info": gen_info,
    }

    module_path = Path(__file__).with_name("project_persistence.py")
    spec = importlib.util.spec_from_file_location("project_persistence", module_path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict("sys.modules", mocks):
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_MOD = _load_module()
_save_project_impl = _MOD._save_project_impl


def _call(tmp_dir, **overrides):
    """Call _save_project_impl with all-default args, overriding specific fields."""
    kwargs = dict(
        task_type="text2music", captions="", lyrics="",
        vocal_language="unknown", bpm=None, key_scale="",
        time_signature="", audio_duration=-1, batch_size_input=2,
        inference_steps=8, guidance_scale=7.0, seed="-1",
        random_seed_checkbox=False, use_adg=False,
        cfg_interval_start=0.0, cfg_interval_end=1.0, shift=3.0,
        infer_method="ode", custom_timesteps="", audio_format="flac",
        mp3_bitrate="128k", mp3_sample_rate=48000, lm_temperature=0.85,
        lm_cfg_scale=2.0, lm_top_k=0, lm_top_p=0.9,
        lm_negative_prompt="NO USER INPUT", use_cot_metas=True,
        use_cot_caption=True, use_cot_language=True,
        audio_cover_strength=1.0, cover_noise_strength=0.0,
        think_checkbox=False, text2music_audio_code_string="",
        repainting_start=0.0, repainting_end=-1, track_name=None,
        complete_track_classes=[], instrumental_checkbox=False, song_name="",
        retake_variance=0.0, retake_seed="",
    )
    kwargs.update(overrides)
    with patch.object(_MOD, "DEFAULT_RESULTS_DIR", tmp_dir):
        return _save_project_impl(**kwargs)


def _read_saved(result):
    """Load the JSON from the path carried in the gr.update() return value."""
    with open(result["value"], encoding="utf-8") as f:
        return json.load(f)


class SaveProjectImplTests(unittest.TestCase):
    """Tests for _save_project_impl serialisation logic."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_caption_and_lyrics_included(self):
        result = _call(self._tmp, captions="Epic track", lyrics="la la la")
        data = _read_saved(result)
        self.assertEqual(data["caption"], "Epic track")
        self.assertEqual(data["lyrics"], "la la la")

    def test_inference_steps_always_present(self):
        result = _call(self._tmp, inference_steps=8)
        self.assertIn("inference_steps", _read_saved(result))

    def test_default_values_omitted(self):
        data = _read_saved(_call(self._tmp))
        self.assertNotIn("task_type", data)       # "text2music" is the default
        self.assertNotIn("vocal_language", data)  # "unknown" is the default

    def test_non_default_values_included(self):
        result = _call(self._tmp, audio_format="mp3", mp3_bitrate="320k")
        data = _read_saved(result)
        self.assertEqual(data["audio_format"], "mp3")
        self.assertEqual(data["mp3_bitrate"], "320k")

    def test_song_name_in_filename_and_json(self):
        result = _call(self._tmp, song_name="My Song")
        fname = os.path.basename(result["value"])
        self.assertTrue(fname.startswith("My_Song"))
        self.assertEqual(_read_saved(result)["song_name"], "My Song")

    def test_blank_song_name_uses_project_prefix(self):
        fname = os.path.basename(_call(self._tmp, song_name="")["value"])
        self.assertTrue(fname.startswith("project"))

    def test_random_seed_suppresses_seed_field(self):
        data = _read_saved(_call(self._tmp, seed="12345", random_seed_checkbox=True))
        self.assertNotIn("seed", data)

    def test_no_tmp_file_left(self):
        _call(self._tmp, captions="test")
        projects_dir = os.path.join(self._tmp, "projects")
        self.assertEqual([f for f in os.listdir(projects_dir) if f.endswith(".tmp")], [])


if __name__ == "__main__":
    unittest.main()
