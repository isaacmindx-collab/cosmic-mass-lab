# E6a: walls (absorbing walls with collection)

- **Owner:** Claude chat session on claude.ai / Claude Fable 5.2 (claude-fable-5-2), sponsor @MostafaDerraz
- **Buddy (newcomers):** none named
- **Claimed:** 2026-11-11, on the sponsor's instruction to continue the work plan; no claim issue
- **Depends on:** E5.1 (merged). Reflecting walls were delivered in MVP-6.
- **Branch:** E6a-absorbing-walls (cut from `E4.5-T9.4`, pull request #16, to avoid conflicts in the shared documents)

## Goal
The rest of E6a (`docs/WORK-PLAN.md`): "absorbing with collection (charge and mass go into the collector's `mu`), wrap-around". Pass criterion: absorbing walls conserve total `m` and `q`, counting the collector.

## Pre-registration (commit before any production run)
Not applicable: engine component, no production run, no finding.

## Plan
1. Boundary `absorbing` in `environment.py`, with a collector.
2. Settings and runner; tests.
3. Wrap-around: see "Open questions"; not delivered.

## Settings
No run. Environment: Python 3.12.3 and the pins of `requirements.txt`.

## Progress (newest first)
- 2026-11-11: wrote the absorbing walls, connected them to the settings and the runner, 2 new tests. `pytest`: 176 passed, 1 deselected; coverage 99%.

## Results
Software facts and conservation checks (mathematics); no finding.
- A body that has crossed an absorbing wall is switched off (`alive = False`), never deleted. Its mass, charge and whole momentum are added to `Environment.collected`. Its row keeps its `m` and `q`.
- **Pass criterion:** total mass and total charge of the state are unchanged, exactly, because the rows are kept; and (alive bodies) + (collector) equals the total. Checked on a hand case and on a run of 12 bodies in a box (at least 8 absorbed).
- The momentum of the bodies plus the momentum collected by the walls is conserved to 1e-9 in that run, while the bodies' own momentum changes by more than 1%.
- The L0 energy of the bodies is **not** conserved with absorbing walls, as it must not be: the energy of an absorbed body leaves the bodies. The run summary reports the number absorbed and the collected mass and charge under `absorbed`.

Choices made:
- **An absorbed body stops acting.** It is no longer a source of the field (the solver sums over alive bodies). The collector of the walls is an account, not a body: the charge it holds exerts no force. For a box wall this is the plain reading of "absorbing"; for a planet's surface (T4.3) the collector must be the planet itself, which is not delivered (question 13).
- **A body is taken as soon as it is outside the box**, whichever way it moves, and once only.
- **Fixed bodies are never absorbed.**
- The event of an absorbing wall carries the whole momentum of the bodies it took; the runner adds it to `wall_impulse`.

## Convergence
Not applicable.

## Open questions
- **Wrap-around is not delivered.** Wrapping the positions is two lines, but what the field does across the wrapped boundary is a choice that changes every result in a periodic box (open-space forces, nearest image, or a periodic sum), and the first breaks energy conservation at each crossing. It is recorded as question 12 of `team/QUESTIONS.md`, to be run as a scenario once the alternatives are agreed.
- Absorbing surfaces of bodies: question 13.

## Handoff (fill in if you stop before finishing)
- State: absorbing walls delivered as a pull request; wrap-around open.
- What works: reflecting and absorbing walls.
- What does not: wrap-around; surfaces of bodies.
- Exact next step: after an answer to question 12, the wrap-around scenario and its implementation; E6b (inflow, heat bath) after that.
