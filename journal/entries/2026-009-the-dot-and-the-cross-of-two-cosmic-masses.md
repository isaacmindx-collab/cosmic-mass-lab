---
id: 2026-009
title: The dot and the cross of two cosmic masses, and why a proton and an electron are almost exactly opposite
kind: teaching
side: mathematics
date: 2026-11-14
authors:
  - name: Claude Fable 5.2
    type: ai
    model: claude-fable-5-2
    provider: Anthropic
    tool: Claude (chat session on claude.ai)
    sponsor: "@MostafaDerraz"
    role: wrote the entry; checked the identities with SymPy and the numbers with 50-digit arithmetic
label: mathematics
status: settled
summary: >
  Multiply one cosmic mass by the conjugate of another and you get two familiar things at once:
  the shadow of the result is the dot product of the two points of the leaning plane, and its
  height is their cross product. Two cosmic masses are parallel exactly when the bodies have the
  same charge-to-mass ratio. A proton and an electron are opposite to within $8.9\times10^{-19}$
  of a radian, and the number that separates them is a nucleon's mass counted in Stoney masses.
tags: [General Numbers, conjugate, dot product, cross product, charge-to-mass ratio, teaching]
links:
  - title: The conjugate and the readings in the compendium
    url: /docs/formulas-compendium/formulas-compendium.tex
  - title: The conjugate in the engine
    url: /engine/cosmicmass/gn.py
  - title: The matter presets
    url: /engine/cosmicmass/matter.py
---

Entry [2026-002](../2026-002/) multiplied two cosmic masses. Entry [2026-007](../2026-007/) read one cosmic mass in four ways. This entry asks a question between the two: **how are two cosmic masses placed relative to each other?** Everything here is **mathematics**: the conjugate of the compendium ("Conjugate, skew flip, division") applied to $\mu = m + q\,\mathcal G$.

## Two points of the leaning plane

A cosmic mass is a point of the leaning plane (entry 2026-007). Its shadow and its height are its ordinary coordinates:

$$\operatorname{Sh}\mu = m + q\,s\cos\bar\varphi, \qquad \operatorname{Ht}\mu = q\,s\sin\bar\varphi .$$

Two bodies give two points, $\mu_a$ and $\mu_b$. Two arrows from the origin have a **dot product** (how much they point the same way) and a **cross product** (the area of the parallelogram they span). The General Numbers give both in one multiplication.

## The conjugate is the mirror image

The conjugate of $z = a + b\,\mathcal G$ is

$$\bar z = (a + 2b\,s\cos\bar\varphi) - b\,\mathcal G .$$

It keeps the shadow and reverses the height: $\operatorname{Sh}\bar z = \operatorname{Sh}z$, $\operatorname{Ht}\bar z = -\operatorname{Ht}z$. So $\bar z$ is the mirror image of $z$ in the real axis. Note what it is *not*: it is not $a - b\,\mathcal G$. That is the skew flip, a different operation, because the Composer Unit leans.

## One product, two answers

Multiply $\mu_a$ by the mirror image of $\mu_b$, with the Rule of the Square $\mathcal G^2 = 2s\cos\bar\varphi\,\mathcal G - s^2$:

$$\mu_a\bar\mu_b = \big(m_a m_b + s^2 q_a q_b + 2s\cos\bar\varphi\, m_a q_b\big) + \big(q_a m_b - m_a q_b\big)\,\mathcal G .$$

Now read it with the shadow and the height:

$$\operatorname{Sh}(\mu_a\bar\mu_b) = m_a m_b + s\cos\bar\varphi\,(m_a q_b + q_a m_b) + s^2 q_a q_b \quad\text{(the dot product)},$$

$$\operatorname{Ht}(\mu_a\bar\mu_b) = s\sin\bar\varphi\,(q_a m_b - m_a q_b) \quad\text{(the cross product)}.$$

The two together give the lengths back, which is the identity of Lagrange:

$$|\mu_a|^2\,|\mu_b|^2 = \operatorname{Sh}(\mu_a\bar\mu_b)^2 + \operatorname{Ht}(\mu_a\bar\mu_b)^2 .$$

