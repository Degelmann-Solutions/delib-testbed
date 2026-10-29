"""Run every shipped model point of one product and print one hash over the results.

    uv run python tools/run_baseline.py basisrente
    uv run python tools/run_baseline.py basisrente --write            # baseline/basisrente/
    uv run python tools/run_baseline.py path/to/scratch --write --out DIR
    uv run python tools/run_baseline.py basisrente --engine modelx     # phase-2b behaviour
    uv run python tools/run_baseline.py basisrente --engine modelx --no-cleanup  # phase 2a
    uv run python tools/run_baseline.py basisrente --workers 8          # eight worker processes

A bare name resolves to ``products/<name>``; anything with a path separator is used as
given, which is how the tests run scratch copies. The folder holds the model (the only
subfolder with a ``_system.json``) and its input CSVs side by side. The runner reads the
model with modelx, evaluates ``result_cf`` and the product's built-in checks for every
point of ``model_point_table.csv``, and prints the engine, the cleanup mode, the worker
count, the point count, the check cells, the SHA-256 and the wall time. The wall time is
measured from the start of this script, before modelx is imported, so it covers the
import, the export, the run, the checks and the hashing; it does not cover interpreter
start-up or ``uv run``. It only reads the product folder: no modelx writer writes into it
and it is left untouched.

Engines
-------
``--engine export`` (the default) reads the model with modelx, exports it with
``mx.export_model`` into a package in a temporary folder, imports that package and runs
the points and checks on the exported model, which computes the same formulas without
modelx's per-cell trace and dependency graph. The exported model's ``path`` is set to the
model folder, so the product's input tables are read from the product folder as under
modelx. The temporary folder, its entry on ``sys.path`` and the imported modules are
removed afterwards. With ``--workers`` > 1 the export transforms the formulas of the
top-level spaces in up to ``W`` forked processes, a large space's source cut between its
functions into pieces of about 12,000 characters, and assembles them with modelx's own code,
so the exported package is the same text as from ``mx.export_model`` alone (see "Workers").
An exception from the export or the import is the failure ``export raised ...``; no point
runs and there is no fallback to modelx.

``--engine modelx`` runs on the modelx model itself, as in phases 2a and 2b; it is the
traced engine, for tracing a contract and for reproducing those measurements. The results,
the hash and the written bytes are the same in both engines. The failure messages differ
in one way: under modelx a raising formula is wrapped in a ``FormulaError``, so a failure
reads ``result_cf raised FormulaError: KeyError: ...``; the exported model raises the plain
exception, ``result_cf raised KeyError: ...``. The first output line names the engine,
``engine: export`` or ``engine: modelx``.

Per-contract cleanup
--------------------
By default the runner deletes each point's ItemSpace (``del Projection[point_id]`` on the
model being run, the modelx or the exported one) once its ``result_cf`` bytes, its CSV
lines and all its checks have been read, also when the point raised, so the ItemSpaces of
earlier points do not accumulate. ``--no-cleanup`` keeps every ItemSpace alive until
``run_product`` returns, as in phase 2a. The second output
line names the mode, ``cleanup: on`` or ``cleanup: off``. The results, the hash and the
written bytes are the same in both modes; how cells are computed and traced is unchanged.

Workers
-------
``--workers W`` (default 1) splits the points of one run over ``W`` worker processes. The
parent reads and exports the model once, as above; for the export it runs modelx's formula
transform of each top-level space (``CoreData``, ``CoreProjection``, ``Data``,
``Projection``) in up to ``W`` processes forked for the export alone, and the exported code
is the same as at ``W`` = 1. If anything in that parallel export raises, the partial package
is removed and the export runs again serially, so a failing export fails as at ``W`` = 1.
The parent then forks the workers from the exported model, so each worker starts with it
already imported; each worker runs one point at a time, with cleanup, and sends back its
hash bytes, columns, CSV lines (only those the run keeps) and failures. The parent takes the results in ascending ``point_id`` order and does
what the single process does with them, so the hash, the written bytes and the failure
lines, in their order, are the same for every ``W``. If a worker dies (a crash, the
out-of-memory killer), the run has the single failure ``worker crashed: ...``: exit 1,
nothing written. ``W`` > 1 needs the export engine and per-contract cleanup; with
``--engine modelx`` or ``--no-cleanup`` it is a usage error. Every process runs with one
BLAS/OpenMP thread (``OPENBLAS_NUM_THREADS``, ``OMP_NUM_THREADS``, ``MKL_NUM_THREADS``
default to 1), also at ``W`` = 1. The third output line names the count, ``workers: W``.
The wall time is that of the whole run across all workers.

Transform cache
---------------
With ``--transform-cache DIR`` (``W`` > 1 only) the parallel export looks every piece of
formula source up in ``DIR`` before transforming it: one file per piece, named by the SHA-256
of the piece, its cell names and its cacheless names, salted with the modelx and libcst
versions and the hashes of modelx's ``exporter.py`` and ``transformer.py``. A hit is used
as the child's result would be; only the misses are transformed, in forked children, and
written to ``DIR`` (atomically, via a temporary file and ``os.replace``, so concurrent runs
can share it). The exported package is the same text with or without the cache
(``tests/test_runner.py``). A mutant changes the source of the piece holding the mutated cell,
so only that piece misses; the cache is never cleaned and grows by the pieces of every
mutant. Without the option nothing is cached.

Checks
------
The checks are the cells of the ``Projection`` space whose name starts with ``check_``,
that take no parameters and whose name does not end in ``_resid``. A ``check_*_resid`` cell
is the residual a check is built on, not a check, even when it takes no parameters. Every
check is expected to return true for every point.

Exit status: 0 if every point ran and every check is true; 1 if a point raised or a check
is false (each failure is printed on stderr with its point and check, and the other points
still run); 2 on a usage error.

Hash recipe
-----------
One SHA-256 over all ``result_cf`` frames, points in ascending ``point_id`` order. For
each point these bytes enter, in this order:

1. the line ``point_id=<id>``;
2. the line ``columns=<column names joined by commas>``;
3. the line ``shape=<rows>,<columns>``;
4. the index as little-endian 64-bit integers;
5. the values as little-endian 64-bit floats, row by row, at full precision.

Nothing is rounded, so any change in any value, row, column or point changes the hash.

Baseline file
-------------
With ``--write`` the runner writes ``result_cf.csv`` to ``--out`` (default
``baseline/<product>``; a path needs ``--out``), and only if every point ran and every check is true. The writer is
explicit: the header ``point_id,t,<result_cf columns>``, then one line per point and ``t``,
points ascending and rows in the frame's order, each value as ``repr(float(value))``, which
round-trips exactly (``-0.0`` and ``nan`` are written as ``repr`` gives them), and ``\\n``
line ends. Two runs give identical bytes. The runner collects the CSV lines only with
``--write``; without it the memory does not grow with the points run.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import multiprocessing
import pickle
import os
import shutil
import sys
import tempfile
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

_PROCESS_START = time.perf_counter()  # taken before the modelx import, which takes seconds

# One BLAS/OpenMP thread per process. The libraries read these when numpy loads, which is
# with modelx below; in a forked worker it is too late. Set for every W, so W = 1 runs alike.
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import modelx as mx  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
BASELINE_DIR = ROOT / "baseline"
CSV_NAME = "result_cf.csv"
ENGINES = ("export", "modelx")


class UsageError(Exception):
    pass


def frame_bytes(point_id: int, frame) -> bytes:
    """The bytes one ``result_cf`` frame contributes to the hash (see module docstring)."""
    header = (
        f"point_id={point_id}\n"
        f"columns={','.join(str(c) for c in frame.columns)}\n"
        f"shape={frame.shape[0]},{frame.shape[1]}\n"
    ).encode("utf-8")
    index = frame.index.to_numpy(dtype="<i8").tobytes()
    values = frame.to_numpy(dtype="<f8").tobytes(order="C")
    return header + index + values


def csv_lines(point_id: int, frame) -> list[str]:
    """The data lines one ``result_cf`` frame contributes to the baseline file."""
    index = frame.index.to_numpy(dtype="<i8")
    values = frame.to_numpy(dtype="<f8")
    return [",".join([str(point_id), str(int(t))] + [repr(float(v)) for v in row])
            for t, row in zip(index, values)]


def is_path(arg: str) -> bool:
    return "/" in arg or "\\" in arg or arg in (".", "..")


def resolve_product(arg: str) -> Path:
    """A bare name is a folder under ``products/``; a path is used as given."""
    if is_path(arg):
        folder = Path(arg).resolve()
    else:
        folder = PRODUCTS_DIR / arg
    if not folder.is_dir():
        raise UsageError(f"no product folder {arg!r} (products: {', '.join(product_names())})")
    return folder


def product_names() -> list[str]:
    return sorted(p.name for p in PRODUCTS_DIR.iterdir() if p.is_dir()) if PRODUCTS_DIR.is_dir() else []


def model_dir(folder: Path) -> Path:
    """The only subfolder of ``folder`` that holds a ``_system.json``."""
    models = sorted(p for p in folder.iterdir() if p.is_dir() and (p / "_system.json").is_file())
    if len(models) != 1:
        raise UsageError(f"expected exactly one model folder in {folder}, found {len(models)}")
    return models[0]


def check_names(model) -> list[str]:
    """The built-in checks of the Projection space (see module docstring)."""
    return sorted(name for name, cell in model.Projection.cells.items()
                  if name.startswith("check_") and not name.endswith("_resid")
                  and len(cell.parameters) == 0)


def describe(exc: Exception) -> str:
    """The exception, by name and one line of its message.

    A modelx ``FormulaError`` wraps the cause: its message starts with a fixed line and
    names the original exception on the second, before the formula traceback and source.
    """
    lines = [line.strip() for line in str(exc).strip().splitlines() if line.strip()]
    if type(exc).__name__ == "FormulaError" and len(lines) > 1:
        return f"FormulaError: {lines[1]}"
    return type(exc).__name__ + (f": {lines[0]}" if lines else "")


def point_digest(data: bytes) -> str:
    """The SHA-256 of a point's hash bytes without their first line ``point_id=<id>``.

    Without the id line, a point that repeats another point's inputs under another id has
    the same digest as the original.
    """
    return hashlib.sha256(data.split(b"\n", 1)[1]).hexdigest()


def keeps(keep_lines: bool | int, point_id: int) -> bool:
    """Whether ``run_product`` keeps the CSV lines of ``point_id`` (see ``run_product``)."""
    if isinstance(keep_lines, bool):
        return keep_lines
    return point_id <= keep_lines


def run_point(space_model, point_id: int, checks: list[str], keep_lines: bool | int,
              cleanup: bool) -> tuple[int, bytes | None, list[str] | None, list[str] | None, list[str]]:
    """Run one point. Return its id, hash bytes, columns, CSV lines and failures.

    The hash bytes and the columns are ``None`` when ``result_cf`` raised; the lines are
    ``None`` then and when ``keep_lines`` does not keep the point. The failures are those of
    ``result_cf`` and of the checks, in check order; the parent adds the columns check.
    """
    projection = space_model.Projection[point_id]
    failures: list[str] = []
    try:
        try:
            frame = projection.result_cf()
            data = frame_bytes(point_id, frame)
        except Exception as exc:
            failures.append(f"point {point_id}: result_cf raised {describe(exc)}")
            return point_id, None, None, None, failures
        columns = [str(c) for c in frame.columns]
        lines = csv_lines(point_id, frame) if keeps(keep_lines, point_id) else None
        for check in checks:
            try:
                passed = getattr(projection, check)()
            except Exception as exc:
                failures.append(f"point {point_id}: {check} raised {describe(exc)}")
                continue
            if not passed:
                failures.append(f"point {point_id}: {check} is false")
        return point_id, data, columns, lines, failures
    finally:
        if cleanup:
            del space_model.Projection[point_id]


class _TransformInputs(Exception):
    """Raised by the recorder in place of modelx's ``FormulaTransformer``; carries its
    arguments ``(source, cells, cacheless)``."""


class _Transformed:
    """Stands in for a ``FormulaTransformer`` whose result was computed in a child: the
    only two attributes ``SpaceTranslator._get_class_def`` reads."""

    def __init__(self, func_attrs, code: str):
        self.func_attrs = func_attrs
        self.transformed = type("_Module", (), {"code": code})()


# modelx's FormulaTransformer the forked children run; set while the parallel class_defs
# runs its pool.
_TRANSFORMER = None


def _transform(inputs: tuple):
    """Run modelx's ``FormulaTransformer`` on one space's inputs (in a forked child)."""
    trans = _TRANSFORMER(*inputs)
    return trans.func_attrs, trans.transformed.code


# A space's formula source is cut into pieces of about this many characters, each piece
# transformed in its own child (see _chunks).
_CHUNK_CHARS = 12000


def _chunks(source: str) -> list[str]:
    """``source`` cut between its top-level functions into pieces of about ``_CHUNK_CHARS``.

    Each piece repeats the statements before the first function (the exporter's dummy
    reference assignments), so every piece binds the same module-level names; the pieces'
    transformed code joined with ``"\n"`` is the whole source's (checked against the serial
    export in tests/test_runner.py). A source that is short, has no function or has a
    statement between its functions is one piece.
    """
    if len(source) <= _CHUNK_CHARS:
        return [source]
    body = ast.parse(source).body
    funcs = [n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not funcs or any(not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and n.lineno > funcs[0].lineno for n in body):
        return [source]
    lines = source.split("\n")
    starts = [f.lineno - 1 - len(f.decorator_list) for f in funcs]
    header = "\n".join(lines[:starts[0]])
    pieces, begin = [], starts[0]
    for start in starts[1:] + [len(lines)]:
        if len("\n".join(lines[begin:start])) >= _CHUNK_CHARS or start == len(lines):
            pieces.append(header + "\n" + "\n".join(lines[begin:start]))
            begin = start
    return pieces


def _cache_key(job: tuple, salt: str) -> str:
    """The cache file name of one transform job: SHA-256 over ``salt`` and the job's inputs.

    ``job`` is ``(source, cells, cacheless)``; the sets enter sorted. ``salt`` names the
    transformer (``_transformer_salt``), so another modelx or libcst never reads an entry.
    """
    source, cells, cacheless = job
    digest = hashlib.sha256()
    for part in (salt, source, "\0".join(sorted(cells)), "\0".join(sorted(cacheless))):
        digest.update(part.encode("utf-8"))
        digest.update(b"\1")
    return digest.hexdigest()


def _transformer_salt(exporter) -> str:
    """The versions and the source of modelx's transformer the cached results depend on."""
    import libcst
    import modelx.export.transformer as transformer_module
    return "|".join([mx.__version__, getattr(libcst, "__version__", "?"),
                     hashlib.sha256(Path(transformer_module.__file__).read_bytes()).hexdigest(),
                     hashlib.sha256(Path(exporter.__file__).read_bytes()).hexdigest()])


