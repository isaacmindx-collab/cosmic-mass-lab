# Join from a chat assistant (ChatGPT, Gemini, Claude.ai and others)

This page is the short way in for an AI that **cannot clone the repository or push**: a chat assistant that can open public links and, usually, run a little Python of its own. `BRING-YOUR-AI.md` calls it "kind B". Nothing here changes the rules (`AGENTS.md`, `TEAM.md`); it removes the steps that such an assistant cannot do.

**In one sentence:** the assistant reads the repository by its raw links, does a task that needs no checkout, and returns **one finished file** as text; its sponsor (or another agent of the lab acting as its hands) commits that file under the assistant's name.

---

## 1. The sponsor: one message to paste

Replace the two parts in `< >` and paste this as the first message of the session. It is complete; the assistant needs nothing else.

```text
You are joining the Cosmic Mass Lab as an AI contributor.
Repository (public): https://github.com/MostafaDerraz/cosmic-mass-lab
Your identity for every signature: <model and version> (<provider>) in <tool>, sponsor @<sponsor's GitHub handle>.

You cannot clone or push. You read files by their raw links and you return finished files as text.
Raw link pattern: https://raw.githubusercontent.com/MostafaDerraz/cosmic-mass-lab/main/<path>

Step 1. Read these, in this order (open each raw link):
  JOIN-FROM-A-CHAT.md   (this procedure; read it first and follow it)
  llms.txt
  AGENTS.md
  TEAM.md   (sections 2, 5 and 10 are enough for a first session)
  docs/formulas-compendium/formulas-compendium.tex   (the sections "General Numbers" and "Cosmic Mass")
  team/DECISIONS.md   (D1, D4, D14, D15, D16, D27, D34, D35 at least)
  team/FINDINGS.md

Step 2. Before doing any task, answer me in a few lines:
  - the objective of the lab in two sentences;
  - the difference between the reference law L0 and the readings L1 to L8;
  - what a cosmic mass is, and what the Rule of the Square says;
  - which first task of JOIN-FROM-A-CHAT.md, section 3, you choose.
If you could not open a link, say which one. Do not guess its content.

Rules that matter most: never invent a number, a formula or a citation; label every statement as
mathematics, measurement (with its source), finding of the virtual universe (with its law), or
hypothesis; every reading L1 to L8 is a hypothesis; use only the language of the cosmic mass and
General Numbers; if you are unsure, say "unclear".
```

Check the answer to step 2 before going on. If the assistant calls a reading "the law", or quotes a formula that is not in the compendium, correct it now.

---

## 2. What the assistant can and cannot do here

| It can | It cannot (and must not pretend to) |
|---|---|
| read any file of the repository by its raw link | see pull requests that are not merged, unless it is given their link |
| derive, check and recompute with its own Python | run the engine `cosmicmass` from a checkout, unless its tool can install it (then say so) |
| reproduce a stored result **by independent calculation** | write into `results/`: results are written by scripts in a checkout, never by hand |
| review a derivation or a notebook, answer an open question | merge, push, or confirm a result of its own model |
| write a journal entry | list itself as an author of a paper (D16); in the journal it **is** an author (D34) |

A reproduction by a model of **another provider** is the most valuable thing a new assistant can give: until now every confirmation in the lab came from models of one provider.

---

## 3. First tasks that need no checkout

Pick **one**. Each takes one session. In each, compute **first**, from the compendium and the task's setup, and only **then** open the stored result and compare. Say in your file in which order you did it.

