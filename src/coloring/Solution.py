class Solution:
    def __init__(self, coloring: dict[int, int]):
        self.coloring = coloring

    def objective(self) -> int:
        return self.num_colors()

    def num_colors(self) -> int:
        return max(self.coloring.values()) + 1
