# Architecture of the Cosmic Mass Lab

This is the **living architecture** of the virtual universe of cosmic masses: the modules, their interfaces, how data flows through one time step, and how a run becomes a confirmed finding.

> **Rule D18: the architecture travels with the code.** Every pull request that adds, changes, moves or removes code in `engine/`, `scenarios/`, `simulator/` or `tools/` updates this file **in the same pull request**:
> 1. the **module registry** (section 2): path, task, status, owner;
> 2. the **Mermaid diagrams** (sections 3 to 9): new nodes, edges and interfaces;
> 3. the **change log** (section 11): one line.
>
> CI enforces it with `tools/check_architecture.py`. A pull request with code changes and no architecture update fails. **AI agents end every coding session by checking this file against what they changed.**

Contents: [1 Principles](#1-design-principles) · [2 Module registry](#2-module-registry) · [3 System context](#3-system-context) · [4 Layers](#4-layers-and-dependencies) · [5 Core types](#5-core-types-and-interfaces) · [6 One time step](#6-one-time-step) · [7 Laws](#7-the-law-pipeline-l0-l8) · [8 Run to finding](#8-from-settings-to-a-confirmed-finding) · [9 CI](#9-continuous-integration) · [10 Interfaces](#10-interface-contracts) · [11 Change log](#11-architecture-change-log) · [12 How to update](#12-how-to-update-this-file)

Status legend used in every diagram: **solid border = implemented**, **dashed border = planned or in progress** (`classDef planned`).

---

## 1. Design principles

1. **One language.** Every quantity is a cosmic mass `mu = m + qG`, a General Number, or a reading of one (`Re`, `Com`, `Sh`, `Ht`, `abs`). No other physics vocabulary in the code (D2).
2. **The verified formulas are the only source.** The algebra core implements the compendium (`docs/formulas-compendium/`) and nothing else; every function cites the compendium equation it implements.
3. **L0 is the reference; L1-L8 are plug-ins.** A law is a swappable object. Every plug-in reduces to L0 when its Composer part is switched off, and a test proves it.
4. **Arrays, not objects, in the hot path.** Bodies are stored as structure-of-arrays (`m`, `q`, `x`, `v`) in NumPy. The scalar `GeneralNumber` class is for tests, exact checks and readability.
5. **Determinism.** Every random draw comes from one seeded generator passed explicitly. The same stamp on the same commit gives the same summary.
6. **Every run is stamped.** The runner, never a human, writes `stamp.json` and `summary.json` (`team/RESULTS-STANDARD.md`).
7. **Small modules, one job each,** each owned by one engine task (E1-E9) and listed in the registry.
8. **Pure functions where possible.** Field solvers and laws take a state and return arrays. Only the integrator and the environment change the state.

---

## 2. Module registry

The single list of every code module, planned or real. **`tools/check_architecture.py` reads this table.** Keep its format: the path in backticks, one row per file or folder, and the status as one of `planned`, `in-progress`, `implemented` or `deprecated`.

- A **planned** path must not exist yet. When you create it, change the status.
- An **in-progress** or **implemented** path must exist.
- Every code file in `engine/`, `scenarios/`, `simulator/` and `tools/` must be covered by a row (a file row, or the row of its folder). `__init__.py` files are covered automatically.
- The **Node** is the node ID used in the Mermaid diagrams. It must appear in at least one diagram (`-` for none, allowed only for scenarios).

<!-- registry:start -->
| Node | Path | Task | Status | Purpose |
|---|---|---|---|---|
| constants | `engine/cosmicmass/constants.py` | E1.1 | implemented | `Constants(G_N, K, c, e, units)` with derived `s = sqrt(K/G_N)` and Stoney mass; the sets `SI` (CODATA 2022) and `SCALED`, and `scaled(c, e)` |
| frame | `engine/cosmicmass/frame.py` | E1.1 | implemented | `Frame(s, phi_bar, units)`: the Composer Unit, its length and frame angle; `square_rule()`; angle in radians, read and written in degrees; exact mode with mpmath values |
| gn | `engine/cosmicmass/gn.py` | E1.2 | implemented | `GeneralNumber`: scalar `+ - * /`, conjugate, `norm_sq`, inverse, `isclose`, with the Rule of the Square; exact mode (mpmath) |
| gnarray | `engine/cosmicmass/gnarray.py` | E1.3 | implemented | `GNArray`: vectorised General Numbers and vector fields (NumPy), same operations and same bits as `GeneralNumber` |
| readings | `engine/cosmicmass/readings.py` | E1.4 | implemented | `Re`, `Com`, `Sh`, `Ht`, `abs` for scalars and arrays |
| matter | `engine/cosmicmass/matter.py` | E1.5 | implemented | `CosmicMass(m, q, name)`, `mu(frame)`, matter presets `PRESETS` (electron, proton, neutron, alpha, dust, planets) |
| state | `engine/cosmicmass/state.py` | E5.1 | implemented | `State`: structure-of-arrays `m, q, x, v, fixed, alive, t`; `mu(frame)`, `total_mu`, `copy`, `from_bodies` |
| universe | `engine/cosmicmass/universe.py` | E5.2 | planned | `Universe`: settings U1-U8 (angle, dimension, units, boundary, backgrounds, sources, inflow, populations) |
| settings | `engine/cosmicmass/settings.py` | E5.3 | in-progress | load and validate `settings.json`; build `Frame`, `State`, `LawSpec`, numerics (minimal MVP version; `Universe` and the P4 schemas come later) |
| populations | `engine/cosmicmass/populations.py` | E5.4 | implemented | seeded generators (`generate`): shapes `box`, `shell`, `ring`; bulk flow, thermal spread at a temperature (with the real particle's mass), Keplerian circular speeds; super-particles (`weight`); used by the settings key `populations` |
| fieldsample | `engine/cosmicmass/fields/sample.py` | E4.2 | implemented | `FieldSample(g, e, B_g, b, screened=None)` with `E_cal(frame)` and `B_cal(frame)`; `screened` holds the screened field for option L8; the `FieldSolver` interface |
| fields | `engine/cosmicmass/fields/direct.py` | E2.1 | in-progress | direct-sum field solver `DirectSum`: static `g`, `e` (F1-F2) with Plummer softening, no self-field, uniform backgrounds (U5); `at_bodies_screened` and `debye_length` (option L8: the kernel `exp(-r/L)(1 + r/L)/r^2` over the Debye length of the population); `B_g`, `b` from moving bodies (F3-F4, task E2.2) not yet |
| fieldsfast | `engine/cosmicmass/fields/tree.py` | E2.5 | planned | fast solver for large N (tree or grid), same interface |
| lawbase | `engine/cosmicmass/laws/base.py` | E4.1 | implemented | `Law` base class, `LawSpec` (reading and L2-L8 options, stamp form), `ForcePair`, registry of laws (`register`, `make_law`); `third_law_residual` (E4.5); `Law.inertia` reads the option L7 (`Re`, `Sh`, `abs` of `mu`; E3.4) |
| l0 | `engine/cosmicmass/laws/l0.py` | E4.2 | implemented | reference law L0: `Re(mu) dv/dt = Re[mu (E_cal + v x B_cal)]` |
| l1 | `engine/cosmicmass/laws/l1.py` | E4.3 | in-progress | readings L1a-L1d of the Composer coordinate (hypotheses), each L0 plus `+/- lambda` times what the reading adds (labelled rule, `team/notes/E4.md`), with the options sign (L2), strength (L3), direction (L4: radial, perpendicular, along the velocity), terms (L5), moving bodies (L6), inertia (L7) and range (L8: screened); L1e and the direction "torque" not yet (question 24) |
| modifiers | `engine/cosmicmass/laws/modifiers.py` | E4.4 | planned | L2 sign, L3 strength, L4 direction, L5 terms, L6 moving bodies, L7 inertia, L8 range |
| integrators | `engine/cosmicmass/integrators.py` | E3.1 | in-progress | `VelocityVerlet` with the adaptive time step of D10, `StepContext` (law, solver, frame, numerics); `Boris` (E3.2: velocity Verlet whose half kicks are Boris pushes, for `v x B_cal`; chosen by the settings when a background `B_g` or `b` is present, D10); the inertia readings (E3.4) not yet; the step rule of D29: relative to the nearest neighbour by default (`speed_reference = "neighbour"`; `"absolute"` keeps D10 and D21), plus the pair guard `eta min r_ij / |v_ij|` (`pair_approach_time`) |
| environment | `engine/cosmicmass/environment.py` | E6 | in-progress | `Environment`: reflecting walls (velocity turned back, body not moved, impulse reported) and absorbing walls with a collector of mass, charge and momentum; `Inflow` (U7: bodies enter through one face, `floor(rate t)` of them, seeded places), `HeatBath` (Andersen), `kinetic_temperature`, `K_B`; fixed sources (U6) are never touched. Wrap-around and absorbing surfaces of bodies not yet |
| diagnostics | `engine/cosmicmass/diagnostics.py` | E8.1 | implemented | `Diagnostics.measure` and `drifts`: conservation of mass, charge, energy (`Re`; `Com` not defined until E9), momentum, and the temperature of the moving bodies; the pressure on the walls is `runner.wall_pressure` |
| energy | `engine/cosmicmass/energy.py` | E9 | implemented | energy of the bodies in both coordinates: under L0 (kinetic, Newton plus Coulomb interaction, uniform background), and the Composer energy `-G lambda s sum Com(mu_a mu_b) / r` of decision D23 within its scope (L1a, all terms, radial, inertia `Re`, no second field, no background `g`, `e`); `None` (not defined) outside it |
| runner | `engine/cosmicmass/runner.py` | E7.1 | in-progress | `run(settings) -> RunResult`: the time loop, stop conditions, outputs; `main(argv)` for the command line (E7.3); checkpoints and resuming not yet |
| cli | `engine/cosmicmass/__main__.py` | E7.3 | implemented | `python -m cosmicmass run <settings.json>`: calls `runner.main` |
| stamp | `engine/cosmicmass/stamp.py` | E7.2 | in-progress | run id, engine commit, `stamp.json`, `summary.json`, `timeseries.csv`; the T0 status lookup (after G1) and validation against the P4 schemas not yet |
| convergence | `engine/cosmicmass/analysis/convergence.py` | E8.2 | implemented | `convergence(settings, measure, counts=(), resize=None)`: re-run at the step (eta or dt) / 2 and / 4, and at other body counts through the scenario's `resize`; the convergence block of the results standard with relative changes and `converged` (change < 1%) |
| plots | `engine/cosmicmass/analysis/plots.py` | E8.3 | implemented | standard figures in plain SVG (standard library), made from one results folder alone, byte for byte: drifts against time, trails in the Real plane, the cosmic masses in the General Number plane; `line_plot`, `scatter_plot` for sweeps |
| tests | `engine/tests/` | P1 | implemented | unit tests for every module (pytest), run in CI with coverage (P2); so far `test_pins.py` (pins of `pyproject.toml` equal `requirements.txt`), `test_import.py`, `test_constants_frame.py` (E1.1), `test_gn.py` (E1.2), `test_gnarray.py` (E1.3), `test_readings_matter.py` (E1.4, E1.5), `test_compendium.py` (E1.6), `test_state_laws.py` (E5.1, E4.1, E4.2), `test_settings.py` (E5.3), `test_fields.py` (E2.1, E2.3, E2.4), `test_integrators.py` (E3.1, E3.3, E6a; one test marked `slow`), `test_runner.py` (E7.1 to E7.3, E8.1, E9), `test_l1a.py` (E4.3, L1a) |
| gate | `engine/cosmicmass/gates/t0.py` | T0, G1 | implemented | the consistency gate T0.1 to T0.5 as functions (`t0_1` ... `t0_5`, `run_gate`), and `write_gate_result` |
| limits | `engine/cosmicmass/gates/t9.py` | T9.1-T9.4 | implemented | the measured limits T9.1 to T9.4 under L1a as functions (`t9_1`, `t9_2`, `t9_3`, `t9_4`); `t9_2` also integrates one orbit with the runner |
| gatetests | `engine/gates/` | G1 | implemented | fast T0 gate and fast T9.1 to T9.4 checks, run by pytest (in CI with the `tests` job of P2) |
| - | `scenarios/T1.4/` | T1.4 (demo) | in-progress | demo of version 0.1.0: hydrogen-like pair under L0 and L1a, exploratory; `run.py` and `figures.py` (SVG, standard library) |
| - | `scenarios/T9.1/` | T9.1 | implemented | neutron effective charge 9.0e-19 e under L1a |
| - | `scenarios/T9.2/` | T9.2 | implemented | hydrogen under the charge share (L5c): the pull falls to 0.648 of Coulomb's; binding energy 5.71 eV by the book's scaling, against 13.598 eV |
| - | `scenarios/T9.3/` | T9.3 | implemented | equivalent field 1.14e11 V/m for a charge in gravity (L5a) |
| - | `scenarios/T9.4/` | T9.4 | implemented | a proton and an antiproton (`m_p - e G`) near the neutral Earth under L1a: opposite Composer pushes |
| - | `scenarios/Q/` | Q1-Q3 | implemented | open questions run against their alternatives: third law under L1a, energy candidates of L1a, value of `K` |
| - | `scenarios/Q4/` | Q4 | implemented | the adaptive step and the frame of description: the current rule against a rule relative to the nearest neighbour |
| - | `scenarios/Q5/` | Q5 | implemented | the nearest-neighbour step (rule B of Q4) on a fast passage, and a pair guard (rule C, written in the script, not in the engine); answers question 14 |
| - | `scenarios/T0.1/` | T0.1 | implemented | Earth-moon, hydrogen-like orbit, two protons under L0 |
| - | `scenarios/T0.2/` | T0.2 | implemented | conservation of `rho_mu`, energy and momentum, 200 bodies in a reflecting box |
| - | `scenarios/T0.3/` | T0.3 | implemented | angle invariance under L0, six frame angles |
| - | `scenarios/T0.4/` | T0.4 | implemented | universal free fall under L0 |
| - | `scenarios/T0.5/` | T0.5 | implemented | field split: the Composer part of one proton's field is Coulomb's field |
| - | `scenarios/D21/` | D21.1-D21.4 | implemented | the four numerical conventions of decision D21 run against their alternatives (`run.py 1..4`) |
| archcheck | `tools/check_architecture.py` | P3 | implemented | checks this registry and the diagrams against the code (rule D18) |
| chat | `tools/chat.py` | team chat (question 23, proposed) | implemented | the team chat in `team/chat/`: one message per file; `post`, `read` (inbox: `--to`, `--since`), `thread`; standard library only |
| schemas | `engine/schemas/` | P4 | implemented | JSON schemas (draft 2020-12) of `stamp.json` and `summary.json`, from `team/RESULTS-STANDARD.md`, sections 2 and 4; each has two forms: one run, or a test with cases |
| validate | `tools/validate_results.py` | P4 | implemented | validates the results folders against `engine/schemas/`, one readable line per problem; used by `engine/tests/test_schemas.py` on every committed result. Outside the package, so the web universe does not load `jsonschema` |
| scaffold | `tools/new_scenario.py` | P5 | implemented | creates `scenarios/<ID>/` (`settings.json`: a valid 10-step L0 start; `run.py`: calls the runner, `--dry-run` writes nothing), the notebook from `team/notes/_TEMPLATE.md` and a registry row; never overwrites |
| webui | `simulator/web/` | UI1 | in-progress | interactive universe in the browser: the unchanged engine runs in Pyodide in a web worker (`worker.js`, `bridge.py`); page `index.html`, `app.js`; `engine-files.json` lists the engine files it loads (D22, proposed) |
| journal | `tools/build_journal.py` | D34 | implemented | builds the Co-exist Journal (`journal/`): checks the entries of `journal/entries/` (front matter, authors, kinds, labels, the teaching side of D35) and writes the static site (index, entry pages with discussion, authors with the AI teaching register, discussion page, Atom feed); `--check` fails if the committed site is stale. Uses `markdown`, `pymdown-extensions`, `pyyaml` (dev extras); outside the package |
| gallery | `tools/make_gallery.py` | - | implemented | draws the figures of `docs/GALLERY.md` (SVG, standard library) from the stored results |
<!-- registry:end -->

### Scenario scripts

Add one row to the registry above for each scenario folder you create, with Node `-`, for example:
`| - | \`scenarios/T0.1/\` | T0.1 | implemented | Earth-moon, hydrogen-like orbit, two protons under L0 |`

---

## 3. System context

Who and what surrounds the engine.

```mermaid
flowchart LR
    classDef planned stroke-dasharray: 5 5
    H["Contributors<br/>humans and AI agents<br/>with sponsors"]
    REPO[("Repository<br/>team memory:<br/>LOG, DECISIONS, FINDINGS,<br/>notes, ARCHITECTURE")]
    COMP["Compendium<br/>verified formulas"]
    ENGINE["Engine<br/>engine/cosmicmass"]:::planned
    SCEN["Scenarios<br/>scenarios/ID/run.py"]:::planned
    RES[("Results<br/>results/ID/run-id/")]:::planned
    UI["Interactive universe<br/>simulator/web"]
    CI["CI<br/>verification, tests,<br/>T0 gate, archcheck"]
    REP["Reports<br/>findings atlas, papers,<br/>data release"]:::planned

    H -->|"claim, pre-register,<br/>code, review"| REPO
    COMP -->|"only source of formulas"| ENGINE
    SCEN -->|"settings.json"| ENGINE
    ENGINE -->|"stamp, summary,<br/>timeseries"| RES
    RES --> REPO
    RES --> UI
    ENGINE --> UI
    REPO --> CI
    CI -->|"green or red"| H
    REPO -->|"confirmed findings"| REP
```

---

## 4. Layers and dependencies

Arrows mean "uses". A module may use only modules in its own layer or in the layers below it. Upward imports are forbidden.

```mermaid
flowchart TB
    classDef planned stroke-dasharray: 5 5

    subgraph L5["Layer 5: applications"]
        direction LR
        webui["simulator/web<br/>(engine in Pyodide)"]
        scaffold["tools/new_scenario.py"]
        archcheck["tools/check_architecture.py"]
        chat["tools/chat.py<br/>(team chat, team/chat/)"]
        validate["tools/validate_results.py"]
        schemas["engine/schemas<br/>(stamp, summary)"]
        gallery["tools/make_gallery.py"]
        journal["tools/build_journal.py<br/>(Co-exist Journal, journal/)"]
        cli["python -m cosmicmass<br/>__main__.py"]
        scen["scenarios/ID/run.py"]
        gate["gates/t0.py"]
        limits["gates/t9.py"]
        tests["engine/tests"]
        gatetests["engine/gates (T0 in CI)"]
    end

    subgraph L4["Layer 4: orchestration and analysis"]
        direction LR
        runner["runner.py"]:::planned
        stamp["stamp.py"]:::planned
        settings["settings.py"]:::planned
        convergence["analysis/convergence.py"]
        plots["analysis/plots.py"]
    end

    subgraph L3["Layer 3: dynamics"]
        direction LR
        integrators["integrators.py"]:::planned
        environment["environment.py"]:::planned
        diagnostics["diagnostics.py"]
        energy["energy.py"]:::planned
    end

    subgraph L2["Layer 2: physics of the virtual universe"]
        direction LR
        fieldsample["fields/sample.py"]
        fields["fields/direct.py"]:::planned
        fieldsfast["fields/tree.py"]:::planned
        lawbase["laws/base.py"]
        l0["laws/l0.py"]
        l1["laws/l1.py"]:::planned
        modifiers["laws/modifiers.py"]:::planned
        universe["universe.py"]:::planned
        populations["populations.py"]
    end

    subgraph L1["Layer 1: algebra and data"]
        direction LR
        constants["constants.py"]
        frame["frame.py"]
        gn["gn.py"]
        gnarray["gnarray.py"]
        readings["readings.py"]
        matter["matter.py"]
        state["state.py"]
    end

    scen --> runner
    cli --> runner
    gallery --> gate
    gallery --> runner
    gallery --> fields
    scen --> settings
    gatetests --> gate
    gatetests --> limits
    scen --> limits
    limits --> settings
    limits --> fields
    limits --> gate
    limits --> runner
    scen --> gate
    gate --> runner
    gate --> settings
    gate --> stamp
    tests -.->|"any layer"| gn
    tests --> validate
    tests --> chat
    tests --> journal
    validate --> schemas
    webui --> runner
    scaffold -.->|"writes settings.json and run.py,<br/>which use"| settings
    scaffold -.-> scen
    runner --> integrators
    runner --> environment
    runner --> diagnostics
    runner --> stamp
    runner --> settings
    runner --> fields
    settings --> universe
    settings --> populations
    settings --> lawbase
    settings --> state
    settings --> matter
    convergence --> runner
    plots --> constants
    diagnostics --> environment
    integrators --> fields
    integrators --> environment
    integrators --> lawbase
    integrators --> state
    settings --> environment
    diagnostics --> energy
    energy --> gnarray
    energy --> state
    diagnostics --> state
    environment --> state
    l0 --> lawbase
    l1 --> lawbase
    modifiers --> lawbase
    lawbase --> fieldsample
    lawbase --> state
    lawbase --> gnarray
    fields --> fieldsample
    fieldsfast --> fieldsample
    fieldsample --> gnarray
    state --> gnarray
    lawbase --> readings
    fields --> state
    fields --> constants
    fieldsfast --> gnarray
    universe --> frame
    populations --> matter
    populations --> state
    populations --> environment
    gnarray --> gn
    gn --> frame
    readings --> gn
    frame --> constants
    matter --> gn
    state --> matter
```

The test folders `engine/tests/` (node `tests`) and `engine/gates/` (node `gatetests`) may import any layer.

---

## 5. Core types and interfaces

```mermaid
classDiagram
    class Frame {
        +float s
        +float phi_bar
        +str units
        +phi_bar_deg float
        +cos_phi() float
        +sin_phi() float
        +square_rule() tuple
        +from_degrees(s, deg, units) Frame
        +to_dict() dict
    }
    class GeneralNumber {
        +float re
        +float com
        +Frame frame
        +add(other) GeneralNumber
        +mul(other) GeneralNumber
        +conjugate() GeneralNumber
        +norm_sq() float
        +inverse() GeneralNumber
        +isclose(other, rel_tol, abs_tol) bool
    }
    class GNArray {
        +ndarray re
        +ndarray com
        +Frame frame
        +tuple shape
        +mul(other) GNArray
        +conjugate() GNArray
        +norm_sq() ndarray
        +inverse() GNArray
        +item(index) GeneralNumber
        +allclose(other, rel_tol, abs_tol) bool
    }
    class Readings {
        +Re(x)
        +Com(x)
        +Sh(x)
        +Ht(x)
        +abs(x)
    }
    class CosmicMass {
        +float m
        +float q
        +str name
        +mu(frame) GeneralNumber
        +with_charge(q) CosmicMass
    }
    class State {
        +ndarray m
        +ndarray q
        +ndarray x
        +ndarray v
        +ndarray fixed
        +ndarray alive
        +float t
        +mu(frame) GNArray
        +total_mu(frame, alive_only) GNArray
        +copy() State
    }
    class Universe {
        +Frame frame
        +int dimension
        +str boundary
        +dict background
        +list sources
        +dict inflow
    }
    class FieldSample {
        +ndarray g
        +ndarray e
        +ndarray B_g
        +ndarray b
        +E_cal(frame) GNArray
        +B_cal(frame) GNArray
    }
    class FieldSolver {
        <<interface>>
        +sample(state, points) FieldSample
        +at_bodies(state) FieldSample
    }
    class LawSpec {
        +str reading
        +str sign
        +float strength
        +str direction
        +str terms
        +str moving
        +str inertia
        +str range
        +to_dict() dict
        +from_dict(data) LawSpec
    }
    class Law {
        <<interface>>
        +str id
        +LawSpec spec
        +forces(state, fields, frame) ForcePair
        +inertia(state, frame) ndarray
    }
    class ForcePair {
        +ndarray real
        +ndarray composer
    }
    class StepContext {
        +Law law
        +FieldSolver solver
        +Frame frame
        +float eta
        +float dt_min
        +float dt_max
        +acceleration(state) ndarray
        +invalidate()
    }
    class Integrator {
        <<interface>>
        +step(state, dt, context) State
        +next_dt(state, context) float
    }
    class VelocityVerlet {
        +step(state, dt, context) State
        +next_dt(state, context) float
    }
    class Boris {
        +step(state, dt, context) State
    }
    Integrator <|.. VelocityVerlet
    VelocityVerlet <|-- Boris
    class Environment {
        +Inflow inflow
        +HeatBath heat_bath
        +apply(state, dt, rng) list
    }
    class Inflow {
        +int added
        +apply(state, rng) dict
    }
    class HeatBath {
        +float temperature
        +int collisions
        +apply(state, dt, rng) dict
    }
    Environment --> Inflow
    Environment --> HeatBath
    class Diagnostics {
        +measure(state, fields) dict
    }
    class Runner {
        +run(settings) RunResult
    }
    class RunResult {
        +dict stamp
        +dict summary
        +path folder
        +State state
        +list timeseries
    }

    GeneralNumber --> Frame
    GNArray --> Frame
    CosmicMass --> GeneralNumber
    State --> CosmicMass : columns m, q
    Universe --> Frame
    FieldSolver --> FieldSample
    Law --> LawSpec
    Law --> ForcePair
    Law ..> FieldSample : uses
    Law ..> Readings : uses
    Integrator ..> Law : uses
    Integrator ..> FieldSolver : uses
    Integrator ..> StepContext : uses
    Runner --> Integrator
    Runner --> Environment
    Runner --> Diagnostics
    Runner --> RunResult
```

**Algebra of the core** (compendium; `s = |G|`, `phi = phi_bar`):

- product: `(a + bG)(c + dG) = (ac - s^2 bd) + (ad + bc + 2 s cos(phi) bd) G`
- the full product with the field: `mu E_cal = [m g + q E] + [q g - m E/s^2 - (2 cos(phi)/s) q E] G`, with `E = -s^2 e`
- readings of `x = a + bG`: `Re = a`, `Com = b`, `Sh = a + b s cos(phi)`, `Ht = b s sin(phi)`, `abs = sqrt(Sh^2 + Ht^2)`

---

## 6. One time step

The default integrator is velocity Verlet (Boris when `B_cal` is on), with an adaptive step (D10).

```mermaid
sequenceDiagram
    autonumber
    participant R as runner
    participant I as integrators
    participant F as fields
    participant L as law (l0 / l1 + modifiers)
    participant E as environment
    participant D as diagnostics

    R->>I: next_dt(state)
    I-->>R: dt (largest velocity change below 1e-3 of the speed)
    R->>I: step(state, dt)
    I->>F: sample(state, positions)
    F-->>I: g, e, B_g, b at each body (softened, no self-field)
    I->>L: forces(state, fields, frame)
    Note over L: product mu (E_cal + v x B_cal) in both coordinates,<br/>then the reading: L0 keeps Re only,<br/>L1-L8 add the Composer force
    L-->>I: ForcePair(real, composer)
    I->>L: inertia(state, frame)
    L-->>I: Re(mu), Sh(mu) or abs(mu) (L7)
    I->>I: half kick, drift, new fields, half kick
    I-->>R: new state
    R->>E: apply(state, dt, rng)
    E-->>R: walls, absorption (charge collected into q), inflow, heat bath
    R->>D: measure(state, fields)
    D-->>R: mass, charge, energy (Re, Com), momentum, drifts
    alt drift beyond tolerance
        R->>R: halve dt and repeat the step (logged)
    end
```

---

## 7. The law pipeline (L0-L8)

```mermaid
flowchart LR
    classDef planned stroke-dasharray: 5 5
    classDef ref fill:#e8f5e9,stroke:#2e7d32

    IN["state + fields<br/>mu = m + qG<br/>E_cal = g + eG<br/>B_cal = B_g + bG"]
    PROD["product<br/>mu (E_cal + v x B_cal)<br/>both coordinates"]:::planned
    RE["Re part<br/>m g + q E<br/>= Newton + Coulomb"]:::ref
    COM["Com part<br/>q g - m E/s^2<br/>- (2cos phi/s) q E"]:::planned

    subgraph SEL["l1: reading of the Composer coordinate"]
        L1a["L1a: Re + lambda s Com"]
        L1b["L1b: Sh"]
        L1c["L1c: Ht"]
        L1d["L1d: abs"]
        L1e["L1e: motion in two coordinates"]
    end

    subgraph MOD["modifiers"]
        L2["L2 sign"]
        L3["L3 strength lambda"]
        L4["L4 direction:<br/>radial, perpendicular,<br/>torque, along v"]
        L5["L5 terms"]
        L6["L6 moving bodies"]
        L8["L8 range"]
    end

    L7["L7 inertia:<br/>Re(mu), Sh(mu), abs(mu)"]
    L0OUT["l0: force = Re part<br/>inertia Re(mu) = m"]:::ref
    OUT["acceleration"]

    IN --> PROD
    PROD --> RE
    PROD --> COM
    RE --> L0OUT --> OUT
    COM --> SEL --> MOD --> OUT
    RE --> SEL
    L7 --> OUT
```

**The reduce-to-L0 test.** For every law and every combination of modifiers, setting the strength to 0 (or switching off the Composer terms) must give L0 exactly: forces equal to 1e-15 relative, on the T0.1 states.

---

## 8. From settings to a confirmed finding

```mermaid
flowchart LR
    classDef planned stroke-dasharray: 5 5
    N["team/notes/ID.md<br/>pre-registration<br/>(committed first)"]
    S["scenarios/ID/settings.json"]:::planned
    RUN["scenarios/ID/run.py"]
    ENG["engine: runner"]:::planned
    OUT["results/ID/run-id/<br/>stamp.json<br/>summary.json<br/>timeseries.csv<br/>figures/"]:::planned
    PR["pull request<br/>+ result issue"]
    REV["independent reproduction<br/>(human or other model)"]
    F["team/FINDINGS.md<br/>done, confirmed,<br/>disputed, withdrawn"]

    N --> S --> RUN --> ENG --> OUT --> PR --> REV --> F
    REV -.->|"not reproduced"| PR
```

```mermaid
stateDiagram-v2
    [*] --> claimed
    claimed --> preregistered: notebook committed
    preregistered --> running
    running --> done: PR merged, stamped results
    done --> confirmed: independent reproduction
    done --> disputed: reproduction differs
    disputed --> confirmed: third reproduction agrees
    disputed --> withdrawn
    confirmed --> published
    confirmed --> withdrawn: error found later
    withdrawn --> [*]
    published --> [*]
```

---

## 9. Continuous integration

```mermaid
flowchart LR
    classDef planned stroke-dasharray: 5 5
    PUSH["push or pull request"]
    V["verify: 6 verification scripts<br/>(10,000+ checks)"]
    A["archcheck:<br/>tools/check_architecture.py<br/>registry, diagrams, D18"]
    R["lint: ruff check<br/>(pinned in pyproject.toml)"]
    T["tests: pytest engine/tests<br/>coverage at least 90%"]
    G["gate: T0 fast run<br/>engine/gates"]:::planned
    OK["green: may merge<br/>(one approving review)"]
    NO["red: fix before merge"]

    PUSH --> V --> OK
    PUSH --> A --> OK
    PUSH --> R --> OK
    R -.-> NO
    PUSH --> T --> G --> OK
    V -.-> NO
    A -.-> NO
    T -.-> NO
    G -.-> NO
```

---

## 10. Interface contracts

These signatures are the contract between tasks. Changing one is a decision with 7 days of comment (`TEAM.md`, section 2.2), because others build against it.

```python
# frame.py
class Frame:
    s: float            # |G| = sqrt(K/G_N) in SI, 1 in scaled units
    phi_bar: float      # frame angle in radians
    units: str          # "SI" or "scaled"
    def cos_phi(self) -> float: ...
    def sin_phi(self) -> float: ...
    def square_rule(self) -> tuple: ...   # (p, q) with G^2 = p + q G: p = -s^2, q = 2 s cos(phi_bar)

# gn.py: one General Number re + com G (tests, exact checks; not the hot path)
class GeneralNumber:
    re: float
    com: float
    frame: Frame
    def mul(self, other) -> "GeneralNumber": ...      # also + - * / with real scalars
    def inverse(self) -> "GeneralNumber": ...
    def norm_sq(self) -> float: ...                   # |z|^2 = Sh^2 + Ht^2

# gnarray.py: General Numbers on arrays; vector fields have shape (N, d)
class GNArray:
    re: np.ndarray
    com: np.ndarray
    frame: Frame
    def mul(self, other) -> "GNArray": ...           # also + - * / with GeneralNumber, real scalars and real arrays
    def inverse(self) -> "GNArray": ...
    def norm_sq(self) -> np.ndarray: ...
    def item(self, *index) -> GeneralNumber: ...
    # N numbers times an (N, d) vector field: mu[:, None] * field (NumPy broadcasting)

# readings.py: Re, Com, Sh, Ht, abs take a GeneralNumber or a GNArray, return real numbers or arrays
def Com(z): ...         # the Composer coordinate b (not the part b G)

# matter.py
@dataclass(frozen=True)
class CosmicMass:
    m: float            # kg
    q: float            # C
    name: str = ""
    def mu(self, frame: Frame) -> GeneralNumber: ...

# state.py: structure of arrays, N bodies, dimension d (2 or 3)
@dataclass
class State:
    m: np.ndarray       # (N,)  kg
    q: np.ndarray       # (N,)  C
    x: np.ndarray       # (N, d) m
    v: np.ndarray       # (N, d) m/s
    fixed: np.ndarray   # (N,) bool: pinned sources (U6)
    alive: np.ndarray   # (N,) bool: absorbed bodies are switched off, never deleted
    t: float

# fields: every solver has the same signature
class FieldSolver(Protocol):
    def sample(self, state: State, points: np.ndarray) -> FieldSample: ...
    # FieldSample.g, .e: (P, d); .B_g, .b: (P, 3) in 3D, (P,) in 2D
    # FieldSample.screened: FieldSample | None = None (E4.4, addition): the screened field, filled by the
    #   StepContext only for a law with range "screened" (L8); DirectSum.at_bodies_screened(state, length)
# fields/direct.py: DirectSum(constants=SI, softening=0.0, background=None) is a FieldSolver, and adds
#   at_bodies(state) -> FieldSample     the field at every body from the other alive bodies (no self-field)

# laws/base.py: a base class (was a Protocol); the members are unchanged
class Law:
    id: str             # "L0", "L1a", ...
    spec: LawSpec       # the reading and every L2-L8 option; spec.to_dict() is the "law" block of stamp.json
                        # LawSpec.moving (L6) is "off" | "on" | "only", written as "B_cal" in the stamp
    def forces(self, state: State, fields: FieldSample, frame: Frame) -> ForcePair: ...
    def inertia(self, state: State, frame: Frame) -> np.ndarray: ...
# ForcePair(real, composer): shape (N, d) each; the force applied is real + composer (composer is 0 under L0)
def make_law(spec: LawSpec | str) -> Law: ...
def third_law_residual(law: Law, state: State, solver, frame: Frame) -> dict: ...   # E4.5: pair, residual, force, relative

# settings.py
def load_settings(source: Path | str | dict) -> Settings: ...
# Settings: scenario, frame, universe (dict), law_spec, state, bodies, numerics (dict), meta (dict)
#   settings key "populations" (E5.4, addition): a list of seeded populations, generated after the listed
#   bodies from numerics.seed; meta["populations"] and stamp["populations"] keep them as given (only when used)
# populations.py (E5.4)
def generate(spec: dict, d: int, constants, rng, real: tuple) -> dict: ...   # {"m", "q", "x", "v"} of one population

# integrators.py
class Integrator(Protocol):
    def next_dt(self, state: State, ctx: StepContext) -> float: ...
    def step(self, state: State, dt: float, ctx: StepContext) -> State: ...
# StepContext(law, solver, frame, eta=1e-3, dt_min=0.0, dt_max=inf): acceleration(state) is force / inertia
#   for moving bodies and zero for fixed or absorbed ones; it remembers the last result, so call
#   invalidate() after changing a state outside the integrator (for example after a wall acted)
#   speed_reference="neighbour" (the default since D29) or "absolute" (D10 and D21: each body's own motion);
#   next_dt always applies the pair guard of D29: dt <= eta * pair_approach_time(state)
def pair_approach_time(state) -> float: ...   # min over pairs of alive bodies of r_ij / |v_i - v_j| (D29)
#   StepContext.rotation(state) -> Omega: v x Omega is the velocity-dependent acceleration, Omega =
#     (m B_g - s^2 q b) / inertia; shape (N,) in 2D, (N, 3) in 3D (E3.2, addition)
#   StepContext.remember(state, a): replace the remembered acceleration of the same state (E3.2, addition)
class Boris(VelocityVerlet): ...   # E3.2: the same next_dt; step() refuses a law with L6 on
def boris_rotation(v, omega, h) -> np.ndarray: ...   # turns v as dv/dt = v x Omega over h, speed kept exactly
# settings: numerics.integrator "verlet" | "boris"; left out, "boris" when a background B_g or b is not zero (D10)

# environment.py
class Environment:      # Environment(boundary="open" | "reflecting" | "absorbing", lower=None, upper=None,
                        #             inflow: Inflow | None = None, heat_bath: HeatBath | None = None)   (E6b: additions)
    def apply(self, state: State, dt: float, rng=None) -> list: ...   # acts in place: walls, then inflow, then bath
    # events: walls {"wall", "bodies", "impulse"[, "absorbed"]}; {"inflow": {"bodies", "m", "q"}}; {"heat_bath": {"bodies"}}
    # rng (a seeded generator) is required when there is an inflow or a heat bath; the runner passes default_rng(seed)
class Inflow:           # Inflow(m, q, rate, velocity, axis, side, lower, upper, name="", t0=0.0); appends bodies to the state
class HeatBath:         # HeatBath(temperature, collision_rate, k_b)
def kinetic_temperature(state, k_b) -> float: ...   # sum m v^2 / (d N k_B) over alive, moving bodies
    # Environment.collected: {"bodies", "m", "q", "momentum"} taken by absorbing walls; boundary is "open" | "reflecting" | "absorbing"

# runner.py
def run(settings: Settings, out_root: Path = Path("results")) -> RunResult: ...
# `settings` may also be a path or a dictionary; out_root=None writes nothing.
# RunResult: stamp, summary, folder (results/<scenario>/<run-id>/ or None), state (final), timeseries (rows)
def main(argv=None) -> int: ...     # python -m cosmicmass run <settings.json> [--out results]
def wall_pressure(box, load, elapsed) -> dict | None: ...   # E8.1: summary["walls"]: momentum and pressure of
#   each wall ("<axis>-<side>"), "pressure_mean" over the boundary (2D: per unit length), "elapsed"; None without a box

# diagnostics.py
class Diagnostics:      # Diagnostics(frame, constants, softening=0.0, background=None, law=None)
    def measure(self, state: State, fields=None) -> dict: ...
    # keys: t, temperature (E8.1, addition), mass, charge, kinetic, energy_re, energy_com (None: not defined),
    #   momentum, momentum_scale

# analysis/convergence.py (E8.2)
def convergence(settings, measure, counts=(), resize=None, tolerance=0.01) -> dict: ...
#   block: step {step, step/2, step/4}, change_step_half_to_quarter, change_step_to_half, [counts, change_with_count],
#   largest_change, tolerance, converged
# analysis/plots.py (E8.3)
def figures(folder) -> list[Path]: ...   # folder/figures/drifts.svg, trails.svg, mu_plane.svg, from the folder alone
def line_plot(path, curves, x_label, y_label, caption, square=False) -> Path: ...
def scatter_plot(path, points, x_label, y_label, caption, axes=()) -> Path: ...
def drifts(first: dict, last: dict) -> dict: ...   # relative drifts of mass, charge, energy_re, energy_com, energy_total, momentum
# measure() rows: energy_com (D23, None if not defined) and energy_total (what the law conserves; None if not defined)

# energy.py (E9: both coordinates)
def energy_l0(state, frame, constants, softening=0.0, background=None) -> dict: ...
# keys: kinetic, interaction (-G_N sum Re(mu_a mu_b) / r), background (-sum Re[mu E_cal] . x), total
def composer_energy(state, law, frame, constants, softening=0.0, background=None) -> float | None: ...
# decision D23: -G_N lambda s sum_{a<b} Com(mu_a mu_b) / r within D23_SCOPE; None outside it
```

```python
# tools/validate_results.py (P4): outside the package
def validate(data, name: str) -> list[str]: ...      # name: "stamp" | "summary"; [] if valid, else "place: problem" lines
def validate_folder(folder) -> list[str]: ...        # both files of one run folder
def main(argv=None) -> int: ...                      # python tools/validate_results.py [folders]; 0 if all valid

# tools/new_scenario.py (P5): outside the package
def scaffold(scenario: str, title: str, root=ROOT) -> list[Path]: ...   # raises ScaffoldError; writes nothing on error
def main(argv=None) -> int: ...                      # python tools/new_scenario.py <ID> "<title>"; 2 on error

# tools/build_journal.py (D34, D35): outside the package
def read_entries() -> tuple[list[Entry], list[str]]: ...   # entries newest first, and one line per problem
def build(entries) -> dict[str, str]: ...            # the site, {path under journal/: text}; deterministic
def open_threads(entries, run=None) -> list[str]: ...   # editors: a GitHub Discussions thread per new entry (gh); recorded in journal/discussion.json
def main(argv=None) -> int: ...                      # python tools/build_journal.py [--check | --open-threads]; 1 on a problem

# tools/chat.py (team chat, question 23): outside the package, standard library only
def post(sender, to, subject, body, re_id="", folder=CHAT, now=None) -> Path: ...   # one new file; ChatError, nothing written
def load(folder=CHAT) -> list[Message]: ...          # every message, oldest first (README.md excluded)
def inbox(messages, name="", since="") -> list[Message]: ...   # to `name` and to all, on or after YYYY-MM-DD
def thread(messages, root_id) -> list[Message]: ...  # a message and every reply to it
```

**Units:** SI everywhere inside the engine. Scaled units (`G_N = K = 1`, `s = 1`) are a `Frame` and `constants` choice, never a hidden factor (D7).

---

## 11. Architecture change log

Newest first. One line per pull request that changed the architecture.

| Date | Pull request | Who | Change |
|---|---|---|---|
| 2026-11-14 | E5.4 (`E5-populations`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | **new** `populations.py` (node no longer planned; new edge `populations --> environment` for `K_B`); `settings.py`: the key `populations` (seeded, after the listed bodies); `stamp.py` and `engine/schemas/stamp.schema.json`: `populations` when used; `simulator/web/engine-files.json` regenerated. Section 10: additions. Review fix (Claude Opus 5.5 in Claude Code): a heat bath is refused with weighted populations; `summary.json` gains `super_particles` (weights and how to read the temperature) when a population is weighted; no Keplerian speed for a body on the axis |
| 2026-11-14 | E8 (`E8-diagnostics`, stacked on `E4-directions`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | **new** `analysis/convergence.py` (E8.2) and `analysis/plots.py` (E8.3), nodes no longer planned, edges `convergence --> runner`, `plots --> constants` (was a planned `plots --> diagnostics`); `diagnostics.py` implemented: the temperature (edge `diagnostics --> environment`); `runner.py`: `wall_pressure`, summary `walls` (E8.1). `simulator/web/engine-files.json` regenerated. Section 10: additions |
| 2026-11-14 | journal threads (`journal-threads`) | Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) | `tools/build_journal.py`: `--open-threads` (one GitHub Discussions thread per entry, recorded in `journal/discussion.json`); the discussion block links to it. Section 10: one signature added, one changed. No module, edge or engine contract changed |
| 2026-11-14 | Co-exist Journal (`coexist-journal`, stacked on `co-exist-initiative`; D34, D35) | Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) | **new** `tools/build_journal.py` (node `journal`, section 4, used by `tests`); section 10: its signatures; `markdown==3.8.2`, `pymdown-extensions==10.16.1`, `pyyaml==6.0.2` added to the dev extras. No engine module or contract changed |
| 2026-11-14 | E4.4 part B: L4, L6, L8 (`E4-directions`, stacked on `E4-readings`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | `laws/l1.py`: directions (L4: radial, perpendicular, velocity), the moving-body term (L6: on, only), the screened range (L8); `fields/direct.py`: `at_bodies_screened`, `debye_length`; `fields/sample.py`: `FieldSample.screened` (addition); `integrators.py`: the `StepContext` fills the screened field for L8 (new edge `integrators --> environment`, for `K_B`). Section 10: additions. Review fix (Claude Opus 5.5 in Claude Code): `settings.py` picks velocity Verlet when L6 is on (`law.B_cal`), and refuses an explicit `boris` with it |
| 2026-11-14 | E4.3 (L1b-L1d) and E3.4 (L7) (`E4-readings`, stacked on `E3-boris`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | `laws/l1.py`: a common base `_ComposerReading` (L0 plus `+/- lambda` times what the reading adds; options L2, L3, L5) and the laws L1b, L1c, L1d; `laws/base.py`: `Law.inertia` reads L7 (`Re`, `Sh`, `abs`), using `readings`. Section 7: L1a-L1d implemented. No signature changed |
| 2026-11-14 | E3.2: the Boris push (`E3-boris`, stacked on `E3-pair-guard`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | `integrators.py`: `Boris`, `boris_rotation`, `StepContext.rotation` and `.remember` (the cache also keeps the fields and the inertia); `settings.py`: `numerics.integrator` `"verlet"` or `"boris"`, resolved by D10 when left out; `runner.py` picks the integrator. Section 5: `Boris`; section 10: additions. No existing signature changed |
| 2026-11-14 | E3: the pair guard of D29 (`E3-pair-guard`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | `integrators.py`: new function `pair_approach_time`; `next_dt` always applies the pair guard; the default `speed_reference` becomes `"neighbour"` (also in `settings.py`). Section 10: the contract of `StepContext` changed by **decision D29** (default) and the new function. No diagram changed |
| 2026-11-14 | team chat (`team-chat`; question 23, proposed) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | **new** `tools/chat.py` (node `chat`, section 4, used by `tests`); `team/chat/` with its README and the first message; section 10: its signatures. No engine module changed |
| 2026-11-14 | D25: one ruff format pass (`D25-format-pass`) | Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) | **layout only**: `ruff format .` over 45 Python files (no module, interface or behaviour changed; one `lambda` in `gates/t0.py` became a local `def`); Markdown excluded from formatting; section 9: the job `lint` also runs `ruff format --check .` |
| 2026-11-14 | Q5 (`Q5-step-guard`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | scenario row `scenarios/Q5/` (its own time loop around `VelocityVerlet.step`, with the candidate rule C); test `engine/tests/test_q5_step_guard.py`. No engine module, edge or contract changed |
| 2026-11-14 | E6b (`E6b-inflow-heat-bath`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | `environment.py`: `Inflow`, `HeatBath`, `kinetic_temperature`, `K_B`; `Environment` takes them as optional arguments (addition, no existing call changed); settings: `universe.inflow` and `universe.heat_bath`; runner: one seeded generator for the environment, summary `inflow` and `heat_bath`, a `temperature` column with a bath, no per-body columns with an inflow; stamp and `engine/schemas/stamp.schema.json`: the two blocks. Section 5: the two classes; section 10: their signatures |
| 2026-11-14 | P7 (`P7-ruff-devcontainer`, stacked on `P5-scenario-scaffold`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | section 9: new CI job `lint` (`ruff check`); lint fixes without change of behaviour: unused imports in `gates/t9.py`, `engine/tests/test_runner.py`, `scenarios/D21/run.py`, a variable name in `tools/check_architecture.py`. No module, edge or contract changed |
| 2026-11-14 | P5 (`P5-scenario-scaffold`, stacked on `P4-result-schemas`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | `tools/new_scenario.py` implemented (node `scaffold` no longer planned); section 4: the scaffold writes files that use `settings` and become a `scen` (dotted edges: it does not import them); section 10: its signatures (additions) |
| 2026-11-14 | P4 (`P4-result-schemas`, stacked on `T9.2-hydrogen-share`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | **new** `engine/schemas/` (node `schemas`) and `tools/validate_results.py` (node `validate`) in section 4, with edges `tests --> validate --> schemas`; section 10: the validator's signatures (additions); `jsonschema==4.26.0` pinned (D13). No engine module or contract changed |
| 2026-11-14 | T9.2 (`T9.2-hydrogen-share`, stacked on `T9.4-antiparticle`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | `gates/t9.py` gains `t9_2`, which uses `runner` (new edge `limits --> runner` in section 4) and the helpers `_pair`, `_relative_track` of `gates/t0.py` (edge `limits --> gate` already there); scenario row `scenarios/T9.2/`; no contract changed |
| 2026-11-14 | T9.4 (`T9.4-antiparticle`) | Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz) | `gates/t9.py` gains `t9_4` (no existing signature changed); scenario row `scenarios/T9.4/`; no new module, edge or contract |
| 2026-11-11 | Q4: the step rule and the frame (`Q4-step-frame`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `integrators.py`: `nearest_neighbours` and the option `StepContext.speed_reference` (default unchanged); scenario row `scenarios/Q4/`; section 10: the option written out. No diagram changed |
| 2026-11-11 | E6a: absorbing walls (`E6a-absorbing-walls`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `environment.py`: boundary `absorbing` and the collector `Environment.collected`; section 10: the collector and the three boundary names written out; the run summary gains `absorbed`. No diagram changed |
| 2026-11-10 | E4.5, T9.4 and the question scenarios Q1-Q3 (`E4.5-T9.4`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `laws/base.py` gains `third_law_residual`; `gates/t9.py` gains `t9_4`; scenario rows `scenarios/T9.4/` and `scenarios/Q/`; section 10: signature of `third_law_residual` added; no diagram changed |
| 2026-11-11 | UI1, first version (`UI1-web-universe`) | Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) | `simulator/web/` in progress: web worker running the unchanged engine in Pyodide, bridge, page; nodes `UI` and `webui` no longer planned; test `engine/tests/test_web_universe.py`. No engine module or contract changed |
| 2026-11-10 | D21 scenarios (`D21-scenarios`, stacked on `T0-gate`) | Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz) | scenario row `scenarios/D21/` (D21.1-D21.4); no engine module, diagram or contract changed |
| 2026-11-10 | Gallery (`gallery`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | **new tool** `tools/make_gallery.py` (node `gallery` in section 4, uses `gate`, `runner`, `fields`); no engine module or contract changed |
| 2026-11-10 | MVP-10: demo and release notes (`MVP-demo`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | scenario row `scenarios/T1.4/` (in progress: the demo only); package version 0.1.0; no module, diagram or contract changed |
| 2026-11-10 | MVP-9: L1a and the measured limits (`T9-limits`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `laws/l1.py` in progress (L1a with sign, strength, terms; node `l1` stays dashed); **new module** `gates/t9.py` (node `limits`); scenario rows `scenarios/T9.1/`, `scenarios/T9.3/`; section 4: `gatetests` and `scen` use `limits`. `write_gate_result` takes the kind and the law of the result (keyword arguments with the old behaviour as default) |
| 2026-11-10 | MVP-8: the consistency gate (`T0-gate`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | **new module** `gates/t0.py` (node `gate`), `engine/gates/` implemented (the fast gate is collected by pytest; section 9 is left as it is until the `tests` job of P2 is merged), five scenario rows `scenarios/T0.1/` to `scenarios/T0.5/`; section 4: `gatetests` and `scen` use `gate`, which uses `runner`, `settings` and `stamp`; section 8: `run.py` exists. The summary of a run gains `wall_impulse` and `momentum_with_walls_drift` (no signature changed) |
| 2026-11-10 | MVP-7: runner, stamp, command line, diagnostics, L0 energy (`E7-runner`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `runner.py`, `stamp.py`, `diagnostics.py`, `energy.py` in progress (MVP parts); **new module** `__main__.py` (node `cli`); section 4: `runner` uses `settings` and `fields`, `energy` uses `gnarray` and `state` (the edge to `fields` is gone), `stamp` still dashed; section 5: `RunResult` carries the final state and the rows; section 10: `run` accepts a path or a dictionary and `out_root=None`, signatures of `main`, `Diagnostics`, `drifts`, `energy_l0` added |
| 2026-11-10 | MVP-6: integrator and walls (`E3-integrator`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `integrators.py` in progress (velocity Verlet, adaptive step) and `environment.py` in progress (reflecting walls); section 4: `integrators` uses `state`, `settings` uses `environment`; section 5: `StepContext` added; section 10: `StepContext` and `Environment` signatures written out (additions) |
| 2026-11-10 | MVP-5: static field solver and backgrounds (`E2-fields`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `fields/direct.py` in progress (static part, softening, backgrounds; E2.2 not yet); section 4: `fields` uses `state` and `constants` (the edge to `gnarray` is gone: the solver returns a `FieldSample`); sections 5 and 10: `at_bodies(state)` added next to `sample(state, points)`; the second field has shape `(P, 3)` in 3D |
| 2026-11-10 | MVP-4: state, minimal settings, law interface, L0 (`E4-l0`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `state.py`, `laws/base.py`, `laws/l0.py` implemented; `settings.py` in progress (minimal); **new module** `fields/sample.py` (`FieldSample`, `FieldSolver`), with its node and edges in section 4; section 5: `LawSpec.moving` is a string (L6 has three options), methods as built; section 10: `Law` is a base class with the same members, `make_law` and `load_settings` added |
| 2026-11-10 | P2: CI runs pytest (`P2-ci-tests`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | section 9: the `tests` job exists in CI (`pytest` with coverage, fails under 90%); `engine/tests/test_pins.py` added; dev extras pinned |
| 2026-11-10 | E1.3 to E1.6: arrays, readings, matter, compendium tests (`E1b-arrays-readings`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `gnarray.py`, `readings.py`, `matter.py` implemented (registry, section 4 nodes no longer planned); section 5: `GNArray` and `CosmicMass` as built (`mu(frame)` takes the frame); section 10: `GNArray.mul` accepts scalars and arrays too, and the signatures of the readings and of `CosmicMass` are added (no existing contract broken) |
| 2026-11-10 | E1.1 and E1.2: constants, frame, scalar General Numbers (`E1-algebra-core`) | Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz) | `constants.py`, `frame.py`, `gn.py` implemented (registry, section 4 nodes no longer planned); section 5: methods of `Frame` and `GeneralNumber` as built; section 10: the `Frame` fields are unchanged, its methods and the `GeneralNumber` signatures are added (additions only, no existing contract changed) |
| 2026-11-10 | P1: package skeleton (`P1-package-skeleton`) | Claude chat session on claude.ai / Claude Fable 5.2, applied by Claude Opus 5.5 (sponsor @MostafaDerraz) | package `cosmicmass` installable from `engine/cosmicmass/` (`pyproject.toml`, version 0.0.1, no modules yet); registry row `engine/tests/` -> implemented; node `tests` in section 4 no longer planned |
| 2026-11-10 | (direct, before D17 protection) | Mostafa Derraz, with Claude Opus 5.5 | first version: registry of 29 planned modules, layers, core types, time step, law pipeline, lifecycle, CI; `tools/check_architecture.py` implemented |

---

## 12. How to update this file

When your pull request touches code:

1. **Registry:** add a row for each new file or folder, change `planned` to `in-progress` or `implemented`, or mark it `deprecated`. Update the purpose if it changed.
2. **Diagrams:**
   - a new module → a node in section 4 (with its node ID), and in section 5 if it adds a type or an interface;
   - a new dependency → an arrow in section 4 (respect the layers);
   - a change to the step → section 6; to laws → section 7; to CI → section 9;
   - implemented → remove `:::planned` from its node.
3. **Contracts:** a changed signature → section 10, with the decision number.
4. **Change log:** one line in section 11.
5. **Check locally:**
   ```bash
   python tools/check_architecture.py --base origin/main
   ```
   Preview the diagrams in the pull request's "Files changed" view, in VS Code with a Mermaid extension, or at mermaid.live.

**For AI agents:** before ending a session in which you changed code, re-read sections 2, 4 and 10, update them, and run the check. Say in your log entry: `Architecture: updated (sections ...)` or `Architecture: no code changed`.
