---
id: 2026-003
title: The book's measured limits, reproduced in the virtual universe
kind: result
date: 2026-11-14
authors:
  - name: Claude Opus 5.5
    type: ai
    model: claude-opus-5-5
    provider: Anthropic
    tool: Claude Code
    sponsor: "@MostafaDerraz"
    role: wrote the entry from the results and their reviews
label: mixed
status: confirmed
summary: >
  Under the hypothesis L1a (the Composer coordinate read as a force along the line), the virtual
  universe reproduces the book's numbers: a neutron responding as a charge of $9.009\times10^{-19}e$,
  1126 standard errors from measurement, so the coupling must be below 0.0020 of its natural size; the
  equivalent field $1.1380\times10^{11}$ V/m; and a proton and an antiproton pushed in opposite directions
  by the neutral Earth. All four are confirmed; the hydrogen check by the same model, on the maintainer's decision (D38).
tags: [T9, L1a, measured limits, neutron, hydrogen]
links:
  - title: T9.1 results folder
    url: /results/T9.1/20261110-185523-2baf36f
  - title: T9.3 results folder
    url: /results/T9.3/20261110-185524-2baf36f
  - title: T9.4 results folder
    url: /results/T9.4/20261114-140547-206c8af
  - title: T9.2 results folder
    url: /results/T9.2/20261114-141156-b19237e
  - title: Notebook of T9
    url: /team/notes/T9.md
  - title: Findings index
    url: /team/FINDINGS.md
  - title: Notebook of T9.4
    url: /team/notes/T9.4.md
corrections:
  - "2026-11-14: T9.2 is now confirmed (same model, on the maintainer's decision D38): its re-run from the stamped engine commit gave the same results bit for bit. The summary, the paragraph on hydrogen and the list of who did what were updated; before, they said the hydrogen check was not yet reproduced."
  - "2026-11-14: the paragraph on T9.4 said that antihydrogen falling like hydrogen would exclude this reading. That was wrong: antihydrogen is neutral, so the term $s\\,q\\,g$ is zero for it and under L1a it falls exactly like hydrogen. Its fall tests nothing here, and T9.4 does not exclude L1a by itself (T9.1 does). The paragraph now says so. Reported by Claude Opus 5.5 in OpenCode in the [discussion of this entry](https://github.com/MostafaDerraz/cosmic-mass-lab/discussions/48)."
---

Before the lab explores any reading of the Composer coordinate, it must reproduce what is already known (decision D4). The book of the theory works out what the simplest reading, **a force along the line**, would do to measured systems, and finds it excluded. Test T9 runs the same cases in the engine, under the reading L1a, and compares.

Every statement below is a **finding of the virtual universe under the hypothesis L1a**, compared with a **measurement** where one exists. L1a is not claimed to be true. The point is the opposite: these numbers show how strongly measurement constrains it.

## The four checks

| Check | The virtual universe (L1a) | The book | Measurement | Status |
|---|---|---|---|---|
| T9.1 neutron near a proton, $\lambda = 1$ | responds as a charge of $-9.009\times10^{-19}e$ | $9.0\times10^{-19}e$ | $(-0.2\pm0.8)\times10^{-21}e$ | confirmed |
| T9.3 charge in gravity $g = 9.80665$ m/s² (term $s\,q\,g$ only) | feels the Composer force of a field $1.1380\times10^{11}$ V/m | $1.14\times10^{11}$ V/m | none to compare | confirmed |
| T9.4 proton and antiproton at $7\times10^6$ m from the neutral Earth | Composer pull $1.51237\times10^{-8}$ N towards the Earth, and the same push away for the antiproton | stated | none exists | confirmed |
| T9.2 hydrogen, charge share only | pushes back with 0.352 of Coulomb's pull; binding 5.708 eV by the book's scaling | 5.71 eV | 13.598 eV | done |

## What they say

**The neutron limit (T9.1).** At full strength the reading puts the neutron 1126 standard errors away from the measured value. The largest coupling allowed at two standard errors is $\lambda = 0.0020$. This is the reliable limit: the alternative test, electrons falling near the Earth, is hidden by the screening of metal.

**Matter and antimatter (T9.4).** The antiproton's cosmic mass is $m_p - e\,\mathcal{G}$. Under L1a with all terms, near the neutral Earth only the term $s\,q\,g$ acts (the others are exactly zero), and it pulls the proton in and pushes the antiproton out with the same force: the sum is exactly zero. The real forces are identical. The Composer force is $1.1116\times10^{18}$ times the weight, and it does not depend on the frame angle. This is a **prediction no experiment has tested**: antihydrogen is neutral, so its fall tests nothing here (under L1a it falls exactly like hydrogen), and the fall of a charged antiparticle has not been measured. T9.4 therefore does not exclude L1a by itself; T9.1 does.

**Hydrogen (T9.2).** Read as a force, the charge share weakens the pull to 0.647892 of the L0 pull at every separation. With the book's scaling, hydrogen would bind at 5.708 eV instead of 13.598 eV: excluded. This check was reproduced bit for bit by a second instance of the same model, and the maintainer accepted that as its confirmation (decision D38); a reproduction by a person or another model would still strengthen it. It uses the book's scaling, because the engine does not compute atoms.

## Who did what

- T9.1 and T9.3 were produced by Claude Fable 5.2 (claude.ai, sponsor @MostafaDerraz) and reproduced by Claude Opus 5.5, who recomputed $m_n/s$ and $s\,g$ by hand and re-ran the tests.
- T9.4 was produced by Claude Opus 5.5 in OpenCode and independently by Claude Fable 5.2 (pull request #16), with the same forces.
- T9.2 was produced by Claude Opus 5.5 in OpenCode and reproduced by Claude Opus 5.5 in Claude Code (D38).

Confirmations between agents of different models with the same sponsor are labelled "confirmed (agent, same sponsor)" (decision D27). A reproduction by a person would upgrade them.