def _cache_get(cache: Path, key: str):
    """The cached ``(func_attrs, code)`` of ``key``, or ``None`` (missing or unreadable)."""
    try:
        with open(cache / key, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def _cache_put(cache: Path, key: str, result) -> None:
    """Store ``result`` under ``key`` atomically; a failure to write is ignored."""
    try:
        cache.mkdir(parents=True, exist_ok=True)
        tmp = cache / f".{key}.{os.getpid()}.tmp"
        with open(tmp, "wb") as f:
            pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, cache / key)
    except Exception:
        pass


def _modelx_exporter():
    """modelx's exporter module, or ``None`` if the internals the parallel export uses are
    missing (then the export runs serially)."""
    try:
        from modelx.export import exporter
    except ImportError:
        return None
    translator = getattr(exporter, "SpaceTranslator", None)
    if (translator is None or not hasattr(translator, "_get_class_def")
            or "class_defs" not in vars(translator)
            or getattr(exporter, "FormulaTransformer", None) is None):
        return None
    return exporter


def _parallel_class_defs(exporter, original, workers: int, cache: Path | None = None):
    """A ``SpaceTranslator.class_defs`` that runs the child spaces' ``FormulaTransformer``
    in up to ``workers`` forked processes and assembles the class definitions with modelx's
    own ``_get_class_def``, so the code is that of ``original``."""
    transformer = exporter.FormulaTransformer

    def class_defs(self):
        global _TRANSFORMER
        spaces = list(self.parent.spaces.values())
        if len(spaces) < 2:
            return original.__get__(self, type(self))

        def record(*args):
            raise _TransformInputs(args)

        # Pass 1: the inputs of every child's transform. The code before the transform
        # has no side effects; the recorder stops _get_class_def there.
        inputs = []
        exporter.FormulaTransformer = record
        try:
            for space in spaces:
                try:
                    self._get_class_def(space)
                except _TransformInputs as stop:
                    inputs.append(stop.args[0])
                else:
                    raise RuntimeError(f"no transform recorded for {space.fullname}")
        finally:
            exporter.FormulaTransformer = transformer

        # The transforms, in forked children, each space's source cut into pieces.
        jobs, owner = [], []
        for i, (source, cells, cacheless) in enumerate(inputs):
            for piece in _chunks(source):
                jobs.append((piece, cells, cacheless))
                owner.append(i)
        done: list = [None] * len(jobs)
        keys = None
        if cache is not None:
            salt = _transformer_salt(exporter)
            keys = [_cache_key(job, salt) for job in jobs]
            done = [_cache_get(cache, key) for key in keys]
        missing = [i for i, result in enumerate(done) if result is None]
        if missing:
            _TRANSFORMER = transformer
            try:
                with ProcessPoolExecutor(max_workers=min(workers, len(missing)),
                                         mp_context=multiprocessing.get_context("fork")) as pool:
                    for i, result in zip(missing, pool.map(_transform, [jobs[i] for i in missing])):
                        done[i] = result
                        if keys is not None:
                            _cache_put(cache, keys[i], result)
            finally:
                _TRANSFORMER = None
        merged = [({}, []) for _ in inputs]
        for i, (func_attrs, code) in zip(owner, done):
            merged[i][0].update(func_attrs)
            merged[i][1].append(code)
        results = [(func_attrs, "\n".join(codes)) for func_attrs, codes in merged]

        # Pass 2: _get_class_def per space, in order, on the children's results.
        pending = iter(zip(inputs, results))

        def replay(*args):
            recorded, (func_attrs, code) = next(pending)
            if args != recorded:
                raise RuntimeError("transform inputs changed between the two passes")
            return _Transformed(func_attrs, code)

        exporter.FormulaTransformer = replay
        try:
            return "\n".join(self._get_class_def(space) for space in spaces)
        finally:
            exporter.FormulaTransformer = transformer

    return property(class_defs)


