"""Provenance of the ten products imported from lifelib's ``delib`` library.

Every product folder under ``products/`` is upstream's product folder at the pinned commit,
copied whole and byte for byte, plus ``LICENSE-lifelib.txt`` and ``UPSTREAM.md``. The
``UPSTREAM.md`` of each product lists every copied file with its SHA-256, taken from the
upstream bytes; these tests compare the files with that list.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

UPSTREAM_COMMIT = "fb1d195ab5423031cfd6d2548fe25a86b76cd0a1"
UPSTREAM_HEAD = "b706d8bbab530cc9ef94e06600e9c9d1468d8cb1"  # v0.17.2, the delib tree is identical
SOURCE_PATH = "lifelib/libraries/delib/products"
LICENSE_SHA256 = "f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51"

# Product folder -> model folder and number of files copied from upstream (without the licence).
PRODUCTS = {
    "basisrente": ("Basis_DE_S", 16),
    "berufsunfaehigkeit": ("BU_DE_S", 16),
    "fondsgebundene_rentenversicherung": ("FRV_DE_S", 15),
    "indexpolice": ("Index_DE_S", 17),
    "kapitallebensversicherung": ("KLV_DE_S", 16),
    "klassische_rentenversicherung": ("RV_DE_S", 17),
    "pflegerentenversicherung": ("Pflege_DE_S", 18),
    "riester_rente": ("Riester_DE_S", 17),
    "risikolebensversicherung": ("RLV_DE_S", 15),
    "sofortrente": ("Sofort_DE_S", 14),
}
WRITERS = ("write_model", "export_model", "zip_model")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def present_files(folder: Path) -> set[str]:
    return {p.relative_to(folder).as_posix() for p in folder.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts}


def recorded_hashes(product: str) -> dict[str, str]:
    text = (PRODUCTS_DIR / product / "UPSTREAM.md").read_text(encoding="utf-8")
    return dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", text, re.MULTILINE))


def test_the_ten_products_are_present():
    assert {p.name for p in PRODUCTS_DIR.iterdir() if p.is_dir()} == set(PRODUCTS)


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_upstream_md_names_the_pinned_commit_and_path(product):
    model, _ = PRODUCTS[product]
    text = (PRODUCTS_DIR / product / "UPSTREAM.md").read_text(encoding="utf-8")
    assert text.startswith(f"# Upstream provenance: `{model}` (lifelib `delib`)\n")
    assert f"- Commit: `{UPSTREAM_COMMIT}`\n" in text
    assert f"- Source path: `{SOURCE_PATH}/{product}/`\n" in text
    assert f"`{UPSTREAM_HEAD}`" in text


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_upstream_md_lists_exactly_the_files_present(product):
    model, count = PRODUCTS[product]
    recorded = recorded_hashes(product)
    assert len(recorded) == count + 1
    assert recorded["LICENSE-lifelib.txt"] == LICENSE_SHA256
    assert f"{model}/_system.json" in recorded
    assert present_files(PRODUCTS_DIR / product) == set(recorded) | {"UPSTREAM.md"}


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_copied_files_match_their_upstream_hash(product):
    folder = PRODUCTS_DIR / product
    for name, digest in recorded_hashes(product).items():
        assert sha256(folder / name) == digest, f"{product}/{name} differs from upstream"


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_product_files_are_lf(product):
    folder = PRODUCTS_DIR / product
    for name in present_files(folder):
        assert b"\r" not in (folder / name).read_bytes(), f"{product}/{name}"


# The one allowed writer call: the runner's export engine (phase 2c) exports the model into
# a package under a ``tempfile.TemporaryDirectory()``, never into the product folder.
EXPORT_CALL = "mx.export_model(model, Path(tmp) / pkg)"


def test_no_modelx_writer_is_mentioned_in_tools():
    # Passes while tools/ does not exist yet; scans every file there once it does.
    tools = ROOT / "tools"
    sources = [p for p in tools.rglob("*")
               if p.is_file() and "__pycache__" not in p.parts] if tools.exists() else []
    for path in sources:
        source = path.read_text(encoding="utf-8")
        if path == tools / "run_baseline.py":
            assert source.count(EXPORT_CALL) == 1, "the runner's export call changed"
            assert "with tempfile.TemporaryDirectory(" in source
            calls = [line for line in source.splitlines() if "export_model(" in line]
            assert [line.strip() for line in calls] == [EXPORT_CALL]
            source = source.replace("export_model", "")
        for writer in WRITERS:
            assert writer not in source, f"{path.relative_to(ROOT)} mentions {writer}"
