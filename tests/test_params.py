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
- Index lists its choice ``mort_table`` and its ``mort_be_factor`` in the layer
  ``tariff_type`` and the eight items of ``dav2008t_proxy`` in the layer ``tables``, each
  with its value, basis and provenance, and exits 0; BU lists its two choices,
  ``mort_table`` and ``mort_dis_table``, its derivation items and the items of both tables,
  eight of ``dav2008t_proxy`` and fourteen of ``dav1997ti_proxy``; RV lists its choice
  ``mort_table``, ``mort_be_factor`` and ``unisex_mix_male`` and the fourteen items of
  ``dav2004r_proxy``, and neither ``mort_base_year`` nor ``omega_age``; KLV lists its choice
  ``mort_table`` with the provenance of the values package, its unchanged ``mort_be_factor``
  and ``unisex_mix_male`` and the eight items of ``dav2008t_proxy``; FRV lists its choice
  ``mort_table``, its new ``unisex_mix_male`` and its ``mort_be_factor``, each with the
  provenance of the values package, and the eight items of ``dav2008t_proxy``; RLV lists
  its two choices ``mort_nr_table`` and ``mort_r_table``, ``mort_be_factor`` and the sixteen
  items of its two tables, and no ``mort_load_first``; Basis lists its choice ``mort_table``,
  its ``mort_be_factor`` and the fourteen items of ``dav2004r_proxy``, and neither
  ``mort_base_year`` nor ``unisex_mix_male``; Riester lists its two choices ``mort_table`` and
  ``annuity_mort_table``, its two factors, its new ``unisex_mix_male`` and the items of both
  tables, eight of ``dav2008t_proxy`` and fourteen of ``dav2004r_proxy``, and no
  ``mort_base_year``; the two products that choose no table list no item of the layer.
- A scratch copy of Index whose tariff chooses a fixture table lists that table's items with
  layer ``tables``, value, basis and provenance, after the core items and before the
  tariff-type items, and no other table's, the shipped one's neither, and exits 0; a copy
  with the fixture tables and no choice lists no item of the layer.
- A scratch copy whose choice stands in a tariff file lists the choice with layer ``tariff``
  and its table's items with layer ``tables``, and exits 0.
- A scratch copy whose choice names a table the factory lacks, whose table parameter file
  holds an item of no table, whose chosen table names an item the layer lacks (listed as
  ``missing``), whose tariff-type file holds an item of a table, whose core file holds a
  table choice, or whose ``Projection`` reads an item of the tables layer itself has the
  scan's line on stderr and exits 1.
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
from test_tables import (BASIS, BU, FIXTURE_DEFINITIONS, FIXTURE_VALUES, FRV,  # noqa: E402
                         INDEX, KLV, RIESTER, RV, SHIPPED_ITEMS, SHIPPED_PROVENANCE,
                         SHIPPED_ROWS, SWITCHED,
                         choosing_copy, fixture_copy, fixture_items, tables_file,
                         unswitched_copy)


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
    rows = [line.split()[:4] for line in lines[2:]]
    assert ["mort_be_factor", "0.75", "tariff_type", "Setzung"] in rows
    # both table choices, the best-estimate factor and the sixteen items of the two tables
    assert ["mort_nr_table", "'dav2008t_nr_proxy'", "tariff_type", "Setzung"] in rows
    assert ["mort_r_table", "'dav2008t_r_proxy'", "tariff_type", "Setzung"] in rows
    for table in ("dav2008t_nr_proxy", "dav2008t_r_proxy"):
        assert len([row for row in rows if row[0].startswith(table + "_")
                    and row[2] == "tables"]) == 8
    assert not [row for row in rows if row[0] in ("mort_load_first", "mort_table")]
    assert not [row for row in rows if row[0].startswith("dav2008t_proxy_")]


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


