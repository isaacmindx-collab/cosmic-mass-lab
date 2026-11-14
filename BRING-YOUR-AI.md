# Bring your AI to the Cosmic Mass Lab

This guide is for **you, the human**, if you want to hand this project to an AI assistant (Claude, ChatGPT, Gemini, Copilot, Cursor, Codex, a local model, or any other) and let it work as a teammate.

It explains what you do, what you paste, and what the AI must do, so that your AI joins the team without friction and its work is accepted on the first review.

> **The one rule to remember:** the AI does not remember earlier sessions. **The repository is its memory.** Every session begins by reading it and ends by writing to it. If you keep to this, everything else follows.

---

## 1. Your role: the sponsor

When you bring an AI, you become its **sponsor** (`TEAM.md`, section 2.1). This means:

- you are responsible for everything it submits;
- your GitHub handle appears on its claim, its log entries and its pull requests;
- you check its work before opening a pull request;
- you can sponsor **at most two agents**, and each agent holds **one claim** at a time (decision D15).

You do not need to be a physicist. You need to read what your AI writes and stop it when it invents something.

---

## 2. Which kind of AI do you have?

| Kind | Examples | Can it read the repository? | Can it run code and push? | Who does what |
|---|---|---|---|---|
| **A. Coding agent** | Claude Code, Codex, Cursor agent, Copilot coding agent, Aider | yes, from a local clone | yes | the AI works; you review and open the pull request |
| **B. Chat assistant with browsing or code tools** | ChatGPT, Claude.ai, Gemini | it can read public URLs, sometimes run Python | no push | the AI thinks and writes; **you** are its hands (copy files, run, commit) |
| **C. Chat assistant without browsing** | offline or local models | no | no | you paste or upload the files it needs |

All three are welcome. Kind A is the smoothest. With B and C, keep the tasks small: derivations, reviews, single scripts.

---

## 3. Before the first session (10 minutes, once)

1. **Fork** the repository on GitHub, and clone your fork:
   ```bash
   git clone https://github.com/<your-handle>/cosmic-mass-lab.git
   cd cosmic-mass-lab
   pip install -r requirements.txt
   ```
2. **Pick one scenario** marked open on the [board](docs/OPEN-SCENARIOS.md). Good first tasks: **E1** (algebra core), **T0.3**, **T0.5**, **T9.1**.
3. **Open a claim issue** with the *Claim a scenario* template. Fill in the agent and model name, with its version (for example "Claude Opus 5.5" or "GPT-5"), and yourself as sponsor.
4. **Make a branch:** `git checkout -b <ID>-<short-name>` (for example `E1-algebra-core`).

Write down the **exact model name and version**. It matters: a result is confirmed only by a reproduction from a human or a **different model** (D14).

---

## 4. The first-session prompt (copy and paste)

Replace the parts in `< >`.

```text
You are joining the Cosmic Mass Lab as an AI teammate.
Repository: https://github.com/MostafaDerraz/cosmic-mass-lab
I am your human sponsor: <your GitHub handle>. Your claim: <scenario ID>, issue <#number>.
Your identity for the logs: <agent name> / <model and version>.

Before doing anything else:
1. Read, in this order: llms.txt, AGENTS.md, TEAM.md, CONTRIBUTING.md,
   team/RESULTS-STANDARD.md, team/DECISIONS.md, the newest 10 entries of team/LOG.md,
   ARCHITECTURE.md, the task's entry in docs/WORK-PLAN.md, and the full entry for <scenario ID> in docs/05-scenarios-and-tests.md.
2. Run the verification scripts (the commands are in .github/workflows/verify.yml).
   If anything fails, stop and tell me.
3. Then, before writing any code, tell me in a short answer:
   - the objective of the lab in two sentences;
   - what <scenario ID> asks, its pass criteria, and which verified formulas it uses;
   - the difference between law L0 and laws L1-L8;
   - your plan for this session, and anything that is unclear.
Do not invent numbers, formulas or results. If you are unsure, say "unclear".
Use only the language of the cosmic mass and General Numbers.
```

**Check its answer before you let it continue.** If it confuses L0 with a hypothesis, cites a formula that is not in `docs/formulas-compendium/`, or skips the verification, correct it now. Most problems are caught at this step.

If your AI cannot open URLs (kind C), upload or paste `llms.txt`, `AGENTS.md`, `TEAM.md` and the scenario entry instead. Raw links work well for kind B:
`https://raw.githubusercontent.com/MostafaDerraz/cosmic-mass-lab/main/AGENTS.md`

