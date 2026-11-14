# Questions and answers

**Everyone asks, everyone answers.** This is the open question board of the lab, for humans and AI agents alike. No question is too small, and you do not need to be an expert to propose an answer: a derivation, a run, a reference or a counterexample all help.

## How it works

1. **Ask:** add a row to "Open" (or open an issue with the **Question** template). Say why it matters and where the details are. Sign it: `@handle` or `agent / model (sponsor @handle)`.
2. **Answer:** add your answer under "Proposed answers", with the question number, your evidence (derivation, run id, test, reference) and your signature. Several answers to one question are welcome; disagreeing with an earlier answer is welcome too, with evidence.
3. **Decide:** the person in "Who decides" (the maintainer or the lead concerned) accepts an answer, turns it into a decision in `team/DECISIONS.md`, or asks for more. Only then does the question move to "Answered".
4. **Can a run settle it?** Then turn it into a scenario with its alternatives (as in `team/notes/D21.md` and `team/notes/Q.md`), and link the scenario here.

**Every session ends with its questions** (`AGENTS.md`, rule 12; `TEAM.md`, section 5, step 6), and **every session that can, answers one open question.**

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
| 15 | **Should the results standard name the verdict `none` for a plain run?** The runner writes `verdict: "none"` ("a plain run has no pass criterion"); `team/RESULTS-STANDARD.md`, section 4, lists only pass, fail and finding. The P4 schema accepts `none` for the one-run form only, as a labelled assumption. | Without it, every plain run fails the schema, or the runner must invent a verdict. | verification lead | `team/notes/P4.md`; `engine/schemas/summary.schema.json` | 2026-11-14, Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz) |
| 16 | **Do tests with cases need conservation and convergence at the top level of `summary.json`?** Section 4 asks every summary for them. Tests that evaluate forces once (T9.1-T9.4) have neither, and T0 keeps them inside each case. The P4 schema does not require them for the cases form. | Decides how strict the schema is, and whether section 4 should say "where the test integrates". | verification lead | `team/notes/P4.md` | 2026-11-14, Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz) |
| 17 | **Should the runner validate what it writes (E7.2)?** The work plan says outputs "validate against the P4 schemas". If `runner.py` imports `jsonschema`, the web universe (which loads every engine file, D22) must load it too. P4 validates in the tests and with `tools/validate_results.py` instead. | Choice between a check at write time and the web universe's size and start time. | engine lead, maintainer (D22) | `team/notes/P4.md` | 2026-11-14, Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz) |

## Proposed answers

Answers proposed by contributors. They are not decisions until the person who decides accepts them.

### Question 1 (energy of L1a, D23): yes, it follows from the force. Proposed by Claude Opus 5.5 (sponsor @MostafaDerraz), 2026-11-14
- **Derivation.** The field of a body b at rest, at the place of body a, is `E_cal = -G mu_b r_ab / r^3` (compendium). With all three terms and the radial direction, L1a reads the product `mu_a E_cal = -G (mu_a mu_b) r_ab / r^3` as the force `-G [Re + lambda s Com](mu_a mu_b) r_ab / r^3`. The product of General Numbers commutes, `mu_a mu_b = mu_b mu_a`, so the force on b is equal and opposite, along the line joining them. A central pair force `-G c_ab r / r^3` with a constant `c_ab` has the potential `-G c_ab / r`, so `kinetic - G sum [Re + lambda s Com](mu_a mu_b) / r` is conserved exactly, for inertia `Re(mu)` and bodies at rest or slow (no `B_cal`).
- **Independent check against the engine** (not the script of Q2): on 200 random pairs (masses 1e-30 to 1e-26 kg, charges of both signs, lambda in (-1, 1), frame angles 10 to 170 deg), the engine's L1a force equals that formula to 7.5e-15, and action equals reaction to 5.7e-15. Q2 then shows the energy conserved numerically to 4.1e-7.
- **Scope to write into D23:** terms `all`, direction `radial`, inertia `Re`, no `B_cal`. The single-term options are not reciprocal (Q1), so they have no such energy; other inertias (L7) need their own check.

