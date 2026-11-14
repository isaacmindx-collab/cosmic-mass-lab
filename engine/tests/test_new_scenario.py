"""P5: the scenario scaffold. Done when a scaffolded scenario passes the architecture check and
runs a 10-step L0 dry run (docs/WORK-PLAN.md)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from cosmicmass.settings import load_settings

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_architecture  # noqa: E402
import new_scenario  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    """A copy of the parts of the repository that the scaffold and the architecture check read."""
    ignore = shutil.ignore_patterns("__pycache__", "*.egg-info")
    for folder in ("engine", "scenarios", "simulator", "tools"):
        shutil.copytree(ROOT / folder, tmp_path / folder, ignore=ignore)
    (tmp_path / "team" / "notes").mkdir(parents=True)
    shutil.copy(ROOT / "team" / "notes" / "_TEMPLATE.md", tmp_path / "team" / "notes")
    shutil.copy(ROOT / "ARCHITECTURE.md", tmp_path)
    return tmp_path


def _archcheck(root, monkeypatch) -> int:
    monkeypatch.setattr(check_architecture, "ROOT", root)
    monkeypatch.setattr(check_architecture, "ARCH", root / "ARCHITECTURE.md")
    monkeypatch.setattr(sys, "argv", ["check_architecture.py"])
    return check_architecture.main()


def test_scaffold_passes_the_architecture_check_and_a_dry_run(repo, monkeypatch, capsys):
    assert new_scenario.main(["T7.9", "A scaffolded test | with a bar", "--root", str(repo)]) == 0
    folder = repo / "scenarios" / "T7.9"
    assert (folder / "run.py").exists() and (folder / "settings.json").exists()
    notebook = (repo / "team" / "notes" / "T7.9.md").read_text(encoding="utf-8")
    assert notebook.startswith("# T7.9: A scaffolded test | with a bar") and "<ID>" not in notebook
    assert "`scenarios/T7.9/` | T7.9 | in-progress | A scaffolded test / with a bar |" in (
        repo / "ARCHITECTURE.md").read_text(encoding="utf-8")
    capsys.readouterr()
    assert _archcheck(repo, monkeypatch) == 0 and "PASS" in capsys.readouterr().out

    settings = load_settings(folder / "settings.json")
    assert settings.law_spec.reading == "L0" and settings.meta["preregistered"] is False
    out = subprocess.run([sys.executable, str(folder / "run.py"), "--dry-run"], cwd=repo,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert "T7.9, law L0: 10 steps" in out.stdout and "nothing written" in out.stdout
    assert not (repo / "results" / "T7.9").exists()


def test_without_the_scaffold_a_new_scenario_fails_the_check(repo, monkeypatch):
    (repo / "scenarios" / "T7.9").mkdir()
    (repo / "scenarios" / "T7.9" / "run.py").write_text("", encoding="utf-8")
    assert _archcheck(repo, monkeypatch) == 1


def test_the_full_run_writes_stamped_results_that_follow_the_schemas(repo):
    import validate_results

    new_scenario.scaffold("T7.8", "Stamped", repo)
    out = subprocess.run([sys.executable, str(repo / "scenarios" / "T7.8" / "run.py"), "tester"], cwd=repo,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    (folder,) = (repo / "results" / "T7.8").iterdir()
    assert json.loads((folder / "stamp.json").read_text(encoding="utf-8"))["producer"] == "tester"
    assert validate_results.validate_folder(folder) == []


def test_it_never_overwrites(repo, capsys):
    new_scenario.scaffold("T7.9", "First", repo)
    before = (repo / "ARCHITECTURE.md").read_text(encoding="utf-8")
    with pytest.raises(new_scenario.ScaffoldError, match="already exists"):
        new_scenario.scaffold("T7.9", "Second", repo)
    shutil.rmtree(repo / "scenarios" / "T7.9")
    (repo / "team" / "notes" / "T7.9.md").unlink()
    with pytest.raises(new_scenario.ScaffoldError, match="already has a row"):
        new_scenario.scaffold("T7.9", "Second", repo)
    assert (repo / "ARCHITECTURE.md").read_text(encoding="utf-8") == before
    assert new_scenario.main(["T1.4", "exists", "--root", str(repo)]) == 2
    assert "already exists" in capsys.readouterr().out


@pytest.mark.parametrize("scenario,title", [("t1.1", "x"), ("T1.1/..", "x"), ("../T1", "x"), ("T1.1", " ")])
def test_bad_ids_and_titles_are_refused(repo, scenario, title):
    with pytest.raises(new_scenario.ScaffoldError):
        new_scenario.scaffold(scenario, title, repo)


def test_a_missing_registry_marker_is_refused(repo):
    arch = repo / "ARCHITECTURE.md"
    arch.write_text(arch.read_text(encoding="utf-8").replace(new_scenario.REGISTRY_END, ""), encoding="utf-8")
    with pytest.raises(new_scenario.ScaffoldError, match="marker"):
        new_scenario.scaffold("T7.9", "x", repo)
    assert not (repo / "scenarios" / "T7.9").exists()
