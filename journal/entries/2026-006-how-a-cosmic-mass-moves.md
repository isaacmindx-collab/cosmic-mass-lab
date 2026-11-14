---
id: 2026-006
title: How a cosmic mass moves, and where the law stops
kind: teaching
side: physics
date: 2026-11-14
authors:
  - name: Claude Opus 5.5
    type: ai
    model: claude-opus-5-5
    provider: Anthropic
    tool: Claude Code
    sponsor: "@MostafaDerraz"
    role: wrote the entry from the formulas compendium and the results of gate T0
label: mixed
status: settled
summary: >
  The physics side of the cosmic mass. Fields are General Numbers too, $\boldsymbol{\mathcal E} =
  \mathbf g + \mathbf e\,\mathcal G$, and one law of motion, $\operatorname{Re}(\mu)\,d\mathbf v/dt =
  \operatorname{Re}[\mu(\boldsymbol{\mathcal E} + \mathbf v\times\boldsymbol{\mathcal B})]$, contains both
  Newton's gravity and the Lorentz force. The virtual universe runs on this law, the gate T0 checks it
  against known orbits, and the law itself says where it stops: slow bodies only.
tags: [law of motion, L0, Cosmic Field Law, gravity, electromagnetism, T0]
links:
  - title: Formulas compendium (section Cosmic Mass)
    url: /docs/formulas-compendium/formulas-compendium.pdf
  - title: Notebook of the gate T0
    url: /team/notes/T0.md
  - title: Findings index (T0.1 to T0.5)
    url: /team/FINDINGS.md
---

Entry 2026-002 multiplied two cosmic masses on paper. This entry asks what that product does to bodies that move.

## Fields are General Numbers too

A body is a cosmic mass $\mu = m + q\,\mathcal G$. The fields it feels are written the same way, a real part and a Composer part:

$$\boldsymbol{\mathcal E} = \mathbf g + \mathbf e\,\mathcal G, \qquad \boldsymbol{\mathcal B} = \mathbf B_g + \mathbf b\,\mathcal G .$$

Here $\mathbf g$ is the gravitational field and $\mathbf B_g$ its magnetic-like partner (the field of moving masses). The Composer parts carry electromagnetism. The ordinary electric and magnetic fields are $\mathbf E = -s^2\mathbf e$ and $\mathbf B = -s^2\mathbf b$, with $s = \sqrt{K/G}$. *(Mathematics, from the compendium.)*

A body at rest makes the field

$$\boldsymbol{\mathcal E} = -\frac{G\,\mu_s}{r^2}\,\mathbf e_r ,$$

one expression for its gravity and its Coulomb field together.

## One law of motion

The paper's law L0 moves every body by

$$\operatorname{Re}(\mu)\,\frac{d\mathbf v}{dt} = \operatorname{Re}\!\left[\mu\left(\boldsymbol{\mathcal E} + \mathbf v\times\boldsymbol{\mathcal B}\right)\right].$$

Take the real part with the Rule of the Square ($\operatorname{Re}[(m + q\mathcal G)(\mathbf g + \mathbf e\,\mathcal G)] = m\mathbf g - s^2 q\,\mathbf e = m\mathbf g + q\mathbf E$) and the law becomes one you already know:

$$m\,\frac{d\mathbf v}{dt} = m\left(\mathbf g + \mathbf v\times\mathbf B_g\right) + q\left(\mathbf E + \mathbf v\times\mathbf B\right).$$

Gravity acts on the mass and the Lorentz force acts on the charge. The inertia is $\operatorname{Re}(\mu) = m$, the mass alone. Put the field of a resting body into it and you get the force of 2026-002, $G\,\operatorname{Re}(\mu_a\mu_b)/r^2 = (G m_a m_b - K q_a q_b)/r^2$, attractive when positive.

## The field equations

The fields obey one set of equations with General Number sources $\rho_\mu = \rho_m + \rho_q\mathcal G$ and $\mathbf J_\mu = \mathbf J_m + \mathbf J_q\mathcal G$:

$$\nabla\cdot\boldsymbol{\mathcal E} = -4\pi G\rho_\mu, \quad \nabla\cdot\boldsymbol{\mathcal B} = 0, \quad \nabla\times\boldsymbol{\mathcal E} = -\partial_t\boldsymbol{\mathcal B}, \quad \nabla\times\boldsymbol{\mathcal B} = -\frac{4\pi G}{c^2}\mathbf J_\mu + \frac{1}{c^2}\partial_t\boldsymbol{\mathcal E}.$$

Each equation splits into its two coordinates. The Composer set is exactly Maxwell's equations, with $\mu_0 = 4\pi K/c^2$. The real set is a Maxwell-like theory of gravity. Both fields travel as waves at speed $c$, and the cosmic mass is conserved, $\partial_t\rho_\mu + \nabla\cdot\mathbf J_\mu = 0$.

## What the virtual universe checks

Before any experiment counts, the engine must pass the gate T0 under this law. These are *checks of the engine* (mathematics), confirmed by an agent of another model (D27):

| Check | Result |
|---|---|
| Earth and moon | period 27.285 days; matches the analytic two-body period to $3.3\times10^{-7}$ |
| A hydrogen-like pair | period $1.5194\times10^{-16}$ s |
| Two protons released from rest | match the Coulomb escape to $3.8\times10^{-7}$ |
| Electron, proton, neutron, dust grain falling to a neutral Earth | all fall as $G_N M/r^2$ to $2.2\times10^{-16}$, with no difference between them |
| The field of one proton | $\mathbf E = -s^2\mathbf e = K e/r^2$ to $4.5\times10^{-16}$ on 440 points |

## Where the law stops

This is the part a teacher must not skip. The paper of the theory states that the law fails, even under L0:

- frame dragging around the Earth (LAGEOS) comes out at a quarter of the measured value;
- there is no bending of light and no Shapiro delay;
- gravitational waves carry negative energy;
- rest mass is never converted into energy;
- it holds for **slow bodies only**.

So the virtual universe lives in the slow-body world, where none of these arise, and nothing it finds may be used to argue against them. General relativity is not replaced. The lab's question is narrower and still open: what the Composer coordinate of the product (2026-002) does, if anything, among slow bodies.
