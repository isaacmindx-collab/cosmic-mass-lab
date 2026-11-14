---
id: 2026-011
title: What is kept, mass, charge, momentum and energy in a universe of cosmic masses
kind: teaching
side: physics
date: 2026-11-14
authors:
  - name: Claude Fable 5.2
    type: ai
    model: claude-fable-5-2
    provider: Anthropic
    tool: Claude (chat session on claude.ai)
    sponsor: "@MostafaDerraz"
    role: wrote the entry; produced the runs T0.2 and Q2 it quotes
label: mixed
status: settled
summary: >
  The physics side of the cosmic mass, seen through its conservation laws. One General Number,
  the total cosmic mass, holds two conserved quantities: mass and charge. Momentum is kept because
  the product of two cosmic masses commutes. The energy of the reference law L0 is one sum,
  $-G\sum\operatorname{Re}(\mu_a\mu_b)/r$, that contains both Newton's and Coulomb's. Under the
  hypothesis L1a that sum stops being conserved and a second one, read from the Composer
  coordinate, restores it. Each statement is labelled, with the run that checks it.
tags: [conservation, energy, momentum, charge, L0, L1a, T0.2, Q2, D23]
links:
  - title: T0.2 results folder (200 bodies in a box)
    url: /results/T0.2/20261110-184959-91ba4ae
  - title: Q2 results folder (which energy does L1a conserve?)
    url: /results/Q2/20261110-202336-e1a3165
  - title: The energies in the engine
    url: /engine/cosmicmass/energy.py
  - title: The conservation diagnostics
    url: /engine/cosmicmass/diagnostics.py
  - title: Decision D23 (the energy of L1a)
    url: /team/DECISIONS.md
---

Entries [2026-006](../2026-006/) and [2026-008](../2026-008/) taught how a cosmic mass moves. This one asks what stays the same while it moves. A conserved quantity is the first thing a simulation is judged by, and in this theory the conserved quantities have an unusual shape: several of them are two coordinates of one General Number.

Labels: the sections on L0 are **mathematics of the reference law**, checked by confirmed runs. The section on L1a is about a **hypothesis**.

## One General Number, two conserved quantities

Each body carries one number, its cosmic mass $\mu = m + q\,\mathcal G$. Add them all:

$$M = \sum_a \mu_a = \Big(\sum_a m_a\Big) + \Big(\sum_a q_a\Big)\,\mathcal G .$$

The real coordinate of $M$ is the total mass and its Composer coordinate is the total charge. The compendium states the same for a continuous source, as one equation: $\partial_t\rho_\mu + \nabla\cdot\mathbf J_\mu = 0$. Read in its two coordinates it is the conservation of mass and the conservation of charge.

In the virtual universe this holds exactly, not approximately, because no rule of the engine changes a body's $\mu$. Even an absorbing wall does not destroy anything: the body is switched off and its mass, charge and momentum go into the wall's collector. In test T0.2 (200 bodies in a box, 10,000 steps) the total mass and the total charge do not change by a single bit.

## Momentum, and why the product must commute

Under the reference law L0 the inertia of a body is $\operatorname{Re}\mu = m$, so the momentum is the ordinary $\sum m\,\mathbf v$. It is conserved when every pair of bodies pushes equally and oppositely. For bodies at rest the force on $a$ from $b$ is

$$\mathbf F_{ab} = \frac{G\,\operatorname{Re}(\mu_a\mu_b)}{r^2}\,\mathbf e_r ,$$

and $\mu_a\mu_b = \mu_b\mu_a$: General Numbers commute. **Newton's third law is the commutativity of the product.**

A box changes the count, but not the law. A reflecting wall turns a body back and receives twice its momentum along the wall's normal. The engine adds up what the walls received. In T0.2 the momentum of the bodies plus the walls' share is constant to $4.4\times10^{-16}$.

## The energy of L0: one sum, two classical energies

The work done by the force above is

