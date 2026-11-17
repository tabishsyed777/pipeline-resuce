# Verification evidence

## Local containers

- Reference solution: **reward 1**, **46/46** checks passed.
- Broken starter: **reward 0**, **8/46** checks passed.
- Hardcoded empty-output shortcut: reward 0.
- Unit tests: **6 passed**.
- Real-container integration tests: **3 passed** (reference, starter, shortcut).

The initial reference run exposed a verifier bug: text-mode reads normalized CSV CRLF line endings, falsely reporting that a rejected same-input/output invocation had changed the file. The verifier now compares exact input bytes. The corrected reference passes without weakening pipeline expectations.

The container's trusted verifier needed file-access permissions after Docker copied host-owned files. It retains FOWNER/DAC_OVERRIDE and SETUID/SETGID capabilities while candidate subprocesses run unprivileged with no supplementary groups. No verifier or reference source is included in the agent build context image layers.

## Actual Harbor trials

Tested with Harbor **0.26.0**, schema **1.4**, local Docker, and a **separate verifier environment**:

| Agent | Recorded reward | Trial exception |
| --- | ---: | --- |
| Oracle/reference | 1.0 | None |
| NOP/unchanged starter | 0.0 | None |

Both `result.json` rewards and `verifier/reward.txt` were checked using `check_trials.py`. A summary is saved in `examples/harbor-results.json`. Full local verifier reports are in `examples/`.

The managed environment had a read-only home directory. The local Harbor invocation used a scratch wrapper that redirected Harbor's cache-path constants to `work/harbor-cache` before loading its normal CLI. No task, scoring, agent, or environment execution logic was changed by that wrapper. Normal machines and GitHub CI use the documented `harbor run` commands directly.

This environment's kernel did not support Harbor's dynamic egress-control network policy. The task instead uses Docker Compose's explicit `network_mode: none`, which was used by the successful trials. The standalone verifier also uses Docker `--network none`.

This is a synthetic public task prototype. Oracle/NOP checks show that the reference solves the task and the unchanged starter fails. They do not measure frontier-agent capability, establish difficulty, prove resistance to every malicious submission, or imply official Terminal-Bench inclusion. No official benchmark or registry submission was made.
