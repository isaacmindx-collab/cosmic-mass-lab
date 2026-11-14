# How the team works

This is the operating model of the project, for human contributors and AI agents alike. Read it fully before your first contribution. The short rules are in `CONTRIBUTING.md` (everyone) and `AGENTS.md` (agents). The format of results is in `team/RESULTS-STANDARD.md`.

It is designed around one aim: **results that are correct, reproducible and trusted**, produced by many people and agents who may never talk to each other directly.

---

## 1. The objective

**Build a virtual universe made only of cosmic masses (`mu = m + q G`), and use it to find out what the unread second coordinate of their product would do, under each possible reading.**

The project runs in five milestones (stages S1-S8 and every task with its acceptance criteria: `docs/WORK-PLAN.md`; the code structure: `ARCHITECTURE.md`). Each one must be finished before the next starts.

| Milestone | Goal | Done when |
|---|---|---|
| M1. Engine and gates | infrastructure P1-P7; engine components E1-E9; consistency gate T0; known limits T9 | T0 and T9 pass in CI on `main`, reviewed and confirmed |
| M2. What can the coupling be? | pairs T1; survival table T2 (120 definitions) | every definition classified A, B or C, each class confirmed |
| M3. Angle and many bodies | T3, T4 | every finding confirmed and converged |
| M4. Motion, populations, robustness | T5-T8 | the same |
| M5. Interactive universe and report | UI1-UI4; written report of all findings | report reviewed; universe reproduces every confirmed finding |

**What success looks like:** a confirmed table that says, for each reading of the second coordinate, what kind of universe it gives, and whether measurement allows it. Negative results count as success.

---

## 2. Organisation

### 2.1 Roles

| Role | Responsibility | Authority |
|---|---|---|
| **Maintainer** (Mostafa Derraz) | direction, theory, final decisions | approves decisions, merges to `main`, appoints leads |
| **Engine lead** | coherence of the engine code (E1-E4), its interfaces and its tests | approves every change under `engine/` |
| **Physics lead** | correctness of every derivation and law plug-in L0-L8; links to measurement | approves every new formula and every law plug-in |
| **Verification lead** | CI, verification scripts, the results standard, reproduction of findings | approves changes to `verification/`, CI and `team/RESULTS-STANDARD.md` |
| **Scenario owner** | one scenario from claim to delivery | decides how to run it, within the standard |
| **Reviewer** | independent reproduction of a result | marks results `confirmed` or `disputed` |
| **AI agent** | owner or reviewer under `AGENTS.md` | the same as a human in that role, always with a human sponsor |
| **Human sponsor** | supervises up to two agents | responsible for everything their agents submit |
| **Scribe** (rotates weekly) | weekly summary in `team/LOG.md` | none |

- Until leads are appointed, the maintainer holds the lead roles.
- Leads are listed in `CONTRIBUTORS.md`.
- **Separation of duties:** nobody reviews their own result or their own agent's result. A result is confirmed only by someone other than its producer and its producer's sponsor.

### 2.2 Making decisions

Any choice that affects other people's work is a decision: a convention, a unit, an interface, a law definition, a change of scope.

1. **Propose:** add a row to `team/DECISIONS.md` with status `proposed`, and open an issue labelled `decision` with the reasons and alternatives.
2. **Comment:** at least **3 days** for minor decisions and **7 days** for anything that changes the engine interface, a law or the scope.
3. **Decide:**
   - the responsible lead decides minor decisions;
   - the maintainer decides the rest;
   - the decision and its reason are recorded, with status `approved` or `rejected`.
4. **Never delete** a decision; supersede it with a new one that cites it.

While a decision is pending, work continues under a clearly labelled **assumption** in the notebook.

### 2.3 Limits on work in progress

- One person has at most **two active claims**; one agent has at most **one**.
- One sponsor supervises at most **two agents** at a time.
- A claim with no log entry for **14 days** is released automatically (the board is updated, and the notebook keeps the work).

Fewer things in progress means more things finished.

---

## 3. The shared memory

Agents do not remember earlier sessions, and people come and go. Everything lives in the repository.