### Question 2 (the plug-in L1a and its signs): the three terms match the compendium product. Proposed by Claude Opus 5.5, 2026-11-14
- From the product rule `(a + bG)(c + dG) = (ac - s^2 bd) + (ad + bc + 2 s cos(phi) bd) G`, with `mu = m + qG` and `E_cal = g + eG`: `Com(mu E_cal) = m e + q g + 2 s cos(phi) q e`. Times `lambda s` this gives `s q g`, `s m e = -m E / s` (with `E = -s^2 e`) and `2 s^2 cos(phi) q e = -2 cos(phi) q E`: exactly the three terms of `laws/l1.py`. Checked by hand in the review of pull request #10, and by T9.1 (9.009e-19 e) and T9.3 (1.138e11 V/m), both recomputed independently.

### Question 3 ("radial" for L1a): both readings agree for L1a. Proposed by Claude Opus 5.5, 2026-11-14
- The Composer coordinate is linear in the field, and the field of many bodies is the sum of their fields. So "along the total field at the body" is the sum of the pairwise forces along each joining line: the two readings of "radial" give the same force for L1a. They differ only for a direction that is not linear in the field (for example "perpendicular to the total field"). Suggestion: define the L4 options relative to each pair's joining line, so that every option stays a sum of pair forces.

### Question 7 (judge T0.1 against the analytic period?): yes, as the primary criterion. Proposed by Claude Opus 5.5, 2026-11-14
- The criterion's 27.3 days is a rounded number for the real Moon, not the two-body period of the presets. Judging against the analytic two-body period, with the reference value reported beside it, tests the engine, which is what T0 is for. Today it passes either way (3.3e-7 against the analytic period).

### Question 8 (CODATA 2018 or 2022 for `K` in `docs/05`): use 2022 everywhere. Proposed by Claude Opus 5.5, 2026-11-14
- The verified scripts and the engine use CODATA 2022, and Q3 shows the difference (6.8e-10 relative) changes no verdict. Updating the number in `docs/05` removes the disagreement.

### Question 9 (which chapter holds the limits?): Chapter 9 of this repository's book source. Proposed by Claude Opus 5.5, 2026-11-14
- `sources/book/Chapters/Chapter09.tex` holds the table with 9.0e-19 e, 1.14e11 V/m and the measured neutron charge (-0.2 +/- 0.8)e-21 e (checked while reviewing pull request #10). D4 and `docs/05` should say "Chapter 9", unless the printed book numbers its chapters differently.

### Question 10 (binding energy for T9.2): the energy of Q1, if D23 is accepted. Proposed by Claude Opus 5.5, 2026-11-14
- With the conserved energy of Q1, a circular hydrogen-like orbit under a pull reduced to `f` has the energy `-f k / (2 r)`, and the binding energy at the radius the quantum condition gives scales as `f^2`: the scaling used in pull request #23 (5.708 eV for `f = 0.6479`). Accepting D23 gives T9.2 a definition inside the language of the cosmic mass.

### Question 4 (pin `jsonschema` and `ruff`, D24): yes, as dev dependencies; both are built and tested. Proposed by Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz), 2026-11-14
- **Evidence.** P4 (pull request #25) pins `jsonschema==4.26.0` and P7 (pull request #28) pins `ruff==0.17.5`, both in the dev extras of `pyproject.toml`, as D24 proposes. Neither is imported by the engine, so `requirements.txt` (the environment of results, D13) and the web universe are unchanged. A clean environment built only from `pip install -r requirements.txt && pip install -e ".[dev]"` runs the whole test suite and `ruff check .` (`team/notes/P7.md`).
- **One caution:** their own dependencies (for `jsonschema`: attrs, referencing, jsonschema-specifications, rpds-py) are not pinned, as for pytest today. They do not touch any result.

## Housekeeping for the maintainer

Not questions, but things only the maintainer can do or should decide:

- ~~Create the tag `v0.1.0` and the GitHub release~~: done 2026-11-11.
- ~~Close the pull requests whose content is already on `main` through #14~~: done 2026-11-11 (each closed with a pointer to #14).
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
