import docplex.cp.model as docp
from ProblemData import ProblemData
from utils import maximum_degree


def cp(data: ProblemData):
    """
    Creates a CP model for the graph coloring problem.
    """
    model = docp.CpoModel()

    colors = [
        model.integer_var(0, data.num_nodes - 1, name=f"C_{i}")
        for i in data.nodes
    ]
    model.minimize(model.max(colors))

    different_colors_adjacent_nodes(data, model, colors)

    greedy_coloring_upper_bound(data, model, colors)

    return model


def different_colors_adjacent_nodes(data, model, colors):
    """
    For any given node, all its adjacent nodes must have different colors.
    This can be implemented using the all different constraint.

    \\begin{equation}
        \\texttt{AllDifferent}(\\{C_j : (i, j) \\in E \\}),
        \\quad \\forall i \\in V.
    \\end{equation}
    """
    for i in data.nodes:
        cons = model.all_diff([colors[j] for j in data.adjacency_list[i]])
        model.add(cons)


def greedy_coloring_upper_bound(data, model, colors):
    """
    An upper bound for the number of colors is the maximum degree of the graph
    plus one.

    \\begin{equation}
        \\max_{i \\in V} C_i \\leq \\Delta(G) + 1
    \\end{equation}
    """
    model.add(model.max(colors) <= maximum_degree(data) + 1)
