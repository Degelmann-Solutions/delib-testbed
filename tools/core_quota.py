"""Measure the core quota of one or more products: the share of executed formulas from the core.

    uv run python tools/core_quota.py risikolebensversicherung
    uv run python tools/core_quota.py --all
    uv run python tools/core_quota.py --all --json /tmp/quota.json
    uv run python tools/core_quota.py path/to/scratch

A bare name resolves to ``products/<name>``; anything with a path separator is used as
given, as in ``tools/run_baseline.py``. The product folder is only read.

Definition
----------
The tool reads the product's model with ``mx.read_model`` (the modelx engine, which keeps
every computed value in its cells) and, for every point of ``model_point_table.csv``,
evaluates ``result_cf()`` and every runner check (``run_baseline.check_names``). A cell of
the point's ``Projection`` ItemSpace that then holds a value (``len(cell) > 0``) is an
**executed formula**; the executed set is the union over the points. An executed cell counts
as **core** when the product's static ``Projection`` cell of that name is derived from the
core base (``_is_derived()``); an override of a core cell and a product-only cell count as
product. ``Data`` cells (the loaders) are not counted. The quota is core over executed::

    quota = |core| / |executed|

Each point's ItemSpace is deleted once it has been read, so the points do not accumulate.

Lower bound
-----------
``LOWER_BOUND`` = 0.20 for every product (Moritz, 2026-10-28, epic-common-core Notes) but
those in ``PRODUCT_BOUNDS``, which carry their own bound at their measured quota (BU, 28 of
148: Moritz, 2026-10-29, epic-night-run Notes, variant c, as recorded in ``3ab6cbc``;
applied when BU's cohort index and *Leistungsdynamik* step became ``Projection`` cells and
took it below 20 %, moved with its per-claim-year rate arrays). A product passes at
``quota >= bound_for(product)``; ``tests/test_core_quota.py`` enforces it.

Output
------
One line per product, in the order given: the product, the executed formulas, those from the
core and the quota, ``<product>: executed <n>, from core <c>, quota <q>``. With ``--json FILE``
the tool also writes ``{product: {"executed": n, "core": c, "quota": q, "executed_cells":
[...], "core_cells": [...]}}``, the cell names sorted.

Exit status: 0 if every quota is at or above its bound, ``bound_for(product)``; 1 if any is
below (each such product is printed on stderr with its bound and figures); 2 on a usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_baseline  # noqa: E402  (imports modelx)
from run_baseline import UsageError, check_names, model_dir, product_names, resolve_product  # noqa: E402

import modelx as mx  # noqa: E402

# Moritz, 2026-10-28: the bound for every product without its own, passed at >=
LOWER_BOUND = 0.20
# Moritz, 2026-10-29 (epic-night-run Notes, variant c, as recorded in 3ab6cbc): BU's own
# bound at its measured quota.
PRODUCT_BOUNDS = {"berufsunfaehigkeit": 28 / 148}


def bound_for(product: str) -> float:
    """The lower bound a product's quota is held to: its own, else ``LOWER_BOUND``."""
    return PRODUCT_BOUNDS.get(product, LOWER_BOUND)


def measure(folder: Path) -> dict:
    """The executed and core cells of one product's ``Projection`` (see module docstring)."""
    model = mx.read_model(model_dir(folder))
    try:
        checks = check_names(model)
        point_ids = sorted(int(i) for i in model.Data.model_point_table().index)
        executed: set[str] = set()
        for point_id in point_ids:
            point = model.Projection[point_id]
            try:
                point.result_cf()
                for check in checks:
                    getattr(point, check)()
                executed |= {name for name, cell in point.cells.items() if len(cell) > 0}
            finally:
                del model.Projection[point_id]
        static = model.Projection.cells
        core = {name for name in executed if static[name]._is_derived()}
    finally:
        model.close()
    return {
        "executed": len(executed),
        "core": len(core),
        "quota": len(core) / len(executed) if executed else 0.0,
        "executed_cells": sorted(executed),
        "core_cells": sorted(core),
    }


def below(quotas: dict, bound: float | None = None) -> list[str]:
    """The products whose quota is below ``bound`` (each its own ``bound_for`` if omitted)."""
    return [product for product, figures in quotas.items()
            if figures["quota"] < (bound_for(product) if bound is None else bound)]


def line(product: str, figures: dict) -> str:
    return (f"{product}: executed {figures['executed']}, from core {figures['core']}, "
            f"quota {figures['quota']:.4f}")


def report(quotas: dict, bound: float | None = None) -> int:
    """Print one line per product and every product below ``bound`` on stderr; the exit code."""
    for product, figures in quotas.items():
        print(line(product, figures))
    failing = below(quotas, bound)
    for product in failing:
        limit = bound_for(product) if bound is None else bound
        print(f"BELOW {limit:g}: {line(product, quotas[product])}", file=sys.stderr)
    return 1 if failing else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="core_quota.py",
        description="Measure the share of executed Projection formulas that derive from the core.")
    parser.add_argument("product", nargs="*",
                        help="product names under products/, or paths to product folders")
    parser.add_argument("--all", action="store_true", help="every product under products/")
    parser.add_argument("--json", type=Path, metavar="FILE", help="also write the figures to FILE")
    args = parser.parse_args(argv)
    if args.all and args.product:
        parser.error("name products or give --all, not both")
    names = product_names() if args.all else args.product
    if not names:
        parser.error("name at least one product, or give --all")
    try:
        folders = {name: resolve_product(name) for name in names}
        for folder in folders.values():
            model_dir(folder)
    except UsageError as exc:
        parser.print_usage(sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 2
    quotas = {Path(name).name if run_baseline.is_path(name) else name: measure(folder)
              for name, folder in folders.items()}
    if args.json is not None:
        args.json.write_text(json.dumps(quotas, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return report(quotas)


if __name__ == "__main__":
    sys.exit(main())