def export_model(model, path: Path, workers: int = 1, cache: Path | None = None) -> None:
    """Export ``model`` into ``path`` with modelx's exporter.

    At ``workers`` = 1 this is modelx's export as it stands. With ``workers`` > 1 the
    top-level spaces' formulas are transformed in up to ``workers`` forked processes (see
    module docstring, "Workers"); the exported code is the same. If anything in the
    parallel path raises, the partial output is removed and the export runs again serially,
    so a failing export raises what the serial one raises.

    ``cache`` (``W`` > 1 only) is a folder of transformed pieces keyed by their input (see
    module docstring, "Transform cache"); ``None`` transforms every piece.
    """
    exporter = _modelx_exporter() if workers > 1 else None
    if exporter is None:
        mx.export_model(model, path)
        return
    translator = exporter.SpaceTranslator
    original = vars(translator)["class_defs"]
    transformer = exporter.FormulaTransformer
    translator.class_defs = _parallel_class_defs(exporter, original, workers, cache)
    try:
        mx.export_model(model, path)
        return
    except Exception:
        pass
    finally:
        translator.class_defs = original
        exporter.FormulaTransformer = transformer
    shutil.rmtree(path, ignore_errors=True)
    mx.export_model(model, path)


# The state a forked worker runs its points on: the exported model, the checks, keep_lines,
# cleanup and whether to report Pss. Set in the parent before the workers fork, cleared when
# the pool is done.
_WORKER_STATE: tuple | None = None


