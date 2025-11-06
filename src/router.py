# src/router.py
import random

def route_after_doctor(env, patient, lab_node, pharmacy_node, p_lab: float):
    """
    Route patient after finishing doctor node.
    This function is designed to be called inside a process context (i.e., yield from).
    """
    # decide to go lab or not
    if random.random() < p_lab:
        # go to lab first
        yield env.process(lab_node.serve(patient))
    # then always go to pharmacy
    yield env.process(pharmacy_node.serve(patient))
