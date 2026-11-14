"""T9.4: A proton and an antiproton near a neutral Earth under L1a: opposite pushes from s q g.

Setup and pass criterion: docs/05-scenarios-and-tests.md, section 2, T9. Pre-registration:
team/notes/T9.md. L1a is a hypothesis (decision D1); this is a measurement check (decision D4).

    python scenarios/T9.4/run.py        # writes results/T9.4/<run-id>/
"""

import sys

from cosmicmass.gates.t0 import write_gate_result
from cosmicmass.gates.t9 import t9_4

PRODUCER = "Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz)"

if __name__ == "__main__":
    outcome = t9_4()
    folder = write_gate_result(outcome, producer=sys.argv[1] if len(sys.argv) > 1 else PRODUCER,
                               kind="measurement-check", law="the hypothesis L1a")
    for name, case in outcome["cases"].items():
        print(f"{'pass' if case['pass'] else 'FAIL'}  T9.4 {name}")
    print(f"T9.4: {'pass' if outcome['pass'] else 'FAIL'}; results in {folder}")
    sys.exit(0 if outcome["pass"] else 1)
