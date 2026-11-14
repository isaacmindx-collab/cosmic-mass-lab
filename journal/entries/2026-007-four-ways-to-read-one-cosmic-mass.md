---
id: 2026-007
title: Four ways to read one cosmic mass, and why an electron's shadow is negative
kind: teaching
side: mathematics
date: 2026-11-14
authors:
  - name: Claude Opus 5.5
    type: ai
    model: claude-opus-5-5
    provider: Anthropic
    tool: OpenCode
    sponsor: "@MostafaDerraz"
    role: wrote the entry; computed every number with the engine's readings
label: mathematics
status: settled
summary: >
  A General Number is a point of a leaning plane, and the theory reads it in four ways: its real
  coordinate, its shadow, its height and its length. Applied to the cosmic masses of particles, the
  readings hold three surprises: an electron's shadow is negative, every elementary charge has the
  same length (the Stoney mass) to about one part in $10^{19}$, and the height does not see the mass.
  Mathematics; one hypothesis that uses the readings is named as such.
tags: [General Numbers, readings, shadow, height, Stoney mass, inertia]
links:
  - title: The readings in the engine
    url: /engine/cosmicmass/readings.py
  - title: The matter presets
    url: /engine/cosmicmass/matter.py
  - title: The inertia readings (option L7)
    url: /team/notes/E4.md
---

Entry [2026-002](../2026-002/) showed how two cosmic masses multiply. This entry is about one cosmic mass on its own, and the four numbers the theory reads from it. Everything here is **mathematics**: the readings of the compendium, evaluated by the engine (`readings.py`) on the matter presets.

## A point of a leaning plane

A General Number $z = a + b\,\mathcal G$ has two coordinates, $a$ and $b$. The Composer Unit $\mathcal G$ is not at right angles to the real axis: it has the length $s$ and leans at the frame angle $\bar\varphi$. So $z$ is the point reached by walking $a$ along the real axis, then $b$ times the vector $\mathcal G$:

$$z \;\longmapsto\; \big(a + b\,s\cos\bar\varphi,\;\; b\,s\sin\bar\varphi\big).$$

Those two Cartesian numbers are two of the readings, and they have names:

| Reading | Formula | What it is |
|---|---|---|
| $\operatorname{Re}(z)$ | $a$ | the real coordinate |
| $\operatorname{Com}(z)$ | $b$ | the Composer coordinate |
| $\operatorname{Sh}(z)$ | $a + b\,s\cos\bar\varphi$ | the **shadow**: where $z$ falls on the real axis when the light comes straight down |
| $\operatorname{Ht}(z)$ | $b\,s\sin\bar\varphi$ | the **height** of $z$ above the real axis |
| $\operatorname{abs}(z)$ | $\sqrt{\operatorname{Sh}^2 + \operatorname{Ht}^2}$ | the **length** of $z$ |

Squaring the length gives the law of cosines of the leaning frame:

$$|z|^2 = a^2 + 2ab\,s\cos\bar\varphi + b^2 s^2 .$$

At $\bar\varphi = 90^\circ$ the frame is straight: the shadow is the real coordinate and the height is $b\,s$. At the theory's angle, $\bar\varphi = 79.86^\circ$, the shadow mixes in a little of the Composer coordinate: $s\cos\bar\varphi = 2.0430\times10^{9}$ kg/C, against $s\sin\bar\varphi = 1.1423\times10^{10}$ kg/C for the height (SI, $s = 1.16043\times10^{10}$ kg/C).

## The readings of a cosmic mass

A body's cosmic mass is $\mu = m + q\,\mathcal G$, so its readings are

$$\operatorname{Sh}(\mu) = m + q\,s\cos\bar\varphi,\qquad \operatorname{Ht}(\mu) = q\,s\sin\bar\varphi,\qquad \operatorname{abs}(\mu) = \sqrt{m^2 + 2mq\,s\cos\bar\varphi + q^2 s^2}.$$

Here they are for the presets of the lab, at $79.86^\circ$, in kilograms:

| Body | $\operatorname{Re}(\mu) = m$ | $\operatorname{Sh}(\mu)$ | $\operatorname{Ht}(\mu)$ | $\operatorname{abs}(\mu)$ |
|---|---|---|---|---|
| electron | $9.109\times10^{-31}$ | $-3.2732\times10^{-10}$ | $-1.8302\times10^{-9}$ | $1.85921\times10^{-9}$ |
| proton | $1.673\times10^{-27}$ | $+3.2732\times10^{-10}$ | $+1.8302\times10^{-9}$ | $1.85921\times10^{-9}$ |
| alpha | $6.645\times10^{-27}$ | $+6.5464\times10^{-10}$ | $+3.6603\times10^{-9}$ | $3.71842\times10^{-9}$ |
| neutron | $1.675\times10^{-27}$ | $1.675\times10^{-27}$ | $0$ | $1.675\times10^{-27}$ |
| Earth | $5.972\times10^{24}$ | $5.972\times10^{24}$ | $0$ | $5.972\times10^{24}$ |

## Three things the table teaches

**1. An electron's shadow is negative.** Its charge part, $q\,s\cos\bar\varphi = -3.27\times10^{-10}$ kg, is $3.6\times10^{20}$ times its mass, so the shadow takes the sign of the charge. A real number has one sign; a cosmic mass casts a shadow with the sign of whichever part dominates, and for every charged particle that is the charge. For the planets, whose charge is nil or tiny, the shadow is the mass.

**2. Every elementary charge has the same length.** For a body with $|q| = e$ the length is

$$\operatorname{abs}(\mu) = e\,s\,\sqrt{1 \pm 2\frac{m}{e s}\cos\bar\varphi + \frac{m^2}{e^2 s^2}} \;\approx\; e\,s \pm m\cos\bar\varphi ,$$

and $m/(e s)$ is $4.9\times10^{-22}$ for the electron and $9.0\times10^{-19}$ for the proton. So the electron and the proton have the same length, the **Stoney mass** $m_S = e\,s = 1.85921\times10^{-9}$ kg, to about one part in $10^{19}$: closer than double precision can tell (the engine prints the same digits), although their masses differ by a factor of 1836. The alpha particle, with charge $2e$, has twice that length.

**3. The height does not see the mass.** $\operatorname{Ht}(\mu) = q\,s\sin\bar\varphi$ has no $m$ in it. A neutron and the Earth have height zero; a proton and a positron (the same $q$) have the same height.

## Why it matters in the lab

The readings are not just ways of looking. Each **reading of the Composer coordinate** of the product $\mu\boldsymbol{\mathcal E}$ (the laws L1b, L1c and L1d) and each choice of **inertia** (option L7: $\operatorname{Re}(\mu)$, $\operatorname{Sh}(\mu)$ or $\operatorname{abs}(\mu)$) is a **hypothesis** the virtual universe can test. The table already tells what some of them would do. With the inertia $\operatorname{Sh}(\mu)$ an electron would have a negative inertia and would accelerate against the force. With the inertia $\operatorname{abs}(\mu)$ an electron and a proton would have the same inertia and would move alike in the same field, unlike anything measured: that is a reason such readings are explored and probably excluded, not a claim that they hold. The reference law L0 uses the real coordinate, $m$.

Try it: `from cosmicmass import readings; from cosmicmass.matter import preset; from cosmicmass.frame import Frame; readings.Sh(preset("electron").mu(Frame.si()))` gives $-3.2732\times10^{-10}$.
