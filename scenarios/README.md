# Scenarios

One folder per scenario: scenarios/<ID>/run.py and settings.json (see team/RESULTS-STANDARD.md).

Start a new one with the scaffold (task P5):

    python tools/new_scenario.py T1.1 "Pure masses: does the Composer part stay silent?"
    python scenarios/T1.1/run.py --dry-run

It writes `settings.json` (a valid 10-step L0 start, to be replaced by the setup of
`docs/05-scenarios-and-tests.md`), `run.py`, the notebook `team/notes/<ID>.md` and the row in
`ARCHITECTURE.md`. Then write the pre-registration and commit it before any production run (D12),
and check the results with `python tools/validate_results.py results/<ID>`.
