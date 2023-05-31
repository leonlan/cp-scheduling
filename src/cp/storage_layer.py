import itertools
from dataclasses import dataclass

import docplex.cp.model as docp
import numpy as np


@dataclass
class ProblemData:
    products: list
    batches: list
    lines: list
    machines: list
    eligible: np.ndarray
    product2batch: np.ndarray
    batch_start: np.ndarray
    batch_end: np.ndarray


def storage_layer(data):
    """
    Creates a storage layer CP model.
    """
    model = docp.CpoModel()

    batches_tasks = create_batch_tasks(model, data)
    tasks = create_product_tasks(model, data)
    assignments = create_product_assignments(model, data)
    sequences = create_sequence_variables(data, model, assignments)

    assign_one_line(data, model, tasks, assignments)
    assign_only_eligible_lines(data, model, assignments)

    products_span_batches(data, model, tasks, batches_tasks)
    no_overlap_on_machines(data, model, sequences)

    return model


def create_batch_tasks(model, data):
    """
    Creates a task interval variable $T_{b}$ for each batch $b \\in B$.
    """
    tasks = {}
    for b in data.batches:
        var = model.interval_var(name=f"T_{b}")

        # Set start and end min/max for batches since we don't have any
        # intra-stage precedence constraints.
        var.set_start_min(data.batch_start[b])
        var.set_end_min(data.batch_end[b])

        tasks[b] = var
    return tasks


def create_product_tasks(model, data):
    """
    Creates a task interval variable $Tp_{p}$ for each product $p \\in P$.
    """
    tasks = {p: model.interval_var(name=f"Tp_{p}") for p in data.products}
    return tasks


def create_product_assignments(model, data):
    """
    Creates an assignment interval variable $Tp_{pu}$ for each product
    $p \\in P$ and machine $i \\in M$.
    """
    assignments = {}

    for p, i in itertools.product(data.products, data.machines):
        name = f"Ap_{p}_{i}"
        assignments[(p, i)] = model.interval_var(name=name, optional=True)

    return assignments


def create_sequence_variables(data, model, assignments):
    """
    Creates a sequence variable $Sp_{i}$ for each machine $i \\in M$.
    """
    Sp = {}

    for i in data.machines:
        intervals = [assignments[(product, i)] for product in data.products]
        name = f"Sp_{i}"
        Sp[i] = model.sequence_var(intervals, name=name)

    return Sp


def assign_one_line(data, model, tasks, assignments):
    """
    Assigns each product to exactly one machine.

    \\begin{equation}
        \\texttt{Alternative}(Tp_{p}, \\{Ap_{pi} : i \\in M \\})
        \\quad \\forall p \\in P.
    \\end{equation}
    """
    for j in data.products:
        intervals = [assignments[(j, i)] for i in data.machines]
        model.add(model.alternative(tasks[j], intervals))


def assign_only_eligible_lines(data, model, assign):
    """
    Assigns each product to only eligible machines.

    \\begin{equation}
        \\texttt{PresenceOf}(A_{pi}) = 0,
        \\quad \\forall i \\in M, p \\in E_{i}.
    \\end{equation}
    """
    for job, line in itertools.product(data.products, data.lines):
        if not data.eligible[job][line]:
            cons = model.presence_of(assign[(job, line)]) == 0
            model.add(cons)


def products_span_batches(data, model, product_tasks, batches_tasks):
    """
    Product interval variables span the corresponding batch interval variables.

    \\begin{equation}
        \\texttt{Span}(Tp_{p}, \\{T_{b} : b \\in B_p \\})
        \\quad \\forall p \\in P,
    \\end{equation}

    where $B_p$ denotes the set of batches that belong to product $p$.
    """
    for product in data.products:
        batches = [
            batches_tasks[batch]
            for batch in data.batches
            if data.product2batch[product][batch]
        ]
        product = product_tasks[product]
        cons = model.span(product, batches)

        model.add(cons)


def no_overlap_on_machines(data, model, sequences):
    """
    No overlap on machines.

    \\begin{equation}
        \\texttt{NoOverlap}(Sp_{i}) \\quad \\forall i \\in M.
    \\end{equation}
    """
    for machine in data.machines:
        model.add(model.no_overlap(sequences[machine]))


if __name__ == "__main__":
    products = [0, 1, 2]
    batches = [0, 1, 2, 3, 4, 5]
    lines = [0, 1]
    machines = [0, 1]
    eligible = np.ones((len(products), len(lines)), dtype=bool)

    product2batch = np.zeros((len(products), len(batches)), dtype=bool)
    product2batch[0, [0, 1]] = True
    product2batch[1, [2, 3]] = True
    product2batch[2, [4, 5]] = True
    print(product2batch)

    batch_start = [1, 4, 1, 2, 8, 10]
    batch_end = [2, 8, 2, 3, 10, 12]

    data = ProblemData(
        products=products,
        batches=batches,
        lines=lines,
        machines=machines,
        eligible=eligible,
        product2batch=product2batch,
        batch_start=batch_start,
        batch_end=batch_end,
    )

    model = storage_layer(data)
    result = model.solve(TimeLimit=10, LogVerbosity="Terse")

    for product in data.products:
        interval = result.get_var_solution(f"Tp_{product}")
        print(
            f"Product {product} starts at {interval.get_start()} and ends at {interval.get_end()}"
        )

    for batch in data.batches:
        interval = result.get_var_solution(f"T_{batch}")
        print(
            f"Batch {batch} starts at {interval.get_start()} and ends at {interval.get_end()}"
        )
