import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compile import ACTrie
from search import TextSearch


class ACTrieTests(unittest.TestCase):
    def _run(self, patterns, text):
        trie = ACTrie(patterns)
        return TextSearch(text, trie).search()

    def test_overlapping_suffix_patterns(self):
        result = self._run(["a", "aa", "aaa", "aaaa"], "aaaa")
        self.assertEqual(result[0], [0, 1, 2, 3])
        self.assertEqual(result[1], [1, 2, 3])
        self.assertEqual(result[2], [2, 3])
        self.assertEqual(result[3], [3])

    def test_classic_ushers_example(self):
        result = self._run(["he", "she", "his", "hers"], "ushers")
        self.assertEqual(result.get(0), [3])
        self.assertEqual(result.get(1), [3])
        self.assertNotIn(2, result)
        self.assertEqual(result.get(3), [5])

    def test_non_matching_pattern_absent(self):
        result = self._run(["cat", "dog"], "the cat sat")
        self.assertIn(0, result)
        self.assertNotIn(1, result)
        self.assertEqual(result[0], [6])

    def test_disjoint_repeated_hits(self):
        result = self._run(["ab"], "ababab")
        self.assertEqual(result[0], [1, 3, 5])

    def test_prefix_pattern_also_matches(self):
        result = self._run(["he", "hello"], "hello")
        self.assertEqual(result[0], [1])
        self.assertEqual(result[1], [4])

    def test_empty_pattern_rejected(self):
        with self.assertRaises(ValueError):
            ACTrie([""])

    def test_empty_pattern_list_rejected(self):
        with self.assertRaises(ValueError):
            ACTrie([])

    def test_no_matches_returns_empty_dict(self):
        result = self._run(["xyz"], "abcdef")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
