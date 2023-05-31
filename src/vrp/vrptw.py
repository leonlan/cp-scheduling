from dataclasses import dataclass
from itertools import product
from typing import Dict

import docplex.cp.model as docp
import numpy as np
from vrplib import read_instance


@dataclass
class ProblemData:
    num_vehicles: int
    capacity: int
    num_locations: int
    edge_weights: np.ndarray
    service_time: np.ndarray
    time_windows: np.ndarray
    demand: np.ndarray

    def __post_init__(self):
        self.vehicles = range(self.num_vehicles)
        self.clients = range(1, self.num_locations - 1)
        self.locations = range(self.num_locations)


def instance2data(instance: Dict) -> ProblemData:
    """
    Transforms an instance dictionary into a ProblemData object.

    In the CP model, we assume that there is an n+1-th location that is the
    depot. We only need it for the edge weights.
    """
    num_locs = instance["demand"].size + 1
    distance_matrix = np.zeros((num_locs, num_locs))
    distance_matrix[:-1, :-1] = instance["edge_weight"]

    for idx in range(num_locs - 1):
        # From end depot to all other locations is the same as from the
        # start depot to all other locations
        distance_matrix[num_locs - 1, idx] = instance["edge_weight"][0, idx]
        distance_matrix[idx, num_locs - 1] = instance["edge_weight"][idx, 0]

    # DIMACS convention: scale all time durations by 10 and truncate
    distance_matrix = np.floor(distance_matrix * 10).astype(int)
    service_times = instance["service_time"] * 10
    time_windows = instance["time_window"] * 10

    return ProblemData(
        num_vehicles=instance["vehicles"],
        capacity=instance["capacity"],
        num_locations=num_locs,
        edge_weights=distance_matrix,
        service_time=service_times,
        time_windows=time_windows,
        demand=instance["demand"],
    )


def vehicle_routing_problem_time_windows(data: ProblemData) -> docp.CpoModel:
    """
    Creates a CP model for the Vehicle Routing Problem with Time Windows
    (VRPTW) based on the formulation presented in [Laborie2018].

    # TODO figure out how the referencing works in mkdocstrings
    References
    ----------
    [Laborie2018]: https://doi.org/10.1007/s10601-018-9281-x
    Laborie, P., Rogerie, J., Shaw, P., & Vilím, P. (2018).
    IBM ILOG CP optimizer for scheduling. Constraints, 23(2), 210–250.
    """
    model = docp.CpoModel()

    visits = create_visit_variables(model, data)
    vvisits = create_vehicle_visit_variables(model, data)
    routes = create_route_variables(model, data, vvisits)

    minimize_total_travel_time(model, data, vvisits)

    no_overlap_between_visits(model, data, routes)
    routes_start_and_end_at_depot(model, data, vvisits, routes)
    assign_each_client_to_one_vehicle(model, data, visits, vvisits)

    # TODO capacity constraints

    return model


def create_visit_variables(model, data):
    """
    Creates the visit variables $T_{i}$ for each client $i \\in V$.

    A visit variable is an interval variable that represents the time that
    is spent at a client location to perform the service. This does not
    include the travel time to the client location.
    """
    visits = {}

    for client in data.clients:
        service_time = data.service_time[client]
        var = model.interval_var(name=f"T_{client}", size=service_time)

        # Set time window constraints on visit variables
        tw_early, tw_late = data.time_windows[client]
        var.set_start_min(tw_early)
        var.set_end_max(tw_late + service_time)

        visits[client] = var

    return visits


def create_vehicle_visit_variables(model, data):
    """
    Creates the optional vehicle visit variables $V_{ik}$ for each vehicle
    $k \\in K$ and location $i \\in N$ (including depots!).
    """
    vvisits = {}

    for vehicle, location in product(data.vehicles, data.locations):
        var = model.interval_var(name=f"T_{vehicle}_{location}", optional=True)
        vvisits[(vehicle, location)] = var

    return vvisits


