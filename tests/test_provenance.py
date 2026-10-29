"""Provenance of the ten products imported from lifelib's ``delib`` library.

Every product folder under ``products/`` is upstream's product folder at the pinned commit,
copied whole and byte for byte, plus ``LICENSE-lifelib.txt`` and ``UPSTREAM.md``. The
``UPSTREAM.md`` of each product lists every copied file with its SHA-256, taken from the
upstream bytes; these tests compare the files with that list.

Phase 3 changes product files and adds symlinks to the common core (``docs/core.md``). A
product's ``UPSTREAM.md`` names every such path in its section ``## Changed in phase 3``;
the hash check skips the listed files, which stay in the hash table with upstream's hash,
and every symlink in a product folder must be listed and resolve to a core space folder.
A listed change starting ``added:`` that is no symlink names a regular file phase 3 added,
which has no upstream hash; one starting ``removed:`` names a copied file phase 3 removed,
which keeps its row in the hash table and must be absent.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
CORE_DIR = ROOT / "core"

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


def changed_in_phase_3(product: str) -> dict[str, str]:
    """The paths listed under ``## Changed in phase 3`` in ``UPSTREAM.md``, with their change."""
    text = (PRODUCTS_DIR / product / "UPSTREAM.md").read_text(encoding="utf-8")
    _, found, section = text.partition("\n## Changed in phase 3\n")
    if not found:
        return {}
    section = section.split("\n## ", 1)[0]
    return dict(re.findall(r"^\| `([^`]+)` \| (.*\S) \|$", section, re.MULTILINE))


def added_files(product: str) -> set[str]:
    """Regular files listed as ``added:`` under ``## Changed in phase 3`` (symlinks excluded)."""
    links = symlinks(PRODUCTS_DIR / product)
    return {name for name, change in changed_in_phase_3(product).items()
            if change.startswith("added:") and name not in links}


def removed_files(product: str) -> set[str]:
    """Copied files listed as ``removed:`` under ``## Changed in phase 3``."""
    return {name for name, change in changed_in_phase_3(product).items()
            if change.startswith("removed:")}


def symlinks(folder: Path) -> set[str]:
    """Every symlink below ``folder``, without descending into symlinked directories."""
    found = set()
    for dirpath, dirnames, filenames in os.walk(folder):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            if path.is_symlink():
                found.add(path.relative_to(folder).as_posix())
    return found


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
    expected = (set(recorded) - removed_files(product)) | added_files(product) | {"UPSTREAM.md"}
    assert present_files(PRODUCTS_DIR / product) == expected


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_copied_files_match_their_upstream_hash(product):
    folder = PRODUCTS_DIR / product
    changed = changed_in_phase_3(product)
    for name, digest in recorded_hashes(product).items():
        if name in changed:
            continue
        assert sha256(folder / name) == digest, f"{product}/{name} differs from upstream"


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_changed_in_phase_3_lists_hashed_files_and_core_symlinks_only(product):
    folder = PRODUCTS_DIR / product
    recorded = recorded_hashes(product)
    links = symlinks(folder)
    added = added_files(product)
    removed = removed_files(product)
    for name in changed_in_phase_3(product):
        path = folder / name
        if name in links:
            continue
        if name in removed:
            assert name in recorded, f"{product}/{name} is listed as removed but not in the hash table"
            assert not path.exists(), f"{product}/{name} is listed as removed but present"
            continue
        assert path.is_file(), f"{product}/{name} is listed as changed but is no file or symlink"
        if name in added:
            assert name not in recorded, f"{product}/{name} is listed as added but in the hash table"
            continue
        assert name in recorded, f"{product}/{name} is listed as changed but not in the hash table"


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_every_symlink_is_listed_and_points_into_the_core(product):
    folder = PRODUCTS_DIR / product
    changed = changed_in_phase_3(product)
    core = CORE_DIR.resolve()
    for name in sorted(symlinks(folder)):
        assert name in changed, f"{product}/{name} is a symlink not listed as changed in phase 3"
        target = (folder / name).resolve()
        assert target.is_relative_to(core) and target.is_dir(), \
            f"{product}/{name} does not resolve to a core space folder under core/: {target}"


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_product_files_are_lf(product):
    folder = PRODUCTS_DIR / product
    for name in present_files(folder):
        assert b"\r" not in (folder / name).read_bytes(), f"{product}/{name}"


# The one allowed writer call: the runner's export engine (phase 2c) exports the model into
# a package under a ``tempfile.TemporaryDirectory()``, never into the product folder. It goes
# through the runner's ``export_model`` helper (story 2.10), whose only writes are modelx's
# own ``mx.export_model`` into the path it is given (the transform cache writes only pickled
# transform results into its own folder, never a model file).
EXPORT_CALL = "export_model(model, Path(tmp) / pkg, workers, transform_cache)"
HELPER_DEF = "def export_model(model, path: Path, workers: int = 1, cache: Path | None = None) -> None:"
HELPER_CALL = "mx.export_model(model, path)"


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
            calls = [line.strip() for line in source.splitlines() if "export_model(" in line]
            assert calls.count(EXPORT_CALL) == 1 and calls.count(HELPER_DEF) == 1
            assert set(calls) == {EXPORT_CALL, HELPER_DEF, HELPER_CALL}
            source = source.replace("export_model", "")
        for writer in WRITERS:
            assert writer not in source, f"{path.relative_to(ROOT)} mentions {writer}"


def test_added_and_removed_files_are_read_from_changed_in_phase_3(tmp_path, monkeypatch):
    product = tmp_path / "probe"
    (product / "M").mkdir(parents=True)
    (product / "M" / "Core").symlink_to(tmp_path)
    (product / "UPSTREAM.md").write_text(
        "| `a.csv` | `" + "0" * 64 + "` |\n"
        "\n## Changed in phase 3\n\n| Path | Change |\n|---|---|\n"
        "| `a.csv` | removed: merged into `b.csv` |\n"
        "| `b.csv` | added: merged from `a.csv` |\n"
        "| `M/Core` | added: symlink to the core space folder |\n"
        "| `M/x.py` | cell renamed |\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "PRODUCTS_DIR", tmp_path)
    assert added_files("probe") == {"b.csv"}
    assert removed_files("probe") == {"a.csv"}
