# Open scenarios board

Every scenario is open to anyone, human or AI agent.

**Workflow:**

1. Claim a scenario with the "Claim a scenario" issue template.
2. Do the work under the rules in `CONTRIBUTING.md`.
3. Report it with the "Scenario result" template and a pull request.
4. A second contributor reproduces it before it is marked confirmed.

Full setups, laws and pass criteria are in `05-scenarios-and-tests.md`.

**Status values:**

- `open`: free to claim.
- `claimed`: someone is working on it (with their handle).
- `done`: result submitted.
- `confirmed`: reproduced independently.
- `blocked`: waiting for another scenario.

**Dependencies:** T0 blocks everything. T9 blocks T1 to T8 for coupling laws (L1 to L8).

Every task, with its files, acceptance criteria and effort, is in `docs/WORK-PLAN.md`. Code tasks also update `ARCHITECTURE.md` (rule D18).

## Stage S1: project infrastructure

| ID | Task | Needs | Difficulty | Status |
|---|---|---|---|---|
| P1 | Package skeleton: `pyproject.toml`, `engine/cosmicmass/`, pytest | none | easy | done |
| P2 | CI job for tests and coverage | P1 | easy | done |
| P3 | Architecture check `tools/check_architecture.py` in CI | none | easy | done |
| P4 | JSON schemas for `stamp.json` and `summary.json` | P1 | easy | done (Claude Opus 5.5 agent, sponsor @MostafaDerraz; pull request waiting for review) |
| P5 | Scenario scaffold `tools/new_scenario.py` | P1, P4 | easy | done (Claude Opus 5.5 agent, sponsor @MostafaDerraz; pull request waiting for review) |
| P6 | Branch protection, labels, description and topics | P2 | maintainer | done 2026-11-14: `main` protected (pull request and the 4 CI checks required; D26), 8 project labels, 9 topics |
| P7 | Ruff lint and format; check the Codespaces dev container | P1 | easy | done (Claude Opus 5.5 agent, sponsor @MostafaDerraz; lint in CI; the first format pass waits for D25) |

## Milestone 1: the engine and the gates

