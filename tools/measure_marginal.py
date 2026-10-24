"""Measure the marginal time per contract of one or more products.

    uv run python tools/measure_marginal.py risikolebensversicherung
    uv run python tools/measure_marginal.py --all --json /tmp/phase2c.json
    uv run python tools/measure_marginal.py basisrente --factor 3 --repeats 5 --pool 20000
    uv run python tools/measure_marginal.py --all --engine modelx                # phase 2b
    uv run python tools/measure_marginal.py --all --engine modelx --no-cleanup   # phase 2a

What is measured
----------------
``run_product`` of ``tools/run_baseline.py`` as it stands: ``read_model``, the export (in
the export engine), ``result_cf``, every built-in check and the hashing, for every point.
``--engine`` passes the runner's engine through: ``export`` (the default) runs on the
exported model, ``modelx`` on the traced modelx model. By default the runner deletes each
point's ItemSpace after reading it (per-contract cleanup); ``--no-cleanup`` passes the
runner's switch through. Reproducing phase 2a needs ``--engine modelx --no-cleanup``,
phase 2b ``--engine modelx``. The header line above the table and the JSON (``engine``,
``cleanup``) state the modes. Each product runs at two sizes, in
two temporary scratch copies of its folder under one temp root: one with the shipped ``n``
model points, one with ``K·n`` points whose ids ``n+1 … K·n`` repeat the rows of ids
``1 … n`` in order. The product folder itself is only read.

Every (size, repeat) runs in its own fresh child process (this script with ``--child``),
one after another, never in parallel, sizes alternating: n, K·n, n, K·n, … The child times
``import run_baseline`` (which imports modelx) and ``run_product`` separately and reports
its peak RSS. With ``T`` the median ``run_product`` time of a size::

    t_marginal   = (T(K·n) − T(n)) / ((K − 1)·n)
    fixed        = import + T(n) − n·t_marginal          (import: median over all runs)
    MB/contract  = (RSS(K·n) − RSS(n)) / ((K − 1)·n)      (medians of the peak RSS)

Two sizes give the slope; that time per contract is constant in n is assumed, not tested.

Verification
------------
Every run is checked by the parent, and a failed check is an error (exit 1, no slope):
no point failed and every id is present; every replicated point's ``result_cf`` equals
that of its original exactly; the first ``n`` points reproduce
``baseline/<product>/result_cf.csv`` byte for byte. The child asks the runner for the CSV
lines of the ids ``1 … n`` only, and for a digest of every point's hash bytes without the
``point_id`` line (``point_digest`` in the runner); replicas are compared with their
originals by digest. So the child's memory does not grow with collected lines.

Forecast
--------
Per product, under stated assumptions (``--mutants``, ``--pool``, ``--workers``; slope
from the shipped point mix): ``M·P·t_marginal/W`` in hours against the 10 h night, and
``M·(fixed + P·t_marginal)/W``, since every mutant pays its own import and ``read_model``.
Both are linear extrapolations without trace pruning, and forecasts: mutants exist only
after phase 4. The memory line extrapolates ``MB/contract × P`` for one process and warns
when it exceeds the machine's total RAM; the warning does not change the exit status.

Exit status: 0 if every product is ``ok``; 1 if a product failed a check, its child
crashed or its slope is not positive (``unreliable``); 2 on a usage error. With several
products every product is measured and the worst status is returned.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
BASELINE_DIR = ROOT / "baseline"
THIS = Path(__file__).resolve()
TABLE = "model_point_table.csv"
NIGHT_HOURS = 10.0


class UsageError(Exception):
    pass


class VerificationError(Exception):
    pass


# --------------------------------------------------------------------------- pure helpers

def product_names() -> list[str]:
    return sorted(p.name for p in PRODUCTS_DIR.iterdir() if p.is_dir()) if PRODUCTS_DIR.is_dir() else []


def replicate_table(text: str, factor: int) -> str:
    """The model point table with ``factor·n`` rows: ids ``n+1 …`` repeat ids ``1 … n`` in order.

    Only the leading ``point_id`` field of a row changes; the rest of each row is kept as
    text. The shipped ids must be ``1 … n`` in this order.
    """
    if factor < 1:
        raise ValueError("factor must be at least 1")
    lines = text.split("\n")
    trailing = lines[-1] == ""
    if trailing:
        lines = lines[:-1]
    header, rows = lines[0], lines[1:]
    if header.split(",", 1)[0] != "point_id":
        raise ValueError(f"first column is not point_id: {header[:40]!r}")
    rests = []
    for expected, row in enumerate(rows, start=1):
        pid, sep, rest = row.partition(",")
        if pid != str(expected) or not sep:
            raise ValueError(f"row {expected} has point_id {pid!r}, expected {expected}")
        rests.append(rest)
    n = len(rests)
    out = [header]
    for k in range(factor):
        out.extend(f"{k * n + i},{rest}" for i, rest in enumerate(rests, start=1))
    return "\n".join(out) + ("\n" if trailing else "")


def count_points(text: str) -> int:
    return len([line for line in text.split("\n")[1:] if line])


def original_of(point_id: int, n: int) -> int:
    return (point_id - 1) % n + 1


def verify_run(result: dict, size: int, n: int, baseline: bytes) -> list[str]:
    """The failed checks of one child run, empty if it verifies (see module docstring)."""
    problems = [f"run_product failure: {f}" for f in result["failures"]]
    points = {int(k): v for k, v in result["points"].items()}
    digests = {int(k): v for k, v in result["digests"].items()}
    if result["n"] != size:
        problems.append(f"{result['n']} points run, expected {size}")
    missing = sorted(set(range(1, size + 1)) - set(digests))
    extra = sorted(set(digests) - set(range(1, size + 1)))
    if missing:
        problems.append(f"points missing from result_cf: {', '.join(map(str, missing))}")
    if extra:
        problems.append(f"unexpected points in result_cf: {', '.join(map(str, extra))}")
    for pid in range(n + 1, size + 1):
        orig = original_of(pid, n)
        if pid in digests and orig in digests and digests[pid] != digests[orig]:
            problems.append(f"point {pid}: result_cf differs from its original, point {orig}")
    if all(pid in points for pid in range(1, n + 1)):
        csv = baseline_text(result["header"], points, n)
        if csv.encode("ascii") != baseline:
            problems.append(f"points 1-{n} do not reproduce the baseline result_cf.csv byte for byte")
    return problems


def baseline_text(header: str, points: dict[int, list[str]], n: int) -> str:
    lines = [header] + [f"{pid},{rest}" for pid in range(1, n + 1) for rest in points[pid]]
    return "\n".join(lines) + "\n"


def derive(n: int, factor: int, import_s: float, t_n: float, t_kn: float,
           rss_n_kib: float, rss_kn_kib: float) -> dict:
    """Slope, fixed cost and memory per contract; ``unreliable`` if the slope is not positive."""
    extra = (factor - 1) * n
    t_marginal = (t_kn - t_n) / extra
    mb_per_contract = (rss_kn_kib - rss_n_kib) / 1024 / extra
    if t_marginal <= 0:
        return {"status": "unreliable", "t_marginal_s": t_marginal, "fixed_s": None,
                "mb_per_contract": mb_per_contract}
    return {"status": "ok", "t_marginal_s": t_marginal,
            "fixed_s": import_s + t_n - n * t_marginal, "mb_per_contract": mb_per_contract}


def forecast(t_marginal_s: float, fixed_s: float, mb_per_contract: float,
             mutants: int, pool: int, workers: int, total_ram_mb: float) -> dict:
    hours = mutants * pool * t_marginal_s / workers / 3600
    hours_fixed = mutants * (fixed_s + pool * t_marginal_s) / workers / 3600
    ram_mb = mb_per_contract * pool
    return {"mutants": mutants, "pool": pool, "workers": workers,
            "hours": hours, "fits_night": hours <= NIGHT_HOURS,
            "hours_with_fixed": hours_fixed,
            "ram_mb_per_process": ram_mb, "total_ram_mb": total_ram_mb,
            "ram_warning": ram_mb > total_ram_mb}


def forecast_lines(product: str, fc: dict) -> list[str]:
    m, p, w = fc["mutants"], fc["pool"], fc["workers"]
    verdict = "fits" if fc["fits_night"] else "does not fit"
    lines = [
        f"{product}: M·P·t_marginal/W = {m:,}·{p:,}·t/{w} = {fc['hours']:.1f} h "
        f"({verdict} the {NIGHT_HOURS:.0f} h night)",
        f"{product}: with fixed cost per mutant, M·(fixed + P·t_marginal)/W = "
        f"{fc['hours_with_fixed']:.1f} h",
        f"{product}: memory, MB/contract × P = {fc['ram_mb_per_process'] / 1024:.1f} GB in one process",
    ]
    if fc["ram_warning"]:
        lines.append(f"WARNING {product}: {fc['ram_mb_per_process'] / 1024:.1f} GB exceeds the "
                     f"machine's total RAM of {fc['total_ram_mb'] / 1024:.1f} GB")
    return lines


def assumption_lines(mutants: int, pool: int, workers: int, factor: int) -> list[str]:
    return [
        f"Assumptions: M = {mutants:,} mutants, P = {pool:,} contracts, W = {workers} worker(s);",
        "  slope from each product's shipped point mix; two sizes (n and "
        f"{factor}·n), so linearity is assumed, not tested.",
        "  A linear extrapolation without trace pruning, and a forecast: mutants exist only "
        "after phase 4.",
    ]


def total_ram_mb() -> float:
    return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 / 1024


# --------------------------------------------------------------------------- child

def child(folder: Path, originals: int, cleanup: bool = True, engine: str = "export") -> int:
    """Run ``run_product`` once and print the measurement as JSON on the last stdout line."""
    import resource

    start = time.perf_counter()
    import run_baseline  # noqa: E402  (script mode: tools/ is on sys.path; imports modelx)
    import_s = time.perf_counter() - start
    start = time.perf_counter()
    count, _checks, _sha, failures, lines, digests = run_baseline.run_product(
        folder, cleanup=cleanup, engine=engine, keep_lines=originals)
    run_s = time.perf_counter() - start
    maxrss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    points: dict[str, list[str]] = {}
    for line in lines[1:]:
        pid, _, rest = line.partition(",")
        points.setdefault(pid, []).append(rest)
    print(json.dumps({"n": count, "originals": originals, "import_s": import_s,
                      "run_s": run_s, "maxrss_kib": maxrss_kib, "failures": failures,
                      "header": lines[0] if lines else "", "points": points,
                      "digests": {str(k): v for k, v in digests.items()}}))
    return 0


def run_child(folder: Path, originals: int, cleanup: bool, engine: str = "export") -> dict:
    """One fresh child process; raises ``VerificationError`` on a crash or missing JSON."""
    command = [sys.executable, str(THIS), "--child", str(folder), "--originals", str(originals),
               "--engine", engine]
    if not cleanup:
        command.append("--no-cleanup")
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    tail = "\n".join(proc.stderr.strip().splitlines()[-5:])
    if proc.returncode != 0:
        raise VerificationError(f"child exited {proc.returncode}; stderr tail:\n{tail}")
    out = proc.stdout.strip().splitlines()
    try:
        result = json.loads(out[-1])
    except (IndexError, json.JSONDecodeError):
        raise VerificationError(f"child printed no JSON; stderr tail:\n{tail}") from None
    return result


# --------------------------------------------------------------------------- parent

def measure(product: str, args, ram_mb: float) -> dict:
    """Measure one product. The returned record has ``status`` ok, unreliable or failed."""
    factor, repeats, cleanup, engine = args.factor, args.repeats, not args.no_cleanup, args.engine
    record: dict = {"product": product, "factor": factor, "repeats": repeats,
                    "runs": [], "errors": [], "status": "failed"}

    def fail(message: str) -> dict:
        record["errors"].append(message)
        print(f"FAILED {product}: {message}", file=sys.stderr)
        return record

    source = PRODUCTS_DIR / product
    baseline = (BASELINE_DIR / product / "result_cf.csv").read_bytes()
    table = (source / TABLE).read_bytes().decode("ascii")
    n = count_points(table)
    size_kn = factor * n
    record.update(n=n, size_kn=size_kn)
    with tempfile.TemporaryDirectory(prefix=f"measure-{product}-") as tmp:
        root = Path(tmp)
        folder_n = root / "n" / product
        shutil.copytree(source, folder_n)
        if args.prepared is not None:
            folder_kn = args.prepared
            got = count_points((folder_kn / TABLE).read_bytes().decode("ascii"))
            if got != size_kn:
                return fail(f"--prepared folder has {got} points, expected {factor}·{n} = {size_kn}")
        else:
            folder_kn = root / "kn" / product
            shutil.copytree(source, folder_kn)
            try:
                (folder_kn / TABLE).write_bytes(replicate_table(table, factor).encode("ascii"))
            except ValueError as exc:
                return fail(f"cannot replicate {TABLE}: {exc}")
        for repeat in range(1, repeats + 1):
            for label, folder, size in (("n", folder_n, n), ("K·n", folder_kn, size_kn)):
                print(f"{product}: run {repeat}/{repeats}, {label} = {size} points ...",
                      file=sys.stderr, flush=True)
                try:
                    result = run_child(folder, n, cleanup, engine)
                except VerificationError as exc:
                    return fail(f"size {size} ({label}), run {repeat}: {exc}")
                problems = verify_run(result, size, n, baseline)
                if problems:
                    for problem in problems:
                        fail(f"size {size} ({label}), run {repeat}: {problem}")
                    return record
                record["runs"].append({"size": size, "repeat": repeat, "import_s": result["import_s"],
                                       "run_s": result["run_s"], "maxrss_kib": result["maxrss_kib"]})

    def med(size: int, key: str) -> float:
        return statistics.median(r[key] for r in record["runs"] if r["size"] == size)

    import_s = statistics.median(r["import_s"] for r in record["runs"])
    record["medians"] = {"import_s": import_s,
                         "run_s_n": med(n, "run_s"), "run_s_kn": med(size_kn, "run_s"),
                         "maxrss_kib_n": med(n, "maxrss_kib"), "maxrss_kib_kn": med(size_kn, "maxrss_kib")}
    m = record["medians"]
    derived = derive(n, factor, import_s, m["run_s_n"], m["run_s_kn"],
                     m["maxrss_kib_n"], m["maxrss_kib_kn"])
    record["status"] = derived.pop("status")
    record["derived"] = derived
    if record["status"] == "unreliable":
        print(f"UNRELIABLE {product}: T(K·n) = {m['run_s_kn']:.2f} s is not above "
              f"T(n) = {m['run_s_n']:.2f} s", file=sys.stderr)
        record["forecast"] = None
    else:
        record["forecast"] = forecast(derived["t_marginal_s"], derived["fixed_s"],
                                      derived["mb_per_contract"], args.mutants, args.pool,
                                      args.workers, ram_mb)
    return record


def table_lines(records: list[dict]) -> list[str]:
    head = ("product", "n", "K·n", "T(n) s", "T(K·n) s", "import s", "fixed s",
            "t_marginal ms", "RSS(n) MB", "RSS(K·n) MB", "MB/contract", "status")
    rows = [head]
    for r in records:
        m, d = r.get("medians"), r.get("derived")
        def f(v, fmt):
            return "-" if v is None else format(v, fmt)
        rows.append((
            r["product"], str(r.get("n", "-")), str(r.get("size_kn", "-")),
            f(m and m["run_s_n"], ".2f"), f(m and m["run_s_kn"], ".2f"),
            f(m and m["import_s"], ".2f"), f(d and d["fixed_s"], ".2f"),
            f(d and d["t_marginal_s"] * 1000, ".0f"),
            f(m and m["maxrss_kib_n"] / 1024, ".0f"), f(m and m["maxrss_kib_kn"] / 1024, ".0f"),
            f(d and d["mb_per_contract"], ".1f"), r["status"]))
    widths = [max(len(row[i]) for row in rows) for i in range(len(head))]
    return ["  ".join(c.ljust(w) if i == 0 or i == len(head) - 1 else c.rjust(w)
                      for i, (c, w) in enumerate(zip(row, widths))).rstrip() for row in rows]


def positive_int(minimum: int):
    def parse(text: str) -> int:
        try:
            value = int(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"not an integer: {text!r}") from None
        if value < minimum:
            raise argparse.ArgumentTypeError(f"must be at least {minimum}: {value}")
        return value
    return parse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="measure_marginal.py",
        description="Measure the marginal time per contract of products and forecast the night run.")
    parser.add_argument("products", nargs="*", help="product names under products/")
    parser.add_argument("--all", action="store_true", help="measure every product, in name order")
    parser.add_argument("--factor", type=positive_int(2), default=2, help="K, the size multiple (default 2)")
    parser.add_argument("--repeats", type=positive_int(1), default=3, help="R, runs per size (default 3)")
    parser.add_argument("--mutants", type=positive_int(1), default=500, help="M for the forecast (default 500)")
    parser.add_argument("--pool", type=positive_int(1), default=10000, help="P for the forecast (default 10000)")
    parser.add_argument("--workers", type=positive_int(1), default=1, help="W for the forecast (default 1)")
    parser.add_argument("--json", type=Path, metavar="FILE", help="write all measurements as JSON")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="run the runner without per-contract cleanup (phase-2a behaviour)")
    parser.add_argument("--engine", choices=("export", "modelx"), default="export",
                        help="the runner's engine: export (default) or modelx (phases 2a and 2b)")
    parser.add_argument("--child", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--originals", type=positive_int(1), help=argparse.SUPPRESS)
    parser.add_argument("--prepared", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.child is not None:
        return child(args.child.resolve(), args.originals or 0, cleanup=not args.no_cleanup,
                     engine=args.engine)

    names = product_names()
    if args.all and args.products:
        parser.error("give product names or --all, not both")
    if not args.all and not args.products:
        parser.error("give at least one product name, or --all")
    products = names if args.all else list(dict.fromkeys(args.products))
    unknown = [p for p in products if p not in names]
    if unknown:
        parser.error(f"unknown product(s) {', '.join(map(repr, unknown))} (products: {', '.join(names)})")
    if args.prepared is not None:
        if len(products) != 1:
            parser.error("--prepared needs exactly one product")
        args.prepared = args.prepared.resolve()
        if not (args.prepared / TABLE).is_file():
            parser.error(f"--prepared folder has no {TABLE}")

    if args.json is not None and not args.json.resolve().parent.is_dir():
        parser.error(f"--json: no directory {str(args.json.parent)!r}")

    ram_mb = total_ram_mb()
    records = [measure(product, args, ram_mb) for product in products]

    print(f"factor K = {args.factor}, repeats R = {args.repeats}; times are medians of "
          "run_product, import is the median modelx import, "
          f"cleanup {'off' if args.no_cleanup else 'on'}, engine {args.engine}")
    for line in table_lines(records):
        print(line)
    print()
    for line in assumption_lines(args.mutants, args.pool, args.workers, args.factor):
        print(line)
    for r in records:
        if r.get("forecast"):
            for line in forecast_lines(r["product"], r["forecast"]):
                print(line)
        else:
            print(f"{r['product']}: no forecast ({r['status']})")
    if args.json is not None:
        args.json.write_text(json.dumps({"factor": args.factor, "repeats": args.repeats,
                                         "cleanup": not args.no_cleanup,
                                         "engine": args.engine,
                                         "mutants": args.mutants, "pool": args.pool,
                                         "workers": args.workers, "total_ram_mb": ram_mb,
                                         "products": records}, indent=2) + "\n")
    return 0 if all(r["status"] == "ok" for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())
