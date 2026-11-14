# Rules of the project

These rules apply to everyone, human or AI agent. They exist so that every result in this project can be trusted, reproduced and credited. **How we work day to day (roles, reading order, work cycle, notes, log and handoffs) is in `TEAM.md`; read it first.**

## 1. The foundation is fixed; the hypotheses are explicit

1. **Verified formulas are the base.** The formulas in `docs/formulas-compendium/` are verified by the scripts in `verification/`. Engine code must use them as they are.
2. **The paper's law L0 is the reference.** That is `Re(mu) dv/dt = Re[mu (E_cal + v x B_cal)]` with the field law F1-F4. Every other law (L1-L8) is a **hypothesis** and must be labelled as one in code, outputs and text.
3. **Do not change a verified formula or a verification script to make a result pass.** If you think a verified formula is wrong, open an issue with a counterexample, computed to at least 30 significant digits.
4. **Stay in the language of the theory:** `mu`, `G`, the Rule of the Square, `E_cal`, `B_cal`, and the readings `Re`, `Com`, `Sh`, `Ht`, `abs`. Temperature and pressure are properties of populations of `mu`.

## 2. Gates before findings

5. **T0 must pass.** No coupling result counts unless the same engine version passes the consistency gate T0. The engine must reproduce Newton plus Coulomb, conserve `rho_mu`, energy and momentum, and show angle invariance under L0.
6. **T9 must pass.** Before exploring a coupling reading, the engine must reproduce the measured limits of the book's Chapter 10: neutron 9.0e-19 e, hydrogen 5.71 eV under the charge share, 1.14e11 V/m.
7. **CI must be green.** Every pull request must keep all verification checks passing.

## 3. Reproducibility

8. **Every result comes with:**
   - the script that produced it;
   - the **settings stamp** (universe U, matter M, law L, units, dimension, time step, engine commit);
   - the raw output;
   - the T0 status of that engine commit.
9. **Convergence is shown, not assumed.** Halve the time step and change the particle count (T7). A result that moves by more than 1% when you do this is not a result yet.
10. **SI and scaled units.** If a finding uses scaled units, show the SI run, or explain why it cannot be done.

## 4. Honesty

11. **Three kinds of statement, never mixed:**
    - **mathematics:** proved or verified;
    - **measurement:** cited, with its source;
    - **finding of the virtual universe:** a simulation result, which says nothing about nature by itself.
12. **Negative results are welcome**, and are recorded like positive ones. A reading that breaks conservation, or is excluded by measurement, is a finding.
13. **No tuning to fit.** Parameters are fixed before a run. If you scan a parameter, report the whole scan.
14. **Stay within scope.** The field law is valid for slow bodies. It fails known tests of general relativity (LAGEOS 1/4, no light bending, negative wave energy). Do not use the simulator to argue against those results.

## 5. Working together

15. **Claim before you work.** Use the "Claim a scenario" issue, so two people do not do the same test. A claim with no activity for 14 days is released.
16. **Small pull requests**, one scenario or one engine component each, with the test ID in the title (for example `T1.4: hydrogen-like pair under L1e`).
17. **Review by someone else.** Every finding is reproduced by a second contributor, human or agent, before it is marked "confirmed".
18. **Respect.** Discuss results, not people. Critique is welcome; contempt is not.

## 5b. Architecture

18b. **The architecture travels with the code (D18).** A pull request that changes code in `engine/`, `scenarios/`, `simulator/` or `tools/` updates `ARCHITECTURE.md` (registry, Mermaid diagrams, contracts, change log). CI checks it.
18c. **The plan:** tasks, their order and their acceptance criteria are in `docs/WORK-PLAN.md`.

## 5b2. Code format

18c2. **Format before you commit:** run `ruff format .` (and `ruff check .`); CI rejects unformatted Python (decision D25).

## 5c. Questions

18d. **Ask and answer in the open.** Put questions on `team/QUESTIONS.md` (or open a Question issue). Anyone, human or agent, may propose an answer with evidence; the person who decides accepts it.

## 6. AI agents

19. **AI agents follow `AGENTS.md` as well.** Every agent contribution names the agent and model, and has a human sponsor who is responsible for it.

## 7. Credit and licence

19b. **Papers** are published under the affiliation **Co-exist initiative of Cosmic mass universe**, after review and a vote of the Board (`PUBLISHING.md`).


20. **Credit.** Every merged contribution is listed in `CONTRIBUTORS.md`. Publications of findings credit the contributors who produced and confirmed them; authorship follows the contribution.
21. **Licence:**
    - code under the **MIT** licence;
    - documents and findings under **CC BY 4.0**;
    - the books and papers in `sources/` remain the author's work; they are shared for reference and are not relicensed.
