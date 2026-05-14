"""Unit tests for library_ratings module."""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import acestep.ui.gradio.events.library_ratings as _mod


class LoadRatingsTests(unittest.TestCase):
    """Tests for load_ratings."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._path = os.path.join(self._tmp, "ratings.json")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _patch_file(self):
        return patch.object(_mod, "RATINGS_FILE", self._path)

    def test_missing_file_returns_empty(self):
        with self._patch_file():
            self.assertEqual(_mod.load_ratings(), {})

    def test_corrupt_json_returns_empty(self):
        with open(self._path, "w") as f:
            f.write("not-valid-json!")
        with self._patch_file():
            self.assertEqual(_mod.load_ratings(), {})

    def test_non_dict_json_returns_empty(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)
        with self._patch_file():
            self.assertEqual(_mod.load_ratings(), {})

    def test_valid_ratings_returned(self):
        data = {"/path/song.mp3": 4, "/path/other.flac": 2}
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        with self._patch_file():
            self.assertEqual(_mod.load_ratings(), data)


class SaveRatingsTests(unittest.TestCase):
    """Tests for save_ratings."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._path = os.path.join(self._tmp, "ratings.json")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _patch(self):
        return patch.multiple(
            _mod,
            RATINGS_FILE=self._path,
            DEFAULT_RESULTS_DIR=self._tmp,
        )

    def test_round_trip(self):
        data = {"/a/b.mp3": 5, "/c/d.flac": 1}
        with self._patch():
            _mod.save_ratings(data)
            self.assertEqual(_mod.load_ratings(), data)

    def test_no_tmp_file_left(self):
        with self._patch():
            _mod.save_ratings({"x": 3})
        leftovers = [f for f in os.listdir(self._tmp) if f.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_empty_dict_writes_valid_json(self):
        with self._patch():
            _mod.save_ratings({})
        with open(self._path, encoding="utf-8") as f:
            self.assertEqual(json.load(f), {})

    def test_unicode_keys_preserved(self):
        data = {"/music/track.mp3": 3}
        with self._patch():
            _mod.save_ratings(data)
            self.assertEqual(_mod.load_ratings(), data)


if __name__ == "__main__":
    unittest.main()