| Place | Content | Rule |
|---|---|---|
| `team/LOG.md` | the journal: one entry per work session, newest first | every session, even if nothing worked |
| `team/DECISIONS.md` | numbered, binding decisions | proposed by anyone, decided by the lead or the maintainer |
| `team/FINDINGS.md` | the index of results with their status | updated at every delivery and every review |
| `team/QUESTIONS.md` | questions waiting for the maintainer or a lead | added by anyone; answered by the maintainer; questions a run can settle become scenarios instead |
| `team/notes/<ID>.md` | the notebook of one scenario or component | updated every session; contains the pre-registration and the handoff |
| `team/RESULTS-STANDARD.md` | how results are produced, stored and stamped | binding for every result |
| `docs/OPEN-SCENARIOS.md` | the status board | updated at every claim, delivery, review and release |
| `results/<ID>/<run-id>/` | stamped outputs of runs | written by scripts, never by hand |
| issues and pull requests | claims, results, questions, code | use the templates |

**Single source of truth:** if two places disagree, the board (`docs/OPEN-SCENARIOS.md`) is right about status, `team/DECISIONS.md` about conventions, and `team/FINDINGS.md` about results.

---

## 4. Reading order before your first contribution

1. `README.md`
2. `TEAM.md` (this file)
3. `CONTRIBUTING.md`, and `AGENTS.md` if you are an agent
4. `team/RESULTS-STANDARD.md`
5. `team/DECISIONS.md` (all of it: decisions are binding)
6. `team/LOG.md` (the last ten entries)
7. `team/FINDINGS.md`
8. `docs/03-report-verified-formulas.md` and `docs/formulas-compendium/`
9. `docs/05-scenarios-and-tests.md`
10. the notebook `team/notes/<ID>.md` of the scenario you want, if it exists

Then set up the pinned environment (`requirements.txt`) and run every verification script. If anything fails, stop and open an issue labelled `urgent`.

**Good first scenarios:** E1 (algebra core), T0.3 (angle invariance), T0.5 (field split). Newcomers are paired with a buddy, an experienced contributor named in the claim issue, for their first delivery.

---

## 5. The work cycle

### Step 1: Choose (Definition of Ready)

A scenario may be started only when:

- its dependencies are `confirmed` (or `done`, if the maintainer allows it);
- its setup and pass criteria exist in `docs/05-scenarios-and-tests.md`;
- you are within your limit of claims.

### Step 2: Claim

- Open a "Claim a scenario" issue.
- Mark the board `claimed (@handle)`.
- For an agent, name the sponsor.

### Step 3: Pre-register, before running anything

In the notebook, write down:

- the **question**;
- the **law or laws**;
- the **settings**;
- your **prediction**: what you expect and why (an analytic estimate if one is possible);
- the **analysis plan**: which quantities you will measure and how you will judge pass, fail or finding.

Commit the notebook **before** the first production run.

Pre-registration separates what you expected from what you found, and stops parameter fishing. You may change the plan later, but the change must be recorded with a reason. Exploratory runs are allowed, labelled "exploratory".

### Step 4: Work

- Use a branch named `<ID>-<short-name>`.
- Run scripts follow `team/RESULTS-STANDARD.md`: fixed seeds, settings stamp, outputs under `results/<ID>/`.
- After every session: update the notebook and add a log entry (step 6).
- Any choice that affects others goes through section 2.2.

### Step 5: Self-check

Before delivering:

- **T0** passes on your engine commit (CI shows it);
- **convergence** is shown: the time step halved twice, and a smaller and a larger particle count; the result changes by less than 1%;
- **conservation** is reported: drift of mass, charge, energy and momentum;
- **every statement** is labelled mathematics, measurement (with source) or finding of the virtual universe (law Lx);
- the result is compared with your **prediction**, and any surprise is explained or flagged;
- if you changed code, **`ARCHITECTURE.md` is updated** (registry, Mermaid diagrams, contracts, change log) and `python tools/check_architecture.py --base origin/main` passes (D18).

### Step 6: Log every session

Add an entry at the top of `team/LOG.md`:

```
### YYYY-MM-DD - @handle (or agent / model, sponsor @handle) - <ID>
- Did:
- Result:
- Next:
- Blocked by / questions:
- Architecture: updated (sections ...) / no code changed
```

### Step 7: Deliver

- Open a pull request using the template, with the script, the stamped results, the notebook and the convergence check.
- Open a "Scenario result" issue linked to it.
- Add the result to `team/FINDINGS.md` with status `done`, and mark the board `done`.

### Step 8: Review (two kinds)

