"""Unit tests for library_handlers module."""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import acestep.ui.gradio.events.library_handlers as _mod


def _touch(path):
    open(path, "w").close()
    return path


class RatingStarsTests(unittest.TestCase):
    """Tests for rating_stars."""

    def test_zero_returns_dash(self):
        self.assertEqual(_mod.rating_stars(0), "—")

    def test_none_returns_dash(self):
        self.assertEqual(_mod.rating_stars(None), "—")

    def test_three_stars(self):
        self.assertEqual(_mod.rating_stars(3), "★★★☆☆")

    def test_five_stars(self):
        self.assertEqual(_mod.rating_stars(5), "★★★★★")


class ScanLibraryTests(unittest.TestCase):
    """Tests for scan_library."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _patch(self, ratings=None):
        return (
            patch.object(_mod, "DEFAULT_RESULTS_DIR", self._tmp),
            patch.object(_mod, "load_ratings", return_value=ratings or {}),
        )

    def _audio(self, name):
        return _touch(os.path.join(self._tmp, name))

    def test_empty_dir_returns_empty(self):
        d, r = self._patch()
        with d, r:
            self.assertEqual(_mod.scan_library(), [])

    def test_non_audio_files_ignored(self):
        _touch(os.path.join(self._tmp, "readme.txt"))
        d, r = self._patch()
        with d, r:
            self.assertEqual(_mod.scan_library(), [])

    def test_audio_file_discovered(self):
        self._audio("mysong.mp3")
        d, r = self._patch()
        with d, r:
            songs = _mod.scan_library()
        self.assertEqual(len(songs), 1)
        self.assertEqual(songs[0]["stem"], "mysong")

    def test_sort_by_name(self):
        for name in ["zebra.mp3", "alpha.flac", "middle.wav"]:
            self._audio(name)
        d, r = self._patch()
        with d, r:
            songs = _mod.scan_library(sort_by="name")
        stems = [s["stem"] for s in songs]
        self.assertEqual(stems, sorted(stems, key=str.lower))

    def test_sort_by_rating_highest_first(self):
        paths = {n: os.path.normpath(self._audio(n)).replace("\\", "/")
                 for n in ["low.mp3", "high.flac", "mid.wav"]}
        ratings = {paths["low.mp3"]: 1, paths["high.flac"]: 5, paths["mid.wav"]: 3}
        d, r = self._patch(ratings=ratings)
        with d, r:
            songs = _mod.scan_library(sort_by="rating")
        self.assertEqual(songs[0]["rating"], 5)
        self.assertEqual(songs[-1]["rating"], 1)

    def test_min_rating_filter(self):
        low = os.path.normpath(self._audio("lowrated.mp3")).replace("\\", "/")
        high = os.path.normpath(self._audio("highrated.flac")).replace("\\", "/")
        d, r = self._patch(ratings={low: 1, high: 4})
        with d, r:
            songs = _mod.scan_library(min_rating=3)
        stems = [s["stem"] for s in songs]
        self.assertIn("highrated", stems)
        self.assertNotIn("lowrated", stems)

    def test_sidecar_json_populates_caption_and_bpm(self):
        self._audio("track.mp3")
        with open(os.path.join(self._tmp, "track.json"), "w", encoding="utf-8") as f:
            json.dump({"caption": "A great track", "bpm": 120}, f)
        d, r = self._patch()
        with d, r:
            songs = _mod.scan_library()
        self.assertEqual(songs[0]["caption"], "A great track")
        self.assertEqual(songs[0]["bpm"], "120")

    def test_caption_truncated_at_80(self):
        self._audio("long.mp3")
        with open(os.path.join(self._tmp, "long.json"), "w", encoding="utf-8") as f:
            json.dump({"caption": "x" * 100}, f)
        d, r = self._patch()
        with d, r:
            songs = _mod.scan_library()
        self.assertTrue(songs[0]["caption"].endswith("…"))


class DeleteSongTests(unittest.TestCase):
    """Tests for delete_song."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _patch(self, ratings=None):
        return (
            patch.object(_mod, "DEFAULT_RESULTS_DIR", self._tmp),
            patch.object(_mod, "load_ratings", return_value=dict(ratings or {})),
            patch.object(_mod, "save_ratings"),
        )

    def _audio(self, name, subdir=None):
        d = os.path.join(self._tmp, subdir) if subdir else self._tmp
        os.makedirs(d, exist_ok=True)
        return _touch(os.path.join(d, name))

    def test_path_outside_root_refused(self):
        with tempfile.TemporaryDirectory() as outside:
            fake = _touch(os.path.join(outside, "evil.mp3"))
            with patch.object(_mod, "DEFAULT_RESULTS_DIR", self._tmp):
                ok, msg = _mod.delete_song(fake)
        self.assertFalse(ok)
        self.assertIn("outside library root", msg)

    def test_non_audio_extension_refused(self):
        txt = _touch(os.path.join(self._tmp, "evil.txt"))
        with patch.object(_mod, "DEFAULT_RESULTS_DIR", self._tmp):
            ok, msg = _mod.delete_song(txt)
        self.assertFalse(ok)
        self.assertIn("not a supported audio file", msg)

    def test_deletes_audio_file(self):
        audio = self._audio("song.mp3")
        d, lr, sr = self._patch()
        with d, lr, sr:
            ok, _ = _mod.delete_song(audio)
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(audio))

    def test_deletes_json_and_session_sidecars(self):
        audio = self._audio("song.mp3")
        json_sc = _touch(os.path.join(self._tmp, "song.json"))
        sess_sc = _touch(os.path.join(self._tmp, "song.session.npz"))
        d, lr, sr = self._patch()
        with d, lr, sr:
            _mod.delete_song(audio)
        self.assertFalse(os.path.exists(json_sc))
        self.assertFalse(os.path.exists(sess_sc))

    def test_removes_empty_parent_dir(self):
        audio = self._audio("song.mp3", subdir="batch_20250101_120000")
        subdir = os.path.dirname(audio)
        d, lr, sr = self._patch()
        with d, lr, sr:
            _mod.delete_song(audio)
        self.assertFalse(os.path.isdir(subdir))

    def test_nonempty_parent_dir_kept(self):
        audio = self._audio("song.mp3", subdir="batch_20250101_120000")
        _touch(os.path.join(os.path.dirname(audio), "other.flac"))
        subdir = os.path.dirname(audio)
        d, lr, sr = self._patch()
        with d, lr, sr:
            _mod.delete_song(audio)
        self.assertTrue(os.path.isdir(subdir))

    def test_rating_removed_on_success(self):
        audio = self._audio("rated.mp3")
        norm = os.path.normpath(audio).replace("\\", "/")
        d, lr, sr = self._patch(ratings={norm: 5, "/other/x.mp3": 3})
        with d, lr, sr as mock_save:
            _mod.delete_song(norm)
        saved = mock_save.call_args[0][0]
        self.assertNotIn(norm, saved)
        self.assertIn("/other/x.mp3", saved)


if __name__ == "__main__":
    unittest.main()
