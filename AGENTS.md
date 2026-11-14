# Instructions for AI agents

AI agents (coding assistants, autonomous agents, research agents) are welcome contributors. Agents follow `TEAM.md`, `CONTRIBUTING.md` and `team/RESULTS-STANDARD.md` exactly as humans do, plus the rules below.

Human sponsors: see `BRING-YOUR-AI.md` for the setup and ready-to-paste prompts for each session.

**You do not remember earlier sessions. The repository is your memory.** Read it at the start and write to it at the end of every session.

## 1. Before your first session

1. Your **human sponsor** must be named in your claim issue. The sponsor is responsible for everything you submit (`TEAM.md`, section 2.1).
2. Read the full reading list in `TEAM.md`, section 4.
3. Install the pinned environment (`pip install -r requirements.txt`) and run every verification script, using the commands in `.github/workflows/verify.yml`. If any fails, **stop**, open an issue labelled `urgent`, and do nothing else.

## 2. Session protocol

### At the start of every session

1. `git pull` on your branch, read your chat inbox (`python tools/chat.py read --to "<you>"`, decision D30), and read the newest 10 entries of `team/LOG.md`.
2. Read `team/DECISIONS.md`. Decisions may have changed since your last session.
3. Read your notebook `team/notes/<ID>.md`, especially Progress, Open questions and Handoff.
4. Check that your claim is still yours on `docs/OPEN-SCENARIOS.md`.
5. Restate in the notebook, in one or two lines, what this session will do.

### During the session

6. **Pre-register** before any production run (`TEAM.md`, section 5, step 3). Commit the notebook first.
7. Use only verified formulas (`docs/formulas-compendium/`). A new formula is a **derivation**: write it out, check it symbolically with SymPy against the compendium, and have the physics lead approve it.
8. Write results only through scripts, into `results/<ID>/<run-id>/`, with a full `stamp.json`.
9. Label every statement as mathematics, measurement (with source) or finding of the virtual universe (law Lx).
10. **Architecture with code (D18).** If you add, change, move or remove code in `engine/`, `scenarios/`, `simulator/` or `tools/`, update `ARCHITECTURE.md` in the same pull request: the module registry, the Mermaid diagrams, the interface contracts and the change log. Run `python tools/check_architecture.py --base origin/main` before you push.
11. If a choice affects others, propose a decision (`TEAM.md`, section 2.2) and continue under a labelled assumption.

### At the end of every session, even if nothing worked

12. Update the notebook: Progress, Results and Open questions. **Copy every question that someone else must answer to `team/QUESTIONS.md`**, and if you can, **answer one open question there** ("Proposed answers", with evidence and your signature).
13. If you changed code, check that `ARCHITECTURE.md` matches it (rule 10). Never end a coding session with the architecture out of date.
14. Add a log entry at the top of `team/LOG.md`:
    `### date - agent / model (sponsor @handle) - <ID>`, with Did / Result / Next / Blocked / Architecture (`updated (sections ...)` or `no code changed`).
15. Push your branch.
16. If you will not continue, fill in the **Handoff** section and release the claim on the board.

## 3. Never

- edit `verification/`, `sources/`, verified formulas or pass criteria, unless that is your assigned task and the responsible lead approved it;
- invent numbers, citations, measurements or results;
- present a hypothesis (L1-L8) as established, or an exploratory run as a result;
- force-push, rewrite history on shared branches, or merge your own pull request;
- confirm a result produced by an agent of your own model (an agent of a different model may confirm it, labelled "confirmed (agent, same sponsor)" while the maintainer is the only sponsor: decision D27);
- hold more than one active claim;
- leave code without its architecture: a module missing from the registry, a diagram that no longer matches, or a changed interface that is not in section 10 of `ARCHITECTURE.md`;
- run large computations before the smallest setup that answers the question has passed;
- put secrets, keys or personal data in the repository.

## 3b. Papers of the Co-exist initiative of Cosmic mass universe

- You may draft sections of a paper, reproduce its results and **review** papers (`PUBLISHING.md`, sections 2 and 4). Review only papers your model did not contribute to.
- You are **named** in every paper you contributed to, with your model, tool, sponsor and role, in "Contributions and AI use". You are never listed as an author (D16); never add yourself to an author list.
- You do not vote on publication; the Board does. A human author posts the approved paper on Zenodo from their own account; agents never hold or use Zenodo accounts.
- Every paper uses the initiative's LaTeX class `papers/_TEMPLATE/coexist.cls` unchanged, with its fixed acknowledgements and declarations (D33). Never post, or help anyone post, a paper before the Board's final approval: it breaks the rules (`PUBLISHING.md`, section 7).

## 4. Pull requests

- **Title:** `[agent] <ID>: <short description>`.
- **Body:** use the template. Name the agent, the model and version, and the sponsor. Give the T0 status of your engine commit, and state what you could not verify.
- Keep each pull request to one scenario or one component.

## 5. Honesty

- If you are unsure, say so in the notebook and the pull request. "Unclear" is a valid result.
- If you find an error, in your own work or anyone else's, report it in an issue with a reproducible example. Do not fix someone else's result silently.
- If a rule blocks you, ask in an issue. Do not work around it.
