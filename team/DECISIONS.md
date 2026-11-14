# Decisions

Numbered, binding decisions. To propose one, add it with status "proposed" and open an issue. The maintainer approves or rejects it. Never delete a decision; supersede it with a new one.

| ID | Decision | Status | Date |
|---|---|---|---|
| D1 | The paper's law L0 (`Re(mu) dv/dt = Re[mu(E_cal + v x B_cal)]` with F1-F4) is the reference law. Every other reading (L1-L8) is a hypothesis. | approved | 2026-11-10 |
| D2 | Engine, outputs and documents use only the language of the cosmic mass and General Numbers. | approved | 2026-11-10 |
| D3 | T0 is a gate: no coupling result counts unless the engine commit used passes T0. | approved | 2026-11-10 |
| D4 | T9 (the measured limits of the book's Chapter 10) must pass before exploring L1-L8. | approved | 2026-11-10 |
| D5 | Verified formulas (`docs/formulas-compendium/`) and verification scripts are not edited to make results pass. | approved | 2026-11-10 |
| D6 | The book's Chapters 7 (Standard Model) and 8 (Closure Law) are not used as engine inputs; their physical claims are unverified. | approved | 2026-11-10 |
| D7 | Units: SI is the reference; scaled units (`G_N = K = 1`, so `s = 1`) are allowed for visibility, with the SI run shown or the reason it cannot be run. | approved | 2026-11-10 |
| D8 | Licence: MIT for code, CC BY 4.0 for documents and findings; the sources remain the author's work. | approved | 2026-11-10 |
| D9 | The repository is public. | approved | 2026-11-10 |
| D10 | Default numerics: velocity Verlet (Boris with `B_cal`), adaptive time step, softening 1e-3 of the smallest initial separation. | approved | 2026-11-10 |
| D11 | Operating model: `TEAM.md` (roles and leads, decision process, limits on work in progress, the nine-step work cycle, two kinds of review, lifecycle of findings). | approved | 2026-11-10 |
| D12 | Pre-registration: question, law, settings, prediction and analysis plan are committed in the notebook before any production run; runs without it are "exploratory" and cannot be cited. | approved | 2026-11-10 |
| D13 | Results follow `team/RESULTS-STANDARD.md` (folder layout, `stamp.json`, determinism, tolerances); the environment is pinned in `requirements.txt`. | approved | 2026-11-10 |
| D14 | A finding is confirmed only by an independent reproduction; reproduction by an AI agent counts only if it is a human or an agent of a different model from the producer's. | approved | 2026-11-10 |
| D15 | Limits: at most 2 active claims per person, 1 per agent, 2 agents per sponsor; claims expire after 14 days without a log entry. | approved | 2026-11-10 |
| D16 | Authorship: authors are humans with substantial contributions to confirmed findings; AI agents are credited in acknowledgements and the declaration of AI use, never as authors. | approved | 2026-11-10 |
| D17 | `main` is protected: changes only by pull request, with green CI and one approving review by someone other than the author. | approved (protection to be switched on in the repository settings) | 2026-11-10 |
| D18 | The architecture travels with the code: every pull request that changes code in `engine/`, `scenarios/`, `simulator/` or `tools/` updates `ARCHITECTURE.md` (module registry, Mermaid diagrams, interface contracts, change log) in the same pull request. Enforced in CI by `tools/check_architecture.py`. | approved | 2026-11-10 |
| D19 | The work plan is `docs/WORK-PLAN.md` (stages S0-S8, tasks P, E, T, G, UI, R with acceptance criteria). Task IDs there are the IDs used for claims. | approved | 2026-11-10 |
| D20 | MVP sprint (`docs/MVP-PLAN.md`): one agent may hold the MVP sequence MVP-1 to MVP-10 as one claim (exception to D15), using stacked pull requests (each based on the previous branch); it never merges or pushes to `main`; the maintainer reviews and merges in order. | approved | 2026-11-10 |
| D21 | Numerical conventions of the engine, for T0 and after: (1) "2D" is planar motion of point bodies of three-dimensional space, with a `1/r^2` field; (2) softening has the Plummer form, and the two-body gate tests (T0.1, T0.4, T0.5) run with softening 0, because D10's softening changes the closest initial force by about 1.5e-6; (3) "energy drift" is the relative change of the energy at the end of the run, and the largest excursion on the way is reported beside it; (4) the adaptive step of D10 has a floor on the speed for bodies at rest (a tenth of the free-fall speed over the distance to the nearest neighbour), skips bodies with no neighbour, and never moves a body by more than 1e-3 of the distance to its nearest neighbour. Details: `team/notes/MVP-5.md`, `team/notes/MVP-6.md`. | **approved as refined** by the maintainer on 2026-11-10 ("Yes, approve D21"), after scenarios D21.1-D21.4 (`team/notes/D21.md`): (1), (2) and (4) as written, with REST_FRACTION = 0.1; (3) refined: every result reports both the end drift and the largest excursion, and each criterion states which one it uses | 2026-11-10 |
| D23 | Code format (P7): one pass of `ruff format .` (settings of `pyproject.toml`: line length 120, double quotes; `verification/` and `sources/` excluded) made by the maintainer in a pull request of its own, when no other pull request is open; after it, CI also runs `ruff format --check .`. Until then only `ruff check` runs in CI. Reason: the first pass rewrites about 36 files (about 2,500 diff lines) and would conflict with every open pull request. | proposed | 2026-11-14 |
| D22 | UI0, design of the interactive universe: the browser runs the **unchanged engine** `cosmicmass` with Pyodide (Python 3.12 and the pinned NumPy in WebAssembly), in a web worker; no second engine in JavaScript. The list of engine files the page loads is checked by a test. Static hosting (GitHub Pages) is enough. | proposed | 2026-11-11 |
