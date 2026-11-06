"""Test package version is correctly set."""

import re
import unittest

from scietex.hal.spi.version import __version__


class TestVersion(unittest.TestCase):
    """The distributive exposes a single X.Y.Z version string."""

    def test_version_is_a_string(self) -> None:
        """The version attribute is a string."""
        self.assertIsInstance(__version__, str)

    def test_version_matches_xyz(self) -> None:
        """The version is three dot-separated integers with no padding."""
        self.assertIsNotNone(re.fullmatch(r"\d+\.\d+\.\d+", __version__))

    def test_version_parts_are_non_negative(self) -> None:
        """Every part parses as a non-negative integer."""
        parts = [int(part) for part in __version__.split(".")]
        self.assertEqual(len(parts), 3)
        self.assertTrue(all(part >= 0 for part in parts))
        self.assertGreater(sum(parts), 0)

    def test_no_whitespace(self) -> None:
        """A version never carries stray whitespace."""
        self.assertEqual(__version__, __version__.strip())


if __name__ == "__main__":
    unittest.main()