def create_route_variables(model, data, vvisits):
    """
    Creates the route variables $R_{k}$ for each vehicle $k \\in K$.

    A route variable is a sequence variable that represents the order in
    which the vehicle visits the clients.
    """
    routes = {}

    for vehicle in data.vehicles:
        intervals = [vvisits[(vehicle, loc)] for loc in data.locations]
        routes[vehicle] = model.sequence_var(intervals, name=f"R_{vehicle}")

    return routes


def minimize_total_travel_time(model, data, vvisits):
    """
    Minimizes the total travel time of all vehicles. This excludes the service
    time at the clients, but includes possible waiting times.
    # TODO how can we remove waiting times?

    \\begin{equation}
        \\min \\sum_{k \\in K} \\texttt{EndOf}(V_{k, n+1})
        - \\sum_{i \\in V} D_{i}.
    \\end{equation}
    """
    last = data.num_locations - 1
    completion_times = [
        model.end_of(vvisits[(k, last)]) for k in data.vehicles
    ]
    service_times = [data.service_time[i] for i in data.clients]
    model.minimize(model.sum(completion_times) - model.sum(service_times))


def no_overlap_between_visits(model, data, routes):
    """
    This constraint ensures that no visits overlap in time, and that
    travel time between visits is respected.

    \\begin{equation}
        \\texttt{NoOverlap}(R_{k}, D),
        \\quad \\forall k \\in K,
    \\end{equation}

    where $D$ is the matrix of travel times between visits.
    """
    for vehicle in data.vehicles:
        model.add(model.no_overlap(routes[vehicle], data.edge_weights))


def routes_start_and_end_at_depot(model, data, vvisits, routes):
    """
    This constraint ensures that each route starts and ends at the depot.

    \\begin{align}
        \\texttt{PresenceOf}(V_{0k}) = 1,
            & \\quad \\forall k \\in K, \\\\
        \\texttt{PresenceOf}(V_{n+1,k}) = 1,
            & \\quad \\forall k \\in K, \\\\
        \\texttt{First}(R_{k}, V_{0k}),
            & \\quad \\forall k \\in K, \\\\
        \\texttt{Last}(R_{k}, V_{n+1,k}),
            & \\quad \\forall k \\in K.
    \\end{align}

    """
    for vehicle in data.vehicles:
        start_depot = 0
        first_visit = vvisits[(vehicle, start_depot)]

        cons = model.presence_of(first_visit) == 1
        model.add(cons)

        end_depot = data.num_locations - 1
        last_visit = vvisits[(vehicle, end_depot)]

        cons = model.presence_of(last_visit) == 1
        model.add(cons)

        cons = model.first(routes[vehicle], first_visit)
        model.add(cons)

        cons = model.last(routes[vehicle], last_visit)
        model.add(cons)


def assign_each_client_to_one_vehicle(model, data, visit, vvisits):
    """
    Each client must be assigned to exactly one vehicle.

    \\begin{equation}
        \\texttt{Alternative}(V_{i},\\{ V_{ik} : k \\in K \\}),
        \\quad \\forall i \\in N.
    \\end{equation}
    """
    for client in data.clients:
        optional = [vvisits[(k, client)] for k in data.vehicles]
        model.add(model.alternative(visit[client], optional))


if __name__ == "__main__":
    instance = read_instance("instances/C101.txt", instance_format="solomon")
    data = instance2data(instance)

    model = vehicle_routing_problem_time_windows(data)
    result = model.solve(
        TimeLimit=50,
        LogVerbosity="Terse",
    )

    def result2solution(result):
        solution = []

        for vehicle in data.vehicles:
            route = []

            for interval in result.get_var_solution(
                f"R_{vehicle}"
            ).get_interval_variables():
                route.append(interval.get_name())

            solution.append(route)

        return solution

    solution = result2solution(result)
    print(solution)
