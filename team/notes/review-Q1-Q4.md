# Review: independent reproduction of Q1, Q2, Q3 and Q4

- **Reviewer:** Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz)
- **Producer:** Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz): a **different model**
- **Rule:** `TEAM.md`, section 5, step 8, and decision **D27** (an agent of a different model may confirm, labelled "confirmed (agent, same sponsor)", while the maintainer is the only sponsor)
- **Date:** 2026-11-14

## Method
1. For each result, the code of **its own engine commit** (from its `stamp.json`): Q1 at `b886db8`, Q2 and Q3 at `e1a3165`, Q4 at `7d98c8d`. `e1a3165` was checked out as a git worktree. `b886db8` and `7d98c8d` cannot be checked out on Windows: their trees contain a result file whose name has a colon (`results/Q2/.../timeseries-i:_pair,_lambda_=_1.csv`, renamed since on `main`). Their `engine/`, `scenarios/` and `pyproject.toml` were exported with `git -c core.protectNTFS=false archive <commit> engine scenarios pyproject.toml` instead: the same files, byte for byte, without the results folder.
2. The pinned environment (`requirements.txt`; Python 3.12.10 on Windows, the producer used 3.12.3 on Linux), with `PYTHONPATH` set to the old `engine/`, and a check that `import cosmicmass` loads that copy and not the current engine.
3. The producer's scripts, unchanged: `python scenarios/Q/run.py 1`, `... 2`, `... 3`, `python scenarios/Q4/run.py`. Outputs written in the throwaway copies, **not** committed (results belong to their producer).
4. Every value of each new `summary.json` compared with the committed one: text, flags and verdicts exactly; numbers by relative difference. Values at rounding level (both at most 1e-8 in size: residuals of 1e-16 or 1e-42, momentum drifts of 1e-14) differ between machines and are listed apart; every value above that is compared with the tolerances of `team/RESULTS-STANDARD.md`, section 5.

## Results

| Result | Values compared | Text, flags, verdicts | Largest relative difference above rounding level | At rounding level (<= 1e-8) | Verdict |
|---|---|---|---|---|---|
| Q1 (`results/Q1/20261110-202417-b886db8`) | 100 numbers, 63 others | identical | 4.4e-16 (largest force, 1.49e-8 N) | 14 values (residuals of 1e-42 and 1e-16) | **reproduced** |
| Q2 (`results/Q2/20261110-202336-e1a3165`) | 32 numbers, 15 others | identical | 1.8e-7 (an energy excursion of 3.06e-7: absolute 5e-14) | 6 values (momentum drifts of 1e-14) | **reproduced** |
| Q3 (`results/Q3/20261110-202336-e1a3165`) | 18 numbers, 17 others | identical | none: every value above rounding level is identical | 2 values (a difference of 3.4e-10 recomputed: absolute 2e-16) | **reproduced** |
| Q4 (`results/Q4/20261111-011850-7d98c8d`) | 48 numbers, 23 others | identical, including the one prediction that failed in the original (setup 3, "A boosted takes more than ten times the steps") | 3.5e-4 on `separation_vs_reference` of setup 4, itself an error of 2.77e-8 (absolute 1e-11); every step count identical; period errors to 3.4e-8 | 12 values (energy drifts of 1e-14, a separation difference of 1e-12) | **reproduced** |

Every quantity named in a pass criterion or a prediction is the same, and every flag and verdict is identical. Each difference is far inside the tolerances of the standard (forces 1e-6, periods 0.1%, drifts below 1e-6). The differences above rounding level are accumulated rounding over thousands of steps on a different platform, in quantities that are themselves small differences.

**Status:** Q1, Q2, Q3 and Q4 are **confirmed (agent, same sponsor)** (D27). A reproduction by a human or by another sponsor's agent can upgrade them.

## Remarks
- A reproduction confirms that the scripts give the same numbers; it does not review the reasoning. Two points of Q2 stay for the physics lead, as they were: the conserved energy of L1a is a **candidate** (decision D23, proposed), not part of the engine.
- Re-running from a stamp on Windows needed the export of step 1. The file names are fixed on `main`; older commits keep them. A reviewer on Windows needs the same export, or Linux.
