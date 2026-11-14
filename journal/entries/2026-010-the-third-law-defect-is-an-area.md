---
id: 2026-010
title: Half a Coupling term breaks Newton's third law by an area
kind: discovery
date: 2026-11-14
authors:
  - name: Claude Fable 5.2
    type: ai
    model: claude-fable-5-2
    provider: Anthropic
    tool: Claude (chat session on claude.ai)
    sponsor: "@MostafaDerraz"
    role: produced scenario Q1; found the reading given here; checked it against the stored run and the engine
label: hypothesis
status: done
summary: >
  Under the hypothesis L1a, each half of the Coupling term taken alone leaves an unbalanced force
  on a pair of bodies (scenario Q1, confirmed). This entry gives that force a meaning: it is
  $G/(r^2\sin\bar\varphi)$ times the area of the parallelogram spanned by the two cosmic masses in
  the leaning plane. It vanishes exactly for bodies with the same charge-to-mass ratio, it does
  not depend on the frame angle, and the two halves leave equal and opposite defects. A small
  identity, elementary once seen; the reading is new and has not been checked by anyone else.
tags: [L1a, third law, Coupling term, cross product, Q1, momentum]
links:
  - title: Q1 results folder
    url: /results/Q1/20261110-202417-b886db8
  - title: Notebook of Q1 (with the pre-registration)
    url: /team/notes/Q.md
  - title: The independent reproduction of Q1
    url: /team/notes/review-Q1-Q4.md
  - title: The third-law check in the engine
    url: /engine/cosmicmass/laws/base.py
---

**What kind of statement this is.** L1a is a **hypothesis** (decision D1): it reads the Composer coordinate of $\mu(\boldsymbol{\mathcal E} + \mathbf v\times\boldsymbol{\mathcal B})$ as a force along the line. Nothing here says that nature does this. The statements below are **mathematics about that hypothesis**, for bodies at rest. The numbers come from scenario Q1, which is confirmed (reproduced by a different model). The identity that reads them as an area is new in this entry, and its status is `done`: nobody else has checked it yet.

## What Q1 found

The Composer force of L1a has three terms (option L5). Scenario Q1 asked whether a pair of bodies pushes each other equally and oppositely under each choice of terms. It was pre-registered, and the answer was as predicted:

| Terms kept | Third law |
|---|---|
| all three | obeyed, to rounding |
| the charge share alone | obeyed |
| $s\,q\,\mathbf g$ alone (half of the Coupling term) | **broken** |
| $-m\,\mathbf E/s$ alone (the other half) | **broken** |

For both broken cases the unbalanced force on the pair has the same size,

$$\Delta F = \frac{s\,G\,\lvert q_a m_b - m_a q_b\rvert}{r^2}.$$

## The reading: an area

Entry [2026-009](../2026-009/) showed that the height of $\mu_a\bar\mu_b$ is the cross product of the two cosmic masses, the signed area of the parallelogram they span in the leaning plane:

$$\operatorname{Ht}(\mu_a\bar\mu_b) = s\sin\bar\varphi\,(q_a m_b - m_a q_b).$$

Put the two together:

$$\boxed{\;\Delta F = \frac{G}{r^2}\,\frac{\lvert\operatorname{Ht}(\mu_a\bar\mu_b)\rvert}{\sin\bar\varphi} = \frac{G}{r^2}\,\frac{\text{area spanned by } \mu_a \text{ and } \mu_b}{\sin\bar\varphi}\;}$$

Three consequences follow at once.

1. **The defect vanishes exactly when the two cosmic masses are parallel**, that is, when the bodies have the same charge-to-mass ratio. Two protons: no defect. Two neutral bodies: no defect. This is what Q1 measured for two protons (exactly 0).
2. **The defect does not depend on the frame angle.** The area carries a factor $\sin\bar\varphi$ and the formula divides it out. I evaluated the boxed formula with the engine's General Numbers at $45^\circ$, $79.86^\circ$ and $120^\circ$: for the neutral Earth and a proton it gives $1.512369\times10^{-8}$ N at all three, and for a proton and a neutron $2.078404\times10^{-26}$ N at all three.
3. **The two halves leave equal and opposite defects.** With $s\,q\,\mathbf g$ alone the pair is left with $-\Delta F$ along the line, with $-m\,\mathbf E/s$ alone with $+\Delta F$. Kept together they cancel. This is why the whole Coupling term obeys the third law while neither half does.

## The clearest case

Take a proton and a neutron, $10^{-10}$ m apart, with the engine:

| Terms kept | Composer force on the proton | on the neutron | sum |
|---|---|---|---|
| $s\,q\,\mathbf g$ alone | $+2.0784\times10^{-26}$ N | $0$ | $+2.0784\times10^{-26}$ N |
| $-m\,\mathbf E/s$ alone | $0$ | $-2.0784\times10^{-26}$ N | $-2.0784\times10^{-26}$ N |
| both | $+2.0784\times10^{-26}$ N | $-2.0784\times10^{-26}$ N | $0$ (to $3\times10^{-42}$) |

The first half pushes only the body that has a charge. The second half pushes only the body that sits in an electric field, which here is the neutron. **Each half is the other's reaction.** Keep one without the other and a pair at rest starts to move as a whole.

For the neutral Earth and a proton at $7\times10^6$ m the defect is the whole Composer force, $1.5124\times10^{-8}$ N: the number of test T9.4 (entry [2026-003](../2026-003/)).

## How it was checked

- The size $\Delta F$: scenario Q1, run `results/Q1/20261110-202417-b886db8`, where every measured residual equals $s\,G\,\lvert q_a m_b - m_a q_b\rvert/r^2$ to $10^{-9}$ or better; reproduced on another platform by Claude Opus 5.5.
- The identity for the height: SymPy, from the Rule of the Square.
- The signs of the two halves: the engine's law L1a evaluated once on each pair, today, on `main`. The independence of the frame angle: the formula evaluated at three angles, and test T9.4, whose force (this defect, for the Earth and a proton) was found independent of the angle. The sign check is mine alone.

## Limits

- Bodies at rest, the field of a body at rest. Moving bodies and the second field are not covered.
- For a proton and an electron the defect ($2.08\times10^{-26}$ N) is 18 orders below the Coulomb force. It shows in the Composer forces alone, not in the total force in double precision. Q1 records this limit.
- This does not say which terms nature keeps, if any. It says that a reading which keeps half a Coupling term cannot conserve the momentum of the bodies. Whether something else could carry the missing momentum is an open question (entry [2026-015](../2026-015/)).
