#!/usr/bin/env python3
from __future__ import annotations

import argparse
import bisect
import sys

from compile import ACTrie
from search import TextSearch


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Usage mirrors fgrep::

        cli.py [-e PATTERN ...] [-f PATTERNS_FILE] CORPUS_FILE

    ``-e`` may be repeated.  ``-f`` reads one pattern per line.
    ``CORPUS_FILE`` may be ``-`` to read from stdin.
    """
    parser = argparse.ArgumentParser(
        description="fgrep-style multi-pattern search powered by Aho-Corasick."
    )
    parser.add_argument(
        "-e",
        dest="patterns",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Pattern to search for (repeatable).",
    )
    parser.add_argument(
        "-f",
        dest="patterns_file",
        metavar="PATTERNS_FILE",
        help="Read patterns from file, one per line.",
    )
    parser.add_argument(
        "corpus",
        metavar="CORPUS_FILE",
        help="File to search; '-' reads from stdin.",
    )
    return parser.parse_args()


def collect_patterns(args: argparse.Namespace) -> list[str]:
    """Assemble the pattern list from ``-e`` flags and/or a ``-f`` file.

    Exits with status 2 if no patterns were supplied.  Blank lines
    in the patterns file are skipped.
    """
    patterns: list[str] = list(args.patterns)
    if args.patterns_file:
        with open(args.patterns_file, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.rstrip("\r\n")
                if line:
                    patterns.append(line)
    if not patterns:
        print("error: at least one pattern required (use -e or -f)", file=sys.stderr)
        sys.exit(2)
    return patterns


def read_corpus(path: str) -> str:
    """Read the entire corpus from a file path, or stdin when ``path == '-'``."""
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def line_starts(text: str) -> list[int]:
    r"""Return the sorted list of character offsets at which each line begins.

    For text ``"ab\ncd\nef"``::

        offsets: 0  1  2  3  4  5  6  7
        chars:   a  b \n  c  d \n  e  f
        starts: [0,       3,       6]

    ``bisect_right(starts, pos) - 1`` then yields the 0-based line
    index containing offset ``pos``.
    """
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def position_to_line_col(starts: list[int], pos: int) -> tuple[int, int]:
    """Convert a 0-based character offset into (1-based line, 1-based column).

    Uses the precomputed line-start table from :func:`line_starts`.
    """
    idx = bisect.bisect_right(starts, pos) - 1
    return idx + 1, pos - starts[idx] + 1


def main() -> int:
    """Glue everything together.

    Reads patterns and corpus, compiles the trie, runs the search,
    and prints one ``line:col:pattern`` per match, sorted by line
    then column.
    """
    args = parse_args()
    patterns = collect_patterns(args)
    corpus = read_corpus(args.corpus)
    trie = ACTrie(patterns)
    matches = TextSearch(corpus, trie).search()
    starts = line_starts(corpus)

    rows: list[tuple[int, int, str]] = []
    for pattern_index, ends in matches.items():
        pattern = patterns[pattern_index]
        length = len(pattern)
        for end_pos in ends:
            start_pos = end_pos - length + 1
            line, col = position_to_line_col(starts, start_pos)
            rows.append((line, col, pattern))
    rows.sort()
    for line, col, pattern in rows:
        print(f"{line}:{col}:{pattern}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
