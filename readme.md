
# Hospital Queue Simulation

A small discrete-event simulation of a simple hospital patient flow using SimPy. The project simulates patients arriving to a registration desk, visiting a doctor, optionally visiting a lab, and then finishing at a pharmacy. It collects per-patient and per-node metrics and writes CSV summaries for analysis.

## Features

- Event-driven simulation with configurable arrival and service rates
- Multiple service nodes (registration, doctor, lab, pharmacy) with multiple servers per node
- Routing probability from doctor to lab (configurable)
- Collection of per-patient timestamps and per-node time-average statistics (queue length, utilization)
- Scripts to run single experiments or batches of replications and produce CSV outputs

## Requirements

This project uses Python 3.10+ (tested with 3.11) and the Python libraries listed in `requirements.txt`.

- simpy
- numpy
- pandas

Install dependencies with pip:

```bash
# from the repository root (macOS / zsh)
python -m pip install -r requirements.txt
```

## Quick start — run a demo experiment

There are two simple entry points:

- Run a single experiment programmatically by importing `sim_engine.run_experiment`.
- Run the provided `src/experiments.py` script to run a small set of example workloads.

From the repository root you can run the demo experiments:

```bash
# run the example experiments (creates outputs/results_csv/...)
python src/experiments.py
```

Or run the full experiment runner with custom arguments:

```bash
python src/sim_engine.py --run_time 2000 --warmup_time 200 --replications 3 --seed 1000 --output outputs/results_csv --workload demo
```

Arguments (short):

- `--run_time`: simulation run length after warmup (time units)
- `--warmup_time`: transient warmup period that is excluded from metrics
- `--replications`: number of independent replications
- `--seed`: base RNG seed (individual reps add rep to base)
- `--output`: directory where CSV files will be written
- `--workload`: workload name used in output filenames

## Project structure

Top-level files and important modules (under `src/`):

- `requirements.txt` — project dependencies
- `readme.md` — this file
- `src/config.py` — simulation parameters (arrival rate, nodes, service rates, servers, defaults)
- `src/arrival.py` — arrival process generator and patient creation
- `src/patient.py` — `Patient` object recording per-node timestamps
- `src/queue_node.py` — `QueueNode` class implementing service, area integrals and utilization
- `src/router.py` — routing logic after doctor (probability to visit lab)
- `src/sim_engine.py` — orchestration: build environment, nodes, run replications and write outputs
- `src/metrics.py` — compute per-patient and per-node statistics and write CSVs
- `src/experiments.py` — example batch runner that modifies `config` and calls the engine

Example outputs are written under `outputs/results_csv/` and include three subfolders:

- `per_patient/` — one CSV per replication with per-patient timestamps and exit times
- `per_node_rep/` — one CSV per replication with per-node statistics (wait, service, utilization)
- `summaries/` — aggregated summaries across replications (mean, std, CI) — e.g. `demo_summary.csv`

Files shipped in `outputs/results_csv/` illustrate the output format for a demo run.

## Configuration

Adjust `src/config.py` to change arrival rates, routing probabilities and node service capacities. Example keys:

- `config['arrival_rate']` — external arrival Poisson rate (lambda)
- `config['nodes']` — per-node `service_rate` (mu) and `servers` (c)
- `config['routing']['p_lab']` — probability a patient goes to lab after doctor

The simulation engine uses these values when constructing `QueueNode`s.

## Outputs and how to interpret

- Per-patient CSV: contains arrival time and timestamps for `registration`, `doctor`, `lab` (if visited) and `pharmacy`. Use this to compute patient-level response times and routing counts.
- Per-node CSV: contains mean waiting time, mean service time, time-average queue length, time-average number in service, and utilization for each node over the measured period (after warmup).
- Summary CSV: aggregate statistics across replications such as E[w] (mean waiting time) and E[R] (mean response time) with confidence intervals.

The `src/metrics.py` module computes these metrics; you can modify its behavior to add extra statistics.

## Extending the model

- Add additional nodes in `src/config.py` and adjust routing in `src/router.py`.
- Replace or extend `QueueNode` to change service time distributions or add priority queues.
- Instrument `src/metrics.py` to export other statistics (percentiles, sojourn time distributions, throughput time series).

## Tests and validation

This repository does not include a formal test suite. For quick checks you can run short deterministic runs by setting the seeds and reducing `run_time` / `replications` in `src/experiments.py` or calling `src/sim_engine.run_once` programmatically.

## Notes and assumptions

- Time units are abstract and consistent across arrival and service rates.
- Service times are exponential (via Python's `random.expovariate`) with parameter `service_rate` (mu).
- The warmup mechanism excludes patients with `registration_arrival < warmup_time` from metric aggregation.
