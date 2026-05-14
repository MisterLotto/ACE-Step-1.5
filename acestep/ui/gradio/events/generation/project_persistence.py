"""Project save/load persistence for generation parameters.

Handles serialising the current UI state to a compact JSON file and
writing it atomically to ``gradio_outputs/projects/``.
"""

import json
import os

import gradio as gr

from acestep.ui.gradio.i18n import t
from acestep.ui.gradio.events.results.generation_info import DEFAULT_RESULTS_DIR


_SAVE_DEFAULTS = {
    "vocal_language": "unknown",
    "bpm": None,
    "keyscale": "",
    "timesignature": "",
    "duration": -1,
    "batch_size": 2,
    "guidance_scale": 7.0,
    "use_adg": False,
    "cfg_interval_start": 0.0,
    "cfg_interval_end": 1.0,
    "shift": 3.0,
    "infer_method": "ode",
    "timesteps": "",
    "audio_format": "flac",
    "mp3_bitrate": "128k",
    "mp3_sample_rate": 48000,
    "lm_temperature": 0.85,
    "lm_cfg_scale": 2.0,
    "lm_top_k": 0,
    "lm_top_p": 0.9,
    "lm_negative_prompt": "NO USER INPUT",
    "use_cot_metas": True,
    "use_cot_caption": True,
    "use_cot_language": True,
    "audio_cover_strength": 1.0,
    "cover_noise_strength": 0.0,
    "repainting_start": 0.0,
    "repainting_end": -1,
    "track_name": None,
    "complete_track_classes": [],
    "instrumental": False,
}


def save_project(
    task_type, captions, lyrics, vocal_language, bpm, key_scale, time_signature,
    audio_duration, batch_size_input, inference_steps, guidance_scale, seed,
    random_seed_checkbox, use_adg, cfg_interval_start, cfg_interval_end, shift,
    infer_method, custom_timesteps, audio_format, mp3_bitrate, mp3_sample_rate,
    lm_temperature, lm_cfg_scale, lm_top_k, lm_top_p, lm_negative_prompt,
    use_cot_metas, use_cot_caption, use_cot_language, audio_cover_strength,
    cover_noise_strength, think_checkbox, text2music_audio_code_string,
    repainting_start, repainting_end, track_name, complete_track_classes,
    instrumental_checkbox, song_name, retake_variance, retake_seed,
):
    """Save current generation parameters to a JSON file, omitting default values.

    Always includes caption and lyrics. All other fields are written only when
    they differ from their known defaults, keeping saved files compact.

    Args:
        All generation UI component values (see _SAVE_PROJECT_INPUT_KEYS in wiring).
        song_name: Optional project name used as the filename base.

    Returns:
        Absolute path to the written JSON temp file, for Gradio File output.
    """
    try:
        return _save_project_impl(
            task_type, captions, lyrics, vocal_language, bpm, key_scale, time_signature,
            audio_duration, batch_size_input, inference_steps, guidance_scale, seed,
            random_seed_checkbox, use_adg, cfg_interval_start, cfg_interval_end, shift,
            infer_method, custom_timesteps, audio_format, mp3_bitrate, mp3_sample_rate,
            lm_temperature, lm_cfg_scale, lm_top_k, lm_top_p, lm_negative_prompt,
            use_cot_metas, use_cot_caption, use_cot_language, audio_cover_strength,
            cover_noise_strength, think_checkbox, text2music_audio_code_string,
            repainting_start, repainting_end, track_name, complete_track_classes,
            instrumental_checkbox, song_name, retake_variance, retake_seed,
        )
    except Exception as e:
        gr.Warning(t("messages.save_error", error=str(e)))
        return gr.update(visible=False)