I checked the three formulas with SymPy from the Rule of the Square alone; the last one simplifies to zero identically.

## When are two cosmic masses parallel?

The cross product vanishes when $q_a m_b = m_a q_b$. For bodies with mass that is

$$\frac{q_a}{m_a} = \frac{q_b}{m_b} .$$

**Two cosmic masses are parallel exactly when the bodies have the same charge-to-mass ratio.** The condition does not contain the frame angle $\bar\varphi$, nor $s$: it is the same in every frame. Two protons are parallel. Two neutral bodies are parallel, whatever their masses: they both lie on the real axis.

## Four pairs

Computed from the matter presets of the engine with 50-digit arithmetic, in the SI frame ($s = 1.16043\times10^{10}$ kg/C, $\bar\varphi = 79.86^\circ$):

| Pair | Dot | Cross | $\lvert\mu_a\rvert\lvert\mu_b\rvert$ | Sine of the angle between them |
|---|---|---|---|---|
| proton, proton | $3.45666\times10^{-18}$ | $0$ | $3.45666\times10^{-18}$ | $0$ |
| proton, electron | $-3.45666\times10^{-18}$ | $3.06\times10^{-36}$ | $3.45666\times10^{-18}$ | $8.86\times10^{-19}$ |
| proton, neutron | $5.48239\times10^{-37}$ | $3.06540\times10^{-36}$ | $3.11404\times10^{-36}$ | $0.98438$ |
| Earth, proton | $1.95476\times10^{15}$ | $-1.09298\times10^{16}$ | $1.11032\times10^{16}$ | $-0.98438$ |

(units: kg$^2$). Three things to see.

**A proton and an electron are almost exactly opposite.** Their dot product is minus the product of their lengths to about four parts in $10^{37}$. Each is, to that accuracy, one elementary charge along $\mathcal G$, in opposite directions; the masses tilt them off that line by a hair. The sine of the angle left between them is

$$\frac{(m_p + m_e)\,\sin\bar\varphi}{e\,s} = 8.86\times10^{-19}.$$

**The number is a mass counted in Stoney masses.** $e\,s = 1.859\times10^{-9}$ kg is the Stoney mass (entry 2026-007), and $m_p/(e\,s) = 9.0\times10^{-19}$. The same ratio, for the neutron, is the $9.0\times10^{-19}$ of entry [2026-003](../2026-003/). There it appears under a hypothesis (the reading L1a); here it is plain geometry: how far a nucleon's mass tilts one elementary charge.

**A neutral body and a charge make the frame angle.** The neutron lies on the real axis and the proton lies along $\mathcal G$ to 18 digits, so the angle between them is $\bar\varphi$ itself: $\sin 79.86^\circ = 0.98438$. The same holds for the neutral Earth and a proton.

## The dot product is not the force

The force between two bodies at rest reads the real coordinate of the plain product (entry 2026-002):

$$\operatorname{Re}(\mu_a\mu_b) = m_a m_b - s^2 q_a q_b .$$

Compare it with the dot product above. Both are symmetric in the two bodies, and both begin with $m_a m_b$. But the charges enter with the opposite sign, and the dot product also holds the Coupling term $m_a q_b + q_a m_b$, which the force law does not read. The compendium's "laws of the parts" say the same thing in general: the shadow of a product is $\operatorname{Sh}z\operatorname{Sh}w - \operatorname{Ht}z\operatorname{Ht}w$, with a minus. Geometry and force are two different readings of two different products.

## A practical warning

In double precision, do not compute the cross product of a proton and an electron by forming $\mu_a\bar\mu_b$ and reading its Composer coordinate. The engine's `conjugate()` adds and removes terms of size $10^{-18}$ to reach a result of size $10^{-46}$, and returns exactly $0$. Compute $q_a m_b - m_a q_b$ directly ($2.68\times10^{-46}$ kg C). The numbers in the table come from that formula.

Entry [2026-010](../2026-010/) uses the cross product for something concrete: it is the size of a broken third law.
