from __future__ import annotations

import unittest

from model.api_paths import append_query_params, path_variants


class ApiPathsTests(unittest.TestCase):
    def test_append_query_params_preserves_existing_query(self) -> None:
        path = append_query_params("/weather/?sort=desc", limit=25)
        self.assertEqual(path, "/weather/?sort=desc&limit=25")

    def test_path_variants_keep_query_before_trailing_slash_switch(self) -> None:
        variants = path_variants("/weather?limit=10")
        self.assertEqual(variants[0], "/weather?limit=10")
        self.assertEqual(variants[1], "/weather/?limit=10")


if __name__ == "__main__":
    unittest.main()
