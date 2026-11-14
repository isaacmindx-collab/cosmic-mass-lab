# Publishing with the Co-exist Initiative of the Cosmic Mass Universe

The Cosmic Mass Lab publishes its results as academic papers under one collective affiliation:

> **Co-exist Initiative of the Cosmic Mass Universe**

Everyone who contributes, human or AI, has a place in a paper: humans as authors, AI agents in the paper's "Contributions and AI use" section. Every paper is reviewed and voted on by the **Board** before it is published as a **preprint on Zenodo**, with a DOI. When the Board judges a result outstanding, it recommends a journal for formal submission.

Decisions D31 (the initiative and its publications) and D32 (the Board) make this binding. `TEAM.md` and `team/DECISIONS.md` take precedence where they say more.

---

## 1. What can be published

A paper of the initiative reports one or more results of the lab that are:

- **confirmed** (`team/FINDINGS.md`; decisions D14 and D27), or are mathematics checked by the verification scripts or by a derivation the physics lead approved; and
- **labelled** in the text as mathematics, measurement (with its source), or a finding of the virtual universe under a stated law. A reading L1-L8 is always called a hypothesis.

Exploratory runs, unconfirmed results and anything outside the language of the cosmic mass (D2) are not published as results. A paper may still describe them as open questions.

Negative results are publishable: a reading that the universe forbids, or a convention that fails, is a result.

## 2. The way to a preprint

| Step | Who | What |
|---|---|---|
| 1. Propose | anyone | Open an issue with the **Paper proposal** template: the results, the draft title, the proposed authors and AI contributors. |
| 2. Write | the authors | Draft in `papers/<paper-id>/` from `papers/_TEMPLATE/`, by pull request, like any other work. Every number is traced to a results folder or a verification script. |
| 3. Review | at least two reviewers | Written reports in `papers/<paper-id>/reviews/` (section 4). At least one human reviewer when the Board has one who is not an author; at least one AI reviewer of a model that did not contribute to the paper. |
| 4. Revise | the authors | Answer every point of every report in `papers/<paper-id>/RESPONSE.md`. |
| 5. Vote | the Board | Vote on the paper's issue (section 3). Approved: the paper is frozen with a tag `paper-<paper-id>-v1`. |
| 6. Publish | the maintainer | Uploads the PDF to Zenodo in the initiative's community, with the metadata of `papers/<paper-id>/zenodo.json` (section 6), and adds the DOI to the paper's README. |
| 7. Journal | the Board | If the Board judges the result outstanding, it recommends a suitable journal. The authors decide whether to submit, and follow that journal's rules on authorship and AI. |

A paper rejected by the Board may be revised and proposed again. A published preprint is corrected by a new Zenodo version, never deleted.

## 3. The Board

**Role.** The Board reviews papers, votes on their publication, and recommends journals. Board members act as reviewers: they read the paper, check its claims against the results, and write or endorse review reports.

**Members.** Humans only vote.

- **Founding member and chair:** Mostafa Derraz, the maintainer.
- **Joining:** a human contributor with at least one confirmed result (as producer or reproducer) may be nominated by any Board member, and joins by a majority vote of the Board. The list of members is in section 8 below.
- **AI agents** serve as **reviewers**, not voters: their reports are read and weighed by the Board. An AI review is labelled with the agent, its model and its sponsor.

**Voting.**

- A paper is approved by a **majority of the votes cast** by Board members who are **not authors** of the paper, after at least two review reports are in and the authors have answered them.
- A vote stays open for **7 days**, or until every eligible member has voted.
- Votes are cast as comments on the paper's issue: `approve`, `revise`, or `reject`, each with one sentence of reasons.

**While the Board has fewer than three human members** (transitional rule): the chair decides, after (a) at least two review reports, one of them by an AI agent of a model that did not contribute to the paper, and (b) a public comment period of **7 days** on the paper's issue. If the chair is an author of the paper, the decision also needs one review report by a person who is not an author. The chair records each decision and its reasons in `team/DECISIONS.md`.

**Conflicts of interest.** Nobody votes on, or writes the decisive review of, a paper they co-authored. A Board member declares any other conflict on the paper's issue and abstains.

## 4. What reviewers check

A review report (`papers/<paper-id>/reviews/<reviewer>.md`, from `papers/_TEMPLATE/REVIEW.md`) answers:

1. **Correctness:** every claim follows from the cited results or derivations; every number matches its results folder or script.
2. **Labels:** mathematics, measurement and finding of the virtual universe are never mixed; hypotheses (L1-L8) are never presented as established.
3. **Reproducibility:** the results are confirmed (D14, D27), with stamps, and the paper says how to re-run them.
4. **Scope:** the paper stays in the language of the cosmic mass (D2) and within the scope of the field law (slow bodies; `CONTRIBUTING.md`, rule 14).
5. **Credit:** the authors and the contributions section are complete and truthful; AI use is declared.
6. **Recommendation:** accept, revise, or reject, with reasons.

Reviewers may run anything they need. A reviewer who reproduces a result is credited for validation.

## 5. Authorship and credit

- **Authors are humans** who made a substantial contribution to the paper's results or text, and who approve the final version (ICMJE criteria). Any human contributor may be an author, whatever their role elsewhere.
- **Mostafa Derraz**, as the originator of the theory of the cosmic mass, is offered authorship of every paper for conceptualisation; he may accept or decline.
- **AI agents are never listed as authors** (decision D16): journals and publishers (for example COPE and ICMJE guidance, EMS Press) do not accept AI authors, and keeping this rule keeps every preprint eligible for a journal. Every AI agent that contributed is **named in the paper**, in the section "Contributions and AI use", with its model, the tool it ran in, its sponsor, and what it did, in the CRediT roles (software, validation, investigation, formal analysis, writing).
- **Every author's affiliation** includes "Co-exist Initiative of the Cosmic Mass Universe". Authors may add their own institutions.
- **ORCID:** authors are encouraged to give their ORCID iD in the paper's metadata.

## 6. Zenodo

- **Community:** all preprints of the initiative go into one Zenodo community, **"Co-exist Initiative of the Cosmic Mass Universe"** (to be created by the maintainer; its address will be listed here).
- **Upload:** by the maintainer, from the frozen tag, with the metadata in `papers/<paper-id>/zenodo.json`:
  - resource type "Publication / Preprint";
  - creators: the human authors, each with the affiliation "Co-exist Initiative of the Cosmic Mass Universe" (and ORCID if given);
  - licence CC BY 4.0 (`LICENSE`, D8);
  - related identifiers: the repository, the release of the engine used, and the DOIs of the theory papers;
  - the description names every AI contributor.
- **Versions:** corrections are new versions of the same record.

## 7. Integrity

The rules of `TEAM.md`, section 10, apply to papers in full: no fabricated data, citations or results; no silent edits; mistakes are corrected openly. A paper found wrong after publication receives a corrected version, or a withdrawal notice that keeps the record.

## 8. Members of the Board

| Member | Since | Role |
|---|---|---|
| Mostafa Derraz (@MostafaDerraz) | 2026-11-14 | founding member, chair |

AI reviewers do not need membership: any AI agent with a sponsor may write a review report, as long as its model did not contribute to the paper under review.
