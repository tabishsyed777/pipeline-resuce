# Pipeline Rescue

A Terminal-Bench-style task: repair an order-event CSV pipeline so it produces a deterministic, exact-money JSON summary and preserves existing output when input is invalid.

Includes a broken starter, public sample, full task contract, reference solution, independent behavioral verifier, fresh-container local runner, and a Harbor 0.26.0 schema-1.4 task with a **separate verifier environment**.

This is an original public benchmark prototype. It has not been submitted to or included in official Terminal-Bench, calibrated for difficulty, or evaluated against a frontier model.

## Task

The agent repairs `/app/pipeline.py` using Python's standard library. The pipeline must:

- Convert currency amounts to integer cents exactly.
- Ignore identical duplicate event IDs and reject conflicting duplicates.
- Select each order's latest event with deterministic timestamp/event-ID tie breaking.
- Convert timezone-aware timestamps to UTC before grouping by day.
- Keep currencies separate and sort the summary deterministically.
- Reject malformed records without changing an existing output or creating a new one.
- Replace successful output atomically.

See [the complete instruction](task/instruction.md). The starter and sample are the only task files copied into the agent image; reference code and evaluation fixtures are not included in that image. Fixtures are public in this repository, so they are withheld during a normal task run, not permanent secrets.

## Local verification

Requires Python 3.10+ and Docker. The candidate needs no third-party packages.

```bash
python -m unittest discover -s tests -p test_unit.py -v
python -m unittest discover -s tests -p test_integration.py -v

# Reference: reward 1
python verify.py task/solution/pipeline.py --out work/reference

# Unchanged broken starter: reward 0
python verify.py task/environment/pipeline.py --out work/starter

# Your candidate
python verify.py /path/to/pipeline.py --out work/candidate
```

The local runner creates a fresh container and transfers only the submitted `pipeline.py`, then injects the pristine verifier. Container networking is disabled. Candidate processes run as UID 65534; the trusted root verifier retains permissions needed to prepare fixtures and write evidence. A 3-second subprocess timeout, 256 MB container memory limit, CPU limit, and PID limit bound execution. The grader never imports candidate or reference code.

Reports are written to `report.json` and `reward.txt`. A reward is 1 only if **all** checks pass. The verification CLI can finish normally with reward 0: inspect the reward rather than treating its exit status as task success.

The verifier runs 46 checks covering fixed examples, three seeded multi-order datasets with shuffled events, exact large integer money, duplicates, lifecycle statuses, UTC boundaries, sort order, malformed input, and preserving both existing and absent outputs. Successful output must have the specified JSON shape and replace the old file's inode. That inode check is evidence of replacement, not an exhaustive crash-durability proof.

## Harbor trials

Harbor 0.26.0 requires Python 3.12+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-harbor.txt
harbor run -p task -a oracle --jobs-dir work/harbor --job-name oracle
python check_trials.py work/harbor/oracle 1
harbor run -p task -a nop --jobs-dir work/harbor --job-name nop
python check_trials.py work/harbor/nop 0
```

Harbor collects `/app/pipeline.py` and transfers it to a newly started verifier environment. Other edits to the agent's filesystem are not transferred as the submitted program. `environment/docker-compose.yaml` explicitly sets `network_mode: none` for Docker execution in both environments; no internet is needed after image pulls.

`check_trials.py` requires one completed trial, no trial exception, the expected recorded reward, and a matching reward file. GitHub CI runs unit tests, real container tests, and actual oracle/NOP trials, then retains evidence even on failure.

## Measured scope

The reference passed 46/46 local checks; the starter and hardcoded-output negative control earned reward 0. Six unit tests and three real-container integration tests passed. Recorded Harbor oracle/NOP outcomes are documented in [VALIDATION.md](VALIDATION.md).

Docker and privilege separation reduce accidental interference; this is not a comprehensive sandbox for hostile code. Do not mount credentials, host sockets, or private data into candidate containers. No secrets or model credentials are required for the included trials.

Earlier user-specific test steps were unavailable in this conversation; these tests document the checks actually performed.
