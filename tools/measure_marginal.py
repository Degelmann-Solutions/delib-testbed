"""Measure the marginal time per contract of one or more products.

    uv run python tools/measure_marginal.py risikolebensversicherung
    uv run python tools/measure_marginal.py --all --json /tmp/phase2d.json --mutants 500
    uv run python tools/measure_marginal.py basisrente --workers 1,4,8 --repeats 5 --pool 20000
    uv run python tools/measure_marginal.py --all --factor 2 --workers 1 --mutants 500           # phase 2c
    uv run python tools/measure_marginal.py --all --factor 2 --engine modelx --mutants 500       # phase 2b
    uv run python tools/measure_marginal.py --all --factor 2 --engine modelx --no-cleanup --mutants 500  # 2a

What is measured
----------------
``run_product`` of ``tools/run_baseline.py`` as it stands: ``read_model``, the export (in
the export engine), ``result_cf``, every built-in check and the hashing, for every point.
``--engine`` passes the runner's engine through: ``export`` (the default) runs on the
exported model, ``modelx`` on the traced modelx model. By default the runner deletes each
point's ItemSpace after reading it (per-contract cleanup); ``--no-cleanup`` passes the
runner's switch through. Reproducing phase 2a needs ``--engine modelx --no-cleanup``,
phase 2b ``--engine modelx``, each with ``--factor 2 --mutants 500``. ``--workers`` is a list of worker
counts (default ``1,4,8,12,16,24``); the runner runs at each of them (``--workers W``) and
every product is measured at every ``W``. Under ``--engine modelx`` or ``--no-cleanup`` the
runner has no workers, so the list defaults to ``1`` there and anything above 1 is a usage
error. The header line above the table and the JSON (``engine``, ``cleanup``, ``workers``)
state the modes. Each product runs at two sizes, in
two temporary scratch copies of its folder under one temp root: one with the shipped ``n``
model points, one with ``K·n`` points whose ids ``n+1 … K·n`` repeat the rows of ids
``1 … n`` in order. The product folder itself is only read.

Every (W, size, repeat) runs in its own fresh child process (this script with
``--child``), one after another, never two children at once, sizes alternating per ``W``:
n, K·n, n, K·n, … The child times ``import run_baseline`` (which imports modelx) and
``run_product(…, workers=W)`` separately and reports its memory. With ``T`` the median
``run_product`` wall time of a size at one ``W``::

    t_marginal(W) = (T(K·n) − T(n)) / ((K − 1)·n)
    fixed(W)      = import + T(n) − n·t_marginal(W)      (import: median over the W's runs)
    MB/contract   = (mem(K·n) − mem(n)) / ((K − 1)·n)    (medians; at W = 1 only)

``t_marginal(W)`` is wall time per contract across all ``W`` workers, so it already holds
the speed-up. Two sizes give the slope; that time per contract is constant in n is
assumed, not tested. At a large ``W``, ``T(n)`` is a single wave of ``n`` points in
parallel and pays the worker start-up once, so ``t_marginal(W)`` and ``fixed(W)`` are
biased slightly low there; this is stated, not corrected.

Memory is ``mem`` = the child's own peak RSS plus, for ``W`` > 1, the sum over the workers
of each worker's largest Pss after a point: every worker reads its Pss from
``/proc/self/smaps_rollup`` after each point (after its cleanup) and the child keeps the
maximum per worker pid. Pss divides pages shared copy-on-write by the processes sharing
them, so they are not counted once per worker. Two biases are stated, not corrected: the
Pss after a point's cleanup understates a worker's true peak during the point, and the
pages the workers share with the parent are counted close to twice (fully in the parent's
RSS, plus each worker's share in its Pss), so at ``W`` > 1 ``mem`` overstates by up to the
parent's shared footprint (about 100 MB).
``MB/contract`` is given at ``W`` = 1 only, where ``mem`` is the peak RSS of one process.

Transform cache
---------------
``--transform-cache off`` (the default) runs the runner without its transform cache, as
before. ``--transform-cache mutant`` (every ``W`` > 1) measures the fixed cost a mutant pays
with the night run's cache: before the timed runs of a product and ``W`` one untimed child
warms a cache on the shipped model (verified like a timed run); every timed run then gets
its own copy of it without the entries of the worst-placed mutant (``mutant_cache``). A
mutant misses every piece holding its cell, one for a product cell and two for a core cell
(its piece of ``CoreProjection`` and the piece of ``Projection`` that inherits it); the cells
are found by name in the cached entries, and the worst-placed one is the cell whose pieces
are largest together. Since the runner cuts pieces of similar size, that is a core cell, so
``fixed(W)`` is a core mutant's; it is used for the product mutants too, for whom it is
slightly high. A source change that shifts a later cut between pieces, which would make the
later pieces of that space miss as well, is not modelled; this is stated, not corrected. If
the warmed cache has no entries (its parallel export fell back to the serial one), one note
goes to stderr and every timed run gets an empty cache; a child's runner line
``parallel export raised …`` is passed on to stderr. The marginal time is unaffected. The
header line and the JSON (``transform_cache``) state the mode.

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
Per product and ``W``, under stated assumptions (``--mutants``, ``--pool``; slope from the
shipped point mix): ``M·P·t_marginal(W)`` in hours against the 10 h night, and
``M·(fixed(W) + P·t_marginal(W))``, since every mutant pays its own import, ``read_model``
and export. Neither divides by ``W`` again: ``t_marginal(W)`` is measured with ``W``
workers. Both are linear extrapolations without trace pruning, and forecasts: mutants
exist only once the separate test-set repository generates them. At ``W`` = 1 the memory
line extrapolates ``MB/contract × P`` for one process and warns when it exceeds the
machine's total RAM; the warning does not change the exit status. At ``W`` > 1 it gives the measured ``mem(K·n)``.

After the per-product lines comes one combined line per ``W`` for all measured products
together, with the formula of the new M (``docs/roadmap.md``, "The new M"): a mutant in the
core runs every measured product, a mutant in a product only that product, each run with its
fixed cost and ``P_p = P / N`` contracts per product (``P`` = ``--pool``, ``N`` the number of
products under ``products/``, ten today; the per-product lines keep ``P``)::

    T(W) = M_core·(Σ_p f_p + P_p·Σ_p t_p) + Σ_p M_p·(f_p + P_p·t_p)

with ``f_p = fixed(W)``, ``t_p = t_marginal(W)`` and the sums over the measured products
only (``--all`` gives the roadmap's formula exactly), in hours against the 10 h night. The
counts ``M_CORE`` and ``M_PRODUCT`` are what the roadmap's command prints on the code they
ship with, held here as constants and updated by every commit that changes them; ``--mutants``
defaults to their sum ``M_NEW``, and any other value scales ``M_core`` and every ``M_p`` by
``M / M_NEW``. The coverage filter is ignored. If a measured product is not ``ok`` at a
``W``, that ``W`` gets no combined forecast. The combined line never changes the exit status.

Exit status: 0 if every (product, W) is ``ok``; 1 if one failed a check, its child crashed
or its slope is not positive (``unreliable``); 2 on a usage error. Every product is
measured at every ``W`` and the worst status is returned.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
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
DEFAULT_WORKERS = (1, 4, 8, 12, 16, 24)

# The new M, counted by where each mutant sits: the counts the command of docs/roadmap.md,
# section "The new M", prints on this code (the roadmap records them at 790706b, the merge of
# PR #38). Every commit that moves a literal out of O6 updates them; recounting is the roadmap's
# command, not this tool's, and tests/test_measure_marginal.py runs it against these constants.
M_CORE = 188
M_PRODUCT = {
    "basisrente": 630,
    "berufsunfaehigkeit": 506,
    "fondsgebundene_rentenversicherung": 414,
    "indexpolice": 343,
    "kapitallebensversicherung": 417,
    "klassische_rentenversicherung": 582,
    "pflegerentenversicherung": 813,
    "riester_rente": 590,
    "risikolebensversicherung": 293,
    "sofortrente": 480,
}
M_NEW = M_CORE + sum(M_PRODUCT.values())


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
           rss_n_kib: float, rss_kn_kib: float, workers: int = 1) -> dict:
    """Slope, fixed cost and memory per contract; ``unreliable`` if the slope is not positive.

    ``mb_per_contract`` is ``None`` for ``workers`` > 1.
    """
    extra = (factor - 1) * n
    t_marginal = (t_kn - t_n) / extra
    mb_per_contract = (rss_kn_kib - rss_n_kib) / 1024 / extra if workers == 1 else None
    if t_marginal <= 0:
        return {"status": "unreliable", "t_marginal_s": t_marginal, "fixed_s": None,
                "mb_per_contract": mb_per_contract}
    return {"status": "ok", "t_marginal_s": t_marginal,
            "fixed_s": import_s + t_n - n * t_marginal, "mb_per_contract": mb_per_contract}


def forecast(t_marginal_s: float, fixed_s: float, mb_per_contract: float | None,
             mutants: int, pool: int, workers: int, total_ram_mb: float,
             mem_kn_mb: float | None = None) -> dict:
    """The night-run forecast at one ``W``; ``t_marginal_s`` already holds the workers."""
    hours = mutants * pool * t_marginal_s / 3600
    hours_fixed = mutants * (fixed_s + pool * t_marginal_s) / 3600
    ram_mb = None if mb_per_contract is None else mb_per_contract * pool
    return {"mutants": mutants, "pool": pool, "workers": workers,
            "hours": hours, "fits_night": hours <= NIGHT_HOURS,
            "hours_with_fixed": hours_fixed,
            "ram_mb_per_process": ram_mb, "mem_kn_mb": mem_kn_mb, "total_ram_mb": total_ram_mb,
            "ram_warning": ram_mb is not None and ram_mb > total_ram_mb}


def forecast_lines(product: str, fc: dict) -> list[str]:
    m, p, w = fc["mutants"], fc["pool"], fc["workers"]
    verdict = "fits" if fc["fits_night"] else "does not fit"
    label = f"{product}, W = {w}"
    lines = [
        f"{label}: M·P·t_marginal(W) = {m:,}·{p:,}·t = {fc['hours']:.1f} h "
        f"({verdict} the {NIGHT_HOURS:.0f} h night)",
        f"{label}: with fixed cost per mutant, M·(fixed(W) + P·t_marginal(W)) = "
        f"{fc['hours_with_fixed']:.1f} h",
    ]
    if fc["ram_mb_per_process"] is not None:
        lines.append(f"{label}: memory, MB/contract × P = "
                     f"{fc['ram_mb_per_process'] / 1024:.1f} GB in one process")
    elif fc.get("mem_kn_mb") is not None:
        lines.append(f"{label}: memory, parent peak RSS + workers' largest Pss after a point at K·n = "
                     f"{fc['mem_kn_mb']:.0f} MB")
    if fc["ram_warning"]:
        lines.append(f"WARNING {label}: {fc['ram_mb_per_process'] / 1024:.1f} GB exceeds the "
                     f"machine's total RAM of {fc['total_ram_mb'] / 1024:.1f} GB")
    return lines


def _num(value: float) -> str:
    """A count with thousands separators; two decimals only if it is not whole."""
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


def combined_forecast(records: list[dict], mutants: int, pool: int, n_products: int) -> dict:
    """The forecast for the measured products together at one ``W`` (see module docstring).

    ``records`` are the records of the measured products at that ``W``. ``hours`` is
    ``None`` if one of them is not ``ok``; ``not_ok`` then names each with its status.
    """
    scale = mutants / M_NEW
    pool_per_product = pool / n_products
    m_core = M_CORE * scale
    m_products = {r["product"]: M_PRODUCT[r["product"]] * scale for r in records}
    fc = {"workers": records[0]["workers"], "products": [r["product"] for r in records],
          "mutants": mutants, "m_core": m_core, "m_products": m_products,
          "pool_per_product": pool_per_product}
    not_ok = {r["product"]: r["status"] for r in records
              if r["status"] != "ok" or r.get("derived") is None}
    if not_ok:
        return {**fc, "hours": None, "fits_night": None, "not_ok": not_ok}
    f = {r["product"]: r["derived"]["fixed_s"] for r in records}
    t = {r["product"]: r["derived"]["t_marginal_s"] for r in records}
    core_s = m_core * (sum(f.values()) + pool_per_product * sum(t.values()))
    product_s = sum(m_products[p] * (f[p] + pool_per_product * t[p]) for p in f)
    hours = (core_s + product_s) / 3600
    return {**fc, "sum_fixed_s": sum(f.values()), "sum_t_marginal_s": sum(t.values()),
            "core_hours": core_s / 3600, "product_hours": product_s / 3600,
            "hours": hours, "fits_night": hours <= NIGHT_HOURS}


def combined_lines(fc: dict, n_products: int) -> list[str]:
    k, w = len(fc["products"]), fc["workers"]
    label = (f"all {k} products together" if k == n_products
             else f"{k} of {n_products} products together ({', '.join(fc['products'])})")
    if fc["hours"] is None:
        failing = ", ".join(f"{p}: {s}" for p, s in fc["not_ok"].items())
        return [f"{label}, W = {w}: no combined forecast ({failing})"]
    m_core, m_sum, p = fc["m_core"], sum(fc["m_products"].values()), fc["pool_per_product"]
    verdict = "fits" if fc["fits_night"] else "does not fit"
    return [
        f"{label}, W = {w}: M_core·(Σ f + P·Σ t) + Σ M_p·(f_p + P·t_p) = "
        f"{_num(m_core)}·({fc['sum_fixed_s']:.2f} s + {_num(p)}·{fc['sum_t_marginal_s'] * 1000:.1f} ms)"
        f" + Σ M_p·(…) = {fc['core_hours']:.1f} h + {fc['product_hours']:.1f} h = "
        f"{fc['hours']:.1f} h ({verdict} the {NIGHT_HOURS:.0f} h night), "
        f"M = {_num(fc['mutants'])} (M_core = {_num(m_core)}, Σ M_p = {_num(m_sum)}), "
        f"P = {_num(p)} per product, fixed cost included",
    ]


def assumption_lines(mutants: int, pool: int, workers: list[int], factor: int,
                     n_products: int | None = None) -> list[str]:
    n_products = len(product_names()) if n_products is None else n_products
    return [
        f"Assumptions: M = {mutants:,} mutants, P = {pool:,} contracts, "
        f"W = {','.join(map(str, workers))} worker(s);",
        "  t_marginal(W) is measured with W workers, so the forecast does not divide by W;",
        "  slope from each product's shipped point mix; two sizes (n and "
        f"{factor}·n), so linearity is assumed, not tested.",
        "  A linear extrapolation without trace pruning, and a forecast: mutants exist only "
        "once the separate test-set repository generates them.",
        "  Combined: a core mutant runs every measured product, a product mutant only its own, "
        f"each with its fixed cost and P/{n_products} = {_num(pool / n_products)} contracts per "
        "product; the coverage filter is ignored; M_core and M_p are the counts of the command of "
        f"docs/roadmap.md, \"The new M\", on this code, scaled by M / {M_NEW:,}.",
    ]


def total_ram_mb() -> float:
    return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 / 1024


# --------------------------------------------------------------------------- child

def child(folder: Path, originals: int, cleanup: bool = True, engine: str = "export",
          workers: int = 1, transform_cache: Path | None = None) -> int:
    """Run ``run_product`` once and print the measurement as JSON on the last stdout line."""
    import resource

    start = time.perf_counter()
    import run_baseline  # noqa: E402  (script mode: tools/ is on sys.path; imports modelx)
    import_s = time.perf_counter() - start
    start = time.perf_counter()
    worker_pss: dict[int, int] = {}
    extra = {} if transform_cache is None else {"transform_cache": transform_cache}
    count, _checks, _sha, failures, lines, digests = run_baseline.run_product(
        folder, cleanup=cleanup, engine=engine, keep_lines=originals, workers=workers,
        worker_pss=worker_pss, **extra)
    run_s = time.perf_counter() - start
    maxrss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    worker_pss_kib = sum(worker_pss.values())
    points: dict[str, list[str]] = {}
    for line in lines[1:]:
        pid, _, rest = line.partition(",")
        points.setdefault(pid, []).append(rest)
    print(json.dumps({"n": count, "originals": originals, "import_s": import_s,
                      "run_s": run_s, "maxrss_kib": maxrss_kib, "workers": workers,
                      "worker_pss_kib": worker_pss_kib, "mem_kib": maxrss_kib + worker_pss_kib,
                      "failures": failures,
                      "header": lines[0] if lines else "", "points": points,
                      "digests": {str(k): v for k, v in digests.items()}}))
    return 0


def run_child(folder: Path, originals: int, cleanup: bool, engine: str = "export",
              workers: int = 1, transform_cache: Path | None = None) -> dict:
    """One fresh child process; raises ``VerificationError`` on a crash or missing JSON."""
    command = [sys.executable, str(THIS), "--child", str(folder), "--originals", str(originals),
               "--workers", str(workers), "--engine", engine]
    if transform_cache is not None:
        command += ["--child-cache", str(transform_cache)]
    if not cleanup:
        command.append("--no-cleanup")
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    tail = "\n".join(proc.stderr.strip().splitlines()[-5:])
    if proc.returncode != 0:
        raise VerificationError(f"child exited {proc.returncode}; stderr tail:\n{tail}")
    for line in proc.stderr.splitlines():
        if line.startswith("parallel export raised"):
            print(line, file=sys.stderr, flush=True)
    out = proc.stdout.strip().splitlines()
    try:
        result = json.loads(out[-1])
    except (IndexError, json.JSONDecodeError):
        raise VerificationError(f"child printed no JSON; stderr tail:\n{tail}") from None
    return result


# --------------------------------------------------------------------------- parent

def cache_entries(warm: Path) -> list[Path]:
    """The entries of the transform cache ``warm`` (not its temporary files); none if it is
    missing."""
    if not warm.is_dir():
        return []
    return sorted(p for p in warm.iterdir() if p.is_file() and not p.name.startswith("."))


def mutant_cache(warm: Path, target: Path) -> Path:
    """A copy of the warm transform cache ``warm`` at ``target`` without the entries of the
    worst-placed mutant.

    An entry is the pickled ``(func_attrs, code)`` of one piece, ``func_attrs`` keyed by the
    piece's cell names. A mutant changes one cell, so its export misses every piece that
    holds the cell and hits every other one: one piece for a product cell, two for a core
    cell (its piece of ``CoreProjection`` and the piece of ``Projection`` that inherits it).
    The worst-placed cell is the name whose entries have the largest summed file size; all
    its entries are dropped, so every timed run transforms what the most expensive mutant
    would. Entries that do not unpickle to a dict and a code string are copied but not
    chosen from. A missing or empty ``warm`` gives an empty ``target``.
    """
    target.mkdir(parents=True)
    entries = cache_entries(warm)
    holders: dict[str, list[Path]] = {}
    for entry in entries:
        try:
            with open(entry, "rb") as f:
                func_attrs, code = pickle.load(f)
        except Exception:
            continue
        if not isinstance(func_attrs, dict) or not isinstance(code, str):
            continue
        for name in func_attrs:
            holders.setdefault(name, []).append(entry)
    drop: set[Path] = set()
    if holders:
        worst = max(sorted(holders), key=lambda name: sum(p.stat().st_size for p in holders[name]))
        drop = set(holders[worst])
    for entry in entries:
        if entry not in drop:
            shutil.copy2(entry, target / entry.name)
    return target


def measure(product: str, args, ram_mb: float, workers: int = 1) -> dict:
    """Measure one product at one ``W``. The record has ``status`` ok, unreliable or failed."""
    factor, repeats, cleanup, engine = args.factor, args.repeats, not args.no_cleanup, args.engine
    record: dict = {"product": product, "workers": workers, "factor": factor, "repeats": repeats,
                    "runs": [], "errors": [], "status": "failed"}

    def fail(message: str) -> dict:
        record["errors"].append(message)
        print(f"FAILED {product}, W = {workers}: {message}", file=sys.stderr)
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
        warm = None
        if getattr(args, "transform_cache", "off") == "mutant":
            warm = root / "cache-warm"
            print(f"{product}, W = {workers}: warming the transform cache ...",
                  file=sys.stderr, flush=True)
            try:
                result = run_child(folder_n, n, cleanup, engine, workers, warm)
            except VerificationError as exc:
                return fail(f"warming the transform cache: {exc}")
            problems = verify_run(result, n, n, baseline)
            if problems:
                return fail(f"warming the transform cache: {problems[0]}")
            if not cache_entries(warm):
                print(f"NOTE {product}, W = {workers}: the warmed transform cache has no entries; "
                      "every timed run transforms every piece", file=sys.stderr, flush=True)
        for repeat in range(1, repeats + 1):
            for label, folder, size in (("n", folder_n, n), ("K·n", folder_kn, size_kn)):
                print(f"{product}, W = {workers}: run {repeat}/{repeats}, {label} = {size} points ...",
                      file=sys.stderr, flush=True)
                cache = None
                if warm is not None:
                    cache = mutant_cache(warm, root / f"cache-{repeat}-{size}")
                try:
                    result = (run_child(folder, n, cleanup, engine, workers) if cache is None
                              else run_child(folder, n, cleanup, engine, workers, cache))
                except VerificationError as exc:
                    return fail(f"size {size} ({label}), run {repeat}: {exc}")
                problems = verify_run(result, size, n, baseline)
                if problems:
                    for problem in problems:
                        fail(f"size {size} ({label}), run {repeat}: {problem}")
                    return record
                record["runs"].append({"size": size, "repeat": repeat, "import_s": result["import_s"],
                                       "run_s": result["run_s"], "maxrss_kib": result["maxrss_kib"],
                                       "worker_pss_kib": result["worker_pss_kib"],
                                       "mem_kib": result["mem_kib"]})

    def med(size: int, key: str) -> float:
        return statistics.median(r[key] for r in record["runs"] if r["size"] == size)

    import_s = statistics.median(r["import_s"] for r in record["runs"])
    record["medians"] = {"import_s": import_s,
                         "run_s_n": med(n, "run_s"), "run_s_kn": med(size_kn, "run_s"),
                         "maxrss_kib_n": med(n, "maxrss_kib"), "maxrss_kib_kn": med(size_kn, "maxrss_kib"),
                         "mem_kib_n": med(n, "mem_kib"), "mem_kib_kn": med(size_kn, "mem_kib")}
    m = record["medians"]
    derived = derive(n, factor, import_s, m["run_s_n"], m["run_s_kn"],
                     m["mem_kib_n"], m["mem_kib_kn"], workers)
    record["status"] = derived.pop("status")
    record["derived"] = derived
    if record["status"] == "unreliable":
        print(f"UNRELIABLE {product}, W = {workers}: T(K·n) = {m['run_s_kn']:.2f} s is not above "
              f"T(n) = {m['run_s_n']:.2f} s", file=sys.stderr)
        record["forecast"] = None
    else:
        record["forecast"] = forecast(derived["t_marginal_s"], derived["fixed_s"],
                                      derived["mb_per_contract"], args.mutants, args.pool,
                                      workers, ram_mb, m["mem_kib_kn"] / 1024)
    return record


def table_lines(records: list[dict]) -> list[str]:
    head = ("product", "W", "n", "K·n", "T(n) s", "T(K·n) s", "import s", "fixed s",
            "t_marginal ms", "mem(n) MB", "mem(K·n) MB", "MB/contract", "status")
    rows = [head]
    for r in records:
        m, d = r.get("medians"), r.get("derived")
        def f(v, fmt):
            return "-" if v is None else format(v, fmt)
        rows.append((
            r["product"], str(r.get("workers", "-")), str(r.get("n", "-")), str(r.get("size_kn", "-")),
            f(m and m["run_s_n"], ".2f"), f(m and m["run_s_kn"], ".2f"),
            f(m and m["import_s"], ".2f"), f(d and d["fixed_s"], ".2f"),
            f(d and d["t_marginal_s"] * 1000, ".1f"),
            f(m and m["mem_kib_n"] / 1024, ".0f"), f(m and m["mem_kib_kn"] / 1024, ".0f"),
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


def worker_list(text: str) -> list[int]:
    """``1,4,8`` as a list of distinct worker counts of at least 1, in the given order."""
    parse = positive_int(1)
    values = [parse(part.strip()) for part in text.split(",")]
    return list(dict.fromkeys(values))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="measure_marginal.py",
        description="Measure the marginal time per contract of products and forecast the night run.")
    parser.add_argument("products", nargs="*", help="product names under products/")
    parser.add_argument("--all", action="store_true", help="measure every product, in name order")
    parser.add_argument("--factor", type=positive_int(2), default=32, help="K, the size multiple (default 32)")
    parser.add_argument("--repeats", type=positive_int(1), default=3, help="R, runs per size (default 3)")
    parser.add_argument("--mutants", type=positive_int(1), default=M_NEW,
                        help=f"M for the forecast (default {M_NEW}, the new M of docs/roadmap.md)")
    parser.add_argument("--pool", type=positive_int(1), default=10000, help="P for the forecast (default 10000)")
    parser.add_argument("--workers", type=worker_list, metavar="W,W,...",
                        help="worker counts to measure at (default 1,4,8,12,16,24; "
                             "1 under --engine modelx or --no-cleanup)")
    parser.add_argument("--json", type=Path, metavar="FILE", help="write all measurements as JSON")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="run the runner without per-contract cleanup (phase-2a behaviour)")
    parser.add_argument("--engine", choices=("export", "modelx"), default="export",
                        help="the runner's engine: export (default) or modelx (phases 2a and 2b)")
    parser.add_argument("--transform-cache", choices=("off", "mutant"), default="off",
                        help="off (default): every run transforms every formula piece; mutant: "
                             "each run gets the runner's transform cache warmed on the product "
                             "without the pieces of the worst-placed mutant, as its export would")
    parser.add_argument("--child", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--child-cache", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--originals", type=positive_int(1), help=argparse.SUPPRESS)
    parser.add_argument("--prepared", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.workers is None:
        single = args.engine == "modelx" or args.no_cleanup
        args.workers = [1] if single else list(DEFAULT_WORKERS)
    if args.child is not None:
        if len(args.workers) != 1:
            parser.error("--child needs exactly one --workers")
        return child(args.child.resolve(), args.originals or 0, cleanup=not args.no_cleanup,
                     engine=args.engine, workers=args.workers[0],
                     transform_cache=args.child_cache)

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

    if max(args.workers) > 1 and args.engine == "modelx":
        parser.error("--workers above 1 needs the export engine, not --engine modelx")
    if max(args.workers) > 1 and args.no_cleanup:
        parser.error("--workers above 1 needs per-contract cleanup, not --no-cleanup")
    if args.transform_cache == "mutant" and min(args.workers) < 2:
        parser.error("--transform-cache mutant needs every --workers above 1")
    if args.json is not None and not args.json.resolve().parent.is_dir():
        parser.error(f"--json: no directory {str(args.json.parent)!r}")

    ram_mb = total_ram_mb()
    records = [measure(product, args, ram_mb, workers)
               for product in products for workers in args.workers]

    print(f"factor K = {args.factor}, repeats R = {args.repeats}, "
          f"workers W = {','.join(map(str, args.workers))}; times are medians of "
          "run_product, import is the median modelx import, mem is peak RSS plus the workers' "
          f"largest Pss after a point, cleanup {'off' if args.no_cleanup else 'on'}, engine {args.engine}"
          + (", transform cache mutant" if args.transform_cache == "mutant" else ""))
    for line in table_lines(records):
        print(line)
    print()
    n_products = len(names)
    for line in assumption_lines(args.mutants, args.pool, args.workers, args.factor, n_products):
        print(line)
    for r in records:
        if r.get("forecast"):
            for line in forecast_lines(r["product"], r["forecast"]):
                print(line)
        else:
            print(f"{r['product']}, W = {r['workers']}: no forecast ({r['status']})")
    combined = [combined_forecast([r for r in records if r["workers"] == w], args.mutants,
                                  args.pool, n_products) for w in args.workers]
    for fc in combined:
        for line in combined_lines(fc, n_products):
            print(line)
    if args.json is not None:
        args.json.write_text(json.dumps({"factor": args.factor, "repeats": args.repeats,
                                         "cleanup": not args.no_cleanup,
                                         "engine": args.engine,
                                         "transform_cache": args.transform_cache,
                                         "mutants": args.mutants, "pool": args.pool,
                                         "workers": args.workers, "total_ram_mb": ram_mb,
                                         "products": records, "combined": combined},
                                        indent=2) + "\n")
    return 0 if all(r["status"] == "ok" for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())
