from __future__ import annotations

from collections import deque


class ACTrie:
    """Aho-Corasick automaton compiled from a fixed list of patterns.

    Three parallel arrays index every node by integer id:

        goto[n]   dict mapping char -> child node id
        fail[n]   id of the longest proper suffix of the string
                  spelled by `n` that is itself a trie prefix
        output[n] pattern indices that match when the automaton
                  reaches `n`, including those propagated along
                  fail links so overlapping suffix patterns are
                  reported in a single pass

    Node 0 is the root.
    """

    def __init__(self, patterns: list[str]):
        """Compile the automaton from a non-empty list of non-empty patterns.

        Empty patterns (and an empty list) are rejected because an
        empty pattern would match at every position and is rarely
        what the caller wants.
        """
        if not patterns:
            raise ValueError("patterns must be non-empty")
        for i, p in enumerate(patterns):
            if not p:
                raise ValueError(f"pattern at index {i} is empty")
        self.patterns: list[str] = list(patterns)
        self.goto: list[dict[str, int]] = [{}]
        self.fail: list[int] = [0]
        self.output: list[list[int]] = [[]]
        self._build_trie()
        self._build_failure_links()

    def _new_node(self) -> int:
        """Allocate a fresh node and return its integer id."""
        self.goto.append({})
        self.fail.append(0)
        self.output.append([])
        return len(self.goto) - 1

    def _build_trie(self) -> None:
        """Insert every pattern, growing the trie one character at a time.

        For patterns = ["he", "hers", "his"] the trie looks like
        (before fail-link propagation)::

                       (0)
                        |
                        h
                        v
                       (1)
                       / \\
                      e   i
                      v   v
                     (2)*(5)
                      |   |
                      r   s
                      v   v
                     (3) (6)*
                      |
                      s
                      v
                     (4)*

        `*` marks terminal nodes whose output list is non-empty:
        output[2]=[0] ("he"), output[4]=[1] ("hers"), output[6]=[2]
        ("his").
        """
        for i, pattern in enumerate(self.patterns):
            node = 0
            for ch in pattern:
                nxt = self.goto[node].get(ch)
                if nxt is None:
                    nxt = self._new_node()
                    self.goto[node][ch] = nxt
                node = nxt
            self.output[node].append(i)

    def _build_failure_links(self) -> None:
        """Compute fail[v] for every non-root node and propagate outputs.

        `fail[v]` is the id of the longest proper suffix of the
        string spelled by `v` that is itself a trie prefix.
        Construction is the textbook BFS: for each child `v` of
        `u` reached via char `c`, walk `fail[u]` back through the
        trie until a node with a `c`-transition is found.

        For patterns ["he", "she", "his", "hers"] (node id : prefix)::

            0:""    1:"h"   2:"he"*   3:"s"    4:"sh"
            5:"she"*  6:"hi"  7:"his"*  8:"her"  9:"hers"*

        the interesting fail links are::

            fail[4] = 1     "sh"   suffix "h"  is a trie prefix
            fail[5] = 2     "she"  suffix "he" is a trie prefix
            fail[7] = 3     "his"  suffix "s"  is a trie prefix
            fail[9] = 3     "hers" suffix "s"  is a trie prefix

        Output sets are merged along the fail link
        (``output[v].extend(output[fail[v]])``), so when the scan
        reaches state 5 it emits both "she" *and* "he" at the same
        end position - overlapping matches drop out for free.
        """
        queue: deque[int] = deque()
        for v in self.goto[0].values():
            self.fail[v] = 0
            queue.append(v)
        while queue:
            u = queue.popleft()
            for ch, v in self.goto[u].items():
                queue.append(v)
                f = self.fail[u]
                while f != 0 and ch not in self.goto[f]:
                    f = self.fail[f]
                cand = self.goto[f].get(ch, 0)
                self.fail[v] = cand if cand != v else 0
                self.output[v].extend(self.output[self.fail[v]])

    def next_state(self, state: int, ch: str) -> int:
        """Advance one character: from `state`, on input `ch`, return the
        next state.

        Falls back via fail links until a node with a `ch`
        transition exists; the root absorbs any character that has
        no transition::

            state --ch--> child            direct hit, done
              |
              +--fail--> s' --ch--> child  fallback succeeded
              |
              +--fail--> ... --fail--> 0   no match anywhere
        """
        while state != 0 and ch not in self.goto[state]:
            state = self.fail[state]
        return self.goto[state].get(ch, 0)

    def matches_at(self, state: int, end_pos: int):
        """Yield ``(end_pos, pattern_index, pattern_text)`` for every
        pattern ending at `state` when the input cursor is at
        `end_pos`.
        """
        for idx in self.output[state]:
            yield (end_pos, idx, self.patterns[idx])
