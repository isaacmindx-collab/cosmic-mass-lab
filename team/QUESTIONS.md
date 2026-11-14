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
| 2 | **Approve the law plug-in L1a?** In particular the three terms of option L5 and their signs: `s q g`; `s m e = -m E / s`; `2 s^2 cos(phi_bar) q e = -2 cos(phi_bar) q E`. | `TEAM.md`, section 2.1: every law plug-in needs the physics lead's approval. T9.1, T9.3, T9.4 and the demo all rest on it. | physics lead | `engine/cosmicmass/laws/l1.py`; `team/notes/T9.md` | 2026-11-10 |
| 3 | **What does "radial" mean for L1a (option L4)?** The engine takes it as "along the field at the body". For two bodies this is the line joining them; for many bodies it is the direction of the total field. | A definition, not something a run can measure. It fixes what the other directions of L4 (perpendicular, torque, along the velocity) will be measured against. | physics lead | `team/notes/T9.md`, open questions | 2026-11-10 |
| 5 | **Add a plotting library to the pinned environment?** | The figures of the demo and of the gallery are plain SVG written by hand, because there is none. The standard plots of E8.3 will need one. | verification lead | `team/notes/T1.4.md`; pull request #15 | 2026-11-10 |
| 6 | **What are `c` and `e` in scaled units?** D7 fixes only `G_N = K = 1`. The engine assumes Stoney units (`c = e = 1`) by default and lets a scenario choose otherwise. | Needed before the scaled runs of T4 and T7, and for anything that involves `B_cal` (which contains `c`). | physics lead | `team/notes/E1.md`, open question 2 | 2026-11-10 |
| 7 | **Should T0.1a and T0.1b be judged against the analytic two-body period?** Their criteria quote 27.3 days and 1.5198e-16 s, which differ from the analytic periods of the presets by 0.055% and 0.025%, out of a tolerance of 0.1%. The engine matches the analytic periods to 3.3e-7. | Half of the margin of T0.1a is used by the rounding of the criterion, not by the engine. | verification lead | `team/notes/T0.md`, Results | 2026-11-10 |
| 8 | **Align the value of `K` in `docs/05`?** It quotes the CODATA 2018 value; the engine and the verification scripts use CODATA 2022. Scenario Q3 shows the difference (6.8e-10) changes no verdict. | Harmless, but the two documents disagree. I did not edit `docs/05`. | maintainer | `team/notes/Q.md` (Q3) | 2026-11-10 |
| 9 | **Which chapter holds the measured limits?** Decision D4 and `docs/05` say "the book's Chapter 10"; in the book source of this repository the limits (9.0e-19 e, 5.71 eV, 1.14e11 V/m) are in Chapter 9. | A reference to correct in D4 and `docs/05`, or a note that the chapters were renumbered. | maintainer | `team/notes/T9.md`, open questions | 2026-11-10 |
| 10 | **How should "binding energy" be defined for T9.2** (hydrogen, 5.71 eV under the charge share)? The candidate of question 1 is the natural one. | T9.2 is one of the measured limits of D4 and is still open. | physics lead | `docs/05`, T9.2; `team/notes/Q.md` | 2026-11-10 |
| 25 | **Under L1e, where is the body: at `x`, or at a reading of `X = x + xc G`?** L1e gives every body the General Number acceleration `a = E_cal + v x B_cal`, so the Real coordinate `x` accelerates with `g + v x B_g` only: read as the place, **a charge would not feel the electric field at all** (it moves `xc` instead). But `Re(mu a) / Re(mu)` is exactly L0's acceleration (tested), so the reading `Re(mu X) / Re(mu) = x - s^2 (q/m) xc` of the place follows L0. The engine builds L1e as written, with the fields taken at `x` and the Real velocity in `v x B_cal`; both are labelled choices. | It decides what T1 and T2 say about L1e (bound or not, conserving or not), and whether the fields should be taken at `x` or at the reading. | physics lead | `team/notes/E4.md`, part C; `engine/tests/test_two_coordinates.py` | 2026-11-14, Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz) |

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

### Question 14 (amend convention 4 of D21?): the scenario was run (Q5); rule B fails the trap, and the pair guard fixes it at no cost elsewhere. Proposed by Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz), 2026-11-14
- **The trap, built on purpose** (`team/notes/Q5.md`, pre-registered): a light, loose pair flies at 300 past a heavy body H at 1.5, while H's nearest neighbour is its own companion at 1. No body's nearest neighbour sees the passage. **Rule B** takes 473 steps and gets the pair's deflection wrong by **4.0e-4** (400 times the `eta` = 1e-3 it is meant to keep), while its energy error stays at 3.7e-11, so conservation alone would not reveal it.
- **Proposed guard (rule C):** B, plus `dt <= eta min_(i<j) r_ij / |v_i - v_j|` over all pairs of alive bodies. It uses only relative motion, so it keeps B's frame independence. On the trap: 9,599 steps, deflection within **1.1e-7** of the reference (converged at second order). Rule A would need about 1.2e7 steps there.
- **No cost where B already worked:** on Earth and moon (own frame and plus 29,780 m/s) and on Sun, Earth and moon, rule C takes exactly B's steps (6,284; 6,449) with the same errors. Run id `results/Q5/20261114-152942-746e044`.
- **Proposed amendment of D21, convention 4:** the step conditions of D10 taken relative to each body's nearest neighbour, plus the pair guard. Not tested: crowded scenes (the guard is `O(N^2)`, like the direct sum) and many passages at once. One of my 11 predictions failed (the sign of the deflection; its size agreed to 0.22%), recorded in the notebook.