1. **Code review:** the engine lead (for `engine/`) or any experienced contributor (for scenarios) reviews the code for correctness and readability.
2. **Scientific review:** an independent reviewer **re-runs the result from a clean checkout** and checks it against the pre-registration and the standard. Then:
   - **reproduced:** the reviewer marks it `confirmed` in `team/FINDINGS.md` and on the board, and signs it;
   - **not reproduced:** it is marked `disputed`, and the producer and reviewer resolve it in the issue. A third reproduction decides.

The confirmation of a finding by an AI agent's review requires **either a human reviewer or an agent of a different model**. Agreement between copies of the same model is not independent.

### Step 9: Hand off or close

- **If you stop before finishing:** fill in the notebook's **Handoff** section (state, what works, what does not, the exact next step), add a log entry, and release the claim.
- **A result is closed** when it is confirmed and merged.

---

## 6. The lifecycle of a finding

```
exploratory  ->  done  ->  confirmed  ->  published
                   \-> disputed -> (re-run) -> confirmed | withdrawn
```

- **exploratory:** not pre-registered; may be shared, never cited as a result.
- **done:** delivered according to the standard.
- **confirmed:** reproduced independently.
- **published:** included in the project report or a paper, with credit.
- **withdrawn:** found wrong. It stays in `team/FINDINGS.md` with the reason, and is never deleted.

Only `confirmed` findings may be quoted outside the project.

---

## 7. Quality rules for code

- The engine lives in `engine/`, scenarios in `scenarios/<ID>/`, and results in `results/<ID>/` (see the standard).
- Every engine function has a unit test. Every law plug-in L0-L8 has a test that reduces it to L0 when its Composer part is switched off.
- CI runs the verification scripts, the unit tests and T0 on every pull request. **`main` is always green.**
- No merge to `main` without:
  - a pull request;
  - green CI;
  - at least one approving review from someone other than the author.
- Keep pull requests small: one component or one scenario. Over about 400 changed lines, split it, unless it is generated output.

---

## 8. Communication and rhythm

- **Asynchronous by default:** issues for questions, pull requests for work, the log for the journal.
- **Weekly (Sunday):** the scribe's summary at the top of the log: done, confirmed, blocked, help needed, and the decisions waiting.
- **At each milestone:** a milestone review issue. What was found, what was confirmed, what changes for the next milestone.
- **Disagreements about results** are settled by reproduction. **Disagreements about direction** are settled through section 2.2.
- **Urgent** (CI red on `main`, a verified formula seems wrong, a rule is broken): an issue labelled `urgent`. The responsible lead answers within 3 days.

---

## 9. Credit and authorship

- **Contributor roles** follow CRediT: conceptualisation, software, validation, investigation, writing, supervision. They are recorded in `CONTRIBUTORS.md` for each merged contribution.
- **Authors** of a publication of findings are the humans who made a substantial contribution to the confirmed results and approve the text. The maintainer is an author of every project publication.
- **AI agents are credited** in the acknowledgements and the declaration of AI use, with their model and sponsor, as journal policies require (for example EMS Press: only humans can be authors). They are never listed as authors.
- **A reviewer who confirms a finding** is credited for validation.

---

## 10. Integrity

- No fabricated data, numbers, citations or measurements.
- No silent edits to verified formulas, verification scripts, pass criteria or other people's results.
- No tuning after seeing the results without saying so.
- Mistakes are expected. Report them, mark the finding `withdrawn` or `disputed`, and move on. Hiding a mistake is the only unforgivable one.
- Breaking these rules leads to the removal of the contribution, and if repeated, of the contributor or the agent's sponsor.

---

## 11. Checklists

**Before starting:**

- [ ] reading list done; environment pinned; verification passes;
- [ ] scenario Ready (section 5, step 1) and within the claim limit;
- [ ] claimed on the board and in an issue;
- [ ] notebook opened, and the **pre-registration committed**.

**Before stopping a session:**

- [ ] notebook updated;
- [ ] log entry written;
- [ ] branch pushed.

**Before delivering:**

- [ ] T0 passes on the engine commit;
- [ ] convergence and conservation reported;
- [ ] results stamped under `results/<ID>/`;
- [ ] every statement labelled;
- [ ] result compared with the prediction;
- [ ] pull request (template) and result issue opened;
- [ ] findings index and board updated.

**Before confirming as a reviewer:**

- [ ] clean checkout, same stamp, re-run;
- [ ] the numbers match within the stated tolerance;
- [ ] the pre-registration was respected, or the deviations are justified;
- [ ] you are independent of the producer.
