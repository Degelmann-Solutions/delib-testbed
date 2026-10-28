"""The baseline-deviation listing ``tools/baseline_deviations.py`` (R6, ``docs/core.md``).

- On this repository the tool exits 0 and every deviation it lists is marked.
- In a throwaway git repository (tag ``phase-2-baseline`` on an initial commit holding the
  baselines of two products ``alpha`` and ``beta``), every row of the plan's I/O matrix: a
  marked change passes and is listed with its Reason; an unmarked change exits 1 and names
  product and SHA; a marker naming a product whose baseline is unchanged exits 1; a marker
  without ``Checked-By`` exits 1; an evil merge exits 1; an added baseline counts as a change;
  a missing tag exits 2 and names ``git fetch --tags``; a clean range prints the no-deviation
  line. A mode-only change is no deviation, an empty ``Result-Change`` is UNMARKED rather than
  INCOMPLETE, and a failing git call exits 2 with ``error:``.
- The trailer parser ignores ``Result-Change:`` inside a body sentence and finds trailers in a
  paragraph before a ``Co-Authored-By`` paragraph.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "baseline_deviations.py"
TAG = "phase-2-baseline"
MARKER = ("Result-Change: {products}\n"
          "Reason: products/{first}/technical-notes.md, section Test\n"
          "Checked-By: test-agent: correct")
CO_AUTHOR = "Co-Authored-By: Someone <someone@example.com>"


def load_tool():
    spec = importlib.util.spec_from_file_location("baseline_deviations", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


baseline_deviations = load_tool()

GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], env=GIT_ENV, check=True,
                          capture_output=True, text=True).stdout.strip()


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], cwd=ROOT, env=GIT_ENV,
                          capture_output=True, text=True, timeout=120)


class Repo:
    """A throwaway repository with the tag on an initial commit of two baselines."""

    def __init__(self, path: Path):
        self.path = path
        path.mkdir()
        git(path, "init", "-q", "-b", "main")
        for product in ("alpha", "beta"):
            self.write(product, "t,cf\n0,1.0\n")
        self.commit("Initial baselines")
        git(path, "tag", TAG)

    def write(self, product: str, text: str) -> None:
        csv = self.path / "baseline" / product / "result_cf.csv"
        csv.parent.mkdir(parents=True, exist_ok=True)
        csv.write_text(text, encoding="utf-8")

    def commit(self, message: str) -> str:
        git(self.path, "add", "-A")
        git(self.path, "commit", "-q", "--allow-empty", "-m", message)
        return git(self.path, "rev-parse", "HEAD")

    def run(self, *args: str) -> subprocess.CompletedProcess:
        return run_tool("--repo", str(self.path), *args)


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path / "repo")


def marked(subject: str, *products: str, body: str = "") -> str:
    marker = MARKER.format(products=", ".join(products), first=products[0])
    return "\n\n".join(part for part in (subject, body, marker, CO_AUTHOR) if part)


def test_this_repository_has_every_deviation_marked(tmp_path):
    out = tmp_path / "listing.json"
    result = run_tool("--json", str(out))
    assert result.returncode == 0, result.stderr
    listing = json.loads(out.read_text(encoding="utf-8"))
    assert listing["problems"] == []
    assert all(deviation["marked"] for deviation in listing["deviations"])
    if not listing["deviations"]:
        assert result.stdout == f"no baseline deviation from {TAG} ({listing['tag']})\n"


def test_no_deviation(repo):
    repo.commit("A docs commit\n\nThe Result-Change: trailer is named in a sentence.\n\n" + CO_AUTHOR)
    result = repo.run()
    tag = git(repo.path, "rev-parse", TAG)
    assert (result.returncode, result.stdout, result.stderr) == (
        0, f"no baseline deviation from {TAG} ({tag})\n", "")


def test_a_marked_change_passes_and_is_listed_with_its_reason(repo, tmp_path):
    repo.write("alpha", "t,cf\n0,2.0\n")
    sha = repo.commit(marked("Change alpha", "alpha"))
    out = tmp_path / "listing.json"
    result = repo.run("--json", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    reason = "products/alpha/technical-notes.md, section Test"
    assert f"alpha {sha} Change alpha -- Reason: {reason}" in result.stdout.splitlines()
    listing = json.loads(out.read_text(encoding="utf-8"))
    assert listing["head"] == sha
    assert listing["deviations"] == [{
        "product": "alpha", "commit": sha, "subject": "Change alpha", "reason": reason,
        "checked_by": "test-agent: correct", "marked": True}]


def test_two_changes_of_one_product_are_two_deviations(repo, tmp_path):
    repo.write("alpha", "t,cf\n0,2.0\n")
    first = repo.commit(marked("Change alpha", "alpha"))
    repo.write("alpha", "t,cf\n0,1.0\n")
    second = repo.commit(marked("Revert alpha's change", "alpha"))
    out = tmp_path / "listing.json"
    assert repo.run("--json", str(out)).returncode == 0
    listing = json.loads(out.read_text(encoding="utf-8"))
    assert [d["commit"] for d in listing["deviations"]] == [first, second]


def test_an_unmarked_change_exits_1_and_names_product_and_sha(repo):
    repo.write("alpha", "t,cf\n0,2.0\n")
    marked_sha = repo.commit(marked("Change alpha", "alpha"))
    repo.write("beta", "t,cf\n0,3.0\n")
    sha = repo.commit("Change beta quietly\n\nThe body says Result-Change: beta in a sentence.\n\n"
                      + CO_AUTHOR)
    result = repo.run()
    assert result.returncode == 1
    unmarked = [line for line in result.stderr.splitlines() if line.startswith("UNMARKED")]
    assert len(unmarked) == 1
    assert "beta" in unmarked[0] and sha in unmarked[0]
    listed = result.stdout.splitlines()[1:]
    assert [line.split()[:2] for line in listed] == [["alpha", marked_sha]]


def test_a_marker_naming_an_unchanged_product_exits_1(repo):
    repo.write("alpha", "t,cf\n0,2.0\n")
    sha = repo.commit(marked("Change alpha", "alpha", "beta"))
    result = repo.run()
    assert result.returncode == 1
    assert [line for line in result.stderr.splitlines() if line.startswith("NO CHANGE")] == [
        f"NO CHANGE: beta {sha} Change alpha -- Result-Change names beta, whose baseline "
        f"this commit does not change"]


def test_a_marker_without_checked_by_exits_1(repo):
    repo.write("alpha", "t,cf\n0,2.0\n")
    message = marked("Change alpha", "alpha").replace("Checked-By: test-agent: correct", "")
    sha = repo.commit(message)
    result = repo.run()
    assert result.returncode == 1
    assert f"INCOMPLETE: {sha} Change alpha -- Result-Change without Checked-By" in (
        result.stderr.splitlines())


def test_an_empty_reason_exits_1(repo):
    repo.write("alpha", "t,cf\n0,2.0\n")
    message = marked("Change alpha", "alpha").replace(
        "Reason: products/alpha/technical-notes.md, section Test", "Reason:")
    sha = repo.commit(message)
    result = repo.run()
    assert result.returncode == 1
    assert f"INCOMPLETE: {sha} Change alpha -- Result-Change without Reason" in (
        result.stderr.splitlines())


def test_an_evil_merge_exits_1(repo):
    git(repo.path, "checkout", "-q", "-b", "side")
    repo.commit("Side work")
    git(repo.path, "checkout", "-q", "main")
    repo.commit("Main work")
    git(repo.path, "merge", "-q", "--no-commit", "--no-ff", "side")
    repo.write("alpha", "t,cf\n0,9.0\n")
    merge = repo.commit("Merge branch 'side'")
    assert len(git(repo.path, "rev-parse", f"{merge}^@").split()) == 2
    result = repo.run()
    assert result.returncode == 1
    unmarked = [line for line in result.stderr.splitlines() if line.startswith("UNMARKED")]
    assert len(unmarked) == 1 and f"alpha {merge}" in unmarked[0]


def test_a_merge_of_a_marked_branch_change_is_not_a_second_deviation(repo, tmp_path):
    git(repo.path, "checkout", "-q", "-b", "side")
    repo.write("alpha", "t,cf\n0,2.0\n")
    branch = repo.commit(marked("Change alpha", "alpha"))
    git(repo.path, "checkout", "-q", "main")
    repo.commit("Main work")
    git(repo.path, "merge", "-q", "--no-ff", "-m", "Merge branch 'side'", "side")
    out = tmp_path / "listing.json"
    result = repo.run("--json", str(out))
    assert result.returncode == 0, result.stderr
    listing = json.loads(out.read_text(encoding="utf-8"))
    assert [d["commit"] for d in listing["deviations"]] == [branch]


def test_an_added_baseline_is_a_change(repo):
    repo.write("gamma", "t,cf\n0,1.0\n")
    sha = repo.commit("Add gamma")
    result = repo.run()
    assert result.returncode == 1
    assert any(line.startswith("UNMARKED: gamma ") and sha in line
               for line in result.stderr.splitlines())


def test_a_removed_baseline_is_a_change(repo):
    (repo.path / "baseline" / "beta" / "result_cf.csv").unlink()
    sha = repo.commit(marked("Remove beta", "beta"))
    result = repo.run()
    assert result.returncode == 0, result.stderr
    assert f"beta {sha} Remove beta" in result.stdout


def test_a_mode_only_change_is_no_deviation(repo):
    (repo.path / "baseline" / "alpha" / "result_cf.csv").chmod(0o755)
    repo.commit("Make alpha's baseline executable")
    assert git(repo.path, "diff", "--name-only", "HEAD~1", "HEAD") == "baseline/alpha/result_cf.csv"
    result = repo.run()
    tag = git(repo.path, "rev-parse", TAG)
    assert (result.returncode, result.stdout, result.stderr) == (
        0, f"no baseline deviation from {TAG} ({tag})\n", "")


def test_an_empty_result_change_is_unmarked_not_incomplete(repo):
    repo.write("alpha", "t,cf\n0,2.0\n")
    message = marked("Change alpha", "alpha").replace("Result-Change: alpha", "Result-Change:")
    sha = repo.commit(message)
    result = repo.run()
    assert result.returncode == 1
    problems = result.stderr.splitlines()
    assert any(line.startswith(f"UNMARKED: alpha {sha}") for line in problems)
    assert not any(line.startswith("INCOMPLETE") for line in problems)


def test_a_failing_git_call_exits_2_without_a_traceback(repo, monkeypatch, capsys):
    def fail(*args):
        raise RuntimeError("git log failed: fatal: bad object")
    monkeypatch.setattr(baseline_deviations, "commits", fail)
    assert baseline_deviations.main(["--repo", str(repo.path)]) == 2
    assert capsys.readouterr().err == "error: git log failed: fatal: bad object\n"


def test_a_missing_tag_exits_2(repo):
    result = repo.run("--tag", "no-such-tag")
    assert result.returncode == 2
    assert "no-such-tag" in result.stderr and "git fetch --tags" in result.stderr


def test_the_trailer_parser_skips_body_sentences_and_finds_a_paragraph_before_co_authored_by():
    message = ("Subject\n\n"
               "The trailers (Result-Change: x, Reason: y) are described here.\n"
               "Result-Change: alpha appears at a line start inside the body.\n\n"
               "Result-Change: alpha, beta\n"
               "Reason: docs, section A\n"
               "Checked-By: agent: ok\n\n"
               "Co-Authored-By: Someone <someone@example.com>\n")
    trailers = baseline_deviations.parse_trailers(message)
    assert trailers["result-change"] == ["alpha, beta"]
    assert trailers["reason"] == ["docs, section A"]
    assert trailers["checked-by"] == ["agent: ok"]
    assert baseline_deviations.named_products(trailers) == ["alpha", "beta"]
    body_only = "Subject\n\nResult-Change: alpha is in a body.\nIt goes on.\n"
    assert baseline_deviations.parse_trailers(body_only) == {}
    assert baseline_deviations.parse_trailers("Result-Change: alpha") == {}
