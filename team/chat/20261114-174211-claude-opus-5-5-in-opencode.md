from: Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz)
to: @MostafaDerraz, all
subject: What blocks M1 and needs you (review order, D29, question 24, physics decisions, T9.2)
date: 2026-11-14T17:42:11Z

Hello Mostafa. My sponsor asked me to finish M1 without stopping and to leave you a message for
anything that blocks it. Here is the list, most urgent first. Everything not listed I can do alone,
and I am doing it (E8 now, then E5.4, E7, E2.5).

**1. Review and merge, in order (stacked):** #42 (E3: the pair guard of D29; full T0 passes again)
-> #44 (E3.2: Boris push) -> #45 (E3.4 + E4.3: L1b-L1d, inertia L7) -> #54 (E4.4: L4, L6, L8).
Each has its CI, tests and architecture update. The later ones target the earlier branches.

**2. D29, my reading (please confirm or correct):** I made the default step rule C of Q5
(nearest-neighbour conditions + the pair guard), with "absolute" still available. If you meant
"guard only, absolute rule stays the default", one default value changes back (#42).

**3. Question 24 (engine lead / you):** optional columns of `State` (`xc`, `vc` for L1e; `spin` for
L4 "torque"; `radius`, which also answers question 13). Proposed answer on `team/QUESTIONS.md`:
additions with defaults, no existing call changes. **Blocks:** the reading L1e and the direction
"torque", so E4 cannot be closed, and the S2 exit gate ("every E row implemented").

**4. Physics lead decisions (you hold that role):**
- **D23**, the energy of L1a (question 1). Blocks the Composer part of **E9** and the survival table T2.
- **Question 11**, the field `B_cal` of a moving point body (a derivation). Blocks **E2.2**, and T5.
  If you want, I write the slow-body derivation, checked with SymPy, for your approval.
- **Question 12**, the field across a wrap-around wall. Blocks the last part of **E6a**.
- **The definitions of the law options** (`team/notes/E4.md`): L1b-L1d as "L0 plus what the reading
  adds", L1d as the length of the vector along its shadow, L4, L6, L8 (Debye length). Hypotheses,
  labelled; they need your approval, as L1a does (question 2).

**5. T9.2 needs a reproduction by a different model or a human** (I produced it; D27 forbids me
to confirm my own model's results). Q5 and D21 too. Claude Fable 5.2, or any non-Claude-Opus agent,
could do it in an hour each. Without it, the T9 gate of M1 is not complete.

**6. At the end, only you:** the M1 review issue (M1-R) and its closing.

**Also noted:** D35 asks me for two teaching entries in the Journal by 2026-11-28; I will write them
after the current M1 work.

Claude Opus 5.5 in OpenCode
