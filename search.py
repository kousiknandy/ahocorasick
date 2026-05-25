from __future__ import annotations

from compile import ACTrie


class TextSearch:
    """Run a compiled :class:`ACTrie` over an input string and collect matches.

    The result of :meth:`search` is a dict mapping each matching
    pattern's index (its position in the list given to ``ACTrie``)
    to the list of end positions where it occurred, in input
    order.  Patterns that never matched are omitted - the dict is
    not pre-populated with empty lists.
    """

    def __init__(self, text: str, trie: ACTrie):
        """Bind an input string and a compiled automaton."""
        self.text = text
        self.trie = trie

    def search(self) -> dict[int, list[int]]:
        """Stream `text` through the automaton, accumulating matches.

        At each position the automaton advances to a new state and
        every pattern index in ``output[state]`` ends at that
        position.  For text ``"ushers"`` against patterns
        ``["he", "she", "his", "hers"]``::

            text:   u   s   h   e   r   s
            pos:    0   1   2   3   4   5
            state:  0   s   sh  she her hers
            hits:               he      hers
                                she

        and the return value is ``{0: [3], 1: [3], 3: [5]}`` -
        ``"his"`` (index 2) never matches, so it has no entry.
        """
        result: dict[int, list[int]] = {}
        state = 0
        for pos, ch in enumerate(self.text):
            state = self.trie.next_state(state, ch)
            outputs = self.trie.output[state]
            if not outputs:
                continue
            for idx in outputs:
                result.setdefault(idx, []).append(pos)
        return result
