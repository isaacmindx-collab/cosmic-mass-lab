# Project log

Newest entries first. One entry per work session, even if nothing worked. Format:

```
### YYYY-MM-DD - @handle (or agent / model, sponsor @handle) - <scenario ID or topic>
- Did:
- Result:
- Next:
- Blocked by / questions:
```

---

### 2026-11-14 - Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) - review of the gallery (#15), D21 results layout
- Did: took the gallery commit of #15 onto `main` with cherry-pick (its branch also carried a stale copy of the D21 work and records); kept `main`'s registry rows and added only the `gallery` row. Ran `tools/make_gallery.py` on today's results: all 14 figures regenerate byte for byte. Updated four stale lines of `docs/GALLERY.md` (T9.1 now confirmed; T9.2 and T9.4 mentioned; Q2 and D23 for the energy of L1a; the web universe is live).
- Found and fixed my own slip from #27: the four re-run D21 results sat in `results/D21.x/` itself instead of `results/D21.x/<run-id>/` (a `cp -r` into a just-deleted folder), so the links in `team/FINDINGS.md` pointed nowhere; moved them into their run-id folders. Added `engine/tests/test_results_layout.py` (run folders named after their stamp's `run_id`, no loose files); it fails on the old layout and passes now.
- Result: ruff clean; 219 tests passed, coverage 99%; architecture check PASS; 20 run folders valid.
- Next: maintainer merges; then D23 and D25.
- Blocked by / questions: none.
- Architecture: updated by the gallery commit (row and node `gallery`); the review adds a test only
- Questions: none new

### 2026-11-14 - Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) - review of P7 (#28)
- Did: brought #28 onto `main` (after #29); resolved `pyproject.toml` (dev extras keep both `jsonschema` and `ruff`) and the log; renumbered P7's format decision from D23 to **D25** (D23 is the energy of L1a; the branch was cut before it existed); ran the pinned `ruff` on the combined code and fixed the two findings it reported in files the branch had not seen (`scenarios/Q/run.py`: unused import; `scenarios/Q4/run.py`: unused loop variable). Neither changes behaviour or results.
- Result: `ruff check .`: all checks passed; 216 tests passed, coverage 99%; architecture check PASS; 20 run folders valid.
- Next: maintainer merges; then decides D23 (energy of L1a) and D25 (one format pass).
- Blocked by / questions: none.
- Architecture: no code module changed by the review
- Questions: none new

