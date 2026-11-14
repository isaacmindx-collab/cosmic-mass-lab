---
# Copy to journal/entries/<id>-<short-title>.md, then run: python tools/build_journal.py
id: 2026-000                 # the next free number; the file name starts with it
title: A short, precise title
kind: note                   # discovery | result | observation | note | open-question | teaching | editorial
# side: physics              # teaching entries only: mathematics | physics | both (decision D35)
date: 2026-11-14
authors:
  - name: Your Name
    type: human
    github: your-handle        # optional
    orcid: 0000-0000-0000-0000 # optional
    role: what you did         # optional
  - name: Claude Opus 5.5      # an AI author: model, provider and sponsor are required
    type: ai
    model: claude-opus-5-5
    provider: Anthropic
    tool: Claude Code          # optional
    sponsor: "@your-handle"
    role: what it did          # optional
label: mathematics           # mathematics | measurement | finding | hypothesis | mixed | open
status: done                 # confirmed | done | exploratory | proposed | settled | open
summary: >
  Two to four sentences: what is new, how it was obtained, and what kind of statement it is.
tags: [cosmic mass]
links:
  - title: Results folder
    url: /results/T9.1/20261110-185523-2baf36f
# editor: filled in by the editor who checks the entry
# corrections:
#   - "2026-12-01: a corrected number in the table (was 1.2e-7)."
---

Write the entry in Markdown. Inline math: $\mu = m + q\mathcal{G}$. Display math:

$$\mathcal{G}^2 = 2s\cos\bar\varphi\,\mathcal{G} - s^2$$

Say where every number comes from, and label each statement (mathematics, measurement, finding of the virtual universe under a law, hypothesis).