$$E = \sum_a \tfrac12 m_a v_a^2 \;-\; G\sum_{a<b}\frac{\operatorname{Re}(\mu_a\mu_b)}{r_{ab}} .$$

Since $\operatorname{Re}(\mu_a\mu_b) = m_a m_b - s^2 q_a q_b$ and $G s^2 = K$, the second term is

$$-\sum_{a<b}\frac{G m_a m_b}{r_{ab}} + \sum_{a<b}\frac{K q_a q_b}{r_{ab}} ,$$

Newton's gravitational energy and Coulomb's electric energy, with their usual signs, from one expression. In T0.2 this energy drifts by $2.3\times10^{-9}$ over the run. That is not zero, and it should not be: the integrator (velocity Verlet) keeps the energy of a slightly different system, and the drift shrinks with the step.

One warning from scenario D21.3: **the drift at the end of a run can hide what happened during it.** On an eccentric orbit the energy error is largest at the closest approach and comes back afterwards. The lab reports both numbers, the end drift and the largest excursion.

## Under the hypothesis L1a, a second sum

L1a reads the Composer coordinate of $\mu\,\boldsymbol{\mathcal E}$ as a force along the line, with a strength $\lambda$. Then the energy $E$ above is no longer conserved. Scenario Q2 measured it on a proton and an electron at $\lambda = 1$: over five orbital periods $E$ ends 44% away from its start, and swings by 50% on the way.

Q2 also tested a candidate, pre-registered before the run: read the same sum with the reading of L1a,

$$E_{\text{L1a}} = \sum_a \tfrac12 m_a v_a^2 \;-\; G\sum_{a<b}\frac{\operatorname{Re}(\mu_a\mu_b) + \lambda\,s\,\operatorname{Com}(\mu_a\mu_b)}{r_{ab}} ,$$

where $\operatorname{Com}(\mu_a\mu_b) = m_a q_b + q_a m_b + 2s\cos\bar\varphi\,q_a q_b$ is the coefficient of $\mathcal G$ in the product.

| Run of Q2 | End drift of $E$ | End drift of $E_{\text{L1a}}$ |
|---|---|---|
| proton and electron, $\lambda = 1$ | $0.44$ | $3.3\times10^{-7}$ |
| the same, $\lambda = 0.3$, opposite sign | $2.5\times10^{-4}$ (excursion $0.045$) | $4.7\times10^{-10}$ |
| the same at $\bar\varphi = 120^\circ$ | $5.4\times10^{-4}$ (excursion $4.0$) | $4.0\times10^{-9}$ |
| 12 bodies, $\lambda = 0.2$ | $1.1\times10^{-3}$ | $9.8\times10^{-9}$ |

$E_{\text{L1a}}$ is conserved as well as any energy is under this integrator. The maintainer approved it as decision D23, within a stated scope: all three terms kept, the force along the line, inertia $\operatorname{Re}\mu$, no second field. Outside that scope the engine reports "not defined" instead of a number. In the same runs the momentum is constant to $2\times10^{-14}$ or better, as the commuting product requires.

What this shows, and what it does not: it is a property of the hypothesis, checked numerically and reproduced by another model. It does not make the hypothesis true. Entry [2026-003](../2026-003/) shows that at $\lambda = 1$ the hypothesis is excluded by measurement.

## What is not kept, and what is not in the engine

- With a **heat bath** or an **inflow**, energy enters and leaves by design; the summary counts what entered.
- With **half a Coupling term** (a variant of L1a), the third law fails and the momentum of the bodies is not conserved (entry [2026-010](../2026-010/)).
- The **energy of the fields** themselves: the compendium gives the density $u = -(g^2 + c^2B_g^2)/8\pi G + (E^2 + c^2B^2)/8\pi K$, with a negative gravitational part. The engine does not use it: its fields are those of bodies at rest, with no waves. The compendium itself lists what follows from that sign among the places where the law fails ("gravity waves carry negative energy"), and limits the law to slow bodies.

A run in the lab reports four drifts, mass, charge, energy and momentum, in its `summary.json`. Read them before reading anything else.
