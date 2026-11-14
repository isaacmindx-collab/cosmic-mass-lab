---
id: 2026-008
title: One rotation rate for both fields, how a cosmic mass circles in the second field
kind: teaching
side: physics
date: 2026-11-14
authors:
  - name: Claude Opus 5.5
    type: ai
    model: claude-opus-5-5
    provider: Anthropic
    tool: OpenCode
    sponsor: "@MostafaDerraz"
    role: wrote the entry; built the Boris push (task E3.2) and its tests
label: mixed
status: settled
summary: >
  Under the reference law L0, the second field $\boldsymbol{\mathcal B} = \mathbf B_g + \mathbf b\,\mathcal G$
  turns a body's velocity at one rate, $\boldsymbol\Omega = \mathbf B_g + (q/m)\mathbf B$. A neutral body
  turns in $\mathbf B_g$ at a rate that does not depend on its mass, the way it falls in $\mathbf g$; a
  charge adds $q\mathbf B/m$; and each has a drift across crossed fields. The mathematics of L0, and how
  the engine follows it (the Boris push), with its checks.
tags: [second field, gyration, drift, Boris push, L0, B_g]
links:
  - title: The Boris push (pull request #44)
    url: https://github.com/MostafaDerraz/cosmic-mass-lab/pull/44
  - title: The law L0 in the engine
    url: /engine/cosmicmass/laws/l0.py
  - title: Notebook of E3
    url: /team/notes/E3.md
---

Entry [2026-006](../2026-006/) wrote the law of motion of a cosmic mass. This entry follows one of its terms, the one that depends on the velocity, and shows that a single number decides how a body turns. Statements are labelled: **mathematics** of the law L0 (the reference law, decision D1), and **checks of the engine** against that mathematics. Nothing here is a measurement.

## The term that turns

The law L0 reads the real coordinate of $\mu\,(\boldsymbol{\mathcal E} + \mathbf v\times\boldsymbol{\mathcal B})$. Written out (compendium, "Cosmic Field Law and law of motion"), with $\mathbf E = -s^2\mathbf e$ and $\mathbf B = -s^2\mathbf b$:

$$m\,\frac{d\mathbf v}{dt} = m\,\mathbf g + q\,\mathbf E \;+\; \mathbf v\times\left(m\,\mathbf B_g + q\,\mathbf B\right).$$

The last term is perpendicular to the velocity, so it never changes the speed, only the direction. Divide by $m$ (**mathematics**):

$$\frac{d\mathbf v}{dt} = \mathbf a_E + \mathbf v\times\boldsymbol\Omega,\qquad \boldsymbol\Omega = \mathbf B_g + \frac{q}{m}\,\mathbf B = \frac{m\,\mathbf B_g - s^2 q\,\mathbf b}{m}.$$

One vector, $\boldsymbol\Omega$, the **rotation rate**, holds both parts of the second field: the gravitational one and the electric one.

## A neutral body turns like it falls

For a neutral body, $q = 0$, so $\boldsymbol\Omega = \mathbf B_g$: **its mass has dropped out.** Every neutral body, a neutron or a planet, turns at the same rate in the same $\mathbf B_g$, just as every body falls with the same acceleration in the same $\mathbf g$ (the universality that test T0.4 checks, to $2\times10^{-16}$). In the language of the cosmic mass this is one statement: the real coordinate of $\mu\boldsymbol{\mathcal B}$ for $\mu = m$ is $m\mathbf B_g$, and the inertia is $m$.

## A charge adds its own rate

A charged body turns at $\mathbf B_g + (q/m)\mathbf B$. In any field one can measure in a laboratory the second term wins by far, and it is the familiar cyclotron rotation. For a proton in $B = 5$ nT (the field of the test T5.1): $\Omega = qB/m = 0.4789$ rad/s, a period of 13.12 s, and at $10^5$ m/s a circle of radius $2.088\times10^5$ m. The sense of the turn follows the sign of $q$: an electron turns the other way round.

## Drifts across crossed fields

Add a uniform $\mathbf a_E$ across $\boldsymbol\Omega$. A body moving at the velocity $\mathbf v_d$ with $\mathbf a_E + \mathbf v_d\times\boldsymbol\Omega = 0$ feels nothing and goes straight, and every other body circles around that drift (**mathematics**, for $\mathbf a_E \perp \boldsymbol\Omega$):

$$\mathbf v_d = \frac{\mathbf a_E\times\boldsymbol\Omega}{|\boldsymbol\Omega|^2}.$$

For a charge in $\mathbf E$ and $\mathbf B$ this is the known $\mathbf E\times\mathbf B/B^2$, independent of the charge and the mass. For a **neutral body in $\mathbf g$ and $\mathbf B_g$** it is

$$\mathbf v_d = \frac{\mathbf g\times\mathbf B_g}{|\mathbf B_g|^2}:$$

in a uniform second field of gravity a neutral body would not fall but drift sideways. That is what L0 says; whether nature has a $\mathbf B_g$ strong enough for this to show is not something the virtual universe can tell (the law holds for slow bodies, and it fails known tests of general relativity, entry [2026-006](../2026-006/)).

## How the engine follows it

A simple step rule would spoil the turn: velocity Verlet treats $\mathbf v\times\boldsymbol\Omega$ as if it did not depend on $\mathbf v$, and the speed would creep. The engine uses the **Boris push** (task E3.2, decision D10): within each half step it gives a quarter kick with $\mathbf a_E$, turns the velocity about $\boldsymbol\Omega$ with Boris's formula, which keeps the length of the vector exactly, and gives another quarter kick. With no second field it is velocity Verlet again.

**Checks of the engine** (`engine/tests/test_boris.py`, pull request #44, under review):

| Check | Result |
|---|---|
| proton in 5 nT, one period, 2D and 3D | radius kept to $10^{-6}$, speed to $10^{-12}$, back at its start to $10^{-6}$ of the circumference |
| charge launched at $\mathbf E\times\mathbf B/B^2$, 50 s | stays on the drift to $10^{-9}$ |
| neutral body in $\mathbf B_g$ | turns at $\Omega = B_g$, one period, back at its start to $10^{-6}$ |
| no second field | the same steps as velocity Verlet, to rounding |

One lesson from building it, for anyone writing an integrator: a first version split the step as "kick, half turn, drift, half turn, kick", and a charge launched exactly at the drift velocity wobbled off it by $1.25\times10^{-7}$ of its speed, an error of order $\theta^2/8$ for a turn of $\theta = 10^{-3}$ per step. Making each half kick a whole Boris push removed the wobble: the push keeps the drift exactly at any step.

## Where it stops

The second field in the engine is, for now, a uniform background: the field made by moving bodies themselves (task E2.2) still needs its slow-body form (question 2 of entry [2026-005](../2026-005/)). The Composer coordinate of $\mu(\mathbf v\times\boldsymbol{\mathcal B})$ is not a force under L0; reading it as one is the hypothesis L6, which the Boris push does not cover.
