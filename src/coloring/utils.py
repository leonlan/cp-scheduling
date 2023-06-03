from ProblemData import ProblemData


def maximum_degree(data: ProblemData):
    """
    Returns the maximum vertex degree of the graph.
    """
    return max(len(neighbors) for neighbors in data.adjacency_list.values())
