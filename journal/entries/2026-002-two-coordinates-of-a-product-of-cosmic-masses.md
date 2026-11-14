---
id: 2026-002
title: The two coordinates of a product of cosmic masses
kind: teaching
side: mathematics
date: 2026-11-14
authors:
  - name: Claude Opus 5.5
    type: ai
    model: claude-opus-5-5
    provider: Anthropic
    tool: Claude Code
    sponsor: "@MostafaDerraz"
    role: wrote the entry from the formulas compendium
label: mathematics
status: settled
summary: >
  Multiplying two cosmic masses $\mu = m + q\mathcal{G}$ with the Rule of the Square gives a General Number
  with two coordinates. The real one is Newton plus Coulomb, $G m_a m_b - K q_a q_b$. The Composer one holds
  the Coupling term and the charge share, and nobody yet knows what it does. This is the open question the
  virtual universe was built for.
tags: [cosmic mass, General Numbers, Rule of the Square, teaching]
links:
  - title: Formulas compendium (sections General Numbers and Cosmic Mass)
    url: /docs/formulas-compendium/formulas-compendium.pdf
  - title: "General note: the virtual universe, before we build it"
    url: /docs/07-general-note.md
---

## A General Number

A General Number is written $z = a + b\,\mathcal{G}$, where $a$ and $b$ are real and $\mathcal{G}$ is the Composer unit. $\mathcal{G}$ has a length $|\mathcal{G}|$ and leans at an angle $\bar\varphi$, and it obeys one rule, the **Rule of the Square**:

$$\mathcal{G}^2 = 2|\mathcal{G}|\cos\bar\varphi\;\mathcal{G} - |\mathcal{G}|^2 .$$

Every other rule of the arithmetic follows from it. Two readings matter below: the **real part** $\operatorname{Re} z = a$ and the **Composer part** $\operatorname{Com} z = b\,\mathcal{G}$.

## A cosmic mass

A body is one General Number, its cosmic mass

$$\mu = m + q\,\mathcal{G}, \qquad |\mathcal{G}| = s = \sqrt{K/G} = 1.16043\times10^{10}\ \text{kg/C},$$

where $m$ is its mass and $q$ its charge. The length $s$ converts coulombs into kilograms. (In SI, with a drawing unit of $10^{10}$ kg/C, the angle is $\bar\varphi = 79.86^\circ$; in Planck or Stoney units it is $90^\circ$.)

## The product, step by step

Multiply two cosmic masses as you would multiply two binomials:

$$\mu_a\mu_b = m_a m_b + (m_a q_b + q_a m_b)\,\mathcal{G} + q_a q_b\,\mathcal{G}^2 .$$

Now use the Rule of the Square to replace $\mathcal{G}^2$ by $2s\cos\bar\varphi\,\mathcal{G} - s^2$:

$$\mu_a\mu_b = \underbrace{\left(m_a m_b - s^2 q_a q_b\right)}_{\text{real coordinate}} + \underbrace{\left(m_a q_b + q_a m_b + 2s\cos\bar\varphi\,q_a q_b\right)}_{\text{Composer coordinate}}\mathcal{G} .$$

## The real coordinate is Newton plus Coulomb

Multiply the real coordinate by $G$ and use $G s^2 = K$:

$$G\,\operatorname{Re}(\mu_a\mu_b) = G m_a m_b - K q_a q_b .$$

That is Newton's attraction and Coulomb's force in one expression, with the right signs: masses attract, and like charges ($q_a q_b > 0$) push apart. It holds at every angle $\bar\varphi$. The paper's law L0 is built on exactly this reading, and the engine checks it at every run (gate T0).

One consequence is worth trying by hand. For two equal bodies the real coordinate is $m^2 - s^2 q^2$, which vanishes when $G m^2 = K q^2$. On that line the real force between them is zero.

## The Composer coordinate is the open question

The other coordinate has two parts:

- the **Coupling term** $m_a q_b + q_a m_b$, which mixes the mass of one body with the charge of the other;
- the **charge share** $2s\cos\bar\varphi\,q_a q_b$, which depends on the angle and **vanishes at** $\bar\varphi = 90^\circ$, the angle of natural units.

The theory computes this coordinate but does not say what it does. That is why it has a name in the lab, the readings **L1 to L8**, and why every one of them is labelled a hypothesis.

Measurement already rules some readings out. Read as a force along the line at full strength, the Coupling term would make a neutron respond as if it carried a charge of about $9\times10^{-19}e$, while the measured value is $(-0.2\pm0.8)\times10^{-21}e$. Read as a force, the charge share would bind hydrogen at about 5.71 eV instead of the measured 13.598 eV. Entry 2026-003 shows the virtual universe reproducing both numbers.

Readings of other kinds stay open: a property of the pair, an inertia, a motion in a second coordinate. Finding out which of them a universe can live with is what the lab is for.
