# autoresearch template

This repo is a template repo, not a runnable benchmark on its own.

The intended flow is:

1. The human reads this `README.md`.
2. The human points a coding agent at this repo and at their real use-case repo.
3. The agent reads `program.md` and `analysis.py` here as templates.
4. The agent writes three use-case-specific artifacts inside the real repo:
   - a `program.md`
   - an `analysis.py`
   - a fixed benchmark harness script
5. The agent then uses the generated `program.md` to run the autoresearch loop in the real repo.

`program.md` is the template for the experiment contract.

`analysis.py` is the template for passive post-run analysis.

The benchmark harness is the missing third piece. It is the immutable measurement contract that the generated `program.md` should rely on.

## What To Tell The Agent

When you ask an agent to adapt this template to your use case, give it these inputs:

- the goal of the experiment
- a concise summary of the codebase or subsystem being optimized
- the primary metric and whether lower or higher is better
- any secondary metrics worth tracking
- hard constraints such as correctness tests, anti-cheating rules, or budget limits
- which files are mutable and which files must remain fixed
- the command that currently runs the system, training job, benchmark, or evaluation
- any per-run time budget
- available hardware, environment assumptions, and required assets
- anything else you want encoded into the experiment contract

If you already know them, also tell the agent:

- where `results.tsv` should live
- what columns it should contain
- what the benchmark script should print at the end of each run

## What The Agent Should Produce

In your real repo, the agent should create or update:

- `program.md`: the concrete autoresearch contract for this workload
- `analysis.py`: a passive script that reads `results.tsv`, prints summaries, and saves plots
- `benchmark_<task>.py` or equivalent: a fixed benchmark harness that all experiments run through

Do not let the agent start experimenting before these artifacts are in place and coherent.

## Benchmark Harness Requirements

A good benchmark harness should have these properties:

- it is fixed during the experiment loop, while the target code remains mutable
- it supports at least two profiles:
  - `smoke`: a fast validation run for catching crashes and obvious bugs
  - `measure`: the official profile used for keep/discard decisions
- it runs the target system as a subprocess instead of mixing benchmark logic into the target code
- it captures raw stdout/stderr to a log file
- it prints a short, stable, parseable summary block at the end
- it exits non-zero on failure and does not hide crashes
- it keeps temporary outputs separate from the benchmark summary
- it can report derived metrics that matter for comparison, such as projected runtime or peak memory

## Suggested Prompt

From the real use-case repo, prompt your agent with something like:

```text
Read the template repo at <path/to/this/repo>.
Use its README.md, program.md, and analysis.py as templates.

Then, in this repo, create:
- a use-case-specific program.md
- a passive analysis.py
- a fixed benchmark harness script with smoke and measure profiles

Use these specs:
- Goal: <goal>
- Codebase summary: <summary>
- Primary metric: <metric and direction>
- Secondary metrics: <optional>
- Hard constraints: <tests, rules, budgets>
- Mutable files: <files>
- Fixed files: <files>
- Current run command: <command>
- Time budget: <budget>
- Environment/assets: <details>

Do NOT start the experiment loop until the benchmark harness, program.md, and analysis.py are all in place and I've checked those and given you permission to proceed.
```

## Running The Agent

Once the generated files exist in the real repo, you can start the run with a prompt like:

```text
Hi, take a look at program.md and let's kick off a new experiment! Let's do the setup first.
```