def _save_project_impl(
    task_type, captions, lyrics, vocal_language, bpm, key_scale, time_signature,
    audio_duration, batch_size_input, inference_steps, guidance_scale, seed,
    random_seed_checkbox, use_adg, cfg_interval_start, cfg_interval_end, shift,
    infer_method, custom_timesteps, audio_format, mp3_bitrate, mp3_sample_rate,
    lm_temperature, lm_cfg_scale, lm_top_k, lm_top_p, lm_negative_prompt,
    use_cot_metas, use_cot_caption, use_cot_language, audio_cover_strength,
    cover_noise_strength, think_checkbox, text2music_audio_code_string,
    repainting_start, repainting_end, track_name, complete_track_classes,
    instrumental_checkbox, song_name, retake_variance, retake_seed,
):
    import datetime

    def _ne(value, default_key):
        return value != _SAVE_DEFAULTS[default_key]

    data = {}

    if task_type and task_type != "text2music":
        data["task_type"] = task_type
    if captions:
        data["caption"] = captions
    if lyrics:
        data["lyrics"] = lyrics

    if _ne(vocal_language, "vocal_language"):
        data["vocal_language"] = vocal_language
    if bpm is not None and _ne(bpm, "bpm"):
        data["bpm"] = bpm
    if key_scale and _ne(key_scale, "keyscale"):
        data["keyscale"] = key_scale
    if time_signature and _ne(time_signature, "timesignature"):
        data["timesignature"] = time_signature
    if audio_duration is not None and _ne(audio_duration, "duration"):
        data["duration"] = audio_duration
    if _ne(batch_size_input, "batch_size"):
        data["batch_size"] = batch_size_input

    # Always save inference_steps — default varies by model
    data["inference_steps"] = inference_steps

    if _ne(guidance_scale, "guidance_scale"):
        data["guidance_scale"] = guidance_scale
    if not random_seed_checkbox and seed and str(seed) != "-1":
        data["seed"] = seed
    if _ne(use_adg, "use_adg"):
        data["use_adg"] = use_adg
    if _ne(cfg_interval_start, "cfg_interval_start"):
        data["cfg_interval_start"] = cfg_interval_start
    if _ne(cfg_interval_end, "cfg_interval_end"):
        data["cfg_interval_end"] = cfg_interval_end
    if _ne(shift, "shift"):
        data["shift"] = shift
    if _ne(infer_method, "infer_method"):
        data["infer_method"] = infer_method
    if custom_timesteps and _ne(custom_timesteps, "timesteps"):
        data["timesteps"] = custom_timesteps
    if _ne(audio_format, "audio_format"):
        data["audio_format"] = audio_format
    if audio_format == "mp3":
        if _ne(mp3_bitrate, "mp3_bitrate"):
            data["mp3_bitrate"] = mp3_bitrate
        if _ne(mp3_sample_rate, "mp3_sample_rate"):
            data["mp3_sample_rate"] = mp3_sample_rate
    if _ne(lm_temperature, "lm_temperature"):
        data["lm_temperature"] = lm_temperature
    if _ne(lm_cfg_scale, "lm_cfg_scale"):
        data["lm_cfg_scale"] = lm_cfg_scale
    if _ne(lm_top_k, "lm_top_k"):
        data["lm_top_k"] = lm_top_k
    if _ne(lm_top_p, "lm_top_p"):
        data["lm_top_p"] = lm_top_p
    if _ne(lm_negative_prompt, "lm_negative_prompt"):
        data["lm_negative_prompt"] = lm_negative_prompt
    if _ne(use_cot_metas, "use_cot_metas"):
        data["use_cot_metas"] = use_cot_metas
    if _ne(use_cot_caption, "use_cot_caption"):
        data["use_cot_caption"] = use_cot_caption
    if _ne(use_cot_language, "use_cot_language"):
        data["use_cot_language"] = use_cot_language
    if _ne(audio_cover_strength, "audio_cover_strength"):
        data["audio_cover_strength"] = audio_cover_strength
    if _ne(cover_noise_strength, "cover_noise_strength"):
        data["cover_noise_strength"] = cover_noise_strength
    data["thinking"] = bool(think_checkbox)
    if text2music_audio_code_string and text2music_audio_code_string.strip():
        data["audio_codes"] = text2music_audio_code_string
    if _ne(repainting_start, "repainting_start"):
        data["repainting_start"] = repainting_start
    if _ne(repainting_end, "repainting_end"):
        data["repainting_end"] = repainting_end
    if track_name and _ne(track_name, "track_name"):
        data["track_name"] = track_name
    if complete_track_classes and _ne(complete_track_classes, "complete_track_classes"):
        data["complete_track_classes"] = complete_track_classes
    if _ne(instrumental_checkbox, "instrumental"):
        data["instrumental"] = instrumental_checkbox
    if song_name and song_name.strip():
        data["song_name"] = song_name.strip()
    try:
        _retake_variance = float(retake_variance) if retake_variance is not None else 0.0
    except (TypeError, ValueError):
        _retake_variance = 0.0
    if _retake_variance != 0.0:
        data["retake_variance"] = _retake_variance
    _retake_seed = str(retake_seed).strip() if retake_seed is not None else ""
    if _retake_seed:
        data["retake_seed"] = _retake_seed

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = (song_name or "").strip()
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in base)[:80].strip("_.")
    safe = safe or "project"
    filename = f"{safe}_{timestamp}.json"

    projects_dir = os.path.join(DEFAULT_RESULTS_DIR, "projects")
    os.makedirs(projects_dir, exist_ok=True)
    filepath = os.path.join(projects_dir, filename)
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, filepath)

    gr.Info(t("messages.project_saved", filename=filename))
    return gr.update(value=filepath, visible=True)
