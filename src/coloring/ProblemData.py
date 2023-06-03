from collections import defaultdict
from dataclasses import dataclass


@dataclass
class ProblemData:
    nodes: list[int]
    edges: list[tuple[int, int]]

    def __post_init__(self):
        self.num_nodes = len(self.nodes)
        self.num_edges = len(self.edges)
        self.adjacency_list = make_adjacency_list(self.edges)


def make_adjacency_list(edges: list[list[int]]) -> dict[int, set]:
    adjacency_list = defaultdict(set)

    for u, v in edges:
        adjacency_list[u].add(v)
        adjacency_list[v].add(u)

    return adjacency_list