| ID | Scenario | Needs | Difficulty | Status |
|---|---|---|---|---|
| E1 | Algebra core: General Numbers, Rule of the Square, readings Re, Com, Sh, Ht, abs, with unit tests against the compendium | none | easy | done |
| E2 | Field solver: F1-F4 in both coordinates (direct sum for N up to 1e3, grid optional) | E1 | medium | open (claim released 2026-11-14, D28). Delivered by Claude Fable 5.2: E2.1, E2.3, E2.4 delivered; E2.2, E2.5 to do |
| E3 | Integrator: Verlet and Boris, adaptive step, settings stamp | E1 | medium | open (claim released 2026-11-14, D28). Delivered by Claude Fable 5.2: E3.1 and E3.3 delivered; E3.2, E3.4 to do |
| E4 | Law plug-in interface: L0-L8 as switchable readings | E1-E3 | medium | open (claim released 2026-11-14, D28). Delivered by Claude Fable 5.2: E4.1, E4.2, L1a of E4.3 and E4.5 delivered; L1b-L1e and E4.4 to do |
| E5 | State, universe U1-U8, settings loader, seeded populations | E1 | medium | open (claim released 2026-11-14, D28). Delivered by Claude Fable 5.2: E5.1 and a minimal E5.3 delivered |
| E6a | Walls: reflecting, absorbing with collection, wrap-around | E5 | easy | open (claim released 2026-11-14, D28). Delivered by Claude Fable 5.2: reflecting and absorbing walls delivered; wrap-around waits for question 12 of `team/QUESTIONS.md` |
| E6b | Inflow, heat bath, fixed sources | E6a | medium | done (Claude Opus 5.5 agent, sponsor @MostafaDerraz; pull request waiting for review) |
| E7 | Runner, stamp, command line | E3-E5 | medium | open (claim released 2026-11-14, D28). Delivered by Claude Fable 5.2: the time loop, the stamp and the command line delivered; checkpoints and schema validation to do |
| E8 | Diagnostics, convergence helper, standard plots | E7 | medium | open (claim released 2026-11-14, D28). Delivered by Claude Fable 5.2: E8.1 conservation diagnostics delivered; pressure, temperature, E8.2, E8.3 to do |
| E9 | Energy in both coordinates (may need an approved derivation) | E2 | hard | open (claim released 2026-11-14, D28). Delivered by Claude Fable 5.2: the L0 energy delivered; the Composer energy needs an approved derivation |
| G1 | Fast T0 gate in CI on every pull request | T0.1-T0.5 | medium | done (a pytest file; runs in CI with the `tests` job of P2) |
| T0.1 | Earth-moon, hydrogen-like orbit, two protons under L0 | E1-E4 | easy | confirmed (agent, same sponsor; D27): reproduced on Windows by Claude Opus 5.5 |
| T0.2 | Conservation of `rho_mu`, energy and momentum, 200 bodies | E1-E4 | medium | confirmed (agent, same sponsor; D27): reproduced on Windows by Claude Opus 5.5 |
| T0.3 | Angle invariance under L0, six frame angles | T0.1 | easy | confirmed (agent, same sponsor; D27): reproduced on Windows by Claude Opus 5.5 |
| T0.4 | Universal free fall under L0 | T0.1 | easy | confirmed (agent, same sponsor; D27): reproduced on Windows by Claude Opus 5.5 |
| T0.5 | Field split: Composer set equals Maxwell | E2 | easy | confirmed (agent, same sponsor; D27): reproduced on Windows by Claude Opus 5.5 |
| T9.1 | Neutron effective charge 9.0e-19 e under L1a | T0 | easy | confirmed (agent, same sponsor; D27): recomputed independently by Claude Opus 5.5 |
| T9.2 | Hydrogen binding 5.71 eV under the charge share | T0 | medium | done (Claude Opus 5.5 agent, sponsor @MostafaDerraz; to be reproduced by a human or another model) |
| T9.3 | Equivalent field 1.14e11 V/m for a charge in gravity | T0 | easy | confirmed (agent, same sponsor; D27): recomputed independently by Claude Opus 5.5 |
| T9.4 | Opposite pushes for particle and antiparticle near a neutral mass | T0 | easy | confirmed (produced independently by Claude Fable 5.2, #16, and Claude Opus 5.5, #22: same forces, 1.5124e-8 N) |

### The numerical conventions of D21, as scenarios

| ID | Scenario | Needs | Difficulty | Status |
|---|---|---|---|---|
| D21.1 | "2D" as planar motion with a `1/r^2` field, against a tilted 3D run | T0 | easy | done (to be reproduced independently) |
| D21.2 | two-body gates with softening 0, against D10's softening | T0 | easy | done (to be reproduced independently) |
| D21.3 | energy drift: end of run, against the largest excursion | T0 | easy | done (to be reproduced independently) |
| D21.4 | speed floor for bodies at rest: 0, 0.01, 0.1, 1.0 | T0 | easy | done (to be reproduced independently) |

## Milestone 2: what can the Composer coordinate be?

| ID | Scenario | Needs | Difficulty | Status |
|---|---|---|---|---|
| T1.1 | Pure masses: does the Composer part stay silent? | T9 | easy | open |
| T1.2 | Mass with charge: the term `s q g` | T9 | easy | open |
| T1.3 | Charge with charge: the charge share | T9 | easy | open |
| T1.4 | Hydrogen-like pair under every law | T9 | medium | open (a demo under L0 and L1a is delivered, exploratory: `scenarios/T1.4/`, `team/notes/T1.4.md`) |
| T1.5 | Pairs with `Re(mu1 mu2) = 0` (the diagonal) | T9 | medium | open |
| T1.6 | Newton's third law under every law | T9 | easy | open (for L0 and L1a see scenario Q1, `team/notes/Q.md`) |
| T2 | Survival table: 120 coupling definitions sorted into classes A (conserving, angle-free), B (conserving, angle-dependent) and C (non-conserving) | T1 | hard | open |

## Milestone 3: the angle and many bodies

| ID | Scenario | Needs | Difficulty | Status |
|---|---|---|---|---|
| T3.1 | Frame-angle sweep over T1.2-T1.4 | T2 | medium | open |
| T3.2 | The 90-degree universe (charge share off) | T2 | easy | open |
| T3.3 | Mirror angles 10.14 and 79.86 degrees | T2 | easy | open |
| T3.4 | Closing frame (1 and 179 degrees) | T2 | medium | open |
| T4.1 | Charged cloud around a neutral star: separation by sign? | T2 | medium | open |
| T4.2 | Charged dust ring around a planet | T2 | medium | open |
| T4.3 | Self-charging planets: does `Re(mu1 mu2)` fall toward zero? | T2 | hard | open |
| T4.4 | Inflowing wind near a star | T2 | hard | open |
| T4.5 | Gas of bound pairs in a box | T2 | medium | open |

## Milestone 4: motion, populations, robustness

| ID | Scenario | Needs | Difficulty | Status |
|---|---|---|---|---|
| T5.1 | Circling in `B_cal`, Real against Composer reading | T2 | medium | open |
| T5.2 | Parallel streams: the magnetic partner | T2 | medium | open |
| T5.3 | Rotating planet and its `B_cal` | T2 | hard | open |
| T6.1 | Pressure from momentum flux equals `n k T` under L0 | T0 | medium | open |
| T6.2 | Pressure and temperature under surviving laws | T2, T6.1 | medium | open |
| T6.3 | Screening of the field and of the coupling | T6.1 | hard | open |
| T6.4 | Does heat destroy charge separation? | T4.1 | medium | open |
| T7.1-T7.4 | Units, dimension, particle count, time step | any finding | medium | open |
| T8.1-T8.3 | Pure charge, extreme ratios, the diagonal | T2 | medium | open |

## Milestone 5: the interactive universe

| ID | Scenario | Needs | Difficulty | Status |
|---|---|---|---|---|
| UI0 | Design decision of the web universe | E7 | easy | done (D22 proposed: the engine in Pyodide) |
| UI1 | Web viewer: Real and Composer planes, trails, live readings | E1-E4 | medium | in progress (Real plane, trails, readouts, L0 overlay done; Composer plane open) |
| UI2 | Input panels: universe U1-U8, matter as `mu`, law L0-L8 | UI1 | medium | open |
| UI3 | Compare mode: one scene under several laws side by side | UI2 | medium | open |
| UI4 | Saved runs with settings stamps, shareable links | UI2 | medium | open |

## Propose a new scenario

Open an issue with the "Propose a scenario" template. Every proposal must state:

- its setup, written in the language of cosmic masses;
- what it measures;
- what would count as a pass or a finding.
