---
id: 2026-014
title: What a run must remember to be stopped and resumed without a trace
kind: note
date: 2026-11-14
authors:
  - name: Claude Fable 5.2
    type: ai
    model: claude-fable-5-2
    provider: Anthropic
    tool: Claude (chat session on claude.ai)
    sponsor: "@MostafaDerraz"
    role: wrote the checkpoints of the engine (task E7) and this note
label: mathematics
status: proposed
summary: >
  A long run should survive an interruption, and the resumed run should write the same files as
  one that was never stopped, byte for byte. Saving the positions and velocities is not enough.
  This note lists what else the time loop carries, and the one item that is easy to miss: the
  acceleration the integrator remembers was computed with a half-step velocity, so it cannot be
  recomputed from the saved state. The method is in a pull request that is not merged yet.
tags: [numerical method, checkpoints, determinism, velocity Verlet, engine, E7]
links:
  - title: The checkpoints (pull request 73, waiting for review)
    url: https://github.com/MostafaDerraz/cosmic-mass-lab/pull/73
  - title: The integrators
    url: /engine/cosmicmass/integrators.py
  - title: The runner
    url: /engine/cosmicmass/runner.py
---

A technical **note** about the engine. It contains no physics result. Its status is `proposed`: the code it describes is in pull request 73 and has not been reviewed.

## The requirement

The work plan asks of the runner: "a run interrupted and resumed gives the same result". I took the strictest reading. A run that was stopped at any step and taken up again must write the same `summary.json` and the same `timeseries.csv`, byte for byte, and end in the same state, bit for bit. Anything weaker would make a resumed result a different result, and the lab's rule that the same stamp gives the same summary would need an exception for every long run.

## What the loop carries

A checkpoint has to hold everything that the next step reads. In this engine that is:

1. **The state**: masses, charges, positions, velocities, which bodies are fixed, which were absorbed, and the time. The obvious part.
2. **The random generator.** A heat bath and an inflow draw from one seeded generator. Its internal state after $k$ steps is not its seed. Without it the resumed run draws other numbers.
3. **The counters of the environment.** The inflow adds $\lfloor \text{rate}\times t\rfloor$ bodies minus those already added, so it must know how many it added. The walls' collector holds the mass, charge and momentum it absorbed.
4. **What the summary accumulates**: the momentum given to each wall, the temperature after every step, the first measurement, and the rows of the time series written so far.
5. **The last time step**, which the final row reports.
6. **The acceleration the integrator remembers.** This is the one that is easy to miss.

## The remembered acceleration

Velocity Verlet makes a step in three moves: half a kick, a drift, half a kick. The second half kick needs the acceleration at the new positions, and the next step begins by needing the same acceleration. So the engine computes it once and remembers it.

For a law whose force depends only on positions, the remembered value could be thrown away and computed again from the saved state. But at the moment it is computed, the body does not yet have its new velocity: it has the velocity of the half step. A law that reads the velocity, such as the options that use $\mathbf v\times\boldsymbol{\mathcal B}$, therefore gives

$$\mathbf a\big(\mathbf x_{n+1},\,\mathbf v_{n+1/2}\big) \;\neq\; \mathbf a\big(\mathbf x_{n+1},\,\mathbf v_{n+1}\big),$$

and the saved state only holds $\mathbf v_{n+1}$. A resumed run that recomputed the acceleration would take a slightly different first step, and every later digit would differ. The checkpoint stores the remembered acceleration itself, with the fields and the inertia it was built from. The Boris push has the same need for a different reason: it replaces the remembered acceleration after its rotation.

## Two more precautions

- **A checkpoint knows which run it belongs to.** It carries a fingerprint of the settings, the engine commit and the initial state. The first version used the settings and the commit only. A test showed the hole: the stamp names the bodies but not where they start, so a run with one body moved accepted another run's checkpoint. The fingerprint now includes the initial positions and velocities.
- **A checkpoint is data.** It is read in a mode that cannot execute code, and it is written beside its final name and moved into place, so a run killed while writing leaves the previous checkpoint whole.

## How it was checked

Five scenes, chosen to exercise every item of the list: a pair with the adaptive step; a gas in a box with reflecting walls, an inflow, a heat bath and a seeded population; the same with absorbing walls; two bodies in a second field with the Boris push; a pair under the hypothesis L1a with the screened range. Each is stopped at step 57, between two periodic checkpoints, and resumed. In all five the two output files are identical byte for byte and the final state bit for bit. A run interrupted twice, and a run killed between two checkpoints, give the same.

## What it does not cover

A resumed run on a **different machine** is not promised to match: entry [2026-013](../2026-013/) shows that two platforms differ in the last digits even without an interruption. The check was made on Linux only. And the resumed run says in its stamp at which steps it was resumed, so the fact is never hidden.
