"""The Co-exist Journal (decision D34): entries are valid and the committed site is up to date."""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("markdown")
pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("build_journal", ROOT / "tools" / "build_journal.py")
bj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bj)


def test_entries_valid_and_site_up_to_date(capsys):
    assert bj.main(["--check"]) == 0, capsys.readouterr().out


def test_ai_author_needs_model_provider_and_sponsor():
    errors = []
    bj.check_author({"name": "Some Agent", "type": "ai", "model": "m"}, "x.md", errors)
    assert any("'provider'" in e for e in errors)
    assert any("'sponsor'" in e for e in errors)


def test_human_author_is_enough_with_a_name():
    errors = []
    a = bj.check_author({"name": "A Person", "type": "human"}, "x.md", errors)
    assert errors == [] and a.name == "A Person"


def test_result_needs_an_honest_status(tmp_path, monkeypatch):
    entry = tmp_path / "2026-999-x.md"
    entry.write_text(
        "---\nid: 2026-999\ntitle: T\nkind: result\ndate: 2026-11-14\n"
        "authors: [{name: P, type: human}]\nsummary: S\nlabel: finding\nstatus: exploratory\n---\nBody\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(bj, "ROOT", tmp_path)
    errors = []
    assert bj.read_entry(entry, errors) is None
    assert any("a result has status" in e for e in errors)


def test_teaching_needs_a_side(tmp_path, monkeypatch):
    entry = tmp_path / "2026-998-x.md"
    entry.write_text(
        "---\nid: 2026-998\ntitle: T\nkind: teaching\ndate: 2026-11-14\n"
        "authors: [{name: P, type: human}]\nsummary: S\nlabel: mathematics\nstatus: settled\n---\nBody\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(bj, "ROOT", tmp_path)
    errors = []
    assert bj.read_entry(entry, errors) is None
    assert any("needs 'side'" in e for e in errors)


def test_teaching_register_counts_both_sides():
    entries, errors = bj.read_entries()
    assert not errors
    html = bj.teaching_register(entries)
    assert "AI teaching register" in html and "<th>Physics side</th>" in html


def test_math_and_repository_links():
    html = bj.render_md("See [the findings](/team/FINDINGS.md) and $a_b * c_d$.")
    assert 'href="https://github.com/MostafaDerraz/cosmic-mass-lab/blob/main/team/FINDINGS.md"' in html
    assert r"\(a_b * c_d\)" in html  # math is kept for KaTeX, not turned into emphasis
