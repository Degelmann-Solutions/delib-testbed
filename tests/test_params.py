"""The parameter tool ``tools/params.py`` (``docs/core.md``, "The parameter files").

- For every product the tool's items are the items of the usage scan's ``reads``, each row's
  value and layer those of ``param_layers()``, each row's basis and provenance those of the
  item's row in the core file or the product's ``param_tariff_type.csv``, and the rows stand
  in layer order, within a layer in the order of its file.
- ``main(["--all"])`` exits 0, names every product and writes nothing on stderr; an unknown
  product exits 2, and so does a product named twice, by the same name or by a name and a
  path of the same folder.
- A scratch copy whose tariff-type file lost a read item lists it with layer ``missing`` and
  no value, names it in one stderr line and exits 1.
- A scratch copy with a tariff-type item nobody reads, or with a ``Projection`` cell reading a
  parameter by a computed name, is listed and its scan problem stands on stderr; exit 1.
- A scratch copy whose loader fails (an item standing twice) is not listed, its error line
  stands on stderr, the next product is listed; exit 1, also under ``--all``; so is a
  scratch copy without its tariff-type file.
- A scratch copy whose read item moved from the tariff-type file into a new tariff file lists
  it with layer ``tariff``, its value, basis and provenance, after the tariff-type rows, and
  exits 0.
- A scratch copy of Index whose tariff chooses a fixture table lists that table's items with
  layer ``tables``, value, basis and provenance, after the core items and before the
  tariff-type items, and no other table's, and exits 0; a copy with the fixture tables and
  no choice lists no item of the layer.
- A scratch copy whose choice names a table the factory lacks, whose table parameter file
  holds an item of no table, or whose chosen table names an item the layer lacks (listed as
  ``missing``) has the scan's line on stderr and exits 1.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import modelx as mx
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
PRODUCTS = sorted(p.name for p in PRODUCTS_DIR.iterdir() if p.is_dir())
CORE_FILE = ROOT / "core" / "Core" / "Data" / "param_core.csv"

sys.path.insert(0, str(ROOT / "tools"))
from run_baseline import model_dir  # noqa: E402

from test_core import _add_params  # noqa: E402
from test_tables import (FIXTURE_DEFINITIONS, FIXTURE_VALUES, INDEX, choosing_copy,  # noqa: E402
                         fixture_copy, fixture_items, tables_file)


def load_tool(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


params = load_tool("params", ROOT / "tools" / "params.py")
param_usage = load_tool("param_usage", ROOT / "core" / "param_usage.py")


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False).set_index("item")


def test_ten_products():
    assert len(PRODUCTS) == 10


@pytest.mark.parametrize("product", PRODUCTS)
def test_the_rows_agree_with_the_scan_and_the_loader(product):
    """No shipped product has a tariff file, so the layers are the core file, the table
    parameter file beside it and the product's ``param_tariff_type.csv``."""
    folder = PRODUCTS_DIR / product
    model = mx.read_model(model_dir(folder))
    try:
        table = params.rows(model)
        reads = param_usage.scan(model).reads
        layers = model.Data.param_layers()
    finally:
        model.close()
    assert list(layers) == ["core", "tables", "tariff_type"]
    frames = {"core": read(CORE_FILE), "tables": read(CORE_FILE.with_name("param_tables.csv")),
              "tariff_type": read(folder / "param_tariff_type.csv")}
    assert [row["item"] for row in table] and len(table) == len(reads)
    assert {row["item"] for row in table} == set(reads)
    order = [(layer, item) for layer, values in layers.items()
             for item in values if item in reads]
    assert [(row["layer"], row["item"]) for row in table] == order
    for row in table:
        value = layers[row["layer"]][row["item"]]
        assert row["value"] == value and type(row["value"]) is type(value)
        frame = frames[row["layer"]]
        assert row["basis"] == frame.at[row["item"], "basis"]
        assert row["provenance"] == frame.at[row["item"], "provenance"]


def test_all_exits_0_and_names_every_product(capsys):
    assert params.main(["--all"]) == 0
    out, err = capsys.readouterr()
    assert headers(out) == PRODUCTS
    assert err == ""


def test_one_product_lists_its_items(capsys):
    assert params.main(["risikolebensversicherung"]) == 0
    out, _err = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0].startswith("risikolebensversicherung: ")
    assert lines[1].split() == list(params.COLUMNS)
    assert any(line.split()[:4] == ["mort_load_first", "2.25", "tariff_type", "Setzung"]
               for line in lines[2:])


def test_an_unknown_product_exits_2(capsys):
    assert params.main(["nosuch"]) == 2
    _out, err = capsys.readouterr()
    assert "nosuch" in err


def rlv_copy(tmp_path) -> Path:
    folder = tmp_path / "risikolebensversicherung"
    shutil.copytree(PRODUCTS_DIR / "risikolebensversicherung", folder)
    return folder