### 2026-11-14 - Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) - review of P4 (#25) and P5 (#26)
- Did: brought #25 and #26 onto `main` (one log conflict, kept both sides); reviewed the schemas, the validator and the scaffold; ran the scaffold for a real scenario in a throwaway copy (files, registry row, architecture check and the first run all work). Two fixes: `KNOWN_NONCONFORMING` emptied (the D21 verdicts were fixed in #27), and `jsonschema` moved from the runtime dependencies and `requirements.txt` to the dev extras, as D24 says (only `tools/validate_results.py` and its tests use it). Recorded D24 as approved by the maintainer ("ok approved"); question 4 answered.
- Result: 216 tests passed, coverage 99%; architecture check PASS; `tools/validate_results.py`: all 20 committed run folders valid.
- Next: the maintainer merges; then P7 (`ruff`, also under D24).
- Blocked by / questions: none.
- Architecture: no code module changed by the review (dependency placement only)
- Questions: answered (# 4, by the maintainer's decision)

### 2026-11-14 - Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) - P7
- Did: configured ruff in `pyproject.toml` (lint rules for errors and likely bugs; `verification/` and `sources/` excluded), pinned `ruff==0.17.5`, added the CI job `lint`, fixed four lint items (no change of behaviour); fixed the dev container, which did not install the engine; proposed D25 for the first format pass.
- Result: `ruff check .` clean; a clean clone in a new environment, with only the container's command, runs `pytest`: 206 passed. Software facts only; no finding.
- Next: review (stacked on P5, #26); D25; a real Codespace start to confirm.
- Blocked by / questions: Docker is not available here, so the container image itself was not built.
- Architecture: updated (section 9: job `lint`; section 11)

### 2026-11-14 - Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) - P5
- Did: wrote `tools/new_scenario.py` (settings, `run.py` with `--dry-run`, notebook, registry row; checks first, never overwrites), `engine/tests/test_new_scenario.py` (9 tests on a copy of the repository) and `scenarios/README.md`.
- Result: a scaffolded scenario passes `tools/check_architecture.py` and runs a 10-step L0 dry run (the done-when of P5); a full run writes results that follow the P4 schemas. Software facts only; no finding.
- Next: review (stacked on P4, #25); P7.
- Blocked by / questions: the scaffold writes a generic valid L0 start, not the setup of `docs/05` (labelled choice in `team/notes/P5.md`).
- Architecture: updated (section 2 row `scaffold`; section 4 node and edges; section 10 additions; section 11)

### 2026-11-14 - Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) - P4
- Did: wrote `engine/schemas/stamp.schema.json` and `summary.schema.json` (two forms each: one run, or a test with cases), `tools/validate_results.py` (readable messages, command line) and `engine/tests/test_schemas.py` (21 tests, every committed result folder included); pinned `jsonschema==4.26.0` (D13).
- Result: 11 of the 15 committed result folders are valid; the summaries of D21.1-D21.4 have verdicts written as sentences instead of pass / fail / finding. Not edited (not mine; written by scripts): listed as known exceptions in the test and reported in an issue. Software facts only; no finding.
- Next: review; the verification lead to answer three questions on the standard (`team/notes/P4.md`); P5 is unblocked.
- Blocked by / questions: see `team/notes/P4.md`, Open questions.
- Architecture: updated (section 2 rows `schemas`, `validate`; section 4 nodes and edges; section 10 additions; section 11)

### 2026-11-14 - Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) - D21 verdicts (issue #24), second-wave integration
- Did: fixed issue #24 (reported by the OpenCode agent while building P4): `scenarios/D21/run.py` now writes the standard verdict `finding` and moves the sentence into `explanation`; re-ran D21.1-D21.4 from the clean commit `f263697` and replaced the four result folders. Integrated #16, #18, #21, #22, #23 and the questions board into `integrate-wave2` (pull request #27); T9.4 produced twice by two models is kept once (#22's code) and marked confirmed.
- Result: the case data of all four D21 summaries is identical to the earlier run; only the verdict field changed. Combined branch: 181 tests passed, coverage 99%, architecture check PASS.
- Next: maintainer merges #27; then #25 (P4) and #26 (P5), whose `KNOWN_NONCONFORMING` list can drop the four D21 ids.
- Blocked by / questions: none.
- Architecture: no code changed (scenario script only)
- Questions: none new

### 2026-11-14 - Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) - open questions board
- Did: on the maintainer's request ("ask everyone to leave their questions and encourage others to answer, include you"), turned `team/QUESTIONS.md` into an open board (ask, answer with evidence, the person who decides accepts); added the rule to the session protocol (`AGENTS.md` rule 12, `TEAM.md` step 6, `BRING-YOUR-AI.md`, `CONTRIBUTING.md` 18d), a Question issue template, and a link on the home page. Answered questions 1, 2, 3, 7, 8, 9 and 10.
- Result: question 1 (D23): the L1a pair force is central and symmetric, so the proposed energy is conserved; checked against the engine on 200 random pairs (force formula to 7.5e-15, action = reaction to 5.7e-15).
- Next: the maintainer (physics lead) accepts or rejects the proposed answers; D23 and D24 wait for a decision.
- Blocked by / questions: none.
- Architecture: no code changed
- Questions: answered (# 1, 2, 3, 7, 8, 9, 10)

### 2026-11-14 - Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) - T9.2
- Did: after delivering T9.4, claimed T9.2; pre-registered it in `team/notes/T9.2.md` (commit `8e2e812`, before any code); wrote `t9_2` in `gates/t9.py` (pull at four separations, one integrated orbit with convergence, the book's scaling), `scenarios/T9.2/run.py` and a fast check; ran it on the clean engine commit `b19237e`.
- Result: **T9.2 passes, as predicted**: under the charge share alone the pull of hydrogen is 0.647892 of L0's at every separation; an orbit keeps the period of that pull (3.3e-7, converged to 6e-8); by the book's scaling the binding energy is 5.708 eV (book 5.71) against the measured 13.598 eV, so this reading at lambda = 1 is excluded. Measurement check under a hypothesis. `pytest`: 176 passed, 1 deselected, coverage 99.45%.
- Next: pull requests for T9.4 and T9.2 (stacked); reproductions by a human or another model (D14). With them, the T9 gate of D4 is complete and Milestone 2 can start.
- Blocked by / questions: GitHub sign-in of this session (pending at the time of writing).
- Architecture: updated (section 2 rows `limits`, `gatetests`, `scenarios/T9.2/`; section 4 edge `limits --> runner`; section 11)

### 2026-11-14 - Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) - T9.4
- Did: fresh clone and pinned environment on Windows (Python 3.12.10); ran the six verification scripts (all pass); pre-registered T9.4 in `team/notes/T9.4.md` (commit `d7003ae`, before any code); wrote `t9_4` in `gates/t9.py`, `scenarios/T9.4/run.py` and a fast check; ran it on the clean engine commit `206c8af`.
- Result: **T9.4 passes, as predicted**: near the neutral Earth a proton and an antiproton (`m_p - e G`) get Composer forces of 1.51237e-8 N in opposite directions (sum exactly 0), with identical Real forces; only `s q g` acts. Measurement check under the hypothesis L1a, no measurement to compare with. `pytest`: 175 passed, 1 deselected, coverage 99.67%.
- Next: pull request; reproduction by a human or another model (D14); then T9.2 (hydrogen under the charge share).
- Blocked by / questions: this session is not signed in to GitHub, so the branch is pushed only after the sponsor signs in. Sponsor handle inferred (see `team/notes/T9.4.md`).
- Architecture: updated (section 2 rows `limits`, `gatetests`, `scenarios/T9.4/`; section 11)

### 2026-11-11 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - Q4 (the step rule and the frame)
- Did: merged `main` (UI1, pull request #19) into my two open branches, renumbering my proposed decisions to D23 and D24 because `main` took D22; my first merge commit left conflict markers in the change log of `ARCHITECTURE.md`, which I removed in a following commit on both branches. Then took up the remark of `team/notes/UI1.md` as a scenario: pre-registered Q4 (`team/notes/Q4.md`, commit `7cd44e0`), added the option `speed_reference` to the step rule (default unchanged), wrote `scenarios/Q4/run.py`, ran it on the clean commit `7d98c8d`.
- Result: the current step rule depends on the frame (29 times more steps for a system moving at the Earth's orbital speed, without loss of accuracy); a rule relative to the nearest neighbour does not, and is as accurate on four setups (Sun, Earth and moon over a month: 6,449 steps instead of 186,692, within 2.8e-8 of a fine reference). Seven of my eight prediction flags hold; the one that fails, and one prediction that was wrong in its value, are described in the notebook. `pytest`: 179 passed, 1 deselected.
- Next: the guard scenario (a fast close pair near a third body) before any proposal to amend D21; then E5.2, E5.4, E8.2.
- Blocked by / questions: question 14 of `team/QUESTIONS.md`. The first run failed while writing its files (a `/` in two case names); nothing had been seen; recorded as a change to the plan.
- Architecture: updated (sections 2, 10, 11)

### 2026-11-11 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - E6a (absorbing walls), milestone check
- Did: on the sponsor's request, checked the milestones and took the next task that needs no decision. Wrote absorbing walls with a collector (`engine/cosmicmass/environment.py`), connected them to the settings and the runner, 2 new tests; notebook `team/notes/E6a.md`; two new questions (12, 13) in `team/QUESTIONS.md`.
- Result: absorbing walls conserve total mass and charge exactly, counting the collector; the momentum of the bodies plus the walls' share is conserved to 1e-9. `pytest`: 176 passed, 1 deselected.
- Milestones (`docs/WORK-PLAN.md`): S0 done. Version 0.1.0 is tagged. **M1 is not reached.** S1: P1, P2, P3 done; P4, P5, P7 wait for decision D23; P6 is the maintainer's. S2: 16 of 33 sub-tasks complete (E1.1-E1.6, E2.1, E2.3, E2.4, E3.1, E3.3, E4.1, E4.2, E4.5, E5.1, E7.3), 7 partly (E4.3, E5.3, E6a, E7.1, E7.2, E8.1, E9), 10 not started (E2.2, E2.5, E3.2, E3.4, E4.4, E5.2, E5.4, E6b, E8.2, E8.3). S3: T0.1-T0.5 and G1 done, T9.1, T9.3, T9.4 done, T9.2 and the milestone review open.
- Next: tasks that need no decision: E5.2 (`Universe`), E5.4 (populations), E8.2 (convergence helper), the checkpoints of E7.1, E3.4 with E4.4 (the options L2 to L8 as defined in `docs/05`).
- Blocked by / questions: the eleven questions of `team/QUESTIONS.md` are unanswered; wrap-around waits for question 12.
- Architecture: updated (sections 2, 10, 11)

### 2026-11-11 - Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) - UI0, UI1 (first version)
- Did: built `simulator/web/`: a page with scenes, body and law editors, L0 overlay, animated trajectories and readouts; a web worker that runs the unchanged engine in Pyodide; a bridge; a test that the page loads exactly the engine's files and that the bridge runs. Proposed D22 (the design).
- Result: works in the browser: engine ready in about 20 s, the T1.4 picture (L1a ellipse over the L0 circle) in 33 s. Tests: 2 new, passing.
- Next: maintainer review and D22; GitHub Pages; the Composer plane (UI1 second part).
- Blocked by / questions: none. Found while testing: the adaptive step uses absolute speeds, which makes moving scenes slow (in `team/notes/UI1.md`).
- Architecture: updated (section 2 row `simulator/web/`, sections 3 and 4 nodes, section 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - T9.4, E4.5, Q1 to Q3
- Did: after the merge of the MVP (pull request #14), on the sponsor's instruction to do the tasks that need no decision and to turn the open questions into scenarios: pre-registered T9.4 and three question scenarios in `team/notes/Q.md` (commit `0fe33a2`, before any code); wrote `third_law_residual` (E4.5), `t9_4`, `scenarios/T9.4/run.py`, `scenarios/Q/run.py`; ran them and committed the stamped results.
- Result: **T9.4 passes** (proton pulled, antiproton pushed, exactly opposite). **Q1:** L1a with all its terms obeys Newton's third law; each half of the Coupling term alone does not. This corrects a sentence of mine in `team/notes/T1.4.md`. **Q2:** under L1a the L0 energy is not conserved but the same sum read with L1a is, to 4.1e-7 on four runs; it is a candidate for the physics lead, not added to the engine. **Q3:** CODATA 2018 or 2022 for `K` changes nothing above 3.5e-10. `pytest`: 174 passed, 1 deselected.
- Next: P4, P5, P7 (asked for, not done yet).
- Blocked by / questions: every open question for the maintainer is now collected in **`team/QUESTIONS.md`** (eleven questions and a housekeeping list); two of them are proposed as decisions D23 (energy of L1a) and D24 (dev dependencies). One flaw of my own Q1 script (a pass tolerance that could not see a tiny residual) was found on the first run and corrected before anything was committed as a result; it is recorded as a change to the plan.
- Architecture: updated (sections 2, 10, 11)

### 2026-11-10 - Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) - D21.1-D21.4
- Did: on the maintainer's request, turned the four conventions of D21 into scenarios; pre-registered them (`team/notes/D21.md`, committed before any run); ran them from commit `7ccf3aa` (`scenarios/D21/run.py`); also reviewed MVP-1 to MVP-8 and reproduced T0 on Windows (identical verdicts, differences at rounding).
- Result: (1) 2D = tilted 3D to 1e-14; (2) softening moves two-body results to a different answer (shown by halving the step), so gates keep softening 0; (3) end drift hides a 3.7e-6 excursion at e = 0.9, eta = 1e-3: report both; (4) without a floor no run can start from rest; floors 0.01-1.0 all accurate. Two predictions failed and are recorded.
- Next: maintainer approves or amends D21; reproduction of D21 by another model or a human; the CI fix (branch `ci-d18-per-pr`) and this branch need pull requests.
- Blocked by / questions: the browser pane is not signed in to GitHub, so the pull requests are not opened yet.
- Architecture: updated (section 2 registry row `scenarios/D21/`, section 11 change log)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - gallery of figures
- Did: on the sponsor's request, added `docs/GALLERY.md`: fourteen commented figures (`docs/gallery/*.svg`) of T0, T9.1, the demo T1.4 and the D21 scenarios, and the tool `tools/make_gallery.py` that redraws them from the stored results. To have all the results in one place, the branch `gallery` first merges `D21-scenarios` (pull request #13) into the top of the MVP stack (`MVP-demo`), with the four documentation conflicts resolved by keeping both sides.
- Result: `python tools/make_gallery.py` regenerates the fourteen figures. No new run was added to `results/`, and no new claim is made: each figure is labelled with its law and its kind; the demo figures are labelled exploratory and L1a a hypothesis. `pytest`: 170 passed, 1 deselected.
- Next: review. If #13 and the stack are merged separately, this branch's merge commit shows how their documents reconcile.
- Blocked by / questions: none. Two figures are recomputed, not read from files (the positions of T0.2 and the field line of T0.5); the gallery says so.
- Architecture: updated (sections 2, 4, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-10 (demo T1.4, release notes)
- Did: wrote down the expectations for the demo before running it (`team/notes/T1.4.md`, commit `d618739`); wrote `scenarios/T1.4/run.py` and `figures.py` (SVG with the standard library); added "Try it" to `README.md`, wrote `CHANGELOG.md` for 0.1.0 and set the package version to 0.1.0; ran the demo on the committed code (engine commit `30f2172`) and committed its stamped, exploratory outputs with two figures.
- Result: one command, `python scenarios/T1.4/run.py`, shows a proton and an electron on a circle under L0 and on an eccentric closed orbit under the hypothesis L1a (farthest separation 3.3808 r0, back after 4.03 L0 periods, both as expected beforehand). **Exploratory, not a result**; L1a at lambda = 1 is excluded by T9.1. `pytest`: 170 passed, 1 deselected.
- Next: the MVP sequence is complete (pull requests #2 to #11). The handoff for the maintainer and for the next agent is at the end of `team/notes/T1.4.md`.
- Blocked by / questions: reviews, independent reproductions of T0 and T9 (D14), confirmation of D21, approval of the plug-in L1a; the tag `v0.1.0` is for the maintainer.
- Architecture: updated (sections 2, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-9 (E4.3 L1a, T9.1, T9.3)
- Did: pre-registered T9.1 and T9.3 in `team/notes/T9.md` before writing any code for them (commit `c713ddc`); wrote `engine/cosmicmass/laws/l1.py` (the reading L1a, a hypothesis, with sign, strength and terms), `gates/t9.py` (new module), `scenarios/T9.1/`, `scenarios/T9.3/`, `test_l1a.py` and `engine/gates/test_t9_limits.py`; ran both scenarios on the clean engine commit `2baf36f` and committed the stamped results.
- Result: **T9.1 and T9.3 pass**, as predicted: under L1a with lambda = 1 a neutron responds as -9.009e-19 e (book: 9.0e-19 e), 1126 standard errors from the measured neutron charge, so lambda must be below 0.0020; a charge in gravity feels the force of a field 1.1380e11 V/m (book: 1.14e11). Measurement checks under a hypothesis; status `done`. `pytest`: 170 passed, 1 deselected. L1a reduces to L0 exactly at lambda = 0.
- Next: MVP-10 (demo T1.4 under L0 and L1a, exploratory, with figures; README; CHANGELOG) on `MVP-demo`.
- Blocked by / questions: the law plug-in L1a needs the physics lead's approval; MVP-10's figures need a plotting library that is not in the pinned environment (D13).
- Architecture: updated (sections 2, 4, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-8 (T0.1 to T0.5, G1)
- Did: the maintainer answered the four questions of the MVP-7 handoff in the sponsoring chat (accepted all four), so the session resumed. Recorded them as decision D21. Pre-registered T0 in `team/notes/T0.md` (committed before the production runs, with a disclosure of the exploratory runs made while coding). Wrote `engine/cosmicmass/gates/t0.py` (new module), `scenarios/T0.1/` to `scenarios/T0.5/` and the fast gate `engine/gates/test_t0_gate.py`; the run summary now reports the impulse given to the walls. Ran the five scenarios on the clean engine commit `91ba4ae` and committed the stamped results.
- Result: **T0.1 to T0.5 all pass** (details and limits in `team/notes/T0.md`; index in `team/FINDINGS.md`, status `done`). `pytest`: 160 passed, 1 deselected. These are checks of the engine against mathematics under L0, not findings.
- Next: MVP-9 (L1a, T9.1, T9.3) on `T9-limits`, cut from this branch. An independent reproduction of T0 is needed before it is `confirmed` (D14).
- Blocked by / questions: T0.1a uses 0.055% of its 0.1% margin by construction (the criterion's 27.3 days is a rounded value); T0.2 reached a wall only once in 10,000 steps; G1 runs in CI only once pull request #4 is merged.
- Architecture: updated (sections 2, 4, 8, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-7 (E7.1 to E7.3, E8.1, E9 L0 part)
- Did: wrote `engine/cosmicmass/energy.py` (L0 energy), `diagnostics.py` (conservation), `stamp.py`, `runner.py` (time loop and command line) and `__main__.py` (new module), with `test_runner.py` (13 new tests). Fixed a fault of the adaptive step on `E3-integrator` (MVP-6): a lone body in a background field never passed its turning point. Opened the notebook `team/notes/MVP-7.md`; updated the board and the MVP checklist.
- Result: `pytest` gives 152 passed and 1 deselected, coverage 99%. `python -m cosmicmass run <settings>` writes `stamp.json`, `summary.json` and `timeseries.csv`; the same settings give the same summary byte for byte; energy and momentum drifts below 1e-6 on the test runs. No finding.
- Next: MVP-8 (T0.1 to T0.5, G1) on `T0-gate`, cut from this branch. **This session stops here** (long context; `docs/MVP-PLAN.md`, section 5). The handoff, with four questions for the maintainer that decide T0 criteria, is in `team/notes/MVP-7.md`.
- Blocked by / questions: the Composer energy is reported as `null`: it needs a derivation approved by the physics lead. Checkpoints, schema validation, temperature and pressure are not done (listed in the notebook).
- Architecture: updated (sections 2, 4, 5, 10, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-6 (E3.1, E3.3, E6a reflecting)
- Did: wrote `engine/cosmicmass/integrators.py` (`StepContext`, `VelocityVerlet` with the adaptive step of D10) and `environment.py` (reflecting walls); added `universe.box`, `numerics.eta`, `dt_min`, `dt_max` to the settings; `test_integrators.py` (13 new tests, one marked `slow`). Opened the notebook `team/notes/MVP-6.md`; updated the board and the MVP checklist.
- Result: `pytest` gives 139 passed and 1 deselected, coverage 100%. Kepler orbit over 1000 periods (6,283,001 steps, run once by hand with `pytest -m slow`): largest energy excursion 3.9e-13, period within 3.3e-7. Checks of the engine against the two-body problem under L0 (mathematics); no finding.
- Next: MVP-7 (runner, stamp, command line, diagnostics, L0 energy) on `E7-runner`, cut from this branch.
- Blocked by / questions: three assumptions for the maintainer, in the notebook: the meaning of "energy drift" (net change or largest excursion: an e = 0.9 orbit swings by 3.7e-6 at pericentre with D10's eta = 1e-3); the floor of the speed for bodies at rest; the displacement limit of the adaptive step.
- Architecture: updated (sections 2, 4, 5, 10, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-5 (E2.1, E2.3, E2.4)
- Did: wrote `engine/cosmicmass/fields/direct.py` (`DirectSum`: static `g` and `e`, Plummer softening, no self-field, uniform backgrounds, NumPy blocks, 2D and 3D); extended `settings.py` for backgrounds; `test_fields.py` (13 new tests). Opened the notebook `team/notes/MVP-5.md`; updated the board and the MVP checklist.
- Result: `pytest` gives 128 passed, coverage 100%. T0.5 as a unit test: one proton gives `E = -s^2 e = K e/r^2` to 1e-12 (asked 1e-6). Mathematics from the compendium; no finding.
- Next: MVP-6 (velocity Verlet, adaptive step, reflecting walls) on `E3-integrator`, cut from this branch.
- Blocked by / questions: two labelled assumptions for the physics lead, in the notebook: "2D" is taken as planar motion with a `1/r^2` field; the softening of D10 (Plummer form) changes the closest initial force by 1.5e-6, more than the 1e-6 of the two-body gate tests, so those should run with softening 0.
- Architecture: updated (sections 2, 4, 5, 10, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-4 (E5.1, E5.3 minimal, E4.1, E4.2)
- Did: wrote `engine/cosmicmass/fields/sample.py` (new module: `FieldSample`, `FieldSolver`), `state.py`, `laws/base.py`, `laws/l0.py` and a minimal `settings.py`, with `test_state_laws.py` and `test_settings.py` (51 new tests). Opened the notebook `team/notes/MVP-4.md`; updated the board and the MVP checklist. (MVP-3, the CI job, is on its own branch `P2-ci-tests`, with its own log entry there.)
- Result: `pytest` gives 115 passed, coverage 100%. Two bodies under L0 feel `(G_N m m' - K q q')/r^2` to 1e-15, with equal and opposite forces; the L0 force is bit-for-bit the same at every frame angle. Mathematics from the compendium; no finding.
- Next: MVP-5 (`fields/direct.py`: static direct sum, softening, backgrounds) on `E2-fields`, cut from this branch.
- Blocked by / questions: none. Choices to review are in the notebook (`Law` as a base class; `LawSpec.moving` as a string; the new module `fields/sample.py`).
- Architecture: updated (sections 2, 4, 5, 10, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-3 (P2)
- Did: added the job `tests` to `.github/workflows/verify.yml` (`pip install -e ".[dev]"`, `pytest` with coverage, fails under 90%); added `engine/tests/test_pins.py`; pinned the dev extras (the two remarks of the P1 review); opened the notebook `team/notes/P2.md`; marked P2 `done` on the board and updated the MVP checklist.
- Result: the job is green on this branch and red on a throwaway branch with one failing test (run links in the notebook). Software facts only; no finding.
- Next: MVP-4 on `E4-l0`, cut from `E1b-arrays-readings`.
- Blocked by / questions: the E1 stack was cut from `main` before this job existed, so its pull requests run the tests in CI only after this one is merged and they are updated. Merging this pull request early removes the gap.
- Architecture: updated (sections 2, 9, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-2 (E1.3 to E1.6)
- Did: wrote `engine/cosmicmass/gnarray.py` (E1.3), `readings.py` (E1.4), `matter.py` (E1.5) and the tests `test_gnarray.py`, `test_readings_matter.py`, `test_compendium.py` (E1.6); 36 new tests. Updated the notebook `team/notes/E1.md`, the board (E1 `done`) and the MVP checklist.
- Result: `pytest` gives 64 passed, coverage 100% of `engine/cosmicmass`. Arrays agree with scalars to 1e-15 on 10,000 values; the product `mu E_cal` matches the compendium in both coordinates; `Re(mu_a mu_b)` is the same number at every frame angle. Mathematics from the compendium; no finding of the virtual universe.
- Next: MVP-3 (P2, CI runs pytest) on `P2-ci-tests`, cut from `main`; then MVP-4 on `E4-l0`, cut from this branch.
- Blocked by / questions: none new. `Com(z)` returns the coordinate `b`, and `CosmicMass.mu(frame)` takes the frame (see the notebook).
- Architecture: updated (sections 2, 4, 5, 10, 11)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - MVP-1 (E1.1, E1.2)
- Did:
  - read `docs/MVP-PLAN.md` and decision D20; took the MVP sequence as one claim;
  - wrote `engine/cosmicmass/constants.py` and `frame.py` (E1.1) and `gn.py` (E1.2), with `engine/tests/test_constants_frame.py` and `test_gn.py` (25 new tests);
  - opened the notebook `team/notes/E1.md`; updated the board, the MVP checklist and `engine/README.md`.
- Result: `pytest` gives 28 passed, coverage 100% of `engine/cosmicmass`. Rule of the Square exact at 50 digits; `z * (1/z) = 1`; products and quotients agree with the bridge to C. All of it is mathematics from the compendium; no finding of the virtual universe.
- Next: MVP-2 (`gnarray.py`, `readings.py`, `matter.py`, `test_compendium.py`) on `E1b-arrays-readings`, cut from this branch.
- Blocked by / questions: three open questions in `team/notes/E1.md`: the value of `K` differs between `docs/05` (CODATA 2018) and the verified constants (CODATA 2022, used here); `c` and `e` in scaled units are not fixed by D7 (assumed Stoney units, `c = e = 1`); the compendium has no equation numbers (tests cite paragraph titles).
- Architecture: updated (sections 2, 4, 5, 10, 11)

### 2026-11-10 - Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) - P1 review and delivery
- Did: applied the P1 patch produced by the claude.ai chat session below (it had no push access), reviewed it as a different model (D14), and re-ran the done-when check on Windows: clean clone of the branch, fresh Python 3.12.10 environment, `pip install -e .[dev]` then `pytest` gives 3 passed (100% coverage); `python tools/check_architecture.py --base origin/main` passes. Corrected the session label in this log and in `team/notes/P1.md`. Pushed the branch and opened the pull request.
- Result: P1 works on Linux (producer) and Windows (reviewer). Remarks for the reviewer of record: the dev extras `pytest` and `pytest-cov` are not pinned (resolved to 9.2.0 and 7.1.0); suggest pinning them in P2 together with a check that `pyproject.toml` and `requirements.txt` pins agree.
- Next: maintainer review and merge (D17); then P2.
- Blocked by / questions: none.
- Architecture: no code changed in this session (the architecture update is in the P1 commit)

### 2026-11-10 - Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2) (sponsor @MostafaDerraz) - P1
- Did:
  - ran the six verification scripts in the pinned environment (Python 3.12.3): 106, 204, 253 checks, 144 laws, 9,304 Gazette checks, 79 General Sinus checks, all pass; `python tools/check_architecture.py` passed before starting;
  - added `pyproject.toml` (package `cosmicmass` from `engine/cosmicmass/`, Python >= 3.12, the three pins of `requirements.txt`, dev extras `pytest` and `pytest-cov`, pytest pointed at `engine/tests`);
  - added `engine/cosmicmass/__init__.py` (`__version__ = "0.0.1"`) and `engine/tests/test_import.py` (3 tests);
  - added packaging and test leftovers to `.gitignore`; updated `engine/README.md`; opened the notebook `team/notes/P1.md`; marked P1 `done` on the board.
- Result: on a clean copy of the branch in a fresh Python 3.12 environment, `pip install -e .[dev]` then `pytest` gives 3 passed. No physics code and no finding; `team/FINDINGS.md` is unchanged.
- Next: P2 (CI job for tests and coverage) can start; it should also keep `pyproject.toml` and `requirements.txt` pins in step. P4 and P7 are unblocked too.
- Blocked by / questions: no claim issue was opened for P1 (the task was assigned directly by the sponsor, who is the maintainer). The pull request needs a review by someone other than the author (D17).
- Architecture: updated (sections 2, 4, 11)

### 2026-11-10 - @MostafaDerraz with Claude Opus 5.5 (AI assistant) - project setup
- Did:
  - verified the three papers and the book's algebra (106, 204, 253 checks, 144 laws, 9,304 Gazette checks, 79 General Sinus checks);
  - audited General Sinus and corrected five errors (see `docs/03-report-verified-formulas.md`);
  - wrote the formulas compendium, the test plan T0-T9, the engine architecture and the general note;
  - created this repository with CI verification, opened it to the public, and wrote the rules (`CONTRIBUTING.md`, `AGENTS.md`), the team guide (`TEAM.md`) and the open scenarios board.
- Result: the foundation is verified and CI is green. No simulator code exists yet.
- Next: milestone 1. Engine components E1-E4, then the T0 gate.
- Blocked by / questions: none. Engine lead wanted.
