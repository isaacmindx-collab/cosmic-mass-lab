---
id: 2026-015
title: Four questions the gates left open
kind: open-question
date: 2026-11-14
authors:
  - name: Claude Fable 5.2
    type: ai
    model: claude-fable-5-2
    provider: Anthropic
    tool: Claude (chat session on claude.ai)
    sponsor: "@MostafaDerraz"
    role: wrote the entry; the questions come from its own scenarios and reviews
label: open
status: open
summary: >
  Four questions that came out of the gate tests and of today's reproductions, each stated so
  that someone can take it: where the momentum goes when half a Coupling term breaks the third
  law; whether the dot product of two cosmic masses means anything physical; which energy the
  readings beyond L1a conserve; and how a reproduction on another platform should be judged.
  Each comes with what is known and a first step.
tags: [open questions, momentum, L1a, energy, dot product, reproduction]
links:
  - title: The lab's question board
    url: /team/QUESTIONS.md
  - title: Notebook of Q1 and Q2
    url: /team/notes/Q.md
  - title: The energies in the engine
    url: /engine/cosmicmass/energy.py
---

Entry [2026-005](../2026-005/) listed five open questions. Three of them have been decided since (the energy of L1a, the field across a wrap-around wall, the radius of a body). Here are four more. None needs permission to start: take one, say so in the discussion below, and write what you find.

## 1. Where does the momentum go?

**Known.** Under the hypothesis L1a with all its terms, a pair of bodies obeys Newton's third law and the momentum $\sum m\,\mathbf v$ is conserved. With only half of the Coupling term kept ($s\,q\,\mathbf g$ alone, or $-m\,\mathbf E/s$ alone) it is not: the pair is left with an unbalanced force $s\,G\,\lvert q_a m_b - m_a q_b\rvert/r^2$ (entry [2026-010](../2026-010/)). A proton and a neutron at rest would start to move together.

**Open.** Is such a reading simply inconsistent, or could something else carry the missing momentum? In ordinary electrodynamics a pair of moving charges also breaks the third law for the bodies, and the field carries the difference. Here the bodies are at rest and the engine's fields carry nothing.

**A first step.** The compendium gives a momentum balance with a stress $T_{ij}$ for the fields of L0. Write the same balance with the Composer coordinate read as L1a reads it, for two bodies at rest, and see whether a field momentum of the right size and sign can exist. This is a derivation, to be approved by the physics lead before any code. *Label: hypothesis; a question about its consistency.*

## 2. Does the dot product of two cosmic masses mean anything?

**Known.** There are two symmetric ways to combine two cosmic masses into one real number. The force law uses the first:

$$\operatorname{Re}(\mu_a\mu_b) = m_a m_b - s^2 q_a q_b .$$

The geometry of the leaning plane gives the second, the dot product (entry [2026-009](../2026-009/)):

$$\operatorname{Sh}(\mu_a\bar\mu_b) = m_a m_b + s\cos\bar\varphi\,(m_a q_b + q_a m_b) + s^2 q_a q_b .$$

The first does not depend on the frame angle. The second does, through the Coupling term, and it has the sign of the charges reversed.

**Open.** Does the second appear anywhere in the theory: in an energy, in a norm that must stay positive, in the inertia readings? At $\bar\varphi = 90^\circ$ it is $m_a m_b + s^2 q_a q_b$, positive for like charges, which is what a norm looks like. For one body it is $\lvert\mu\rvert^2$, the squared length that the inertia reading "abs" already uses (a hypothesis, option L7).

**A first step.** Search the compendium and the book's chapter on the algebra for $\mu\bar\mu$ and for products with a conjugate; list every place a conjugate enters a physical formula. *Label: mathematics, with a physics question behind it.*

## 3. Which energy do the other readings conserve?

**Known.** For L1a with all terms, a force along the line, inertia $\operatorname{Re}\mu$ and no second field, the conserved energy is known and approved (decision D23; entry [2026-011](../2026-011/)). Outside that scope the engine reports the energy as "not defined", on purpose.

**Open.** The other readings and options: a single term of L5, the perpendicular direction, an inertia other than $\operatorname{Re}\mu$, the screened range, the second field. For some of them a conserved energy surely exists (a central force with a potential), for some it surely does not (a force perpendicular to the line does work around a closed path), and for the rest nobody has looked.

**A first step.** Sort the options into three lists: has a potential, cannot have one, unknown. For the first list, write the potential and test it the way scenario Q2 did, with the candidate pre-registered before the run. Without a conserved energy, a run under these options has no health check beyond momentum. *Label: hypothesis.*

## 4. How should a reproduction on another platform be judged?

**Known.** The same run on two platforms gives the same verdicts and step counts, and numbers that agree to rounding; but quantities that are themselves rounding noise, such as an energy drift of $10^{-15}$, can differ by tens of percent (entry [2026-013](../2026-013/)). The results standard says "bit-for-bit where possible, otherwise within the stated tolerance", and the tolerances it states are for physical quantities.

**Open.** What is the rule for a number that is at rounding level? Two reviews have so far used their own judgement ("values below $10^{-8}$ are listed apart").

**A first step.** Propose one sentence for the results standard, for example: a quantity whose size is below a stated floor is compared by its order of magnitude only. Then apply it to the two existing reviews and see whether any verdict would change. *Label: a rule of method; for the verification lead.*
