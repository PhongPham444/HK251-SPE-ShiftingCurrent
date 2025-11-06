# src/arrival.py
import simpy
import random
from patient import Patient

def arrival_generator(env: simpy.Environment, arrival_rate: float, registration_node, metrics, max_arrivals: int = None):
    """
    Generate patients as a homogeneous Poisson process with rate arrival_rate.
    For each patient, start the registration process (env.process(registration_node.serve(patient))).
    metrics.add_patient will collect patient object for later analysis.
    """
    pid = 0
    while True:
        if arrival_rate <= 0:
            # no arrivals
            break
        ia = random.expovariate(arrival_rate)
        yield env.timeout(ia)
        pid += 1
        p = Patient(pid, env.now)
        metrics.add_patient(p)
        # directly start registration serve process; after registration, patient flow continues in registration's logic
        env.process(registration_node.serve(p))
        if max_arrivals is not None and pid >= max_arrivals:
            break
