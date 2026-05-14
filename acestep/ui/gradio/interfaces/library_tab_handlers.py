"""Event handler functions for the Library tab.

Pure handler logic — no Gradio component construction.  All functions
receive their inputs as plain values and return tuples of values/
``gr.update()`` objects for the wiring in :mod:`library_tab`.
"""

import gradio as gr

from acestep.ui.gradio.i18n import t
from acestep.ui.gradio.events.library_handlers import (
    delete_song,
    get_library_rows,
    scan_library,
    set_rating,
)


def do_refresh(sort_by, min_rating):
    """Scan the library and return updated table data."""
    try:
        songs = scan_library(sort_by=sort_by, min_rating=int(min_rating or 0))
        rows = get_library_rows(songs)
    except Exception as e:
        gr.Warning(f"Library scan failed: {e}")
        return gr.update(), gr.update(), "⚠️ Scan failed"
    n = len(songs)
    count_md = t("library.count_found_one") if n == 1 else t("library.count_found_many", n=n)
    return rows, songs, count_md


def select_song(songs, sort_by, min_rating, evt: gr.SelectData):
    """Populate the selected-song panel when a table row is clicked."""
    # If state is empty (race condition on first load), scan now
    if not songs:
        songs = scan_library(sort_by=sort_by, min_rating=int(min_rating or 0))
    if not songs or evt.index[0] >= len(songs):
        return (
            gr.update(visible=False), None, "", None,
            "", "", "", "", "", "", "", None,
        )
    song = songs[evt.index[0]]
    path = song["path"]
    meta = song["metadata"]

    rating_val = int(song["rating"]) if song["rating"] else None
    name_md = f"### {song['stem']}\n_{song['date_str']}_"

    bpm  = song.get("bpm") or "auto"
    key  = meta.get("keyscale") or meta.get("cot_keyscale") or ""
    seed = str(meta.get("seed", "") or "")

    raw_dur = meta.get("duration", -1)
    if raw_dur is None or raw_dur == -1:
        raw_dur = meta.get("cot_duration")
    try:
        secs = int(raw_dur) if (raw_dur and raw_dur != -1) else None
    except (ValueError, TypeError):
        secs = None
    dur = f"{secs // 60}:{secs % 60:02d}" if secs is not None else "auto"

    caption = meta.get("caption", "") or ""
    lyrics  = meta.get("lyrics", "") or ""

    return (
        gr.update(visible=True),  # panel
        path,                      # audio
        name_md,                   # name
        rating_val,                # rating radio
        "",                        # status
        caption,
        bpm,
        key,
        seed,
        dur,
        lyrics,
        path,                      # selected_path state
    )


def save_rating(audio_path, rating_val, songs, sort_by, min_rating):
    """Persist a rating change and refresh the table."""
    status = ""
    if audio_path:
        try:
            set_rating(audio_path, rating_val)
        except Exception as e:
            gr.Warning(f"Failed to save rating: {e}")
            status = f"❌ Failed to save rating: {e}"
    songs_refreshed = scan_library(sort_by=sort_by, min_rating=int(min_rating or 0))
    rows = get_library_rows(songs_refreshed)
    n = len(songs_refreshed)
    count_md = t("library.count_found_one") if n == 1 else t("library.count_found_many", n=n)
    return rows, songs_refreshed, count_md, status


def delete(audio_path, sort_by, min_rating):
    """Delete the selected song then refresh the table."""
    if not audio_path:
        return (
            gr.update(), gr.update(), gr.update(),
            gr.update(), gr.update(), gr.update(), gr.update(), "**No song selected.**",
            gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
            gr.update(),
        )
    _ok, msg = delete_song(audio_path)
    songs_refreshed = scan_library(sort_by=sort_by, min_rating=int(min_rating or 0))
    rows = get_library_rows(songs_refreshed)
    n = len(songs_refreshed)
    count_md = t("library.count_found_one") if n == 1 else t("library.count_found_many", n=n)
    if _ok:
        return (
            rows,
            songs_refreshed,
            count_md,
            gr.update(visible=True),   # keep panel mounted — hiding it re-inits gr.Audio on next select
            None,                       # clear audio
            "_Select a song to preview._",
            None,                       # clear rating
            msg,                        # status
            "",                         # caption
            "",                         # bpm
            "",                         # key
            "",                         # seed
            "",                         # dur
            "",                         # lyrics
            None,                       # clear path state
        )
    # On failure: keep panel visible, show error in status, leave fields intact
    return (
        rows,
        songs_refreshed,
        count_md,
        gr.update(visible=True),   # keep panel open
        gr.update(),               # leave audio unchanged
        gr.update(),               # leave name unchanged
        gr.update(),               # leave rating unchanged
        msg,                       # show error in status
        gr.update(),               # leave caption unchanged
        gr.update(),               # leave bpm unchanged
        gr.update(),               # leave key unchanged
        gr.update(),               # leave seed unchanged
        gr.update(),               # leave dur unchanged
        gr.update(),               # leave lyrics unchanged
        audio_path,                # keep path state
    )
