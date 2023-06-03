from ProblemData import ProblemData
from Solution import Solution


def greedy(data: ProblemData):
    """
    Finds the greedy coloring of G.
    """
    coloring: dict[int, int] = {}
    colors = set(range(data.num_nodes))

    for node in data.nodes:
        neighbor_colors = set()

        for neighbor in data.adjacency_list[node]:
            if neighbor in coloring:
                neighbor_colors.add(coloring[neighbor])

        # Assign the smallest color not used by any neighbor.
        coloring[node] = min(colors - neighbor_colors)

    return Solution(coloring)
