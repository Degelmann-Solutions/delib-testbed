"""The table factory's choice is the only path from a table value to a result.

For each table of the factory's ``definitions()`` the probe scales one value of it by 1.01 in
a scratch copy of ``core/`` and ``products/``, runs all ten products on the copy with the
runner, concurrently as ``tests/test_baseline.py`` does, and compares each run's recipe hash
with the hash that test pins: exactly the products whose tariffs choose the table, read off
the ``*_table`` items of their layer files, leave their pinned hash; every other product
keeps it, with all checks true.

The value scaled is the table's ``m_b``, the scale of the age term of the male rates in both
laws, ``makeham`` (``a + b c^x``) and ``gompertz_force`` (``1 - exp(-b c^x)``): every table
has it, it acts at every age of the table, and every chooser reads male rates on its
shipped points, on a male point's own sex or in the unisex blend of a tariff rate.

The copy holds ``core/`` and ``products/`` side by side, so the products' relative core
symlinks (``../../../core/Core/...``) resolve into the copy and the real
``core/Core/Data/param_tables.csv`` is never touched.
"""
from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path

import modelx as mx
import pytest

from helpers import CORE_DIR, PRODUCTS_DIR, RUNNER, parse_output
from test_baseline import BASELINE

TABLES_FILE = CORE_DIR / "Core" / "Data" / "param_tables.csv"
LAYER_FILES = ("param_tariff_type.csv", "param_tariff.csv")
SCALED = "m_b"
FACTOR = 1.01


def table_names() -> list[str]:
    model = mx.read_model(CORE_DIR / "Core", name="TableProbeCore")
    try:
        return list(model.Tables.definitions())
    finally:
        model.close()


TABLES = table_names()


def choices(product: str) -> dict[str, str]:
    """The table choices of a product's layer files: ``{item: table}`` for each ``*_table``."""
    found = {}
    for name in LAYER_FILES:
        path = PRODUCTS_DIR / product / name
        if not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["item"].endswith("_table") and row["value"]:
                    found[row["item"]] = row["value"]
    return found


def choosers(table: str) -> set[str]:
    return {product for product in BASELINE if table in choices(product).values()}


def scratch_copy(tmp_path: Path, table: str) -> Path:
    """``core/`` and ``products/`` copied side by side, the table's ``m_b`` scaled in the copy."""
    ignore = shutil.ignore_patterns("__pycache__")
    shutil.copytree(CORE_DIR, tmp_path / "core", ignore=ignore)
    shutil.copytree(PRODUCTS_DIR, tmp_path / "products", symlinks=True, ignore=ignore)
    path = tmp_path / "core" / "Core" / "Data" / "param_tables.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    item = f"{table}_{SCALED}"
    hits = [row for row in rows if row[0] == item]
    assert len(hits) == 1, item
    hits[0][1] = repr(float(hits[0][1]) * FACTOR)
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    return tmp_path / "products"


def test_every_table_has_a_chooser_and_the_copy_resolves_into_itself(tmp_path):
    assert TABLES and all(choosers(table) for table in TABLES)
    products = scratch_copy(tmp_path, TABLES[0])
    for product in BASELINE:
        for link in (products / product).glob("*/Core*"):
            assert link.is_symlink(), link
            assert link.resolve().is_relative_to(tmp_path / "core"), link
    assert TABLES_FILE.read_bytes() != (
        tmp_path / "core" / "Core" / "Data" / "param_tables.csv").read_bytes()


@pytest.mark.parametrize("table", TABLES)
def test_a_table_value_moves_exactly_the_results_of_its_choosers(tmp_path, table):
    before = TABLES_FILE.read_bytes()
    products = scratch_copy(tmp_path, table)
    processes = {
        product: subprocess.Popen(
            [sys.executable, str(RUNNER), str(products / product)],
            cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for product in BASELINE}
    hashes, failed = {}, {}
    for product, process in processes.items():
        stdout, stderr = process.communicate(timeout=900)
        output = parse_output(stdout)
        if process.returncode != 0:
            failed[product] = stderr[-2000:]
            continue
        hashes[product] = (output["sha256"], output["checks"])
    assert TABLES_FILE.read_bytes() == before
    assert not failed, failed
    chosen = choosers(table)
    assert chosen
    unmoved = sorted(product for product in chosen if hashes[product][0] == BASELINE[product][2])
    moved = sorted(product for product in set(BASELINE) - chosen
                   if hashes[product] != (BASELINE[product][2], "all true"))
    assert (unmoved, moved) == ([], []), table
