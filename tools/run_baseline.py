"""Run every shipped model point of one product and print one hash over the results.

    uv run python tools/run_baseline.py basisrente
    uv run python tools/run_baseline.py basisrente --write            # baseline/basisrente/
    uv run python tools/run_baseline.py path/to/scratch --write --out DIR
    uv run python tools/run_baseline.py basisrente --no-cleanup        # phase-2a behaviour

A bare name resolves to ``products/<name>``; anything with a path separator is used as
given, which is how the tests run scratch copies. The folder holds the model (the only
subfolder with a ``_system.json``) and its input CSVs side by side. The runner reads the
model with modelx, evaluates ``result_cf`` and the product's built-in checks for every
point of ``model_point_table.csv``, and prints the cleanup mode, the point count, the
check cells, the SHA-256 and the wall time. The wall time is measured from the start of
this script, before modelx is imported, so it covers the import, the run, the checks and the hashing; it does
not cover interpreter start-up or ``uv run``. It only reads: no modelx writer is called and
the product folder is left untouched.

Per-contract cleanup
--------------------
By default the runner deletes each point's ItemSpace (``del model.Projection[point_id]``)
once its ``result_cf`` bytes, its CSV lines and all its checks have been read, also when
the point raised, so the ItemSpaces of earlier points do not accumulate. ``--no-cleanup``
keeps every ItemSpace alive until the model is closed, as in phase 2a. The first output
line names the mode, ``cleanup: on`` or ``cleanup: off``. The results, the hash and the
written bytes are the same in both modes; how cells are computed and traced is unchanged.

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
line ends. Two runs give identical bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

_PROCESS_START = time.perf_counter()  # taken before the modelx import, which takes seconds

import modelx as mx  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
BASELINE_DIR = ROOT / "baseline"
CSV_NAME = "result_cf.csv"


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


def run_product(folder: Path, cleanup: bool = True) -> tuple[int, list[str], str, list[str], list[str]]:
    """Run all points. Return the point count, the checks, the SHA-256, the failures and the CSV.

    With ``cleanup`` (the default) each point's ItemSpace is deleted once its ``result_cf``
    and checks have been read, also when the point raised (see module docstring).
    """
    model = mx.read_model(model_dir(folder))
    try:
        checks = check_names(model)
        point_ids = sorted(int(i) for i in model.Data.model_point_table().index)
        digest = hashlib.sha256()
        failures: list[str] = []
        columns = None
        lines: list[str] = []
        for point_id in point_ids:
            projection = model.Projection[point_id]
            try:
                try:
                    frame = projection.result_cf()
                    data = frame_bytes(point_id, frame)
                except Exception as exc:
                    failures.append(f"point {point_id}: result_cf raised {describe(exc)}")
                    continue
                digest.update(data)
                if columns is None:
                    columns = [str(c) for c in frame.columns]
                    lines.append(",".join(["point_id", "t"] + columns))
                if [str(c) for c in frame.columns] != columns:
                    failures.append(f"point {point_id}: result_cf has other columns than point {point_ids[0]}")
                else:
                    lines.extend(csv_lines(point_id, frame))
                for check in checks:
                    try:
                        passed = getattr(projection, check)()
                    except Exception as exc:
                        failures.append(f"point {point_id}: {check} raised {describe(exc)}")
                        continue
                    if not passed:
                        failures.append(f"point {point_id}: {check} is false")
            finally:
                if cleanup:
                    del model.Projection[point_id]
        return len(point_ids), checks, digest.hexdigest(), failures, lines
    finally:
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
    args = parser.parse_args(argv)
    if args.out is not None and not args.write:
        parser.error("--out needs --write")
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
    count, checks, sha256, failures, lines = run_product(folder, cleanup=cleanup)
    elapsed = time.perf_counter() - _PROCESS_START
    print(f"cleanup: {'on' if cleanup else 'off'}")
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
