# autoresearch program template

This file is a template for the `program.md` that will live in the real
use-case repo.

Its job is to define the operating contract for the autonomous research agent:

- what problem it is optimizing
- which files are in scope
- which files are fixed
- which benchmark harness is authoritative
- how one experiment is run
- how keep/discard decisions are made
- how results are logged for later analysis

Replace every placeholder with concrete details for the workload. Do not leave
template markers behind in the final generated file.

## Mission

This is an experiment to have the agent improve `<SYSTEM_OR_WORKLOAD_NAME>`.

Primary objective:
- optimize `<PRIMARY_METRIC>`

Success criterion:
- `<PRIMARY_METRIC>` should move in the desired direction (`lower is better` or `higher is better`)
- each experiment must finish within `<TIME_BUDGET>`
- the code must remain readable and maintainable

Secondary constraints:
- `<MEMORY_OR_COST_CONSTRAINT>`
- `<LATENCY_OR_RUNTIME_CONSTRAINT>`
- `<ANY_SAFETY_OR_PRODUCT_CONSTRAINT>`

## Benchmark Harness

All official evaluation must go through a fixed benchmark script:

- benchmark script: `<BENCHMARK_SCRIPT>`
- smoke profile command: `<SMOKE_COMMAND>`
- measure profile command: `<MEASURE_COMMAND>`

Requirements for the benchmark harness:

- it stays fixed during the experiment loop
- it runs the mutable target code as a subprocess
- it writes raw logs to a file
- it prints a small stable summary at the end
- it exits non-zero on failure
- the `measure` profile is the only source of truth for keep/discard decisions

Do not evaluate changes with ad hoc commands once the benchmark harness exists.

## In-Scope Files

Read these files before doing any work:

- `<FILE_1>`: `<why it matters>`
- `<FILE_2>`: `<why it matters>`
- `<FILE_3>`: `<why it matters>`
- `<BENCHMARK_SCRIPT>`: fixed benchmark contract

Mutable files:
- `<MUTABLE_FILE_1>`
- `<MUTABLE_FILE_2>`

Fixed files:
- `<FIXED_FILE_1>`
- `<FIXED_FILE_2>`

Never change the fixed files once the run starts unless the human explicitly
resets the contract.

## Setup

Before starting the experiment loop:

1. Use a run tag based on the date or task name.
2. Create a fresh branch: `autoresearch/<tag>`.
3. Verify the required assets exist:
   - `<DATA_OR_CACHE_CHECK>`
   - `<MODEL_OR_BINARY_CHECK>`
   - `<ENVIRONMENT_CHECK>`
   - `<READ_THE_MUST_READ_FILES>`
4. Run the smoke profile once to verify the benchmark harness and environment.
5. Create `results.tsv` if it does not exist, with this header (`<CAN_MODIFY_BASED_ON_TASK>`):

```tsv
commit	metric	memory	status	description
```

6. Run the measure profile once with no code changes.
7. Record the baseline in `results.tsv`.
8. Confirm the setup is valid, then begin the loop.

## Experiment Contract

Each experiment should be one coherent idea. Avoid mixing unrelated changes.

Allowed changes:
- architecture or algorithm changes inside `<MUTABLE_FILE_1>`
- hyperparameter or prompt adjustments inside `<MUTABLE_FILE_2>`
- simplifications that remove complexity without harming the metric

Disallowed changes:
- changing the evaluation definition
- changing the logging format
- changing the time budget or stopping rule without explicit approval
- adding complexity that cannot be justified by measurable gains

Guiding principles:
- keep experiments small enough that the outcome is attributable
- prefer simple wins over clever hacks
- treat crashes as signal, not as progress
- preserve reproducibility: commit before each run and log every outcome
- use the benchmark harness as the measurement boundary, not the mutable script

## Run Commands

All benchmarked experiments should go through the fixed harness.

Run the smoke profile first when needed:

```bash
<SMOKE_COMMAND> > smoke.log 2>&1
```

Official measurements use:

```bash
<MEASURE_COMMAND> > run.log 2>&1
```

After the run:

```bash
<EXTRACT_METRIC_COMMAND>
<EXTRACT_MEMORY_COMMAND>
```

If the run crashes:

```bash
tail -n 50 run.log
```

## Result Format

Append one tab-separated row to `results.tsv` for every experiment:

```tsv
commit	metric	memory	status	description
```

Field meanings:
- `commit`: short git hash
- `metric`: numeric result, or a sentinel value on crash
- `memory`: peak resource use in a single comparable unit
- `status`: `keep`, `discard`, or `crash`
- `description`: one-line summary of the idea being tested

Optional extra columns are allowed if the workload needs them, but keep the
schema stable once the run starts.

Example:

```tsv
commit	metric	memory	status	description
a1b2c3d	0.123456	12.3	keep	baseline
b2c3d4e	0.120100	12.8	keep	increase context mixing depth
c3d4e5f	0.125900	12.2	discard	switch scheduler
d4e5f6g	0.000000	0.0	crash	double hidden width caused OOM
```

## Keep/Discard Rule

Keep a change only if:
- the run completed successfully
- the metric improved according to the optimization direction
- the complexity cost is justified
- `<ANY_OTHER_CORRECTNESS_CHECK>`

Discard a change if:
- the metric regressed
- the gain is too small relative to the added complexity
- the run became unstable or materially more expensive without enough benefit
- `<ANY_OTHER_CORRECTNESS_CHECK>`

## Loop

Once the loop begins, continue until interrupted:

1. Inspect the current git state.
2. Choose one next experiment.
3. Edit only the mutable files.
4. Commit the change.
5. Run the smoke profile if the change is risky or likely to crash.
6. Run the measure profile and capture logs.
7. Extract the metric and resource usage from the benchmark summary.
8. Log the result to `results.tsv`.
9. Keep the commit if it wins; otherwise revert to the last kept commit. In the commit history, only accepted commits should remain.
10. Move to the next idea immediately.

Do not pause to ask whether to continue once autonomous execution has started.
