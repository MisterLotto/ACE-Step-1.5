"""Library tab backend: scan, rate, and delete generated songs."""

import glob
import json
import os
from datetime import datetime

from acestep.ui.gradio.events.results.generation_info import DEFAULT_RESULTS_DIR

RATINGS_FILE = os.path.join(DEFAULT_RESULTS_DIR, "ratings.json")
AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".opus", ".aac"}


# ── Ratings persistence ───────────────────────────────────────────────────────

def _load_ratings() -> dict:
    try:
        if os.path.exists(RATINGS_FILE):
            with open(RATINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_ratings(ratings: dict) -> None:
    os.makedirs(DEFAULT_RESULTS_DIR, exist_ok=True)
    with open(RATINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(ratings, f, indent=2, ensure_ascii=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def rating_stars(rating: int) -> str:
    """Return a star-string representation for a 0-5 rating."""
    if not rating:
        return "—"
    return "★" * int(rating) + "☆" * (5 - int(rating))


def _format_date(ts: int) -> str:
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "Unknown"


# ── Core library operations ───────────────────────────────────────────────────

def scan_library(sort_by: str = "date", min_rating: int = 0) -> list:
    """Scan gradio_outputs for all generated audio files.

    Args:
        sort_by: One of "date" (newest first), "name" (A-Z), "rating" (highest first).
        min_rating: If > 0, exclude songs with a lower rating (unrated = 0).

    Returns:
        List of song dicts, each with keys:
            path, stem, date_str, ts, bpm, caption, rating, metadata.
    """
    if not os.path.exists(DEFAULT_RESULTS_DIR):
        return []

    ratings = _load_ratings()
    songs = []

    batch_dirs = sorted(
        glob.glob(os.path.join(DEFAULT_RESULTS_DIR, "batch_*")),
        key=lambda p: os.path.basename(p),
        reverse=True,  # newest first by default
    )

    for batch_dir in batch_dirs:
        try:
            ts = int(os.path.basename(batch_dir).split("_")[1])
        except (IndexError, ValueError):
            ts = 0

        for audio_file in sorted(os.listdir(batch_dir)):
            stem, ext = os.path.splitext(audio_file)
            if ext.lower() not in AUDIO_EXTENSIONS:
                continue

            audio_path = os.path.normpath(
                os.path.join(batch_dir, audio_file)
            ).replace("\\", "/")
            json_path = os.path.normpath(
                os.path.join(batch_dir, stem + ".json")
            ).replace("\\", "/")

            metadata: dict = {}
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                except Exception:
                    pass

            rating = ratings.get(audio_path, 0)
            if min_rating > 0 and rating < min_rating:
                continue

            caption = metadata.get("caption", "") or ""
            caption_preview = (caption[:80] + "…") if len(caption) > 80 else caption

            raw_bpm = metadata.get("cot_bpm") or metadata.get("bpm")
            bpm_display = str(int(raw_bpm)) if raw_bpm else "auto"

            songs.append({
                "path": audio_path,
                "stem": stem,
                "date_str": _format_date(ts),
                "ts": ts,
                "bpm": bpm_display,
                "caption": caption_preview,
                "rating": rating,
                "metadata": metadata,
            })

    if sort_by == "name":
        songs.sort(key=lambda s: s["stem"].lower())
    elif sort_by == "rating":
        songs.sort(key=lambda s: s["rating"], reverse=True)
    # else "date" — already newest-first from the sorted batch_dirs loop

    return songs


def get_library_rows(songs: list) -> list:
    """Convert a song list to rows suitable for gr.Dataframe."""
    return [
        [s["stem"], s["date_str"], rating_stars(s["rating"])]
        for s in songs
    ]


def set_rating(audio_path: str, rating) -> None:
    """Persist a 1-5 star rating for the given audio path."""
    ratings = _load_ratings()
    if rating is not None and int(rating) > 0:
        ratings[audio_path] = int(rating)
    else:
        ratings.pop(audio_path, None)
    _save_ratings(ratings)


def delete_song(audio_path: str) -> tuple:
    """Delete audio + companion JSON file and remove stored rating.

    Returns:
        (success: bool, message: str)
    """
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        stem = os.path.splitext(audio_path)[0]
        json_path = stem + ".json"
        if os.path.exists(json_path):
            os.remove(json_path)
        # Remove the parent folder if it is now empty
        parent = os.path.dirname(audio_path)
        if parent and os.path.isdir(parent) and not os.listdir(parent):
            os.rmdir(parent)
        ratings = _load_ratings()
        ratings.pop(audio_path, None)
        _save_ratings(ratings)
        return True, f"🗑️ Deleted: **{os.path.basename(audio_path)}**"
    except Exception as exc:
        return False, f"❌ Delete failed: {exc}"