def test_index_lists_its_choice_its_factor_and_the_items_of_its_table(capsys):
    table, listed = tables_rows(PRODUCTS_DIR / INDEX, "ParamsShippedIndex")
    assert [row["item"] for row in listed] == list(SHIPPED_ITEMS["dav2008t_proxy"])
    for row in listed:
        text, basis = SHIPPED_ROWS[row["item"]]
        assert row["value"] == (int(text) if text.isdigit() else float(text))
        assert row["basis"] == basis
        assert row["provenance"].startswith(SHIPPED_PROVENANCE["dav2008t_proxy"])
    by_item = {row["item"]: row for row in table}
    assert (by_item["mort_table"]["value"], by_item["mort_table"]["layer"],
            by_item["mort_table"]["basis"]) == ("dav2008t_proxy", "tariff_type", "Setzung")
    assert (by_item["mort_be_factor"]["value"], by_item["mort_be_factor"]["layer"],
            by_item["mort_be_factor"]["basis"]) == (0.75, "tariff_type", "source")
    assert by_item["mort_table"]["provenance"] and by_item["mort_be_factor"]["provenance"]

    assert params.main([INDEX]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [INDEX]
    split = [line.split() for line in out.splitlines()]
    assert ["mort_table", "'dav2008t_proxy'", "tariff_type", "Setzung"] in [
        line[:4] for line in split]
    assert ["mort_be_factor", "0.75", "tariff_type", "source"] in [line[:4] for line in split]
    for item in SHIPPED_ITEMS["dav2008t_proxy"]:
        text, basis = SHIPPED_ROWS[item]
        value = int(text) if text.isdigit() else float(text)
        assert [item, repr(value), "tables", basis] in [line[:4] for line in split], item
    assert len([line for line in split if "dav2008t_proxy" in " ".join(line[:2])]) == 9
    # no item of the tables it does not choose
    assert "dav1997ti_proxy" not in out and "dav2004r_proxy" not in out


def test_bu_lists_its_two_choices_and_the_items_of_both_tables(capsys):
    table, listed = tables_rows(PRODUCTS_DIR / BU, "ParamsShippedBu")
    assert SWITCHED[BU] == {"mort_table": "dav2008t_proxy", "mort_dis_table": "dav1997ti_proxy"}
    assert [row["item"] for row in listed] == [
        item for chosen in ("dav2008t_proxy", "dav1997ti_proxy") for item in SHIPPED_ITEMS[chosen]]
    assert len(listed) == 8 + 14
    for row in listed:
        text, basis = SHIPPED_ROWS[row["item"]]
        assert row["value"] == (int(text) if text.isdigit() else float(text))
        assert row["basis"] == basis
        (chosen,) = [name for name in SHIPPED_ITEMS if row["item"] in SHIPPED_ITEMS[name]]
        assert row["provenance"].startswith(SHIPPED_PROVENANCE[chosen])
    by_item = {row["item"]: row for row in table}
    expected = {"mort_table": ("dav2008t_proxy", "Setzung"),
                "mort_dis_table": ("dav1997ti_proxy", "Setzung"),
                "mort_be_factor": (0.75, "source"), "unisex_mix_male": (0.5, "Setzung"),
                "mort_actv_load_first": (0.6, "Setzung"), "mort_dis_load_first": (0.7, "source")}
    for item, (value, basis) in expected.items():
        row = by_item[item]
        assert (row["value"], row["layer"], row["basis"]) == (value, "tariff_type", basis), item
        assert row["provenance"], item

    assert params.main([BU]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [BU]
    split = [line.split() for line in out.splitlines()]
    for item, (value, basis) in expected.items():
        assert [item, repr(value), "tariff_type", basis] in [line[:4] for line in split], item
    for chosen in ("dav2008t_proxy", "dav1997ti_proxy"):
        for item in SHIPPED_ITEMS[chosen]:
            text, basis = SHIPPED_ROWS[item]
            value = int(text) if text.isdigit() else float(text)
            assert [item, repr(value), "tables", basis] in [line[:4] for line in split], item
    # the two choices and the items of both tables, 2 + 8 + 14 lines
    assert len([line for line in out.splitlines()
                if "dav2008t_proxy" in line or "dav1997ti_proxy" in line]) == 24
    assert "dav2004r_proxy" not in out


def test_riester_lists_its_two_choices_its_factors_and_the_items_of_both_tables(capsys):
    table, listed = tables_rows(PRODUCTS_DIR / RIESTER, "ParamsShippedRiester")
    assert SWITCHED[RIESTER] == {"mort_table": "dav2008t_proxy",
                                 "annuity_mort_table": "dav2004r_proxy"}
    assert sorted(row["item"] for row in listed) == sorted(
        item for chosen in ("dav2008t_proxy", "dav2004r_proxy") for item in SHIPPED_ITEMS[chosen])
    assert len(listed) == 8 + 14
    for row in listed:
        text, basis = SHIPPED_ROWS[row["item"]]
        assert row["value"] == (int(text) if text.isdigit() else float(text))
        assert row["basis"] == basis == "Setzung"
        (chosen,) = [name for name in SHIPPED_ITEMS if row["item"] in SHIPPED_ITEMS[name]]
        assert row["provenance"].startswith(SHIPPED_PROVENANCE[chosen])
    by_item = {row["item"]: row for row in table}
    expected = {"mort_table": ("dav2008t_proxy", "Setzung"),
                "annuity_mort_table": ("dav2004r_proxy", "Setzung"),
                "mort_be_factor": (0.75, "source"), "annuity_mort_be_factor": (1.15, "Setzung"),
                "unisex_mix_male": (0.45, "Setzung")}
    for item, (value, basis) in expected.items():
        row = by_item[item]
        assert (row["value"], row["layer"], row["basis"]) == (value, "tariff_type", basis), item
        assert row["provenance"], item
    # the values package's provenance of the three new rows, verbatim
    assert by_item["mort_table"]["provenance"] == (
        "accumulation phase: the death table, the proxy of DAV 2008 T its file names")
    assert by_item["annuity_mort_table"]["provenance"] == (
        "payout phase: the annuitant table, the proxy of DAV 2004 R its file names, read at the"
        " birth year, issue year less issue age")
    assert by_item["unisex_mix_male"]["provenance"] == (
        "male share of the unisex blend of the annuity factor at Rentenbeginn, as Sofort's 0.45"
        " on the same table; Riester's files are unisex today (open point 7)")
    # the item the table's own base year replaced
    assert "mort_base_year" not in by_item
    assert by_item["dav2004r_proxy_base_year"]["value"] == 2005
    assert by_item["dav2004r_proxy_end_age"]["value"] == 121

    assert params.main([RIESTER]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [RIESTER]
    split = [line.split() for line in out.splitlines()]
    for item, (value, basis) in expected.items():
        assert [item, repr(value), "tariff_type", basis] in [line[:4] for line in split], item
    for chosen in ("dav2008t_proxy", "dav2004r_proxy"):
        for item in SHIPPED_ITEMS[chosen]:
            text, basis = SHIPPED_ROWS[item]
            value = int(text) if text.isdigit() else float(text)
            assert [item, repr(value), "tables", basis] in [line[:4] for line in split], item
    # the two choices and the items of both tables, 2 + 8 + 14 lines
    assert len([line for line in out.splitlines()
                if "dav2008t_proxy" in line or "dav2004r_proxy" in line]) == 24
    assert "dav1997ti_proxy" not in out
    assert not [line for line in split if line[:1] == ["mort_base_year"]]


def test_rv_lists_its_choice_its_derivation_items_and_the_items_of_its_table(capsys):
    table, listed = tables_rows(PRODUCTS_DIR / RV, "ParamsShippedRv")
    assert SWITCHED[RV] == {"mort_table": "dav2004r_proxy"}
    assert [row["item"] for row in listed] == list(SHIPPED_ITEMS["dav2004r_proxy"])
    assert len(listed) == 14
    for row in listed:
        text, basis = SHIPPED_ROWS[row["item"]]
        assert row["value"] == (int(text) if text.isdigit() else float(text))
        assert row["basis"] == basis == "Setzung"
        assert row["provenance"].startswith(SHIPPED_PROVENANCE["dav2004r_proxy"])
    by_item = {row["item"]: row for row in table}
    expected = {"mort_table": "dav2004r_proxy", "mort_be_factor": 1.15, "unisex_mix_male": 0.45}
    for item, value in expected.items():
        row = by_item[item]
        assert (row["value"], row["layer"], row["basis"]) == (value, "tariff_type", "Setzung")
        assert row["provenance"], item
    # the values package's provenance of the two new rows, verbatim
    assert by_item["mort_table"]["provenance"] == (
        "the first-order annuitant table, the proxy of DAV 2004 R with its trend, read at the"
        " birth year, issue year less issue age")
    assert by_item["unisex_mix_male"]["provenance"] == (
        "male share of the unisex blend of the tariff rate, as Sofort's 0.45 on the same"
        " table: sex does not enter the risk charge; before the switch the tariff rate was"
        " read on the own sex (open point 1)")
    # the two items the table's own replaced
    assert "mort_base_year" not in by_item and "omega_age" not in by_item
    assert by_item["dav2004r_proxy_base_year"]["value"] == 2005
    assert by_item["dav2004r_proxy_end_age"]["value"] == 121

    assert params.main([RV]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [RV]
    split = [line.split() for line in out.splitlines()]
    for item, value in expected.items():
        assert [item, repr(value), "tariff_type", "Setzung"] in [line[:4] for line in split], item
    for item in SHIPPED_ITEMS["dav2004r_proxy"]:
        text, basis = SHIPPED_ROWS[item]
        value = int(text) if text.isdigit() else float(text)
        assert [item, repr(value), "tables", basis] in [line[:4] for line in split], item
    # the choice and the fourteen items of its table, and no other table's
    assert len([line for line in out.splitlines() if "dav2004r_proxy" in line]) == 15
    assert "dav2008t_proxy" not in out and "dav1997ti_proxy" not in out
    assert not [line for line in split if line[:1] in (["mort_base_year"], ["omega_age"])]


def test_basis_lists_its_choice_its_factor_and_the_items_of_its_table(capsys):
    table, listed = tables_rows(PRODUCTS_DIR / BASIS, "ParamsShippedBasis")
    assert SWITCHED[BASIS] == {"mort_table": "dav2004r_proxy"}
    assert [row["item"] for row in listed] == list(SHIPPED_ITEMS["dav2004r_proxy"])
    assert len(listed) == 14
    for row in listed:
        text, basis = SHIPPED_ROWS[row["item"]]
        assert row["value"] == (int(text) if text.isdigit() else float(text))
        assert row["basis"] == basis == "Setzung"
        assert row["provenance"].startswith(SHIPPED_PROVENANCE["dav2004r_proxy"])
    by_item = {row["item"]: row for row in table}
    expected = {"mort_table": "dav2004r_proxy", "mort_be_factor": 1.15}
    for item, value in expected.items():
        row = by_item[item]
        assert (row["value"], row["layer"], row["basis"]) == (value, "tariff_type", "Setzung")
        assert row["provenance"], item
    # the values package's provenance of the new row, verbatim
    assert by_item["mort_table"]["provenance"] == (
        "the tariff's first-order annuitant table, the proxy of DAV 2004 R its docs name; read"
        " at the model point's sex and its birth year, issue year less issue age")
    # the item the table's own replaced, and no unisex mix: Basis forms no tariff rate
    assert "mort_base_year" not in by_item and "unisex_mix_male" not in by_item
    assert by_item["dav2004r_proxy_base_year"]["value"] == 2005
    assert by_item["dav2004r_proxy_end_age"]["value"] == 121

    assert params.main([BASIS]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [BASIS]
    split = [line.split() for line in out.splitlines()]
    for item, value in expected.items():
        assert [item, repr(value), "tariff_type", "Setzung"] in [line[:4] for line in split], item
    for item in SHIPPED_ITEMS["dav2004r_proxy"]:
        text, basis = SHIPPED_ROWS[item]
        value = int(text) if text.isdigit() else float(text)
        assert [item, repr(value), "tables", basis] in [line[:4] for line in split], item
    # the choice and the fourteen items of its table, and no other table's
    assert len([line for line in out.splitlines() if "dav2004r_proxy" in line]) == 15
    assert "dav2008t_proxy" not in out and "dav1997ti_proxy" not in out
    assert not [line for line in split
                if line[:1] in (["mort_base_year"], ["unisex_mix_male"])]


def test_klv_lists_its_choice_its_derivation_items_and_the_items_of_its_table(capsys):
    table, listed = tables_rows(PRODUCTS_DIR / KLV, "ParamsShippedKlv")
    assert SWITCHED[KLV] == {"mort_table": "dav2008t_proxy"}
    assert [row["item"] for row in listed] == list(SHIPPED_ITEMS["dav2008t_proxy"])
    assert len(listed) == 8
    for row in listed:
        text, basis = SHIPPED_ROWS[row["item"]]
        assert row["value"] == (int(text) if text.isdigit() else float(text))
        assert row["basis"] == basis == "Setzung"
        assert row["provenance"].startswith(SHIPPED_PROVENANCE["dav2008t_proxy"])
    by_item = {row["item"]: row for row in table}
    expected = {"mort_table": ("dav2008t_proxy", "Setzung"),
                "mort_be_factor": (0.75, "source"), "unisex_mix_male": (0.5, "Setzung")}
    for item, (value, basis) in expected.items():
        row = by_item[item]
        assert (row["value"], row["layer"], row["basis"]) == (value, "tariff_type", basis), item
        assert row["provenance"], item
    # the values package's provenance of the new row, verbatim; the two kept rows keep theirs
    assert by_item["mort_table"]["provenance"] == (
        "the first-order death table of the tariff, the proxy of DAV 2008 T; the table is"
        " KLV's present file")
    assert by_item["mort_be_factor"]["provenance"].startswith(
        "[std] the step from the first-order table to the best estimate, a 33 Prozent")
    assert by_item["unisex_mix_male"]["provenance"].startswith(
        "[std] the male share of the unisex tariff blend; new business is unisex [REG-R34]")

    assert params.main([KLV]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [KLV]
    split = [line.split() for line in out.splitlines()]
    for item, (value, basis) in expected.items():
        assert [item, repr(value), "tariff_type", basis] in [line[:4] for line in split], item
    for item in SHIPPED_ITEMS["dav2008t_proxy"]:
        text, basis = SHIPPED_ROWS[item]
        value = int(text) if text.isdigit() else float(text)
        assert [item, repr(value), "tables", basis] in [line[:4] for line in split], item
    # the choice and the eight items of its table, and no other table's
    assert len([line for line in out.splitlines() if "dav2008t_proxy" in line]) == 9
    assert "dav1997ti_proxy" not in out and "dav2004r_proxy" not in out


def test_frv_lists_its_choice_its_derivation_items_and_the_items_of_its_table(capsys):
    table, listed = tables_rows(PRODUCTS_DIR / FRV, "ParamsShippedFrv")
    assert SWITCHED[FRV] == {"mort_table": "dav2008t_proxy"}
    assert [row["item"] for row in listed] == list(SHIPPED_ITEMS["dav2008t_proxy"])
    assert len(listed) == 8
    for row in listed:
        text, basis = SHIPPED_ROWS[row["item"]]
        assert row["value"] == (int(text) if text.isdigit() else float(text))
        assert row["basis"] == basis == "Setzung"
        assert row["provenance"].startswith(SHIPPED_PROVENANCE["dav2008t_proxy"])
    by_item = {row["item"]: row for row in table}
    expected = {"mort_table": ("dav2008t_proxy", "Setzung"),
                "mort_be_factor": (0.75, "source"), "unisex_mix_male": (0.5, "Setzung")}
    for item, (value, basis) in expected.items():
        row = by_item[item]
        assert (row["value"], row["layer"], row["basis"]) == (value, "tariff_type", basis), item
    # the values package's provenance of the three rows, verbatim
    assert by_item["mort_table"]["provenance"] == (
        "the first-order death table of the Risikobeitrag, the proxy of DAV 2008 T its file"
        " names")
    assert by_item["mort_be_factor"]["provenance"] == (
        "[std] [REG-R47] a flat step from the first-order death table to the best estimate,"
        " on the own sex; 0.75 steps down from the first-order margin of DAV 2008 T, bib"
        " DAV-Fortbildung/DAV vor Ort/Niedersachsen-Bremen/"
        "NBr-2022-11-08_Keil_Klimwandel-und-LV.pdf p. 4; the value is unchanged, the"
        " provenance is new: with a unisex tariff rate the factor no longer makes the"
        " Risikoergebnis exactly 25 Prozent of the Risikobeitrag (open point 10)")
    assert by_item["unisex_mix_male"]["provenance"] == (
        "male share of the unisex blend of the tariff rate, 50/50 absent a portfolio, as KLV"
        " on the same death table; FRV's file is unisex today (open point 7)")

    assert params.main([FRV]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [FRV]
    split = [line.split() for line in out.splitlines()]
    for item, (value, basis) in expected.items():
        assert [item, repr(value), "tariff_type", basis] in [line[:4] for line in split], item
    for item in SHIPPED_ITEMS["dav2008t_proxy"]:
        text, basis = SHIPPED_ROWS[item]
        value = int(text) if text.isdigit() else float(text)
        assert [item, repr(value), "tables", basis] in [line[:4] for line in split], item
    # the choice and the eight items of its table, and no other table's
    assert len([line for line in out.splitlines() if "dav2008t_proxy" in line]) == 9
    assert "dav1997ti_proxy" not in out and "dav2004r_proxy" not in out


@pytest.mark.parametrize("product", [name for name in PRODUCTS if name not in SWITCHED])
def test_a_product_that_chooses_no_table_lists_no_tables_item(product, capsys):
    table, listed = tables_rows(PRODUCTS_DIR / product, "ParamsNoTable")
    assert table and listed == []
    assert params.main([product]) == 0
    out, err = capsys.readouterr()
    assert err == "" and "_proxy" not in out
    assert not [line for line in out.splitlines() if line.split()[2:3] == ["tables"]]


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
    others = set(FIXTURE_DEFINITIONS) - {"period_fixture"} | set(SHIPPED_ITEMS)
    assert others and not any(table in out for table in others)


def test_no_tables_item_is_listed_without_a_choice(tmp_path, capsys):
    folder = unswitched_copy(tmp_path)
    table, listed = tables_rows(folder, "ParamsNoChoice")
    assert table and listed == []
    assert params.main([str(folder)]) == 0
    out, err = capsys.readouterr()
    assert err == "" and headers(out) == [INDEX]
    assert "_fixture" not in out and " tables " not in out and "_proxy" not in out


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


def test_a_choice_in_the_tariff_file_is_listed_in_the_tariff_layer(tmp_path, capsys):
    folder = choosing_copy(tmp_path, "period_fixture", "param_tariff.csv")
    table, listed = tables_rows(folder, "ParamsTariffChoice")
    assert [row["item"] for row in listed] == list(fixture_items("period_fixture"))
    assert table[-1] == {"item": "mort_table", "value": "period_fixture", "layer": "tariff",
                         "basis": "", "provenance": "[std] test fixture"}
    layers = [row["layer"] for row in table]
    assert layers == sorted(layers, key=["core", "tables", "tariff_type", "tariff"].index)

    assert params.main([str(folder)]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    split = [line.split() for line in out.splitlines()]
    assert ["mort_table", "'period_fixture'", "tariff"] in [line[:3] for line in split]
    for row in listed:
        assert [row["item"], repr(row["value"]), "tables"] in [line[:3] for line in split]


def test_an_item_of_a_table_in_another_layer_is_reported_and_exits_1(tmp_path, capsys):
    folder = choosing_copy(tmp_path, "broken_fixture")
    add_row(folder, "broken_fixture_f_b", "1.092")
    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == [INDEX]
    assert err.splitlines() == [
        f"{INDEX}: item 'broken_fixture_f_b' of the table 'broken_fixture' stands in the"
        f" tariff_type layer (param_tariff_type.csv), not in the tables layer"]


def test_a_table_choice_in_the_core_file_is_reported_and_exits_1(tmp_path, capsys):
    folder = unswitched_copy(tmp_path)
    _add_params(model_dir(folder) / "CoreData" / "param_core.csv",
                {"mort_table": "period_fixture"})
    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == [INDEX] and "_fixture" not in out
    assert err.splitlines() == [
        f"{INDEX}: item 'mort_table' of the core layer (param_core.csv) is a table choice"
        f" outside the tariff-type and tariff files"]


def test_a_cell_reading_a_tables_item_directly_is_reported_and_exits_1(tmp_path, capsys):
    folder = fixture_copy(tmp_path)
    path = model_dir(folder) / "Projection" / "__init__.py"
    marker = "# " + "-" * 75 + "\n# References"
    text = path.read_text(encoding="utf-8")
    assert text.count(marker) == 1
    cell = ('def probe_direct():\n'
            '    return data.param("gen_fixture_m_a")                        # noqa: F821\n'
            '\n\n')
    path.write_text(text.replace(marker, cell + marker), encoding="utf-8")
    assert params.main([str(folder)]) == 1
    out, err = capsys.readouterr()
    assert headers(out) == [INDEX]
    assert err.splitlines() == [
        f"{INDEX}: cell probe_direct reads the item 'gen_fixture_m_a' of the tables layer"
        f" directly, not through the table factory"]
