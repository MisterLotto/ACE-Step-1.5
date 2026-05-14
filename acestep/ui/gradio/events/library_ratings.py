"""Atomic ratings persistence for the Library tab.

Handles reading and writing the ``ratings.json`` file that stores
per-song star ratings keyed by audio file path.
"""

import json
import os
import tempfile

from loguru import logger

from acestep.ui.gradio.events.results.generation_info import DEFAULT_RESULTS_DIR

RATINGS_FILE = os.path.join(DEFAULT_RESULTS_DIR, "ratings.json")


def load_ratings() -> dict:
    """Load the ratings dict from disk, returning {} on any error."""
    try:
        if os.path.exists(RATINGS_FILE):
            with open(RATINGS_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, dict):
                logger.error(
                    f"[Library] Ratings file is not a dict "
                    f"(got {type(payload).__name__}), ignoring: {RATINGS_FILE}"
                )
                return {}
            return payload
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"[Library] Failed to load ratings from {RATINGS_FILE}: {e}")
    return {}


def save_ratings(ratings: dict) -> None:
    """Atomically write *ratings* to disk."""
    os.makedirs(DEFAULT_RESULTS_DIR, exist_ok=True)
    dir_ = os.path.dirname(RATINGS_FILE)
    fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(ratings, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, RATINGS_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
