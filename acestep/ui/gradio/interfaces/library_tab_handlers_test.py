"""Unit tests for library_tab_handlers module."""

import unittest
from unittest.mock import patch

import acestep.ui.gradio.interfaces.library_tab_handlers as _mod
from acestep.ui.gradio.interfaces.library_tab_handlers import delete, select_song


class _Sel:
    """Minimal stand-in for gr.SelectData."""
    def __init__(self, row):
        self.index = [row, 0]


def _song(stem="track", path="/audio/track.mp3", rating=0, **meta):
    return {
        "path": path,
        "stem": stem,
        "date_str": "2025-01-01 12:00",
        "ts": 1735732800,
        "bpm": "auto",
        "caption": "Test caption",
        "rating": rating,
        "metadata": meta,
    }


class SelectSongTests(unittest.TestCase):
    """Tests for select_song."""

    def test_out_of_bounds_returns_hidden_panel(self):
        result = select_song([_song()], "date", 0, _Sel(99))
        self.assertEqual(len(result), 12)
        self.assertIsNone(result[1])   # audio = None
        self.assertEqual(result[2], "")

    def test_empty_songs_scans_then_returns_hidden_on_miss(self):
        with patch.object(_mod, "scan_library", return_value=[]):
            result = select_song([], "date", 0, _Sel(0))
        self.assertIsNone(result[1])

    def test_valid_song_populates_fields(self):
        s = _song(
            stem="mysong", path="/audio/mysong.mp3", rating=3,
            keyscale="C major", seed="42", duration=200,
            caption="Epic", lyrics="la la la",
        )
        result = select_song([s], "date", 0, _Sel(0))
        self.assertEqual(result[1], "/audio/mysong.mp3")  # audio
        self.assertIn("mysong", result[2])                # name_md
        self.assertEqual(result[3], 3)                    # rating
        self.assertEqual(result[4], "")                   # status cleared
        self.assertEqual(result[5], "Epic")               # caption
        self.assertEqual(result[7], "C major")            # key
        self.assertEqual(result[8], "42")                 # seed
        self.assertEqual(result[10], "la la la")          # lyrics
        self.assertEqual(result[11], "/audio/mysong.mp3") # path state

    def test_duration_formatted_as_mm_ss(self):
        result = select_song([_song(path="/a.mp3", duration=200)], "date", 0, _Sel(0))
        self.assertEqual(result[9], "3:20")

    def test_missing_duration_shows_auto(self):
        result = select_song([_song(path="/a.mp3")], "date", 0, _Sel(0))
        self.assertEqual(result[9], "auto")

    def test_cot_keyscale_fallback(self):
        result = select_song([_song(path="/a.mp3", cot_keyscale="D minor")], "date", 0, _Sel(0))
        self.assertEqual(result[7], "D minor")

    def test_zero_rating_becomes_none(self):
        result = select_song([_song(path="/a.mp3", rating=0)], "date", 0, _Sel(0))
        self.assertIsNone(result[3])


class DeleteTests(unittest.TestCase):
    """Tests for delete."""

    def _mock_backend(self, ok, msg="done"):
        return (
            patch.object(_mod, "delete_song", return_value=(ok, msg)),
            patch.object(_mod, "scan_library", return_value=[]),
            patch.object(_mod, "get_library_rows", return_value=[]),
        )

    def test_no_path_returns_no_song_selected(self):
        result = delete(None, "date", 0)
        self.assertEqual(len(result), 15)
        self.assertIn("No song selected", result[7])

    def test_success_clears_audio_and_path_state(self):
        d, s, r = self._mock_backend(ok=True, msg="🗑️ Deleted")
        with d, s, r:
            result = delete("/audio/song.mp3", "date", 0)
        self.assertEqual(len(result), 15)
        self.assertIsNone(result[4])   # audio cleared
        self.assertIsNone(result[14])  # path state cleared
        self.assertEqual(result[7], "🗑️ Deleted")

    def test_failure_preserves_path_state(self):
        d, s, r = self._mock_backend(ok=False, msg="❌ error")
        with d, s, r:
            result = delete("/audio/song.mp3", "date", 0)
        self.assertEqual(result[7], "❌ error")
        self.assertEqual(result[14], "/audio/song.mp3")


if __name__ == "__main__":
    unittest.main()
