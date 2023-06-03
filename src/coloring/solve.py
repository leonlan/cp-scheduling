import argparse
from pathlib import Path

from cp import cp
from greedy import greedy
from ProblemData import ProblemData


def parse_instance(loc: str | Path) -> ProblemData:
    with open(loc, "r") as fh:
        lines = fh.readlines()

    nodes = set()
    edges = []

    for line in lines[1:]:
        u, v = [int(node) for node in line.split()]

        nodes.add(u)
        nodes.add(v)
        edges.append((u, v))

    return ProblemData(nodes, edges)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=str, default="data/gc_4_1")
    parser.add_argument("--algorithm", type=str, default="cp")

    return parser.parse_args()


def main():
    args = parse_args()
    data = parse_instance(Path(args.instance))

    if args.algorithm == "cp":
        model = cp(data)
        model.solve(LogVerbosity="Terse")
    elif args.algorithm == "greedy":
        solution = greedy(data)
        print(f"Number of colors used: {solution.objective()}.")

        max_degree = max(len(nbs) for nbs in data.adjacency_list.values())
        print(f"Maximum vertex degree: {max_degree}.")


if __name__ == "__main__":
    main()