def add_row(folder: Path, item: str, value: str) -> None:
    path = folder / "param_tariff_type.csv"
    path.write_text(path.read_text(encoding="utf-8") + f"{item},{value},Setzung,test fixture\n",
                    encoding="utf-8")


def headers(out: str) -> list[str]:
    return [line.split(":", 1)[0] for line in out.splitlines() if line.endswith(" items read")]


def test_a_product_named_twice_exits_2(capsys):
    assert params.main(["risikolebensversicherung", "risikolebensversicherung"]) == 2
    out, err = capsys.readouterr()
    assert out == "" and "named twice" in err and err.startswith("usage:")
    path = str(PRODUCTS_DIR / "risikolebensversicherung")
    assert params.main(["risikolebensversicherung", path]) == 2
    out, err = capsys.readouterr()
    assert out == "" and "named twice" in err


def test_an_unread_item_is_reported_and_exits_1(tmp_path, capsys):
    folder = rlv_copy(tmp_path)
    add_row(folder, "probe_unused", "1.5")
    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == ["risikolebensversicherung"]
    assert "probe_unused" not in out
    assert err.splitlines() == [
        "risikolebensversicherung: item 'probe_unused' of the tariff_type layer"
        " (param_tariff_type.csv) is read by no reachable cell"]


def test_an_undeclared_indirect_read_is_reported_and_exits_1(tmp_path, capsys):
    folder = rlv_copy(tmp_path)
    path = model_dir(folder) / "Projection" / "__init__.py"
    marker = "# ---------------------------------------------------------------------------\n# References"
    text = path.read_text(encoding="utf-8")
    assert text.count(marker) == 1
    cell = ('def probe_indirect():\n'
            '    name = "expense_infl"\n'
            '    return data.param(name)                                      # noqa: F821\n'
            '\n\n')
    path.write_text(text.replace(marker, cell + marker), encoding="utf-8")
    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == ["risikolebensversicherung"]
    assert err.splitlines() == [
        "risikolebensversicherung: cell probe_indirect reads a parameter by a computed name"
        " and is not declared in param_indirect()"]


