from .base_model import base_model
from .constraints.minimize_makespan import minimize_makespan


def FlowShop(data):
    model, tasks, _ = base_model(data)
    minimize_makespan(data, model, tasks)

    return model
