"""The generic runner ``tools/run_baseline.py``, on scratch copies of one product.

The runs start together in separate processes in a session fixture, so the tests wait for
the slowest run only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tools" / "run_baseline.py"
PRODUCT = "risikolebensversicherung"
FOLDER = ROOT / "products" / PRODUCT
N_POINTS = 14
BASELINE = ROOT / "baseline" / PRODUCT / "result_cf.csv"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_baseline", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def folder_hashes(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def scratch_copy(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(FOLDER, target)
    return target


def edit_point(folder: Path, point_id: int, **changes: str) -> None:
    """Change columns of one model point in a scratch copy, as text."""
    path = folder / "model_point_table.csv"
    lines = path.read_bytes().decode("ascii").split("\n")
    columns = lines[0].split(",")
    values = lines[point_id].split(",")
    assert values[0] == str(point_id)
    for column, value in changes.items():
        assert values[columns.index(column)] != value
        values[columns.index(column)] = value
    lines[point_id] = ",".join(values)
    path.write_bytes("\n".join(lines).encode("ascii"))


def parse_output(stdout: str) -> dict[str, str]:
    return dict(line.split(": ", 1) for line in stdout.splitlines() if ": " in line)


@pytest.fixture(scope="session")
def runs(tmp_path_factory):
    """Run the runner in parallel processes and collect exit code, output and stderr.

    ``write_a`` and ``write_b`` run the product by name with ``--write`` to two folders.
    ``false_check`` is a scratch copy whose point 1 is in force for its whole term, so its
    policy roll-forward check is false; it also asks for ``--write``. ``raises`` is a
    scratch copy in which points 2 and 13 name a benefit schedule that does not exist.
    ``path_write`` is a scratch copy named like the product, with ``--write`` and no ``--out``.
    ``write_nc`` and ``raises_nc`` repeat ``write_a`` and ``raises`` with ``--no-cleanup``.
    ``write_mx`` and ``raises_mx`` repeat them with ``--engine modelx``, ``write_mx_nc`` also
    with ``--no-cleanup``; ``bad_engine`` names an engine that does not exist.
    """
    tmp_path = tmp_path_factory.mktemp("runner")
    false_check = scratch_copy(tmp_path, "false_check")
    edit_point(false_check, 1, duration_y="25")
    raises = scratch_copy(tmp_path, "raises")
    edit_point(raises, 2, benefit_schedule_id="nosuch")
    edit_point(raises, 13, benefit_schedule_id="nosuch")
    named = scratch_copy(tmp_path / "named", PRODUCT)

    out = tmp_path / "out"
    commands = {
        "write_a": [PRODUCT, "--write", "--out", str(out / "a")],
        "write_b": [PRODUCT, "--write", "--out", str(out / "b")],
        "false_check": [str(false_check), "--write", "--out", str(out / "false_check")],
        "raises": [str(raises)],
        "write_nc": [PRODUCT, "--no-cleanup", "--write", "--out", str(out / "c")],
        "raises_nc": [str(raises), "--no-cleanup"],
        "write_mx": [PRODUCT, "--engine", "modelx", "--write", "--out", str(out / "m")],
        "raises_mx": [str(raises), "--engine", "modelx"],
        "write_mx_nc": [PRODUCT, "--engine", "modelx", "--no-cleanup", "--write", "--out", str(out / "mnc")],
        "bad_engine": [PRODUCT, "--engine", "foo"],
        "unknown": ["nosuch"],
        "path_write": [str(named), "--write"],
    }
    before = folder_hashes(FOLDER)
    baseline_before = BASELINE.read_bytes()
    processes = {
        name: subprocess.Popen([sys.executable, str(RUNNER), *args], cwd=ROOT,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for name, args in commands.items()}
    results = {}
    for name, process in processes.items():
        stdout, stderr = process.communicate(timeout=900)
        results[name] = (process.returncode, parse_output(stdout), stderr)
    results["before"] = before
    results["after"] = folder_hashes(FOLDER)
    results["out"] = out
    results["baseline_unchanged"] = BASELINE.read_bytes() == baseline_before
    return results


def test_happy_path_prints_count_hash_time_and_all_true(runs):
    code, output, stderr = runs["write_a"]
    assert code == 0, stderr
    assert int(output["model points"]) == N_POINTS
    assert re.fullmatch(r"[0-9a-f]{64}", output["sha256"])
    assert re.fullmatch(r"\d+\.\d s", output["wall time"])
    assert output["checks"] == "all true"
    assert output["cleanup"] == "on"
    assert output["engine"] == "export"
    assert "FAILED" not in stderr


def test_engine_and_cleanup_are_the_first_two_output_lines(runs):
    for name, engine in (("write_a", "export"), ("write_mx", "modelx")):
        assert list(runs[name][1].items())[:2] == [("engine", engine), ("cleanup", "on")]


def test_default_run_writes_the_stored_baseline(runs):
    assert (runs["out"] / "a" / "result_cf.csv").read_bytes() == BASELINE.read_bytes()


def test_write_twice_gives_identical_bytes(runs):
    a = runs["out"] / "a" / "result_cf.csv"
    b = runs["out"] / "b" / "result_cf.csv"
    assert a.read_bytes() == b.read_bytes()
    assert runs["write_a"][1]["sha256"] == runs["write_b"][1]["sha256"]
    lines = a.read_bytes().split(b"\n")
    assert lines[0].startswith(b"point_id,t,")
    assert lines[-1] == b"" and b"\r" not in a.read_bytes()


def test_false_check_exits_1_names_point_and_check_and_writes_nothing(runs):
    code, output, stderr = runs["false_check"]
    assert code == 1
    assert "point 1: check_pols_roll_fwd is false" in stderr
    assert int(output["model points"]) == N_POINTS
    assert not (runs["out"] / "false_check").exists()


def test_raising_point_exits_1_and_the_other_points_still_run(runs):
    code, output, stderr = runs["raises"]
    assert code == 1
    failed = [line for line in stderr.splitlines() if line.startswith("FAILED ")]
    assert failed, stderr
    assert "FAILED point 2: result_cf raised KeyError: ('nosuch', 1)" in failed, stderr
    assert not any("FormulaError" in line for line in failed), stderr
    assert any(line.startswith("FAILED point 13: result_cf raised ") for line in failed), stderr
    assert {re.match(r"FAILED point (\d+):", line).group(1) for line in failed} == {"2", "13"}
    assert int(output["model points"]) == N_POINTS
    assert output["sha256"] != runs["write_a"][1]["sha256"]


def test_raising_point_under_modelx_is_wrapped_in_a_formula_error(runs):
    code, output, stderr = runs["raises_mx"]
    assert code == 1
    assert output["engine"] == "modelx"
    failed = [line for line in stderr.splitlines() if line.startswith("FAILED ")]
    assert "FAILED point 2: result_cf raised FormulaError: KeyError: ('nosuch', 1)" in failed, stderr
    assert {re.match(r"FAILED point (\d+):", line).group(1) for line in failed} == {"2", "13"}
    assert output["sha256"] == runs["raises"][1]["sha256"]


def test_unknown_product_gives_usage_and_exit_2(runs):
    code, output, stderr = runs["unknown"]
    assert code == 2
    assert stderr.startswith("usage: run_baseline.py")
    assert "nosuch" in stderr
    assert output == {}


def test_unknown_engine_gives_usage_and_exit_2(runs):
    code, output, stderr = runs["bad_engine"]
    assert code == 2
    assert stderr.startswith("usage: run_baseline.py")
    assert "--engine" in stderr and "foo" in stderr
    assert output == {}


@pytest.mark.parametrize("name, folder", [("write_mx", "m"), ("write_mx_nc", "mnc")])
def test_modelx_engine_gives_the_same_hash_and_bytes(runs, name, folder):
    code, output, stderr = runs[name]
    assert code == 0, stderr
    assert output["engine"] == "modelx"
    assert output["cleanup"] == ("on" if name == "write_mx" else "off")
    assert output["sha256"] == runs["write_a"][1]["sha256"]
    assert (runs["out"] / folder / "result_cf.csv").read_bytes() == (
        runs["out"] / "a" / "result_cf.csv").read_bytes()


def test_runs_leave_the_product_folder_untouched(runs):
    assert runs["after"] == runs["before"]


def test_write_from_a_path_without_out_is_a_usage_error(runs):
    code, output, stderr = runs["path_write"]
    assert code == 2
    assert stderr.startswith("usage: run_baseline.py")
    assert "--out" in stderr
    assert output == {}
    assert runs["baseline_unchanged"]


def test_no_cleanup_gives_the_same_hash_and_bytes(runs):
    code, output, stderr = runs["write_nc"]
    assert code == 0, stderr
    assert output["cleanup"] == "off"
    assert output["sha256"] == runs["write_a"][1]["sha256"]
    assert (runs["out"] / "c" / "result_cf.csv").read_bytes() == (
        runs["out"] / "a" / "result_cf.csv").read_bytes()


def test_no_cleanup_gives_the_same_failures(runs):
    def failed(name):
        return [line for line in runs[name][2].splitlines() if line.startswith("FAILED ")]
    code, output, _ = runs["raises_nc"]
    assert code == 1
    assert output["cleanup"] == "off" and runs["raises"][1]["cleanup"] == "on"
    assert failed("raises_nc") == failed("raises") and failed("raises")
    assert output["sha256"] == runs["raises"][1]["sha256"]


@pytest.mark.parametrize("engine", ["export", "modelx"])
@pytest.mark.parametrize("cleanup", [True, False])
def test_cleanup_deletes_every_itemspace_also_of_raising_points(tmp_path, monkeypatch, cleanup, engine):
    import importlib

    from modelx.core.space import UserSpace

    raises = scratch_copy(tmp_path, "raises")
    edit_point(raises, 2, benefit_schedule_id="nosuch")
    edit_point(raises, 13, benefit_schedule_id="nosuch")
    deleted = []

    def spy_on(cls):
        original = cls.__delitem__

        def spy(self, key):
            deleted.append(key)
            return original(self, key)

        monkeypatch.setattr(cls, "__delitem__", spy)

    if engine == "modelx":
        spy_on(UserSpace)
    else:
        import_module = importlib.import_module

        def spying_import(name, *args, **kwargs):
            module = import_module(name, *args, **kwargs)
            if name.startswith("_delib_export_"):
                spy_on(type(module.mx_model.Projection))
            return module

        monkeypatch.setattr(importlib, "import_module", spying_import)
    runner = load_runner()
    count, _checks, _sha, failures, _lines = runner.run_product(raises, cleanup=cleanup, engine=engine)
    assert count == N_POINTS
    assert {int(re.match(r"point (\d+):", f).group(1)) for f in failures} == {2, 13}
    assert deleted == (list(range(1, N_POINTS + 1)) if cleanup else [])
    assert not [k for k in sys.modules if k.startswith("_delib_export_")]
    assert not [p for p in sys.path if "delib-export-" in p]


def test_failing_export_is_one_failure_and_main_writes_nothing(tmp_path, monkeypatch, capsys):
    runner = load_runner()

    def boom(*args, **kwargs):
        raise RuntimeError("cannot export this model")

    monkeypatch.setattr(runner.mx, "export_model", boom)
    count, _checks, _sha, failures, lines = runner.run_product(FOLDER)
    assert count == N_POINTS
    assert failures == ["export raised RuntimeError: cannot export this model"]
    assert lines == []
    out = tmp_path / "out"
    assert runner.main([PRODUCT, "--write", "--out", str(out)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "engine: export"
    assert "checks: 1 failure(s)" in captured.out
    assert "FAILED export raised RuntimeError: cannot export this model" in captured.err
    assert "nothing written" in captured.err
    assert not out.exists()
