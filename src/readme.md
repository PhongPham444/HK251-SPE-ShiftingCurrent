
# src/ — Developer README (detailed)

This document describes the implementation details in the `src/` folder: the public interfaces, data shapes, how the simulation is composed, and how CSV outputs are produced. It is intended for developers who will read or extend the simulation code. It intentionally does not repeat the project-level overview in the top-level README.

## High-level flow

1. The simulation environment is a `simpy.Environment()` instance created by `sim_engine`.
2. `QueueNode` objects represent service stations (registration, doctor, lab, pharmacy). Each node uses a `simpy.Resource` with a configured number of `servers`.
3. An `arrival_generator` process produces patients with exponential inter-arrival times (Poisson arrivals) and starts a registration process for each patient.
4. After registration completes, the code chains the patient to the doctor and then to an optional lab (with probability `p_lab`) before the pharmacy. The chain is implemented in the engine by wrapping the registration serve function.
5. `Metrics` collects patient objects and node areas to compute per-patient and per-node metrics and writes CSVs.

## Files and public interfaces

- `config.py`
	- Exposes a `config` dict. Key fields:
		- `arrival_rate` (float): external arrival rate (lambda).
		- `routing.p_lab` (float): probability of visiting the lab after the doctor.
		- `nodes`: mapping of node name to `{ 'service_rate': mu, 'servers': c }`.
		- Defaults for run/warmup/replications.

- `arrival.py`
	- Function: `arrival_generator(env, arrival_rate, registration_node, metrics, max_arrivals=None)`
		- Runs as a process: waits `random.expovariate(arrival_rate)` between arrivals, creates `Patient` objects and calls `env.process(registration_node.serve(patient))`.
		- Calls `metrics.add_patient(patient)` for later processing.

- `patient.py`
	- Class: `Patient(id: int, arrival_time: float)`
		- `timestamps` dict stores standardized keys: `<node>_arrival`, `<node>_service_start`, `<node>_service_end`.
		- Methods: `record_arrival(node, t)`, `record_service_start(node, t)`, `record_service_end(node, t)`, `get(key)`, `exit_time()` (pharmacy end if present, else doctor end).

- `queue_node.py`
	- Class: `QueueNode(env, name, service_rate, servers)`
		- Public methods:
			- `serve(patient)` — generator to yield resource request and service time. Records patient timestamps and updates internal area integrals.
			- `finalize(sim_end_time)` — adjust area integrals to account for the tail interval until `sim_end_time`.
			- `avg_queue_length(effective_time)`, `avg_in_service(effective_time)`, `utilization(effective_time)` — return time-average metrics.
		- Behavior:
			- Uses `self.resource = simpy.Resource(env, capacity=servers)`.
			- Maintains `queue_area` and `busy_area` by calling `_update_areas()` at state changes.
			- Service time is sampled via `_sample_service_time()` which uses `random.expovariate(self.service_rate)`.

- `router.py`
	- `route_after_doctor(env, patient, lab_node, pharmacy_node, p_lab)`
		- Generator that yields `lab_node.serve(patient)` if random draw < `p_lab`, then yields `pharmacy_node.serve(patient)`.

- `metrics.py` (class `Metrics`)
	- Constructor: `Metrics(nodes: Dict[str, QueueNode], warmup_time: float, run_time: float, output_dir: str)`
	- Responsibilities:
		- `add_patient(patient)` — store created patients.
		- `_patients_after_warmup()` — return patients whose `registration_arrival` >= warmup_time.
		- `finalize_nodes(sim_end_time)` — call `finalize` on each node so area integrals reflect the full measured interval.
		- `compute_node_metrics()` — compute per-node waiting/service/response means using patient timestamps; also query node `avg_queue_length`, `avg_in_service`, `utilization`, and `completed_jobs`.
		- `compute_overall_metrics()` — compute system-level metrics E[w], E[R] from patient timestamps.
		- `write_per_patient_csv(filepath, workload, rep, seed)` and `write_per_node_csv(filepath, workload, rep, seed)` — write CSV files. (See CSV schema below.)

- `sim_engine.py`
	- `run_once(run_time, warmup_time, seed, out_dir, workload_name='default')`:
		- Builds `QueueNode` instances from `config['nodes']`.
		- Creates `Metrics` and starts `arrival_generator`.
		- Wraps `registration.serve` to chain `doctor` and `router` calls (this is a simple chaining approach; see notes below).
		- Runs the env until `warmup_time + run_time` and calls `metrics.finalize_nodes(sim_end_time)`.
		- Returns the `Metrics` instance for caller to write CSVs or inspect.
	- `run_experiment(run_time, warmup_time, replications, base_seed, output_dir, workload_name='default')`:
		- Runs multiple replications, saves per-patient and per-node CSVs per replication and a summary CSV that aggregates metrics across replications.

## CSV schemas (developer-facing)

- Per-patient CSV (one row per patient included after warmup):
	- workload, rep, seed, patient_id, arrival_time,
	- reg_arrival, reg_service_start, reg_service_end,
	- doc_arrival, doc_service_start, doc_service_end,
	- lab_arrival, lab_service_start, lab_service_end,
	- phar_arrival, phar_service_start, phar_service_end,
	- exit_time

- Per-node CSV (one row per node per replication):
	- workload, rep, seed, node_name, servers, mu, lambda_effective,
	- mean_waiting_time, mean_service_time, mean_response_time,
	- avg_queue_length_timeavg, avg_in_service_timeavg, utilization, num_completed_jobs

- Summary CSV (aggregated across replications):
	- Each row: metric, mean, std, ci_low, ci_high, n_rep (e.g., E[w], E[R]).

## Warmup and time measurement

- The engine runs until `sim_end_time = warmup_time + run_time` and `Metrics.finalize_nodes(sim_end_time)` must be called to ensure node area integrals include the final interval.
- Warmup exclusion: metrics include only patients whose `registration_arrival` >= `warmup_time`.

## Assumptions and limitations

- Service times are exponential and generated via the `random` module (`random.expovariate`). If reproducible streams for different components are required, consider using dedicated RNG instances.
- The current chaining of node visits uses a monkey-patch wrapper around `registration.serve`. That works for the simple flow here but is brittle if you later change `QueueNode.serve` signature. Consider refactoring to an explicit router or passing `next` handlers.
- `lambda_effective` in per-node CSV is estimated via visit ratios inside `metrics` (caller may prefer to supply external arrival rate for some nodes).

## Extension ideas (quick wins)

- Replace the wrapper-based chaining with a Router class or explicit next node parameter on `serve`.
- Add unit/smoke tests under `tests/` that call `run_once` with a fixed seed and short run_time and assert CSV headers and non-empty outputs.
- Make service-time distribution pluggable (pass a sampler function into `QueueNode`).
- Add logging or debug hooks to dump per-patient timelines for troubleshooting.
