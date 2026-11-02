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


def guarded() -> dict[str, str]:
    """The product folder and the core, which the product reaches through symlinks."""
    hashes = folder_hashes(FOLDER)
    hashes.update({f"core/{k}": v for k, v in folder_hashes(ROOT / "core").items()})
    return hashes


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
    with ``--no-cleanup``; ``bad_engine`` names an engine that does not exist. ``write_w4``
    and ``raises_w4`` repeat ``write_a`` and ``raises`` with ``--workers 4``; ``workers_0``,
    ``workers_mx`` and ``workers_nc`` are the usage errors of ``--workers``.
    """
    tmp_path = tmp_path_factory.mktemp("runner")
    false_check = scratch_copy(tmp_path, "false_check")
    edit_point(false_check, 1, duration_init="25")
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
        "write_w4": [PRODUCT, "--workers", "4", "--write", "--out", str(out / "w4")],
        "raises_w4": [str(raises), "--workers", "4"],
        "workers_0": [PRODUCT, "--workers", "0"],
        "workers_mx": [PRODUCT, "--workers", "2", "--engine", "modelx"],
        "workers_nc": [PRODUCT, "--workers", "2", "--no-cleanup"],
        "unknown": ["nosuch"],
        "path_write": [str(named), "--write"],
    }
    before = guarded()
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
    results["after"] = guarded()
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


def test_engine_cleanup_and_workers_are_the_first_three_output_lines(runs):
    for name, engine, workers in (("write_a", "export", "1"), ("write_mx", "modelx", "1"),
                                  ("write_w4", "export", "4")):
        assert list(runs[name][1].items())[:3] == [
            ("engine", engine), ("cleanup", "on"), ("workers", workers)]


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
    count, _checks, _sha, failures, _lines, digests = runner.run_product(raises, cleanup=cleanup,
                                                                        engine=engine)
    assert count == N_POINTS
    assert {int(re.match(r"point (\d+):", f).group(1)) for f in failures} == {2, 13}
    assert sorted(digests) == [i for i in range(1, N_POINTS + 1) if i not in (2, 13)]
    assert deleted == (list(range(1, N_POINTS + 1)) if cleanup else [])
    assert not [k for k in sys.modules if k.startswith("_delib_export_")]
    assert not [p for p in sys.path if "delib-export-" in p]


def run_without_garbage_collection(folder: Path, monkeypatch):
    """Run ``folder`` with the collector off. Return the run's count and failures, the keys
    deleted from ``Projection`` in order, and the keys of the deleted items still alive."""
    import gc
    import importlib

    deleted, keys = {}, []

    def spy_on(cls):
        original = cls.__delitem__

        def spy(self, key):
            item = self._mx_itemspaces[key]
            deleted[id(item)] = (key, type(item))
            keys.append(key)
            del item
            original(self, key)

        monkeypatch.setattr(cls, "__delitem__", spy)

    import_module = importlib.import_module

    def spying_import(name, *args, **kwargs):
        module = import_module(name, *args, **kwargs)
        if name.startswith("_delib_export_"):
            spy_on(type(module.mx_model.Projection))
        return module

    monkeypatch.setattr(importlib, "import_module", spying_import)
    runner = load_runner()
    gc.collect()
    gc.disable()
    try:
        count, _checks, _sha, failures, _lines, _digests = runner.run_product(folder)
        survivors = [deleted[id(o)][0] for o in gc.get_objects()
                     if id(o) in deleted and type(o) is deleted[id(o)][1]]
    finally:
        gc.enable()
    return count, failures, keys, survivors


def test_cleanup_frees_every_exported_itemspace_without_garbage_collection(tmp_path, monkeypatch):
    """With the collector off, no deleted point's item survives its ``del``: the runner broke
    the item's reference cycles first. Points 2 and 13 raise, so their release runs too."""
    raises = scratch_copy(tmp_path, "raises")
    edit_point(raises, 2, benefit_schedule_id="nosuch")
    edit_point(raises, 13, benefit_schedule_id="nosuch")
    count, failures, keys, survivors = run_without_garbage_collection(raises, monkeypatch)
    assert count == N_POINTS and len(failures) == 2
    assert keys == list(range(1, N_POINTS + 1))
    assert survivors == []


