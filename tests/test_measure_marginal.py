"""The measuring tool ``tools/measure_marginal.py``.

Pure tests cover the arithmetic, the forecast, the replicated table and the comparison of
replicas and the baseline. One session fixture starts the tool's runs together in separate processes; the
tests assert no timings, since those depend on the machine.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "measure_marginal.py"
PRODUCT = "risikolebensversicherung"
FOLDER = ROOT / "products" / PRODUCT
N_POINTS = 14
# The export engine's slope is small (tens of ms per contract against an export of about a
# second), so its tool runs use a larger K: with K = 2 and one repeat, the parallel runs of the
# fixture made T(K·n) come out below T(n) now and then, and the tool rightly said unreliable.
FACTOR = 8

_spec = importlib.util.spec_from_file_location("measure_marginal", TOOL)
mm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mm)


def folder_hashes(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def guarded() -> dict[str, str]:
    hashes = {f"products/{k}": v for k, v in folder_hashes(ROOT / "products").items()}
    hashes.update({f"baseline/{k}": v for k, v in folder_hashes(ROOT / "baseline").items()})
    hashes["tools/run_baseline.py"] = hashlib.sha256(
        (ROOT / "tools" / "run_baseline.py").read_bytes()).hexdigest()
    return hashes


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


# --------------------------------------------------------------------------- pure tests

def test_slope_and_fixed_cost():
    d = mm.derive(n=10, factor=3, import_s=1.0, t_n=5.0, t_kn=9.0,
                  rss_n_kib=100 * 1024, rss_kn_kib=140 * 1024)
    assert d["status"] == "ok"
    assert d["t_marginal_s"] == pytest.approx(0.2)        # (9 - 5) / (2 * 10)
    assert d["fixed_s"] == pytest.approx(4.0)             # 1 + 5 - 10 * 0.2
    assert d["mb_per_contract"] == pytest.approx(2.0)     # 40 MB / 20


def test_memory_per_contract_only_at_one_worker():
    d = mm.derive(n=10, factor=3, import_s=1.0, t_n=5.0, t_kn=9.0,
                  rss_n_kib=100 * 1024, rss_kn_kib=140 * 1024, workers=8)
    assert d["t_marginal_s"] == pytest.approx(0.2) and d["mb_per_contract"] is None


@pytest.mark.parametrize("t_kn", [5.0, 4.0])
def test_non_positive_slope_is_unreliable_without_fixed(t_kn):
    d = mm.derive(n=10, factor=2, import_s=1.0, t_n=5.0, t_kn=t_kn, rss_n_kib=1, rss_kn_kib=2)
    assert d["status"] == "unreliable"
    assert d["fixed_s"] is None


def test_forecast_hours_and_lines():
    fc = mm.forecast(t_marginal_s=0.007, fixed_s=2.0, mb_per_contract=1.0,
                     mutants=500, pool=10000, workers=1, total_ram_mb=64 * 1024)
    assert fc["hours"] == pytest.approx(500 * 10000 * 0.007 / 3600)
    assert fc["hours_with_fixed"] == pytest.approx(500 * (2.0 + 70.0) / 3600)
    assert fc["fits_night"] is True
    assert fc["ram_warning"] is False
    lines = mm.forecast_lines("x", fc)
    assert "9.7 h (fits the 10 h night)" in lines[0]
    assert "M·(fixed(W) + P·t_marginal(W))" in lines[1] and "10.0 h" in lines[1]
    assert not any(line.startswith("WARNING") for line in lines)
    slow = mm.forecast(0.008, 2.0, 1.0, 500, 10000, 1, 64 * 1024)
    assert slow["fits_night"] is False
    assert "does not fit" in mm.forecast_lines("x", slow)[0]
    four = mm.forecast(0.008, 2.0, None, 500, 10000, 4, 64 * 1024, mem_kn_mb=900.0)
    assert four["hours"] == pytest.approx(slow["hours"])   # t_marginal(W) holds the workers
    assert four["ram_mb_per_process"] is None and four["ram_warning"] is False
    lines = mm.forecast_lines("x", four)
    assert lines[0].startswith("x, W = 4: M·P·t_marginal(W) = ")
    assert lines[-1] == "x, W = 4: memory, parent peak RSS + workers' largest Pss after a point at K·n = 900 MB"


def test_ram_warning_when_extrapolated_memory_exceeds_the_machine():
    fc = mm.forecast(0.001, 1.0, mb_per_contract=10.0, mutants=1, pool=10000, workers=1,
                     total_ram_mb=50 * 1024)
    assert fc["ram_warning"] is True
    assert mm.forecast_lines("x", fc)[-1].startswith("WARNING x, W = 1: ")


def test_assumptions_are_stated():
    text = "\n".join(mm.assumption_lines(500, 10000, [1, 4], 2))
    for phrase in ("500 mutants", "10,000 contracts", "W = 1,4 worker(s)", "does not divide by W",
                   "shipped point mix", "assumed, not tested", "without trace pruning",
                   "forecast", "phase 4"):
        assert phrase in text


def test_replicated_table_repeats_rows_in_order():
    text = "point_id,a,b\n1,x,1.0\n2,y,2.0\n3,z,3.0\n"
    assert mm.replicate_table(text, 2) == (
        "point_id,a,b\n1,x,1.0\n2,y,2.0\n3,z,3.0\n4,x,1.0\n5,y,2.0\n6,z,3.0\n")
    assert mm.replicate_table(text, 1) == text
    assert mm.count_points(mm.replicate_table(text, 3)) == 9
    assert mm.replicate_table(text.rstrip("\n"), 2).endswith("6,z,3.0")


@pytest.mark.parametrize("text", ["id,a\n1,x\n", "point_id,a\n2,x\n", "point_id,a\n1,x\n3,y\n"])
def test_replicated_table_needs_ids_one_to_n(text):
    with pytest.raises(ValueError):
        mm.replicate_table(text, 2)


def test_replicated_shipped_table_keeps_every_field_but_the_id():
    text = (FOLDER / "model_point_table.csv").read_bytes().decode("ascii")
    rows = mm.replicate_table(text, 2).split("\n")
    assert rows[1:N_POINTS + 1] == text.split("\n")[1:N_POINTS + 1]
    for i in range(1, N_POINTS + 1):
        assert rows[N_POINTS + i].split(",", 1)[1] == rows[i].split(",", 1)[1]
        assert rows[N_POINTS + i].split(",", 1)[0] == str(N_POINTS + i)


def _digest(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("ascii")).hexdigest()


def _result(points, failures=(), n=None, originals=2):
    """A child result: lines of the ids up to ``originals``, a digest for every point."""
    return {"n": len(points) if n is None else n, "failures": list(failures), "header": "point_id,t,v",
            "points": {str(k): v for k, v in points.items() if k <= originals},
            "digests": {str(k): _digest(v) for k, v in points.items()}}


BASE = b"point_id,t,v\n1,0,1.0\n1,1,2.0\n2,0,3.0\n"
GOOD = {1: ["0,1.0", "1,2.0"], 2: ["0,3.0"], 3: ["0,1.0", "1,2.0"], 4: ["0,3.0"]}


def test_comparison_accepts_equal_replicas_and_the_baseline():
    assert mm.verify_run(_result(GOOD), size=4, n=2, baseline=BASE) == []
    assert mm.verify_run(_result({1: GOOD[1], 2: GOOD[2]}), size=2, n=2, baseline=BASE) == []


def test_comparison_names_a_differing_replica_by_its_digest():
    points = {**GOOD, 3: ["0,1.0", "1,2.0000000000000004"]}
    assert mm.verify_run(_result(points), 4, 2, BASE) == [
        "point 3: result_cf differs from its original, point 1"]


def test_comparison_finds_baseline_mismatch_missing_points_and_failures():
    assert "do not reproduce the baseline" in mm.verify_run(_result(GOOD), 4, 2, BASE + b"x")[0]
    missing = {k: v for k, v in GOOD.items() if k != 4}
    problems = mm.verify_run(_result(missing, failures=["point 4: check_x is false"], n=4), 4, 2, BASE)
    assert "run_product failure: point 4: check_x is false" in problems
    assert "points missing from result_cf: 4" in problems


# --------------------------------------------------------------------------- tool runs

@pytest.fixture(scope="session")
def runs(tmp_path_factory):
    """Run the tool in parallel processes and collect exit code, output and stderr.

    ``rlv`` measures the product with K = ``FACTOR`` and one repeat at W = 1 and 2 and
    writes JSON; ``rlv_nc`` does the same at W = 1 with ``--no-cleanup``; ``rlv_mx`` uses
    ``--engine modelx``, whose slope is large enough for K = 2. ``replica`` gets a prepared
    K·n folder (K = 2) whose replica of point 1 (point 15) has another sum assured. The
    others are usage errors.
    """
    tmp_path = tmp_path_factory.mktemp("measure")
    prepared = tmp_path / "prepared"
    shutil.copytree(FOLDER, prepared)
    table = prepared / "model_point_table.csv"
    table.write_bytes(mm.replicate_table(table.read_bytes().decode("ascii"), 2).encode("ascii"))
    edit_point(prepared, N_POINTS + 1, sum_assured="123456.0")
    json_path = tmp_path / "rlv.json"
    json_nc = tmp_path / "rlv_nc.json"
    json_mx = tmp_path / "rlv_mx.json"
    commands = {
        "rlv": [PRODUCT, "--factor", str(FACTOR), "--repeats", "1", "--workers", "1,2",
                "--json", str(json_path)],
        "rlv_nc": [PRODUCT, "--factor", str(FACTOR), "--repeats", "1", "--no-cleanup",
                   "--json", str(json_nc)],
        "rlv_mx": [PRODUCT, "--factor", "2", "--repeats", "1", "--engine", "modelx",
                   "--json", str(json_mx)],
        "replica": [PRODUCT, "--factor", "2", "--repeats", "1", "--workers", "1",
                    "--prepared", str(prepared)],
        "workers_mx": [PRODUCT, "--engine", "modelx", "--workers", "1,2"],
        "unknown": ["nosuch"],
        "factor_1": [PRODUCT, "--factor", "1"],
        "repeats_0": [PRODUCT, "--repeats", "0"],
    }
    before = guarded()
    processes = {
        name: subprocess.Popen([sys.executable, str(TOOL), *args], cwd=ROOT,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for name, args in commands.items()}
    results = {}
    for name, process in processes.items():
        stdout, stderr = process.communicate(timeout=900)
        results[name] = (process.returncode, stdout, stderr)
    results["before"] = before
    results["after"] = guarded()
    results["json"] = json.loads(json_path.read_text()) if json_path.exists() else None
    results["json_nc"] = json.loads(json_nc.read_text()) if json_nc.exists() else None
    results["json_mx"] = json.loads(json_mx.read_text()) if json_mx.exists() else None
    return results


def test_one_product_prints_a_row_per_worker_count_and_the_forecast(runs):
    code, stdout, stderr = runs["rlv"]
    assert code == 0, stderr
    rows = [line for line in stdout.splitlines() if line.startswith(PRODUCT + " ")]
    assert [row.split()[1:4] for row in rows] == [
        [w, str(N_POINTS), str(FACTOR * N_POINTS)] for w in ("1", "2")]
    assert all(row.endswith(" ok") for row in rows)
    assert rows[0].split()[-2] != "-" and rows[1].split()[-2] == "-"   # MB/contract at W = 1 only
    assert "Assumptions: M = 500 mutants, P = 10,000 contracts, W = 1,2 worker(s);" in stdout
    for w in (1, 2):
        assert f"{PRODUCT}, W = {w}: M·P·t_marginal(W) = " in stdout
        assert f"{PRODUCT}, W = {w}: with fixed cost per mutant, M·(fixed(W) + P·t_marginal(W)) = " in stdout
    assert "FAILED" not in stderr


def test_json_holds_inputs_runs_medians_derived_and_forecast_per_worker_count(runs):
    data = runs["json"]
    assert data is not None
    assert (data["factor"], data["repeats"], data["cleanup"], data["engine"], data["mutants"],
            data["pool"], data["workers"]) == (FACTOR, 1, True, "export", 500, 10000, [1, 2])
    assert [(r["product"], r["workers"]) for r in data["products"]] == [(PRODUCT, 1), (PRODUCT, 2)]
    for record in data["products"]:
        assert record["status"] == "ok"
        assert (record["n"], record["size_kn"]) == (N_POINTS, FACTOR * N_POINTS)
        assert [r["size"] for r in record["runs"]] == [N_POINTS, FACTOR * N_POINTS]
        assert set(record["medians"]) == {"import_s", "run_s_n", "run_s_kn", "maxrss_kib_n",
                                          "maxrss_kib_kn", "mem_kib_n", "mem_kib_kn"}
        d = record["derived"]
        m = record["medians"]
        assert d["t_marginal_s"] == pytest.approx((m["run_s_kn"] - m["run_s_n"]) / ((FACTOR - 1) * N_POINTS))
        assert d["fixed_s"] == pytest.approx(m["import_s"] + m["run_s_n"] - N_POINTS * d["t_marginal_s"])
        assert record["forecast"]["hours"] == pytest.approx(500 * 10000 * d["t_marginal_s"] / 3600)
        for run in record["runs"]:
            assert run["mem_kib"] == run["maxrss_kib"] + run["worker_pss_kib"]
            assert (run["worker_pss_kib"] > 0) == (record["workers"] > 1)
    one, two = data["products"]
    assert one["derived"]["mb_per_contract"] is not None and two["derived"]["mb_per_contract"] is None


def test_header_line_names_the_workers_the_cleanup_mode_and_the_engine(runs):
    header = runs["rlv"][1].splitlines()[0]
    assert header.startswith(f"factor K = {FACTOR}, repeats R = 1, workers W = 1,2; ")
    assert header.endswith(", cleanup on, engine export")


def test_no_cleanup_measures_and_verifies_without_cleanup(runs):
    code, stdout, stderr = runs["rlv_nc"]
    assert code == 0, stderr
    assert stdout.splitlines()[0].endswith(", cleanup off, engine export")
    data = runs["json_nc"]
    assert data is not None and data["cleanup"] is False and data["workers"] == [1]
    (record,) = data["products"]
    assert record["status"] == "ok" and not record["errors"]
    assert "FAILED" not in stderr


def test_modelx_engine_measures_and_verifies_on_the_modelx_model(runs):
    code, stdout, stderr = runs["rlv_mx"]
    assert code == 0, stderr
    assert stdout.splitlines()[0].endswith(", cleanup on, engine modelx")
    data = runs["json_mx"]
    assert data is not None and data["engine"] == "modelx" and data["cleanup"] is True
    assert data["workers"] == [1]
    (record,) = data["products"]
    assert record["status"] == "ok" and not record["errors"]
    assert "FAILED" not in stderr


def test_the_child_passes_the_switch_to_the_runner(monkeypatch):
    calls = []
    monkeypatch.setattr(mm.subprocess, "run", lambda command, **k: calls.append(command) or
                        subprocess.CompletedProcess(command, 0, "{}\n", ""))
    mm.run_child(FOLDER, N_POINTS, cleanup=True)
    mm.run_child(FOLDER, N_POINTS, cleanup=False)
    mm.run_child(FOLDER, N_POINTS, cleanup=True, engine="modelx")
    mm.run_child(FOLDER, N_POINTS, cleanup=True, workers=8)
    assert "--no-cleanup" not in calls[0] and calls[1][-1] == "--no-cleanup"
    assert calls[0][-4:] == ["--workers", "1", "--engine", "export"]
    assert calls[2][-2:] == ["--engine", "modelx"] and "--no-cleanup" not in calls[2]
    assert calls[3][-4:] == ["--workers", "8", "--engine", "export"]


@pytest.mark.parametrize("argv, cleanup, engine, workers", [
    (["--workers", "1"], True, "export", 1), (["--no-cleanup"], False, "export", 1),
    (["--engine", "modelx"], True, "modelx", 1),
    (["--engine", "modelx", "--no-cleanup"], False, "modelx", 1),
    (["--workers", "8"], True, "export", 8)])
def test_the_child_runs_the_runner_in_the_chosen_mode(monkeypatch, capsys, argv, cleanup, engine,
                                                      workers):
    seen = []

    def run_product(folder, cleanup=True, engine="export", keep_lines=True, workers=1,
                    worker_pss=None):
        seen.append((cleanup, engine, keep_lines, workers))
        if workers > 1:
            worker_pss.update({101: 2048, 102: 1024})
        return 0, [], "", [], [], {}

    fake = type(sys)("run_baseline")
    fake.run_product = run_product
    monkeypatch.setitem(sys.modules, "run_baseline", fake)
    assert mm.main(["--child", str(FOLDER), "--originals", str(N_POINTS), *argv]) == 0
    assert seen == [(cleanup, engine, N_POINTS, workers)]
    result = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert result["n"] == 0 and result["workers"] == workers
    assert result["worker_pss_kib"] == (3072 if workers > 1 else 0)
    assert result["mem_kib"] == result["maxrss_kib"] + result["worker_pss_kib"]


def test_a_differing_replica_exits_1_and_names_the_point(runs):
    code, stdout, stderr = runs["replica"]
    assert code == 1
    assert (f"FAILED {PRODUCT}, W = 1: size {2 * N_POINTS} (K·n), run 1: "
            f"point {N_POINTS + 1}: result_cf differs from its original, point 1") in stderr
    row = [line for line in stdout.splitlines() if line.startswith(PRODUCT + " ")]
    assert len(row) == 1 and row[0].endswith(" failed")
    assert f"{PRODUCT}, W = 1: no forecast (failed)" in stdout
    assert "M·P·t_marginal(W)" not in stdout


@pytest.mark.parametrize("name, needle", [("unknown", "nosuch"), ("factor_1", "--factor"),
                                          ("repeats_0", "--repeats"), ("workers_mx", "--workers")])
def test_usage_errors_exit_2(runs, name, needle):
    code, stdout, stderr = runs[name]
    assert code == 2
    assert stderr.startswith("usage: measure_marginal.py")
    assert needle in stderr
    assert stdout == ""


def test_runs_leave_products_baseline_and_runner_untouched(runs):
    assert runs["after"] == runs["before"]


# --------------------------------------------------------------------------- matrix rows in process

def _baseline_points() -> tuple[str, dict[str, list[str]]]:
    lines = (ROOT / "baseline" / PRODUCT / "result_cf.csv").read_bytes().decode("ascii").splitlines()
    points: dict[str, list[str]] = {}
    for line in lines[1:]:
        pid, _, rest = line.partition(",")
        points.setdefault(pid, []).append(rest)
    return lines[0], points


def _measure(argv):
    args = mm.argparse.Namespace(factor=2, repeats=1, mutants=500, pool=10000, workers=[1],
                                 prepared=None, json=None, no_cleanup=False, engine="export")
    for key, value in argv.items():
        setattr(args, key, value)
    return mm.measure(PRODUCT, args, ram_mb=64 * 1024, workers=1)


def test_a_failing_point_in_the_child_fails_the_product(monkeypatch, capsys):
    header, points = _baseline_points()
    del points["3"]
    monkeypatch.setattr(mm, "run_child", lambda folder, n, cleanup, engine, workers: {
        "n": N_POINTS, "failures": ["point 3: check_x is false"], "header": header,
        "points": points, "digests": {k: _digest(v) for k, v in points.items()},
        "import_s": 0.1, "run_s": 1.0, "maxrss_kib": 1, "worker_pss_kib": 0, "mem_kib": 1})
    record = _measure({})
    assert record["status"] == "failed" and "derived" not in record and "forecast" not in record
    err = capsys.readouterr().err
    assert f"FAILED {PRODUCT}, W = 1: size {N_POINTS} (n), run 1: run_product failure: point 3: check_x is false" in err


@pytest.mark.parametrize("returncode, stdout, needle", [
    (1, "", "child exited 1; stderr tail:\nTraceback\nboom"),
    (0, "not json\n", "child printed no JSON; stderr tail:\nTraceback\nboom"),
    (0, "", "child printed no JSON"),
])
def test_a_crashing_child_fails_the_product(monkeypatch, capsys, returncode, stdout, needle):
    monkeypatch.setattr(mm.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], returncode, stdout, "Traceback\nboom\n"))
    record = _measure({})
    assert record["status"] == "failed" and record.get("forecast") is None
    err = capsys.readouterr().err
    assert f"FAILED {PRODUCT}, W = 1: size {N_POINTS} (n), run 1: {needle}" in err


def test_a_non_positive_slope_is_unreliable_and_exits_1(monkeypatch, capsys):
    header, points = _baseline_points()

    def fake(folder, n, cleanup, engine, workers):
        size = mm.count_points((folder / mm.TABLE).read_bytes().decode("ascii"))
        return {"n": size, "failures": [], "header": header, "points": points,
                "digests": {str(p): _digest(points[str(mm.original_of(p, n))])
                            for p in range(1, size + 1)},
                "import_s": 0.1, "run_s": 2.0, "maxrss_kib": 1024, "worker_pss_kib": 0,
                "mem_kib": 1024}

    monkeypatch.setattr(mm, "run_child", fake)
    assert mm.main([PRODUCT, "--repeats", "1", "--factor", "2", "--workers", "1,4"]) == 1
    out = capsys.readouterr()
    rows = [line for line in out.out.splitlines() if line.startswith(PRODUCT + " ")]
    assert len(rows) == 2
    assert all(row.endswith(" unreliable") and " - " in row for row in rows)
    assert f"{PRODUCT}, W = 4: no forecast (unreliable)" in out.out
    assert f"UNRELIABLE {PRODUCT}, W = 1" in out.err


def test_all_measures_every_product_in_name_order_and_returns_the_worst(monkeypatch, capsys):
    seen = []

    def fake(product, args, ram_mb, workers):
        seen.append((product, workers))
        return {"product": product, "workers": workers,
                "status": "failed" if len(seen) == 1 else "ok",
                "runs": [], "errors": [], "forecast": None}

    monkeypatch.setattr(mm, "measure", fake)
    assert mm.main(["--all"]) == 1
    names = mm.product_names()
    assert len(names) == 10 and names == sorted(names)
    assert seen == [(p, w) for p in names for w in mm.DEFAULT_WORKERS]
    rows = [tuple(line.split()[:2]) for line in capsys.readouterr().out.splitlines()[2:2 + len(seen)]]
    assert rows == [(p, str(w)) for p, w in seen]


def test_defaults_are_factor_32_and_the_worker_counts(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(mm, "measure", lambda product, args, ram_mb, workers: seen.append(
        (args.factor, workers)) or {"product": product, "workers": workers, "status": "ok",
                                    "runs": [], "errors": [], "forecast": None})
    assert mm.main([PRODUCT]) == 0
    assert seen == [(32, w) for w in (1, 4, 8, 12, 16, 24)]
    seen.clear()
    assert mm.main([PRODUCT, "--engine", "modelx"]) == 0
    assert mm.main([PRODUCT, "--no-cleanup"]) == 0
    assert mm.main([PRODUCT, "--workers", "8,1,8"]) == 0
    assert [w for _, w in seen] == [1, 1, 8, 1]


@pytest.mark.parametrize("argv", [[PRODUCT, "--workers", "0"], [PRODUCT, "--workers", "1,0"],
                                  [PRODUCT, "--workers", "1,x"],
                                  [PRODUCT, "--workers", "4", "--no-cleanup"],
                                  [PRODUCT, "--workers", "4", "--engine", "modelx"],
                                  [PRODUCT, "--repeats", "two"],
                                  [PRODUCT, "--factor", "1.5"], [], [PRODUCT, "--all"],
                                  [PRODUCT, "--json", "/nonexistent-dir/x.json"],
                                  [PRODUCT, "--engine", "foo"]])
def test_more_usage_errors_exit_2(argv, capsys):
    with pytest.raises(SystemExit) as exc:
        mm.main(argv)
    assert exc.value.code == 2
    assert capsys.readouterr().err.startswith("usage: measure_marginal.py")
