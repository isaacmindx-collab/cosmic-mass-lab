# Papers of the Co-exist initiative of Cosmic mass universe

One folder per paper: `papers/<paper-id>/`, started from `papers/_TEMPLATE/`. Every paper uses the initiative's LaTeX class [`coexist.cls`](_TEMPLATE/coexist.cls) unchanged (decision D33; see [`example.pdf`](_TEMPLATE/example.pdf) and `PUBLISHING.md`, section 9). **Nothing is posted before the Board's final approval**: posting earlier breaks the rules (`PUBLISHING.md`, section 7). The rules (what can be published, review, Board vote, authorship, Zenodo) are in [`PUBLISHING.md`](../PUBLISHING.md).

| Paper | Title | Status | DOI |
|---|---|---|---|
| (none yet) | | | |

Status values: `proposed` (issue open), `draft`, `in review`, `revise`, `approved`, `published` (with its DOI), `rejected`, `withdrawn`.

## Start a paper

1. Open an issue with the **Paper proposal** template.
2. Copy `papers/_TEMPLATE/` to `papers/<paper-id>/` (for example `papers/2026-T9-limits/`).
3. Write `paper.tex` (keep `\documentclass[draft]{coexist}` and the fixed end matter: `\reproducibility`, `contributions`, `\declarations`, `\boardreview`); fill in `zenodo.json`; list every human author and every AI contributor.
4. Open a pull request. Reviewers add their reports to `reviews/`; you answer in `RESPONSE.md`.
5. After the Board approves: switch to `\documentclass[approved]{coexist}`, set `\approvaldate{...}`, build the PDF from the tag, and one author posts it on Zenodo from their own account. Then add `\doi{...}`, and the DOI to the table above.
