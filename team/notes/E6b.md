# E6b: inflow (U7), heat bath, fixed sources (U6)

- **Owner:** Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz)
- **Buddy (newcomers):** none named
- **Claimed:** 2026-11-14, after delivering P4, P5 and P7 (one claim at a time, D15); no claim issue (claim on the board and here)
- **Depends on:** E6a (reflecting and absorbing walls, merged in #27)
- **Branch:** E6b-inflow-heat-bath (cut from `main` after #29)

## Goal
`docs/WORK-PLAN.md`, E6b: "inflow (U7), heat bath, fixed sources (U6)" in `environment.py`. **Acceptance:** inflow rate within 1% over 10^4 steps; the heat bath holds the temperature within 2% (needed by T4.4 and T6).

## Pre-registration
Not applicable: engine component, no production run, no finding.

## What was built
- **Inflow** (`Inflow` in `environment.py`; settings `universe.inflow`): bodies of one cosmic mass (a preset, or `m` and `q`) enter the box through one face (`{"axis", "side"}`), with one velocity, which must point into the box. A box is required.
- **Heat bath** (`HeatBath`; settings `universe.heat_bath`: `temperature`, `collision_rate`): in a step `dt` each alive, moving body is hit with probability `1 - exp(-nu dt)` and gets a new velocity from the Maxwell distribution of the bath temperature for its own mass.
- **Temperature** (`kinetic_temperature`): `(d/2) N k_B T = sum m v^2 / 2` over alive, moving bodies.
- **Fixed sources** (U6) already existed as bodies with `"fixed": true`. E6b adds the guarantee, with a test, that walls, inflow and heat bath never touch them.
- **Runner:** one generator, `numpy.random.default_rng(numerics.seed)`, for every draw of the environment (the seed is in the stamp, D13). The summary gains `inflow` (`bodies`, `m`, `q`) and `heat_bath` (`temperature`, `collisions`, `temperature_mean_second_half`); the time series gains a `temperature` column when there is a bath. With an inflow, the per-body columns are left out (the number of bodies grows; a CSV cannot change its header). The stamp records both blocks; `engine/schemas/stamp.schema.json` (P4) describes them.
- Tests: `engine/tests/test_environment_e6b.py` (17).

## Choices (labelled; each could be a decision)
1. **Deterministic count of the inflow:** `floor(rate (t - t0))` bodies have entered by time `t`, counted from the start of the run. So the rate is exact to one body, and the criterion "within 1%" holds whenever 100 or more bodies are due. A Poisson stream (random count) is the alternative; it would make the 1% criterion a matter of luck for small counts. The places on the face are random (seeded).
2. **Andersen bath:** canonical, and correct for mixtures of masses (each kind takes the bath temperature; tested on three masses, 1 to 1836, within 2%). It is stochastic, so the **instantaneous** temperature of N bodies fluctuates by about `sqrt(2 / (d N))` (about 2.4% for 1200 bodies in 3D). The criterion "holds the temperature within 2%" is therefore checked on the **time average** after equilibration; the runner reports the mean over the second half of the run. Alternatives: Berendsen rescaling (holds the instantaneous value but is not canonical), Langevin (adds friction to the law of motion).
3. **The bath acts everywhere** in the universe, on every alive, moving body. A bath limited to a region (a wall at a temperature, for T6) is not built.
4. **`k_B` = 1 in scaled units** (an assumption, like `c = e = 1` in question 6); exact 1.380649e-23 J/K in SI.
5. **Thermal velocities use the inertia `Re(mu) = m`.** Other inertias (L7) are not implemented anywhere yet.
6. **Inflowing bodies enter on the face itself**, at rest relative to the given velocity: no thermal spread (U7 names rate, `mu` type and velocity only). A temperature for the stream can be added when T4.4 needs it.

## Progress (newest first)
- 2026-11-14: built and tested. The runner test found that the inflow first counted from the end of the first step (one step of bodies lost); fixed by an explicit start time `t0`.

## Results
Software facts and checks against mathematics; no finding.
- Inflow over 10^4 steps: 1369 bodies against `rate t` = 1369.0, within one body (0.07%).
- Heat bath: 1200 bodies of three masses, from far off (light ones hot, heavy ones at rest): mean temperature over the second half within 2% of the bath, and each mass within 2% (equipartition).
- Same seed, same run, bit for bit; another seed, another run.

## Open questions (copied to `team/QUESTIONS.md`)
- Question 20: choices 1 and 2 (deterministic inflow count; Andersen bath judged on the time average).
- Question 21: `k_B = 1` in scaled units.

## Handoff
- State: delivered as a pull request, waiting for review.
- What works: inflow, heat bath, fixed sources, with the runner, the settings, the stamp and the schema.
- What does not: a bath limited to a region; a thermal spread for the inflow; inertias other than `Re(mu)`.
- Exact next step: T6.1 (pressure from momentum flux equals `n k T` under L0) can now be pre-registered: it needs E6b and E8.1 (the wall impulse already exists).