@pytest.mark.parametrize("product", load_runner().product_names())
def test_cleanup_frees_every_exported_itemspace_of_every_product(monkeypatch, product):
    folder = ROOT / "products" / product
    count, failures, keys, survivors = run_without_garbage_collection(folder, monkeypatch)
    assert failures == []
    assert keys == list(range(1, count + 1)) and count > 0
    assert survivors == []


def test_release_leaves_an_item_without_export_internals_alone():
    runner = load_runner()
    item = type("Item", (), {"_space": "kept", "_v_result_cf_columns": "kept"})()
    runner.release_item(item)
    assert item._space == "kept" and item._v_result_cf_columns == "kept"


def test_failing_export_is_one_failure_and_main_writes_nothing(tmp_path, monkeypatch, capsys):
    runner = load_runner()

    def boom(*args, **kwargs):
        raise RuntimeError("cannot export this model")

    monkeypatch.setattr(runner.mx, "export_model", boom)
    count, _checks, _sha, failures, lines, digests = runner.run_product(FOLDER)
    assert count == N_POINTS
    assert failures == ["export raised RuntimeError: cannot export this model"]
    assert lines == [] and digests == {}
    out = tmp_path / "out"
    assert runner.main([PRODUCT, "--write", "--out", str(out)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "engine: export"
    assert "checks: 1 failure(s)" in captured.out
    assert "FAILED export raised RuntimeError: cannot export this model" in captured.err
    assert "nothing written" in captured.err
    assert not out.exists()


def test_keep_lines_chooses_the_collected_lines_and_leaves_hash_and_digests_alone():
    runner = load_runner()
    baseline = BASELINE.read_bytes().decode("ascii").splitlines()
    _, _, sha_none, failures, lines_none, digests_none = runner.run_product(FOLDER, keep_lines=False)
    assert failures == [] and lines_none == []
    _, _, sha_three, failures, lines_three, digests_three = runner.run_product(FOLDER, keep_lines=3)
    assert failures == []
    assert lines_three == [baseline[0]] + [line for line in baseline[1:]
                                           if int(line.split(",", 1)[0]) <= 3]
    assert sha_none == sha_three
    assert digests_none == digests_three and sorted(digests_none) == list(range(1, N_POINTS + 1))
    assert len(set(digests_none.values())) == N_POINTS


def failed_lines(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.startswith("FAILED ")]


def test_workers_give_the_same_hash_and_bytes(runs):
    code, output, stderr = runs["write_w4"]
    assert code == 0, stderr
    assert output["workers"] == "4"
    assert output["sha256"] == runs["write_a"][1]["sha256"]
    assert (runs["out"] / "w4" / "result_cf.csv").read_bytes() == BASELINE.read_bytes()


def test_workers_give_the_same_failures_in_point_order(runs):
    code, output, stderr = runs["raises_w4"]
    assert code == 1
    assert failed_lines(stderr) == failed_lines(runs["raises"][2]) and failed_lines(stderr)
    assert output["sha256"] == runs["raises"][1]["sha256"]


@pytest.mark.parametrize("name, needle", [("workers_0", "--workers must be at least 1"),
                                          ("workers_mx", "--engine modelx"),
                                          ("workers_nc", "--no-cleanup")])
def test_bad_workers_give_usage_and_exit_2(runs, name, needle):
    code, output, stderr = runs[name]
    assert code == 2
    assert stderr.startswith("usage: run_baseline.py")
    assert needle in stderr
    assert output == {}


def test_failing_export_with_workers_is_the_same_one_failure(monkeypatch):
    runner = load_runner()

    def boom(*args, **kwargs):
        raise RuntimeError("cannot export this model")

    monkeypatch.setattr(runner.mx, "export_model", boom)
    count, _checks, sha, failures, lines, digests = runner.run_product(FOLDER, workers=4)
    assert (count, failures, lines, digests) == (
        N_POINTS, ["export raised RuntimeError: cannot export this model"], [], {})
    assert sha == runner.run_product(FOLDER)[2]


def test_a_worker_that_dies_is_one_failure_and_main_writes_nothing(tmp_path, monkeypatch, capsys):
    import os

    runner = load_runner()
    # The pool pickles its worker function by module name, so the module must be findable.
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    frame_bytes = runner.frame_bytes

    def dies_on_point_3(point_id, frame):
        if point_id == 3:
            os._exit(7)
        return frame_bytes(point_id, frame)

    monkeypatch.setattr(runner, "frame_bytes", dies_on_point_3)
    out = tmp_path / "out"
    assert runner.main([PRODUCT, "--workers", "4", "--write", "--out", str(out)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[:3] == ["engine: export", "cleanup: on", "workers: 4"]
    assert "checks: 1 failure(s)" in captured.out
    failed = failed_lines(captured.err)
    assert len(failed) == 1 and failed[0].startswith("FAILED worker crashed: BrokenProcessPool"), captured.err
    assert "nothing written" in captured.err
    assert not out.exists()
    assert not [k for k in sys.modules if k.startswith("_delib_export_")]
    assert not [p for p in sys.path if "delib-export-" in p]


def exported_sources(path: Path) -> dict[str, bytes]:
    return {str(p.relative_to(path)): p.read_bytes() for p in sorted(path.rglob("*.py"))}


def counting_export(runner, monkeypatch) -> list:
    """Count the calls of ``mx.export_model``: one for a parallel export that succeeded,
    two when it fell back to the serial export."""
    calls = []
    export = runner.mx.export_model

    def counted(*args, **kwargs):
        calls.append(args)
        return export(*args, **kwargs)

    monkeypatch.setattr(runner.mx, "export_model", counted)
    return calls


@pytest.mark.parametrize("product", load_runner().product_names())
def test_parallel_export_writes_the_same_package(tmp_path, monkeypatch, product):
    runner = load_runner()
    # The pool pickles its function by module name, so the module must be findable.
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    model = runner.mx.read_model(runner.model_dir(runner.PRODUCTS_DIR / product))
    try:
        runner.export_model(model, tmp_path / "serial", 1)
        calls = counting_export(runner, monkeypatch)
        runner.export_model(model, tmp_path / "parallel", 24)
    finally:
        model.close()
    assert len(calls) == 1  # the parallel path ran, no fallback
    serial = exported_sources(tmp_path / "serial")
    assert serial and exported_sources(tmp_path / "parallel") == serial


def originals(runner):
    from modelx.export import exporter
    return vars(exporter.SpaceTranslator)["class_defs"], exporter.FormulaTransformer


def test_one_worker_exports_without_replacing_class_defs(monkeypatch):
    runner = load_runner()
    from modelx.export import exporter
    class_defs, _ = originals(runner)
    seen = []
    export = runner.mx.export_model

    def watched(*args, **kwargs):
        seen.append(vars(exporter.SpaceTranslator)["class_defs"])
        return export(*args, **kwargs)

    monkeypatch.setattr(runner.mx, "export_model", watched)
    failures = runner.run_product(FOLDER, workers=1)[3]
    assert failures == [] and seen == [class_defs]


def test_parallel_export_restores_modelx_also_when_it_raises(tmp_path, monkeypatch):
    runner = load_runner()
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    before = originals(runner)
    model = runner.mx.read_model(runner.model_dir(FOLDER))
    try:
        runner.export_model(model, tmp_path / "ok", 4)
        assert originals(runner) == before

        def boom(*args, **kwargs):
            raise RuntimeError("cannot export this model")

        monkeypatch.setattr(runner.mx, "export_model", boom)
        with pytest.raises(RuntimeError, match="cannot export this model"):
            runner.export_model(model, tmp_path / "raises", 4)
        assert originals(runner) == before
    finally:
        model.close()


def test_a_transform_raising_in_a_child_falls_back_to_the_serial_export(tmp_path, monkeypatch,
                                                                         capsys):
    import os

    runner = load_runner()
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    from modelx.export import exporter
    transformer = exporter.FormulaTransformer
    parent = os.getpid()

    def raises_in_a_child(*args):
        if os.getpid() != parent:
            raise RuntimeError("transform failed in a child")
        return transformer(*args)

    model = runner.mx.read_model(runner.model_dir(FOLDER))
    try:
        runner.export_model(model, tmp_path / "serial", 1)
        runner.export_model(model, tmp_path / "parallel", 4)
        assert capsys.readouterr().err == ""  # a parallel export that succeeds prints nothing
        monkeypatch.setattr(exporter, "FormulaTransformer", raises_in_a_child)
        calls = counting_export(runner, monkeypatch)
        class_defs = vars(exporter.SpaceTranslator)["class_defs"]
        runner.export_model(model, tmp_path / "fallback", 4)
        assert exporter.FormulaTransformer is raises_in_a_child
        assert vars(exporter.SpaceTranslator)["class_defs"] is class_defs
    finally:
        model.close()
    assert len(calls) == 2  # the parallel export, then the serial one
    assert capsys.readouterr().err.splitlines() == [
        "parallel export raised RuntimeError: transform failed in a child; exporting serially"]
    assert exported_sources(tmp_path / "fallback") == exported_sources(tmp_path / "serial")
    _count, _checks, sha, failures, _lines, _digests = runner.run_product(FOLDER, workers=4)
    assert failures == [] and sha == runner.run_product(FOLDER)[2]


def no_pool(runner, monkeypatch) -> None:
    """Make any process pool raise, so an export that needs a transform fails loudly."""
    class NoPool:
        def __init__(self, *args, **kwargs):
            raise AssertionError("a transform ran although every piece was cached")

    monkeypatch.setattr(runner, "ProcessPoolExecutor", NoPool)


@pytest.mark.parametrize("product", load_runner().product_names())
def test_cached_export_writes_the_same_package_cold_and_warm(tmp_path, monkeypatch, product):
    runner = load_runner()
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    cache = tmp_path / "cache"
    model = runner.mx.read_model(runner.model_dir(runner.PRODUCTS_DIR / product))
    try:
        runner.export_model(model, tmp_path / "serial", 1)
        calls = counting_export(runner, monkeypatch)
        runner.export_model(model, tmp_path / "cold", 24, cache)
        assert len(calls) == 1  # the parallel path ran, no fallback
        assert any(cache.iterdir())
        no_pool(runner, monkeypatch)
        runner.export_model(model, tmp_path / "warm", 24, cache)
        assert len(calls) == 2
    finally:
        model.close()
    serial = exported_sources(tmp_path / "serial")
    assert serial and exported_sources(tmp_path / "cold") == serial
    assert exported_sources(tmp_path / "warm") == serial


def test_a_mutated_cell_misses_only_its_own_piece(tmp_path, monkeypatch):
    runner = load_runner()
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    cache = tmp_path / "cache"
    model = runner.mx.read_model(runner.model_dir(FOLDER))
    try:
        runner.export_model(model, tmp_path / "original", 24, cache)
        before = set(cache.iterdir())
        cell = model.Projection.cells["mort_rate_mth"]
        cell.formula = cell.formula.source.replace("1.0 / 12.0", "1.0 / 13.0")
        runner.export_model(model, tmp_path / "mutant_serial", 1)
        runner.export_model(model, tmp_path / "mutant", 24, cache)
    finally:
        model.close()
    assert len(set(cache.iterdir()) - before) == 1  # one new piece, every other one a hit
    assert exported_sources(tmp_path / "mutant") == exported_sources(tmp_path / "mutant_serial")
    assert exported_sources(tmp_path / "mutant") != exported_sources(tmp_path / "original")


def test_an_unreadable_cache_entry_is_a_miss(tmp_path, monkeypatch):
    runner = load_runner()
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    cache = tmp_path / "cache"
    model = runner.mx.read_model(runner.model_dir(FOLDER))
    try:
        runner.export_model(model, tmp_path / "serial", 1)
        runner.export_model(model, tmp_path / "cold", 24, cache)
        entries = sorted(cache.iterdir())
        entries[0].write_bytes(b"not a pickle")
        runner.export_model(model, tmp_path / "repaired", 24, cache)
    finally:
        model.close()
    assert exported_sources(tmp_path / "repaired") == exported_sources(tmp_path / "serial")
    assert sorted(cache.iterdir()) == entries
    runner._cache_get(cache, entries[0].name)  # rewritten: readable again
    assert runner._cache_get(cache, entries[0].name) is not None


@pytest.mark.parametrize("entry", [None, ("code",), ({}, "a", "b"), ("not a dict", "code"),
                                   ({}, b"bytes"), [{}, "code"]])
def test_a_cache_entry_of_the_wrong_shape_is_a_miss_and_rewritten(tmp_path, monkeypatch, entry):
    import pickle

    runner = load_runner()
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    cache = tmp_path / "cache"
    model = runner.mx.read_model(runner.model_dir(FOLDER))
    try:
        runner.export_model(model, tmp_path / "serial", 1)
        runner.export_model(model, tmp_path / "cold", 24, cache)
        entries = sorted(cache.iterdir())
        good = runner._cache_get(cache, entries[0].name)
        entries[0].write_bytes(pickle.dumps(entry))
        assert runner._cache_get(cache, entries[0].name) is None
        runner.export_model(model, tmp_path / "repaired", 24, cache)
    finally:
        model.close()
    assert exported_sources(tmp_path / "repaired") == exported_sources(tmp_path / "serial")
    assert sorted(cache.iterdir()) == entries
    assert runner._cache_get(cache, entries[0].name) == good


@pytest.mark.parametrize("fails", ["dump", "replace"])
def test_a_failed_cache_write_leaves_no_temporary_file(tmp_path, monkeypatch, fails):
    runner = load_runner()
    cache = tmp_path / "cache"

    def boom(*args, **kwargs):
        raise OSError("disk full")

    if fails == "dump":
        monkeypatch.setattr(runner.pickle, "dump", boom)
    else:
        monkeypatch.setattr(runner.os, "replace", boom)
    runner._cache_put(cache, "k" * 64, ({"f": None}, "code"))
    assert list(cache.iterdir()) == []


def test_run_product_with_a_transform_cache_gives_the_same_hash(tmp_path, monkeypatch):
    runner = load_runner()
    monkeypatch.setitem(sys.modules, "run_baseline", runner)
    sha = runner.run_product(FOLDER)[2]
    for _ in range(2):  # cold, then warm
        _count, _checks, cached, failures, _lines, _digests = runner.run_product(
            FOLDER, workers=4, transform_cache=tmp_path / "cache")
        assert failures == [] and cached == sha


def test_transform_cache_needs_workers(tmp_path, capsys):
    runner = load_runner()
    with pytest.raises(SystemExit) as exc:
        runner.main([PRODUCT, "--transform-cache", str(tmp_path)])
    assert exc.value.code == 2
    assert "--transform-cache needs --workers > 1" in capsys.readouterr().err


def test_the_cache_key_changes_with_every_input_and_ignores_set_order():
    runner = load_runner()
    job = ("def f():\n    return 1\n", {"f", "g"}, {"h"})
    key = runner._cache_key(job, "salt")
    assert runner._cache_key(("def f():\n    return 1\n", {"g", "f"}, {"h"}), "salt") == key
    assert runner._cache_key(("def f():\n    return 2\n", job[1], job[2]), "salt") != key
    assert runner._cache_key((job[0], {"f"}, job[2]), "salt") != key
    assert runner._cache_key((job[0], job[1], {"h", "i"}), "salt") != key
    assert runner._cache_key(job, "other salt") != key


def test_the_salt_names_the_installed_libcst(monkeypatch):
    import importlib.metadata

    from modelx.export import exporter

    runner = load_runner()
    version = importlib.metadata.version("libcst")
    salt = runner._transformer_salt(exporter)
    assert version in salt.split("|") and "?" not in salt.split("|")
    monkeypatch.setattr(importlib.metadata, "version",
                        lambda name: "0.0.0" if name == "libcst" else version)
    other = runner._transformer_salt(exporter)
    assert "0.0.0" in other.split("|") and other != salt
    job = ("x = 1\n", set(), set())
    assert runner._cache_key(job, other) != runner._cache_key(job, salt)


@pytest.fixture(scope="session")
def modelx_runs(tmp_path_factory):
    """Every product run by name with ``--engine modelx --write``, in parallel processes."""
    out = tmp_path_factory.mktemp("modelx_runs")
    processes = {
        product: subprocess.Popen(
            [sys.executable, str(RUNNER), product, "--engine", "modelx", "--write",
             "--out", str(out / product)],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for product in load_runner().product_names()}
    results = {}
    for product, process in processes.items():
        stdout, stderr = process.communicate(timeout=1800)
        results[product] = (process.returncode, parse_output(stdout), stderr)
    return out, results


@pytest.mark.parametrize("product", load_runner().product_names())
def test_the_modelx_engine_writes_every_products_baseline(modelx_runs, product):
    out, results = modelx_runs
    code, output, stderr = results[product]
    assert code == 0, stderr
    assert output["engine"] == "modelx" and output["checks"] == "all true"
    assert (out / product / "result_cf.csv").read_bytes() == (
        ROOT / "baseline" / product / "result_cf.csv").read_bytes()
