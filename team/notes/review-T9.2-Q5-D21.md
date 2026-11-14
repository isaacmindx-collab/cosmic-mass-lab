# Review: independent reproduction of T9.2, Q5 and D21.1 to D21.4 by a different model

- **Reviewer:** Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz)
- **Producers:** T9.2 and Q5: Claude Opus 5.5 in OpenCode. D21.1 to D21.4 (the stored runs at `f263697`): Claude Opus 5.5 in Claude Code. A **different model** from the reviewer.
- **Rule:** `TEAM.md`, section 5, step 8, and decision **D27** (an agent of a different model may confirm, labelled "confirmed (agent, same sponsor)", while the maintainer is the only sponsor). T9.2 and Q5 were confirmed until now only by the same-model exceptions D38 and D39, which both say that a later reproduction by a person or another model can upgrade the label.
- **Date:** 2026-11-14

## Method

1. For each result, the code of **its own engine commit**, from its `stamp.json`: T9.2 at `b19237e`, Q5 at `746e044`, D21 at `f263697`. Each was checked out as a git worktree.
2. The pinned environment (`requirements.txt`): **Linux, Python 3.12.3**, NumPy 1.26.4. The producers and the earlier reproductions ran Python 3.12.10 on Windows. `PYTHONPATH` was set to the old `engine/`, with a check that `import cosmicmass` loaded that copy.
3. The producers' scripts, unchanged: `python scenarios/T9.2/run.py`, `python scenarios/Q5/run.py`, `python scenarios/D21/run.py`. The outputs were written in the throwaway copies and are **not** committed (results belong to their producer).
4. Every value of each new `summary.json` compared with the committed one: texts, flags and verdicts exactly; numbers by relative and by absolute difference.
5. For T9.2, also an **independent calculation** that does not use the engine: the constants typed from CODATA 2022 and the formulas of the pre-registration.

## Results

| Result | Values compared | Texts, flags, verdicts | Numbers | Largest difference on a judged quantity | Verdict |
|---|---|---|---|---|---|
| T9.2 (`results/T9.2/20261114-141156-b19237e`) | 33 numbers, 11 others | identical | 27 identical bit for bit, 6 differ in the last digits | the period of the orbit: 1.3e-16 relative; the period error 3.3333831e-07 is the same to 6.7e-10 of itself | **reproduced** |
| Q5 (`results/Q5/20261114-152942-746e044`) | 67 numbers, 29 others | identical, including the one prediction that failed in the original (the sign of the deflection) | 37 identical, 30 differ in the last digits | the Earth-moon separation of setup 3: 1.1e-11 relative (4 mm in 3.8e8 m); every step count identical | **reproduced** |
| D21.1 (`results/D21.1/20261114-143325-f263697`) | 18 numbers, 6 others | identical | 7 identical, 11 differ | only energy drifts of 1e-15 (rounding level) differ visibly | **reproduced** |
| D21.2 (`results/D21.2/20261114-143404-f263697`) | 15 numbers, 10 others | identical | 6 identical, 9 differ | as D21.1 | **reproduced** |
| D21.3 (`results/D21.3/20261114-143721-f263697`) | 18 numbers, 16 others | identical | 8 identical, 10 differ | end drifts of 1e-14 differ in their second digit; the excursions that the scenario is about are the same | **reproduced** |
| D21.4 (`results/D21.4/20261114-143734-f263697`) | 18 numbers, 8 others | identical | 15 identical, 3 differ | 2.7e-8 relative on a separation error of 8.1e-9 (absolute 2e-16) | **reproduced** |

What differs, and why it does not matter:

- The largest relative differences are in quantities that are themselves at rounding level: energy drifts of 1e-15 and 1e-14 differ by 10% to 45% between the two machines. They are sums of rounding errors, and a different Python build adds them differently.
- In Q5, `separation_error_vs_reference` of setup 3 (a value of 2.77e-8) differs by 3.5e-4 of itself, an absolute 1e-11. The earlier review of Q4 saw the same size on the same setup (`team/notes/review-Q1-Q4.md`): it is the accumulated rounding of thousands of steps of three bodies.
- Every difference is far inside the tolerances of `team/RESULTS-STANDARD.md`, section 5.

**The earlier reproductions of T9.2 and Q5 were "bit for bit" because they ran on the producer's own platform. This one, on another platform, is the first that could have differed, and shows what stays the same when the last digits move: every flag, every verdict, every step count.**

### T9.2 computed without the engine

With `G_N`, `K`, `e`, `m_p`, `m_e` typed from CODATA 2022 and `a0 = 5.29177e-11` m:

| Quantity | Independent arithmetic | The stored run |
|---|---|---|
| `f = 1 - 2 cos(79.86 deg)` | 0.6478920076403478 | 0.6478920076403477 (engine, four separations) |
| binding energy `f^2 x 13.598` eV | 5.707951600 | 5.707951600 |
| ratio to the measured 13.598 eV | 0.41976 | 0.41976 |
| period of the weaker pull | 1.887666065e-16 s | predicted 1.887666064e-16 s; integrated 1.887666693e-16 s |
| Newton's share of the pull | 4.4e-40 of Coulomb's | 4.4e-40 (pre-registration) |

The two predicted periods agree to 7.6e-10; the difference is the last digits of the masses I typed.

### A note on D21

The D21 scenarios were first produced by this reviewer (Claude Fable 5.2, engine commit `7ccf3aa`, 2026-11-10) and re-run on 2026-11-14 by Claude Opus 5.5 in Claude Code at `f263697` "with standard verdicts: identical case data" (issue #24). The stored runs are those re-runs. So two models have each produced them, and each has now reproduced the other's run.

## Status

- **T9.2:** confirmed (agent, same sponsor; D27), upgrading "confirmed (same model, maintainer's exception; D38)".
- **Q5:** confirmed (agent, same sponsor; D27), upgrading "confirmed (same model, maintainer's exception; D39)".
- **D21.1 to D21.4:** confirmed (agent, same sponsor; D27).

A reproduction by a person or by another sponsor's agent can still upgrade all six.

## Remarks

- A reproduction confirms that the scripts give the same numbers; it does not review the reasoning. For T9.2 the independent arithmetic above checks the formulas too. Step (C) of T9.2 stays what its notebook says: the book's scaling argument, not a quantum calculation by the engine.
- With this, every T0 and T9 test of the S3 exit gate is confirmed under D27 itself, with no exception left.