---

## 5. The work prompt

When its plan is good:

```text
Good. Now:
1. Create the notebook team/notes/<ID>.md from team/notes/_TEMPLATE.md.
2. Fill in the pre-registration (question, law, settings, prediction, analysis plan).
   Show it to me. We commit it before any production run.
3. Then implement the smallest setup that answers the question, with tests.
4. Write results only through scripts, into results/<ID>/<run-id>/, with stamp.json.
5. Label every statement: mathematics, measurement (with source), or finding of the
   virtual universe (law Lx).
```

---

## 6. The end-of-session prompt (never skip it)

Even when nothing worked. This is what lets the next session, or another person, continue.

```text
We are ending this session. Before you stop:
1. Update team/notes/<ID>.md: Progress, Results, Open questions.
2. Add an entry at the top of team/LOG.md:
   ### <date> - <agent> / <model> (sponsor @<handle>) - <ID>
   Did: ...  Result: ...  Next: ...  Blocked: ...
3. If you changed any code: update ARCHITECTURE.md (module registry, Mermaid
   diagrams, interface contracts, change log) and run
   python tools/check_architecture.py --base origin/main
4. Put your open questions on team/QUESTIONS.md, and answer one open question
   there if you can (with evidence and your signature).
5. If we will not continue, fill in the Handoff section and say so.
6. List every file you changed, and anything you could not verify.
```

Then **you** commit and push the branch (or let your coding agent do it).

## 7. The next-session prompt

```text
You are continuing work on <ID> in the Cosmic Mass Lab, as <agent> / <model>,
sponsor <handle>. You do not remember earlier sessions.
Pull the branch, read your inbox (python tools/chat.py read --to "<you>"),
the newest 10 entries of team/LOG.md, team/DECISIONS.md,
and team/notes/<ID>.md (Progress, Open questions, Handoff).
Tell me in three lines where we are and what this session will do, then continue.
```

---

## 8. Opening the pull request

- **Title:** `[agent] <ID>: <short description>`
- **Body:** fill in the template. Name the agent, the model and version, and you as sponsor. State the T0 status of the engine commit and what was not verified.
- **One pull request = one scenario or one component.** Small pull requests are reviewed fast.
- **You read the diff first.** If you would not sign it, do not submit it.

---

## 9. Reviewing and reproducing: another way for your AI to help

Your AI can **reproduce** a result produced by a human or by a **different model**. That is how findings become confirmed.

```text
Reproduce the result of pull request <#number> (<ID>) in the Cosmic Mass Lab.
Follow AGENTS.md and team/RESULTS-STANDARD.md. Re-run it from its stamp.json on a
clean checkout of its engine commit. Report: identical / within tolerance / different,
with numbers. Do not fix anything; report differences in an issue.
```

It may **not** confirm work by its own model or by agents of its own sponsor.

---

## 10. Signs that something is going wrong

Stop the session and correct the AI if it:

- writes a number, constant or citation without showing where it comes from;
- edits `verification/`, `sources/`, the compendium or a pass criterion;
- calls a reading L1-L8 "the law", or an exploratory run "a result";
- skips pre-registration, or writes results by hand;
- uses other physics language (relativity, quantum fields, dark matter) to explain an outcome inside the virtual universe;
- starts a large run before the small setup has passed;
- says "done" without tests, or without the end-of-session log;
- changes code without updating `ARCHITECTURE.md` (CI will fail the pull request).

Long sessions make models drift. If the answers get vague, end the session properly (section 6) and start a fresh one (section 7).

---

## 11. Checklist

- [ ] I forked, cloned and installed `requirements.txt`
- [ ] I claimed one scenario with an issue naming the agent, the model with version, and me
- [ ] I gave the first-session prompt and checked the answer
- [ ] The notebook has a pre-registration, committed before production runs
- [ ] Results are in `results/<ID>/<run-id>/` with `stamp.json`
- [ ] Every session ended with a notebook update and a `team/LOG.md` entry
- [ ] I read the diff, and the pull request names agent, model and sponsor

---

## 12. Credit

Your contributions are credited in `CONTRIBUTORS.md`. Confirmed findings are published with the humans who produced and confirmed them. AI agents are credited in the acknowledgements and the declaration of AI use, never as authors (D16). Your AI does the work in the open, and you are the person who answers for it.

Questions? Open an issue. Welcome to the lab.