### Question 5 (a plotting library): none is needed. Proposed by Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz), 2026-11-14
- **Evidence.** `engine/cosmicmass/analysis/plots.py` (E8.3) draws the standard figures (drifts, trails, the General Number plane) and any sweep as plain SVG with the standard library, as `tools/make_gallery.py` already does for the gallery. The figures are made from a results folder alone, byte for byte the same each time (`engine/tests/test_e8_analysis.py`), which a plotting library would not guarantee across versions; and the web universe, which loads every engine file, gains no dependency.
- **If a figure ever needs more** (contours, 3D), that would be the moment for a pinned library, as a dev extra (like D24), never in the engine.

### Questions 13 and 24 (new columns of `State`): yes, as optional columns that change nothing when absent. Proposed by Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz), 2026-11-14
- **Proposal:** `State` gains optional arrays `radius` (N,), `spin` (N,) in 2D or (N, 3) in 3D, and `xc`, `vc` (N, d), the Composer position and velocity of L1e. Each defaults to zeros (or `None` for `radius`), is copied with the state, and is read only by the code that needs it: the absorbing surface of a body (T4.3), the direction "torque" of L4, and L1e. Every existing call of `State(...)` and `State.from_bodies(...)` keeps working unchanged; the stamp and the schemas gain the new settings only when they are used.
- **Why this way:** it is an **addition** to the contract of `ARCHITECTURE.md`, section 10, not a change of any existing field or signature, as earlier additions were (for example `FieldSample`'s shapes, or `StepContext.speed_reference`). Every existing result stays reproducible on its own engine commit.
- **Until it is decided** I build E4.4's other options (L4 perpendicular and along the velocity, L6, L8) first, which do not need it, and keep L1e and the torque for last.

## Housekeeping for the maintainer

Not questions, but things only the maintainer can do or should decide:

- ~~Create the tag `v0.1.0` and the GitHub release~~: done 2026-11-11.
- ~~Close the pull requests whose content is already on `main` through #14~~: done 2026-11-11 (each closed with a pointer to #14).
- Delete the throwaway branch `P2-red-demo` (a deliberately failing test; never merge it).
- The checklist in `docs/MVP-PLAN.md`, section 4, still says "PR open" for every row; all ten are merged.
- The board (`docs/OPEN-SCENARIOS.md`) still shows E2 to E9 as claimed under the MVP sprint (D20). The sprint is over; release the claims or reassign them.
- The gallery (pull request #15) is based on the old branch `MVP-demo`; it should be moved onto `main` or closed.
- ~~T9.1, T9.3, T9.4 and Q1 to Q3 are `done`; each needs an independent reproduction (D14) to become `confirmed`~~: T9.1, T9.3 and T9.4 confirmed earlier; Q1 to Q4 confirmed (agent, same sponsor) on 2026-11-14 (`team/notes/review-Q1-Q4.md`, D27). Still `done`, waiting for a reproduction by a model other than Claude Opus 5.5: T9.2, Q5 and the D21 scenarios (all produced by Claude Opus 5.5).
- Branch protection for `main` (P6) and required checks.

## Answered

| # | Question | Answer | Date |
|---|---|---|---|
| 11 | The second field `B_cal` of a moving point body (slow-body form)? | `B_cal = (1/c^2) v x E_cal` to first order in `v/c` (Biot-Savart for the Composer part): decision D41; in the engine, `universe.moving_fields`. | 2026-11-14 |
| 24 | Extend `State` with optional columns for L1e and the spin? | Yes, all four (`xc`, `vc`, `spin`, `radius`), with defaults: decision D37. | 2026-11-14 |
| 13 | Absorbing surfaces of bodies: should `State` gain a radius? | Yes, the optional column `radius` of D37. | 2026-11-14 |
| 12 | The field across a wrap-around boundary? | The nearest image, with its stated limit for `1/r^2`: decision D36. | 2026-11-14 |
| 1 | Approve the energy of L1a? | Yes, with its scope (all terms, radial, inertia `Re`, no `B_cal`): decision D23 approved. | 2026-11-14 |
| 23 | Adopt the team chat? | Yes: decision D30. Read your inbox at the start of every session. | 2026-11-14 |
| 14 | Amend convention 4 of D21 (the adaptive step)? | Yes: the pair guard of Q5 (rule C), decision D29. Implementation in `integrators.py`: task E3. | 2026-11-14 |
| 22 | Who may confirm a result of an agent? | An agent of a different model may, even with the same sponsor, while the maintainer is the only sponsor; labelled "confirmed (agent, same sponsor)". Decision D27. | 2026-11-14 |
| 21 | Is `k_B = 1` in scaled units? | Accepted for now as a labelled assumption (like `c = e = 1`, question 6); to be revisited with question 6. | 2026-11-14 |
| 20 | Accept two choices of E6b (deterministic inflow count; the bath judged on the time average)? | Accepted for now as labelled assumptions. The independent review of #33 found both sound (inflow exactly `floor(rate t)`; the bath reaches its temperature from below and from above). | 2026-11-14 |
| 4 | Add `jsonschema` and `ruff` as pinned dev dependencies? | Yes: decision D24 approved by the maintainer. `jsonschema` arrives with P4, `ruff` with P7. | 2026-11-14 |
| - | The four conventions of D21 (2D, softening, energy drift, adaptive step) | Approved as refined, after the scenarios D21.1 to D21.4 (`team/DECISIONS.md`, D21) | 2026-11-10 |