def pss_kib() -> int:
    """This process's proportional set size in KiB, from ``/proc/self/smaps_rollup``."""
    with open("/proc/self/smaps_rollup") as f:
        for line in f:
            if line.startswith("Pss:"):
                return int(line.split()[1])
    raise RuntimeError("no Pss line in /proc/self/smaps_rollup")


def worker_point(point_id: int):
    """``run_point`` on the state inherited from the parent (module-level, so it pickles).

    Returns the point's result, the worker's pid and, if asked for, its Pss in KiB after
    the point (else ``None``).
    """
    space_model, checks, keep_lines, cleanup, report_pss = _WORKER_STATE
    result = run_point(space_model, point_id, checks, keep_lines, cleanup)
    return result, os.getpid(), pss_kib() if report_pss else None


def run_product(folder: Path, cleanup: bool = True, engine: str = "export",
                keep_lines: bool | int = True, workers: int = 1,
                worker_pss: dict[int, int] | None = None,
                transform_cache: Path | None = None,
                ) -> tuple[int, list[str], str, list[str], list[str], dict[int, str]]:
    """Run all points. Return the point count, the checks, the SHA-256, the failures, the CSV
    lines and the per-point digests.

    With ``cleanup`` (the default) each point's ItemSpace is deleted once its ``result_cf``
    and checks have been read, also when the point raised. ``engine`` is ``export`` (the
    default) or ``modelx`` (see module docstring).

    ``keep_lines`` chooses which points' CSV lines are collected: ``True`` (the default)
    every point's, ``False`` none, an integer ``n`` those of the ids ``1 … n``. The header
    line comes first whenever any point's lines may be kept. Collecting every point's lines
    makes the memory grow with the points run, so ``main`` keeps them only for ``--write``.
    The digests map every point whose ``result_cf`` was read to ``point_digest`` of its hash
    bytes; a point whose ``result_cf`` raised has neither lines nor a digest. The overall
    SHA-256 does not depend on ``keep_lines``.

    ``workers`` > 1 runs the points in that many forked worker processes (see module
    docstring, "Workers"); it needs the export engine and cleanup. Given a dict as
    ``worker_pss``, each worker reads its Pss (``/proc/self/smaps_rollup``) after every
    point and the dict is filled with the largest Pss in KiB per worker pid; it stays empty
    at ``workers`` = 1. This is for the measuring tool.
    """
    global _WORKER_STATE
    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r} (engines: {', '.join(ENGINES)})")
    if workers < 1:
        raise ValueError(f"workers must be at least 1: {workers}")
    if workers > 1 and (engine != "export" or not cleanup):
        raise ValueError("workers > 1 needs the export engine and cleanup")
    model = mx.read_model(model_dir(folder))
    pkg = None
    try:
        checks = check_names(model)
        point_ids = sorted(int(i) for i in model.Data.model_point_table().index)
        digest = hashlib.sha256()
        failures: list[str] = []
        columns = None
        lines: list[str] = []
        digests: dict[int, str] = {}
        with tempfile.TemporaryDirectory(prefix="delib-export-") as tmp:
            if engine == "export":
                pkg = f"_delib_export_{uuid.uuid4().hex}"
                try:
                    export_model(model, Path(tmp) / pkg, workers, transform_cache)
                    model.close()
                    model = None
                    sys.path.insert(0, tmp)
                    space_model = importlib.import_module(pkg).mx_model
                    # Data.input_dir() is _model.path.parent: point it at the product folder.
                    space_model.path = model_dir(folder)
                except Exception as exc:
                    failures.append(f"export raised {describe(exc)}")
                    return len(point_ids), checks, digest.hexdigest(), failures, lines, digests
            else:
                space_model = model

            def replay(result) -> None:
                """Today's loop body on one point's result, in ascending point order."""
                nonlocal columns
                point_id, data, point_columns, point_lines, point_failures = result
                if data is None:
                    failures.extend(point_failures)
                    return
                digest.update(data)
                digests[point_id] = point_digest(data)
                if columns is None:
                    columns = point_columns
                    if keep_lines is not False:
                        lines.append(",".join(["point_id", "t"] + columns))
                if point_columns != columns:
                    failures.append(f"point {point_id}: result_cf has other columns than point {point_ids[0]}")
                elif point_lines is not None:
                    lines.extend(point_lines)
                failures.extend(point_failures)

            if workers == 1:
                for point_id in point_ids:
                    replay(run_point(space_model, point_id, checks, keep_lines, cleanup))
                return len(point_ids), checks, digest.hexdigest(), failures, lines, digests
            _WORKER_STATE = (space_model, checks, keep_lines, cleanup, worker_pss is not None)
            try:
                with ProcessPoolExecutor(max_workers=workers,
                                         mp_context=multiprocessing.get_context("fork")) as pool:
                    for result, pid, pss in pool.map(worker_point, point_ids):
                        replay(result)
                        if worker_pss is not None:
                            worker_pss[pid] = max(worker_pss.get(pid, 0), pss)
            except BrokenProcessPool as exc:
                return len(point_ids), checks, digest.hexdigest(), [f"worker crashed: {describe(exc)}"], [], {}
            finally:
                _WORKER_STATE = None
            return len(point_ids), checks, digest.hexdigest(), failures, lines, digests
    finally:
        if pkg is not None:
            while tmp in sys.path:
                sys.path.remove(tmp)
            for name in [k for k in sys.modules if k == pkg or k.startswith(pkg + ".")]:
                del sys.modules[name]
        if model is not None:
            model.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_baseline.py",
        description="Run every shipped model point of one product and hash the results.")
    parser.add_argument("product", help="a product name under products/, or a path to a product folder")
    parser.add_argument("--write", action="store_true", help=f"write {CSV_NAME} to --out")
    parser.add_argument("--out", type=Path, help="output folder for --write (default baseline/<product>)")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="keep every point's ItemSpace alive until the end (phase-2a behaviour)")
    parser.add_argument("--engine", choices=ENGINES, default="export",
                        help="export: run on the model exported by mx.export_model (default); "
                             "modelx: run on the traced modelx model (phases 2a and 2b)")
    parser.add_argument("--workers", type=int, default=1, metavar="W",
                        help="run the points in W forked worker processes (default 1)")
    parser.add_argument("--transform-cache", type=Path, metavar="DIR",
                        help="with --workers > 1: reuse transformed formula pieces from DIR "
                             "and store new ones there (see 'Transform cache')")
    args = parser.parse_args(argv)
    if args.out is not None and not args.write:
        parser.error("--out needs --write")
    if args.workers < 1:
        parser.error(f"--workers must be at least 1: {args.workers}")
    if args.workers > 1 and args.engine == "modelx":
        parser.error("--workers > 1 needs the export engine, not --engine modelx")
    if args.workers > 1 and args.no_cleanup:
        parser.error("--workers > 1 needs per-contract cleanup, not --no-cleanup")
    if args.transform_cache is not None and args.workers < 2:
        parser.error("--transform-cache needs --workers > 1")
    if args.write and args.out is None and is_path(args.product):
        parser.error("--write with a path needs --out; only a product name writes to baseline/")
    try:
        folder = resolve_product(args.product)
        model_dir(folder)
    except UsageError as exc:
        parser.print_usage(sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cleanup = not args.no_cleanup
    count, checks, sha256, failures, lines, _digests = run_product(
        folder, cleanup=cleanup, engine=args.engine, keep_lines=args.write, workers=args.workers,
        transform_cache=args.transform_cache)
    elapsed = time.perf_counter() - _PROCESS_START
    print(f"engine: {args.engine}")
    print(f"cleanup: {'on' if cleanup else 'off'}")
    print(f"workers: {args.workers}")
    print(f"model points: {count}")
    print(f"check cells: {','.join(checks)}")
    print(f"sha256: {sha256}")
    print(f"wall time: {elapsed:.1f} s")
    if failures:
        for failure in failures:
            print(f"FAILED {failure}", file=sys.stderr)
        print(f"checks: {len(failures)} failure(s)")
        if args.write:
            print("nothing written", file=sys.stderr)
        return 1
    print("checks: all true")
    if args.write:
        out = args.out if args.out is not None else BASELINE_DIR / folder.name
        out.mkdir(parents=True, exist_ok=True)
        target = out / CSV_NAME
        target.write_bytes(("\n".join(lines) + "\n").encode("ascii"))
        print(f"written: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
