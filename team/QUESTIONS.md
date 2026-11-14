# Questions for the maintainer

Open questions left by the agents, waiting for an answer from the maintainer (Mostafa Derraz) or from the lead concerned. One row per question. When a question is answered, move it to "Answered" with the date and the answer, or turn it into a decision in `team/DECISIONS.md`.

Questions that a run can settle do not belong here: they are run as scenarios, with their alternatives (see `team/notes/D21.md` and `team/notes/Q.md`).

## Open

| # | Question | Why it matters | Who decides | Where the details are | Asked |
|---|---|---|---|---|---|
| 1 | **Approve the energy of L1a?** Candidate: `kinetic - G sum [Re(mu_a mu_b) + lambda s Com(mu_a mu_b)] / r`. Scenario Q2 found it conserved to 4.1e-7 or better on four runs, while the L0 energy is not. It is not in the compendium. | Proposed as decision D23. Until it is approved, `energy.py` reports the Composer energy as `null`, the Composer part of E9 is blocked, and the survival table T2 cannot classify L1a as conserving or not. | physics lead | `team/notes/Q.md` (Q1, Q2); `results/Q2/` | 2026-11-10 |
| 2 | **Approve the law plug-in L1a?** In particular the three terms of option L5 and their signs: `s q g`; `s m e = -m E / s`; `2 s^2 cos(phi_bar) q e = -2 cos(phi_bar) q E`. | `TEAM.md`, section 2.1: every law plug-in needs the physics lead's approval. T9.1, T9.3, T9.4 and the demo all rest on it. | physics lead | `engine/cosmicmass/laws/l1.py`; `team/notes/T9.md` | 2026-11-10 |
| 3 | **What does "radial" mean for L1a (option L4)?** The engine takes it as "along the field at the body". For two bodies this is the line joining them; for many bodies it is the direction of the total field. | A definition, not something a run can measure. It fixes what the other directions of L4 (perpendicular, torque, along the velocity) will be measured against. | physics lead | `team/notes/T9.md`, open questions | 2026-11-10 |
| 4 | **Add `jsonschema` and `ruff` as pinned dev dependencies?** | Proposed as decision D24. P4 (JSON schemas for `stamp.json` and `summary.json`) needs a validator and P7 (lint and format) needs a linter; neither is in the pinned environment (D13). P5 waits for P4. | verification lead | `docs/WORK-PLAN.md`, P4, P5, P7 | 2026-11-10 |
| 5 | **Add a plotting library to the pinned environment?** | The figures of the demo and of the gallery are plain SVG written by hand, because there is none. The standard plots of E8.3 will need one. | verification lead | `team/notes/T1.4.md`; pull request #15 | 2026-11-10 |
| 6 | **What are `c` and `e` in scaled units?** D7 fixes only `G_N = K = 1`. The engine assumes Stoney units (`c = e = 1`) by default and lets a scenario choose otherwise. | Needed before the scaled runs of T4 and T7, and for anything that involves `B_cal` (which contains `c`). | physics lead | `team/notes/E1.md`, open question 2 | 2026-11-10 |
| 7 | **Should T0.1a and T0.1b be judged against the analytic two-body period?** Their criteria quote 27.3 days and 1.5198e-16 s, which differ from the analytic periods of the presets by 0.055% and 0.025%, out of a tolerance of 0.1%. The engine matches the analytic periods to 3.3e-7. | Half of the margin of T0.1a is used by the rounding of the criterion, not by the engine. | verification lead | `team/notes/T0.md`, Results | 2026-11-10 |
| 8 | **Align the value of `K` in `docs/05`?** It quotes the CODATA 2018 value; the engine and the verification scripts use CODATA 2022. Scenario Q3 shows the difference (6.8e-10) changes no verdict. | Harmless, but the two documents disagree. I did not edit `docs/05`. | maintainer | `team/notes/Q.md` (Q3) | 2026-11-10 |
| 9 | **Which chapter holds the measured limits?** Decision D4 and `docs/05` say "the book's Chapter 10"; in the book source of this repository the limits (9.0e-19 e, 5.71 eV, 1.14e11 V/m) are in Chapter 9. | A reference to correct in D4 and `docs/05`, or a note that the chapters were renumbered. | maintainer | `team/notes/T9.md`, open questions | 2026-11-10 |
| 10 | **How should "binding energy" be defined for T9.2** (hydrogen, 5.71 eV under the charge share)? The candidate of question 1 is the natural one. | T9.2 is one of the measured limits of D4 and is still open. | physics lead | `docs/05`, T9.2; `team/notes/Q.md` | 2026-11-10 |
| 11 | **E2.2 needs a derivation:** the second field `B_cal` of a moving point body in the slow-body form. The compendium gives the field equations F3-F4, not the field of a moving point source. | Blocks E2.2, the Boris push (E3.2), option L6, and the tests T5. | physics lead | `docs/WORK-PLAN.md`, E2.2 | 2026-11-10 |
| 12 | **What does the field do across a wrap-around boundary (U4)?** Three candidates: positions wrap and forces are those of open space; each pair interacts through its nearest image; a full periodic sum. | Wrap-around is the one wall of E6a not delivered. The first candidate breaks energy conservation at every crossing; the choice changes every result in a periodic box. A run can compare the candidates, so this should become a scenario once the alternatives are agreed. | physics lead, numerics lead | `team/notes/E6a.md` | 2026-11-11 |
| 13 | **Absorbing surfaces of bodies (T4.3):** a planet that collects what falls on it needs a radius, which a body does not have (`State` holds `m`, `q`, `x`, `v`). Should `State` gain a `radius` column, and should the collected momentum move the planet? | Needed by T4.3 (self-charging planets). It changes the `State` contract of `ARCHITECTURE.md`, section 10. | engine lead | `team/notes/E6a.md` | 2026-11-11 |
| 14 | **Amend convention 4 of D21 (the adaptive step)?** Scenario Q4 shows that the current rule depends on the frame: a scene moving as a whole costs 29 times more steps (186,692 against 6,449 for Sun, Earth and moon over a month), with no gain that was asked for. A rule relative to the nearest neighbour removes this and is as accurate on four setups. It is available as an option, not as the default. | The web universe and every scenario with a moving system (T4, T5) pay this cost. Before adopting the new rule, one more scenario is needed: a close pair passing fast near a third body, where the new rule could step too far. Should that scenario be run, and with which guard? | numerics lead, maintainer | `team/notes/Q4.md`; `team/notes/UI1.md` | 2026-11-11 |

