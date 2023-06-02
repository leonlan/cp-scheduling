# Graph coloring

## Problem description
In the graph coloring problem, the goal is to color a graph's nodes with as few colors as possible such two adjacent nodes do not share the same color.

Formally, consider a graph $G=(V,E)$ with nodes $V=\{1, \dots, n\}$ and edges $E$, let variable $C_i \in \mathbb{N}$ denote the color of node $i \in V$.
The graph coloring problem can now be formulated as the following optimization problem:

\begin{align}
    \min & \max_{i \in \{1, \dots, n\}} C_{i} \\
    \text{s.t. } & C_{i} \ne C_j & \quad \forall (i, j) \in E. 
\end{align}


## Constraint programming

::: src.coloring.cp


## Background information

TODO

coursera.org/learn/discrete-optimization/home/week/3