def test_a_loader_error_is_reported_and_the_next_product_listed(tmp_path, capsys,
                                                                monkeypatch):
    folder = rlv_copy(tmp_path)
    add_row(folder, "decl_scale", "1.0")
    expected = (f"risikolebensversicherung: ValueError: parameter 'decl_scale' stands twice"
                f" in {folder / 'param_tariff_type.csv'}")
    assert params.main([str(folder), "kapitallebensversicherung"]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == ["kapitallebensversicherung"]
    assert not out.startswith("\n")
    assert err.splitlines() == [expected]

    monkeypatch.setattr(params, "product_names",
                        lambda: [str(folder), "kapitallebensversicherung"])
    assert params.main(["--all"]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == ["kapitallebensversicherung"]
    assert err.splitlines() == [expected]


def test_a_missing_tariff_type_file_is_a_loader_error(tmp_path, capsys):
    folder = rlv_copy(tmp_path)
    path = folder / "param_tariff_type.csv"
    path.unlink()
    assert params.main([str(folder), "kapitallebensversicherung"]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == ["kapitallebensversicherung"]
    assert len(err.splitlines()) == 1
    assert err.startswith(f"risikolebensversicherung: ValueError: parameter file {path}"
                          f" cannot be read: ")


def test_a_read_item_in_no_layer_is_missing_and_exits_1(tmp_path, capsys):
    folder = rlv_copy(tmp_path)
    path = folder / "param_tariff_type.csv"
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    assert "decl_scale" in set(frame["item"])
    frame[frame["item"] != "decl_scale"].to_csv(path, index=False)

    model = mx.read_model(model_dir(folder), name="ParamsMissing")
    try:
        table = params.rows(model)
    finally:
        model.close()
    assert table[-1] == {"item": "decl_scale", "value": None, "layer": "missing",
                         "basis": "", "provenance": ""}
    assert [row for row in table if row["layer"] == "missing"] == [table[-1]]

    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert any(line.split() == ["decl_scale", "missing"] for line in out.splitlines())
    assert len(err.splitlines()) == 1
    assert "'decl_scale'" in err and "stands in no layer" in err


def test_an_item_of_the_tariff_file_is_listed_in_the_tariff_layer(tmp_path, capsys):
    folder = rlv_copy(tmp_path)
    path = folder / "param_tariff_type.csv"
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    moved = frame["item"] == "decl_scale"
    assert moved.sum() == 1
    frame[moved].to_csv(folder / "param_tariff.csv", index=False)
    frame[~moved].to_csv(path, index=False)
    expected = frame[moved].iloc[0]

    model = mx.read_model(model_dir(folder), name="ParamsTariff")
    try:
        table = params.rows(model)
    finally:
        model.close()
    assert table[-1] == {"item": "decl_scale", "value": float(expected["value"]),
                         "layer": "tariff", "basis": expected["basis"],
                         "provenance": expected["provenance"]}
    assert [row["layer"] for row in table[:-1]] == sorted(
        (row["layer"] for row in table[:-1]), key=["core", "tables", "tariff_type"].index)
    assert table[-2]["layer"] == "tariff_type"

    assert params.main([str(folder)]) == 0
    out, err = capsys.readouterr()
    assert any(line.split()[:3] == ["decl_scale", repr(float(expected["value"])), "tariff"]
               for line in out.splitlines())
    assert err == ""


# --------------------------------------------------------------------------- the tables layer

def tables_rows(folder: Path, name: str) -> tuple[list[dict], list[dict]]:
    """The tool's rows for a scratch copy, and those of them in the layer ``tables``."""
    model = mx.read_model(model_dir(folder), name=name)
    try:
        table = params.rows(model)
    finally:
        model.close()
    return table, [row for row in table if row["layer"] == "tables"]


def test_the_items_of_a_chosen_table_are_listed_in_the_tables_layer(tmp_path, capsys):
    folder = choosing_copy(tmp_path, "period_fixture")
    table, listed = tables_rows(folder, "ParamsChosenTable")
    values = FIXTURE_VALUES["period_fixture"]
    assert [row["item"] for row in listed] == list(fixture_items("period_fixture"))
    for row, name in zip(listed, FIXTURE_DEFINITIONS["period_fixture"][2]):
        expected = int(values[name]) if values[name].isdigit() else float(values[name])
        assert row == {"item": f"period_fixture_{name}", "value": expected, "layer": "tables",
                       "basis": "", "provenance": "[std] test fixture"}
        assert type(row["value"]) is type(expected)
    # after the core items and before the tariff-type items, each layer present
    layers = [row["layer"] for row in table]
    assert layers == sorted(layers, key=["core", "tables", "tariff_type"].index)
    assert set(layers) == {"core", "tables", "tariff_type"}
    assert {"item": "mort_table", "value": "period_fixture", "layer": "tariff_type",
            "basis": "", "provenance": "[std] test fixture"} in table

    assert params.main([str(folder)]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    assert headers(out) == [INDEX]
    lines = [line.split() for line in out.splitlines()]
    position = {line[0]: number for number, line in enumerate(lines) if line}
    for row in listed:
        assert lines[position[row["item"]]] == [row["item"], repr(row["value"]), "tables",
                                                "[std]", "test", "fixture"]
    assert (position["check_tol"] < position["period_fixture_m_a"]
            < position["mort_table"])
    assert lines[position["mort_table"]][1:3] == ["'period_fixture'", "tariff_type"]
    # no other table's item
    others = set(FIXTURE_DEFINITIONS) - {"period_fixture"}
    assert others and not any(table in out for table in others)


def test_no_tables_item_is_listed_without_a_choice(tmp_path, capsys):
    folder = fixture_copy(tmp_path)
    table, listed = tables_rows(folder, "ParamsNoChoice")
    assert table and listed == []
    assert params.main([str(folder)]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [INDEX]
    assert "_fixture" not in out and " tables " not in out


def test_a_chosen_name_the_factory_lacks_is_reported_and_exits_1(tmp_path, capsys):
    folder = choosing_copy(tmp_path, "nosuch_table")
    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == [INDEX]
    assert any(line.split()[:3] == ["mort_table", "'nosuch_table'", "tariff_type"]
               for line in out.splitlines())
    assert "_fixture" not in out
    assert err.splitlines() == [
        f"{INDEX}: item 'mort_table' of the tariff_type layer (param_tariff_type.csv) names"
        f" the table 'nosuch_table', which the factory does not hold"]


def test_a_tables_item_of_no_table_is_reported_and_exits_1(tmp_path, capsys):
    folder = choosing_copy(tmp_path, "period_fixture")
    _add_params(tables_file(folder, INDEX), {"stray_item": "1.5"})
    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == [INDEX]
    assert "stray_item" not in out and "period_fixture_m_a" in out
    assert err.splitlines() == [
        f"{INDEX}: item 'stray_item' of the tables layer (param_tables.csv) belongs to no"
        f" table"]


def test_an_item_a_chosen_table_lacks_is_missing_and_exits_1(tmp_path, capsys):
    folder = choosing_copy(tmp_path, "broken_fixture")
    table, listed = tables_rows(folder, "ParamsBrokenTable")
    assert table[-1] == {"item": "broken_fixture_f_b", "value": None, "layer": "missing",
                         "basis": "", "provenance": ""}
    assert [row["item"] for row in listed] == [
        item for item in fixture_items("broken_fixture") if item != "broken_fixture_f_b"]

    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert any(line.split() == ["broken_fixture_f_b", "missing"] for line in out.splitlines())
    assert err.splitlines() == [
        f"{INDEX}: item 'broken_fixture_f_b' read by mort_table_name stands in no layer"]