## Housekeeping for the maintainer

Not questions, but things only the maintainer can do or should decide:

- Create the tag `v0.1.0` and the GitHub release from `CHANGELOG.md` (the MVP is merged; the tag does not exist yet).
- Close the pull requests whose content is already on `main` through #14: #5, #6, #7, #8, #9, #10, #11, #13.
- Delete the throwaway branch `P2-red-demo` (a deliberately failing test; never merge it).
- The checklist in `docs/MVP-PLAN.md`, section 4, still says "PR open" for every row; all ten are merged.
- The board (`docs/OPEN-SCENARIOS.md`) still shows E2 to E9 as claimed under the MVP sprint (D20). The sprint is over; release the claims or reassign them.
- The gallery (pull request #15) is based on the old branch `MVP-demo`; it should be moved onto `main` or closed.
- T9.1, T9.3, T9.4 and Q1 to Q3 are `done`; each needs an independent reproduction (D14) to become `confirmed`.
- Branch protection for `main` (P6) and required checks.

## Answered

| # | Question | Answer | Date |
|---|---|---|---|
| - | The four conventions of D21 (2D, softening, energy drift, adaptive step) | Approved as refined, after the scenarios D21.1 to D21.4 (`team/DECISIONS.md`, D21) | 2026-11-10 |
