## Greedy coloring algorithm
The greedy coloring algorithm is an iterative method of assigning colors to vertices in a graph. It's a simple and often fast approach to solving the graph coloring problem, with a provable approximation guarantee of $\Delta(G) + 1$ colors, where $\Delta(G)$ denotes the maximum vertex degree of $G$.

The description is as follows.

1. Assign the first color to the first vertex.
2. For each remaining vertex:
    - Assign the smallest possible color within the set of already used colors that is not used by any of its adjacent vertices.
    - If no such color exists, introduce a new color and assign it to the vertex.

## Source code
::: src.coloring.greedy
