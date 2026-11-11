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
    """No shipped product has a tariff file, so the layers are the core file and the
    product's ``param_tariff_type.csv``."""
    folder = PRODUCTS_DIR / product
    model = mx.read_model(model_dir(folder))
    try:
        table = params.rows(model)
        reads = param_usage.scan(model).reads
        layers = model.Data.param_layers()
    finally:
        model.close()
    assert list(layers) == ["core", "tariff_type"]
    frames = {"core": read(CORE_FILE), "tariff_type": read(folder / "param_tariff_type.csv")}
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
        (row["layer"] for row in table[:-1]), key=["core", "tariff_type"].index)
    assert table[-2]["layer"] == "tariff_type"

    assert params.main([str(folder)]) == 0
    out, err = capsys.readouterr()
    assert any(line.split()[:3] == ["decl_scale", repr(float(expected["value"])), "tariff"]
               for line in out.splitlines())
    assert err == ""
