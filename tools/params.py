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
``model.Data.param_layers()``; its **basis** and **provenance** are those of the item's row
in that layer of ``model.Data.param_rows()``, the loader's reading of the layer files. The
tool reads no file and builds no path of its own. A core item the tariff does not read is not
listed. A read item that no layer holds (a problem the scan also reports) is listed with
layer ``missing`` and no value.

Output
------
Per product, in the order given (``--all``: name order), a header line ``<product>: <n>
items read``, then a column header and one fixed-width line per item: item, value (its
``repr``), layer, basis, provenance. The items stand in layer order ``core``,
``tariff_type``, ``tariff``, within a layer in the order of its file, the ``missing`` ones
last by name. A blank line separates the products. After a product's listing every problem
of ``scan(model).problems`` stands on stderr, one line ``<product>: <problem>`` each. A
product whose loader fails (a broken parameter file, ``ValueError`` on the first ``param``
call) is not listed: its error line stands on stderr as ``<product>: ValueError: <message>``
and the tool goes on with the next product.

Exit status: 0 if no product has a scan problem or a loader error; 1 if any has; 2 on a
usage error, among them a product named twice (the same name, or two names of one folder).
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
from modelx.core.errors import FormulaError  # noqa: E402

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


def rows(model, usage=None) -> list[dict]:
    """One row per item the model reads: item, value, layer, basis, provenance (module
    docstring). ``usage`` is ``scan(model)``, scanned here if not given."""
    reads = (usage or param_usage.scan(model)).reads
    layers = model.Data.param_layers()
    file_rows = model.Data.param_rows()
    result = []
    for layer, values in layers.items():
        table = {row[0]: row for row in file_rows[layer]}
        for item, value in values.items():
            if item in reads:
                _item, _text, basis, provenance = table[item]
                result.append({"item": item, "value": value, "layer": layer,
                               "basis": basis, "provenance": provenance})
    held = {row["item"] for row in result}
    for item in sorted(set(reads) - held):
        result.append({"item": item, "value": None, "layer": MISSING, "basis": "",
                       "provenance": ""})
    return result


def loader_error(model) -> str | None:
    """The loader's error line if ``param_layers()`` of ``model`` fails with a ``ValueError``,
    else ``None``; any other error is raised.

    modelx wraps the ``ValueError`` in a ``FormulaError`` whose text also holds the formula
    traceback; only the line before ``Formula traceback:`` is the raised error.
    """
    try:
        model.Data.param_layers()
    except ValueError as error:
        return f"ValueError: {error}"
    except FormulaError as error:
        head = str(error).split("Formula traceback:", 1)[0]
        line = ([text for text in head.splitlines() if text.strip()] or [""])[-1]
        if not line.startswith("ValueError: "):
            raise
        return line
    return None


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
        folders = {}
        for name in names:
            folder = resolve_product(name)
            model_dir(folder)
            twice = [given for given, other in folders.items()
                     if other.resolve() == folder.resolve()]
            if twice:
                raise UsageError(f"product {name!r} named twice (as {twice[0]!r})")
            folders[name] = folder
    except UsageError as exc:
        parser.print_usage(sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 2
    status = 0
    listed = False
    for name, folder in folders.items():
        product = Path(name).name if run_baseline.is_path(name) else name
        model = mx.read_model(model_dir(folder))
        try:
            error = loader_error(model)
            if error is None:
                usage = param_usage.scan(model)
                table = rows(model, usage)
        finally:
            model.close()
        if error is not None:
            print(f"{product}: {error}", file=sys.stderr)
            status = 1
            continue
        if listed:
            print()
        listed = True
        print("\n".join(lines(product, table)))
        for problem in usage.problems:
            print(f"{product}: {problem}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
