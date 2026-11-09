"""Show the parameters a tariff reads: item, value, layer, basis and provenance.

    uv run python tools/params.py risikolebensversicherung
    uv run python tools/params.py --all
    uv run python tools/params.py path/to/scratch

A bare name resolves to ``products/<name>``; anything with a path separator is used as
given, as in ``tools/run_baseline.py``. The product folder is only read.

Definition
----------
The tool reads the product's model with ``mx.read_model`` and lists every item the tariff
reads, the keys of ``scan(model).reads`` of the static usage scan ``core/param_usage.py``
(direct and declared indirect reads; ``docs/core.md``, "The parameter files"). It keeps no
list of items of its own. An item's **value** and **layer** are those of
``model.Data.param_layers()``; its **basis** and **provenance** are the columns of the item's
row in that layer's file, ``param_core_path()`` for ``core``, ``input_dir() / param_file``
for ``tariff_type`` and ``param_tariff_path()`` for ``tariff``, read by column name. A core
item the tariff does not read is not listed. A read item that no layer holds (a problem the
scan also reports) is listed with layer ``missing`` and no value.

Output
------
Per product, in the order given (``--all``: name order), a header line ``<product>: <n>
items read``, then a column header and one fixed-width line per item: item, value (its
``repr``), layer, basis, provenance. The items stand in layer order ``core``,
``tariff_type``, ``tariff``, within a layer in the order of its file, the ``missing`` ones
last by name. A blank line separates the products.

Exit status: 0 if every read item stands in a layer; 1 if any does not (each such item is
named on stderr); 2 on a usage error.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_baseline  # noqa: E402  (imports modelx)
from run_baseline import UsageError, model_dir, product_names, resolve_product  # noqa: E402

import modelx as mx  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MISSING = "missing"
COLUMNS = ("item", "value", "layer", "basis", "provenance")


def _load_param_usage():
    """The static usage scan ``core/param_usage.py``, a plain module beside the core model."""
    spec = importlib.util.spec_from_file_location("param_usage", ROOT / "core" / "param_usage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


param_usage = _load_param_usage()


def layer_paths(model) -> dict[str, Path]:
    """The file of each layer ``param_layers()`` reads, by layer."""
    data = model.Data
    paths = {"core": Path(data.param_core_path()),
             "tariff_type": Path(data.input_dir()) / data.param_file}
    if Path(data.param_tariff_path()).is_file():
        paths["tariff"] = Path(data.param_tariff_path())
    return paths


def file_rows(path: Path) -> dict[str, dict]:
    """The rows of one layer file by ``item``, read as the loader ``param_layers()`` reads it."""
    table = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {row["item"]: row for row in table.to_dict("records")}


def rows(model) -> list[dict]:
    """One row per item the model reads: item, value, layer, basis, provenance (module
    docstring)."""
    reads = param_usage.scan(model).reads
    layers = model.Data.param_layers()
    paths = layer_paths(model)
    result = []
    for layer, values in layers.items():
        table = file_rows(paths[layer])
        for item, value in values.items():
            if item in reads:
                row = table[item]
                result.append({"item": item, "value": value, "layer": layer,
                               "basis": row["basis"], "provenance": row["provenance"]})
    held = {row["item"] for row in result}
    for item in sorted(set(reads) - held):
        result.append({"item": item, "value": None, "layer": MISSING, "basis": "",
                       "provenance": ""})
    return result


def lines(product: str, table: list[dict]) -> list[str]:
    """The header and one fixed-width line per row."""
    cells = [[row["item"], "" if row["value"] is None else repr(row["value"]), row["layer"],
              row["basis"], row["provenance"]] for row in table]
    widths = [max([len(name)] + [len(cell[i]) for cell in cells])
              for i, name in enumerate(COLUMNS[:-1])]
    out = [f"{product}: {len(table)} items read"]
    for cell in [list(COLUMNS)] + cells:
        out.append("  " + "  ".join([text.ljust(width) for text, width in zip(cell, widths)]
                                    + [cell[-1]]).rstrip())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="params.py",
        description="Show the parameters a tariff reads, with value, layer, basis and provenance.")
    parser.add_argument("product", nargs="*",
                        help="product names under products/, or paths to product folders")
    parser.add_argument("--all", action="store_true", help="every product under products/")
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
    status = 0
    for number, (name, folder) in enumerate(folders.items()):
        product = Path(name).name if run_baseline.is_path(name) else name
        model = mx.read_model(model_dir(folder))
        try:
            table = rows(model)
        finally:
            model.close()
        if number:
            print()
        print("\n".join(lines(product, table)))
        missing = [row["item"] for row in table if row["layer"] == MISSING]
        if missing:
            print(f"{product}: read items in no layer: {', '.join(missing)}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
