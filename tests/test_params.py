"""The parameter tool ``tools/params.py`` (``docs/core.md``, "The parameter files").

- For every product the tool's items are the items of the usage scan's ``reads``, each row's
  value and layer those of ``param_layers()``, each row's basis and provenance those of the
  item's row in the core file or the product's ``param_tariff_type.csv``, and the rows stand
  in layer order, within a layer in the order of its file.
- ``main(["--all"])`` exits 0 and names every product; an unknown product exits 2.
- A scratch copy whose tariff-type file lost a read item lists it with layer ``missing`` and
  no value, and exits 1.
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
    headers = [line.split(":", 1)[0] for line in out.splitlines() if line.endswith(" items read")]
    assert headers == PRODUCTS
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


def test_a_read_item_in_no_layer_is_missing_and_exits_1(tmp_path, capsys):
    folder = tmp_path / "risikolebensversicherung"
    shutil.copytree(PRODUCTS_DIR / "risikolebensversicherung", folder)
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
    assert "decl_scale" in err


def test_an_item_of_the_tariff_file_is_listed_in_the_tariff_layer(tmp_path, capsys):
    folder = tmp_path / "risikolebensversicherung"
    shutil.copytree(PRODUCTS_DIR / "risikolebensversicherung", folder)
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