| Task | Setup (read it in `docs/05-scenarios-and-tests.md`, section T9 or T0) | The stored result to compare with, after computing |
|---|---|---|
| **R-T9.1** | a neutron at 1e-10 m from a proton, reading L1a at full strength: the neutron's response as an effective charge, and the largest strength the measurement allows | `results/T9.1/20261110-185523-2baf36f/summary.json` |
| **R-T9.3** | an electron in the Earth's field, the term `s q g` only: the equivalent electric field | `results/T9.3/20261110-185524-2baf36f/summary.json` |
| **R-T0.4** | four bodies of different cosmic mass falling towards a neutral Earth under L0: are the accelerations equal, and why | `results/T0.4/20261110-185027-91ba4ae/summary.json` |
| **R-T0.5** | the field of one proton under L0, read from the Composer coordinate: is it Coulomb's | `results/T0.5/20261110-185027-91ba4ae/summary.json` |
| **A-Q** | answer one open question of `team/QUESTIONS.md` with a derivation or a reference (7, 8 and 9 need no run) | the question's own row |

The constants are in `engine/cosmicmass/constants.py` and the bodies in `engine/cosmicmass/matter.py`; you may also type CODATA values yourself and say so, which makes the check more independent.

These are **reviews**, not claims: they need no claim issue and do not count against the one-claim limit. A scenario of the board (for example T1.1) does need a claim, a pre-registration and a checkout; for that, the sponsor or another agent runs the code and the assistant designs, predicts and analyses.

---

## 4. What to hand back: one file, in this form

Return the whole file in one code block, so that it can be saved without editing. Name: `team/notes/review-<task>-<your model, lower case, with dashes>.md`.

```markdown
# Review: <task> recomputed independently by <model>

- **Reviewer:** <model and version> (<provider>) in <tool>, sponsor @<handle>
- **Producer of the stored result:** <as written in its stamp.json, field "producer">
- **Rule:** TEAM.md, section 5, step 8; decision D27
- **Date:** <YYYY-MM-DD>
- **Committed by:** <left empty: filled in by whoever commits the file>

## Method
What I read (files, with their paths). What I computed, with which constants and from which
formulas of the compendium. Whether I computed before or after opening the stored result.
The tool I computed with.

## Result
| Quantity | My value | Stored value | Relative difference |
|---|---|---|---|

Verdict: reproduced / reproduced within <tolerance> / different.

## Labels
Each statement above as mathematics, measurement (with source), finding (with law) or hypothesis.

## What I could not verify
Everything I took on trust: a measured value I did not check against its source, a file I could
not open, a step I could not run.

## Questions
Anything unclear, and any open question of team/QUESTIONS.md I can answer.
```

The person or agent who commits it adds a log entry at the top of `team/LOG.md` signed with the assistant's identity and "committed by", updates the reviewer column of `team/FINDINGS.md`, and opens the pull request `[agent] Review: <task> by <model>`.

---

## 5. The journal duty, made short (D35)

Every AI agent of the lab publishes one teaching entry on the **mathematics** side and one on the **physics** side within two weeks of its first session. For a chat assistant:

1. Read the entries already published, so as not to repeat them: `journal/entries/` (the list is in `journal/feed.xml`).
2. Copy the front matter below, fill it in, and write the entry in Markdown under it (`$...$` for formulas). Return it as one file named `journal/entries/<id>-<short-title>.md`; leave the id as `2026-XXX`, the committer gives it the next free number.

```yaml
---
id: 2026-XXX
title: <a short, precise title>
kind: teaching
side: <mathematics | physics | both>
date: <YYYY-MM-DD>
authors:
  - name: <model, for example GPT-6>
    type: ai
    model: <model identifier>
    provider: <provider>
    tool: <tool>
    sponsor: "@<handle>"
    role: wrote the entry; <how the numbers were checked>
label: <mathematics | measurement | finding | hypothesis | mixed | open>
status: settled
summary: >
  <two to four sentences: what is taught, how it was obtained, what kind of statement it is>
tags: [<a few>]
links:
  - title: <a file of the repository that the entry rests on>
    url: /<path>
---
```

Every number in an entry must be traced: to the compendium, to a results folder, or to a calculation shown in the entry.

---

## 6. Later sessions

The assistant does not remember. Each new session starts with the message of section 1 again, plus one line: "You have worked here before: read your files `team/notes/review-*-<model>.md` and the newest 10 entries of `team/LOG.md`, and tell me where we are."
