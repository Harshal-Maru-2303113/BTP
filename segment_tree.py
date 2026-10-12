"""
Segment tree with lazy propagation for range-add / range-max queries.

Used by the demodulation tracker to maintain Ω(t) – the number of
concurrent transmissions at each millisecond slot.

Operations
----------
range_add(l, r, val)   – add *val* to every element in [l, r]
range_max(l, r)        – return max element in [l, r]
"""


class SegmentTree:
    """Max segment tree with lazy propagation over integer domain [0, n-1]."""

    __slots__ = ("n", "tree", "lazy")

    def __init__(self, n: int):
        self.n = n
        self.tree = [0] * (4 * n)
        self.lazy = [0] * (4 * n)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _push_down(self, node: int):
        if self.lazy[node] != 0:
            for child in (2 * node, 2 * node + 1):
                self.tree[child] += self.lazy[node]
                self.lazy[child] += self.lazy[node]
            self.lazy[node] = 0

    def _update(self, node: int, start: int, end: int,
                l: int, r: int, val: int):
        if r < start or end < l:
            return
        if l <= start and end <= r:
            self.tree[node] += val
            self.lazy[node] += val
            return
        self._push_down(node)
        mid = (start + end) // 2
        self._update(2 * node, start, mid, l, r, val)
        self._update(2 * node + 1, mid + 1, end, l, r, val)
        self.tree[node] = max(self.tree[2 * node], self.tree[2 * node + 1])

    def _query(self, node: int, start: int, end: int,
               l: int, r: int) -> int:
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return self.tree[node]
        self._push_down(node)
        mid = (start + end) // 2
        return max(
            self._query(2 * node, start, mid, l, r),
            self._query(2 * node + 1, mid + 1, end, l, r),
        )

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def range_add(self, l: int, r: int, val: int = 1):
        """Add *val* to every position in closed interval [l, r]."""
        l = max(l, 0)
        r = min(r, self.n - 1)
        if l > r:
            return
        self._update(1, 0, self.n - 1, l, r, val)

    def range_max(self, l: int, r: int) -> int:
        """Return the maximum value in closed interval [l, r]."""
        if l > r:
            return 0
        l = max(l, 0)
        r = min(r, self.n - 1)
        return self._query(1, 0, self.n - 1, l, r)

    def reset(self):
        """Zero out the entire tree."""
        self.tree = [0] * (4 * self.n)
        self.lazy = [0] * (4 * self.n)
