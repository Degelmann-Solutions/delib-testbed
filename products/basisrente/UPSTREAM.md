# Upstream provenance: `Basis_DE_S` (lifelib `delib`)

This folder is the basisrente product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/basisrente/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `Basis_DE_S/Data/__init__.py` | `9bf646d88713a39ce0ca8a3cef447425e5e48e2e12c1f659b997cf21585d4cb5` |
| `Basis_DE_S/Projection/__init__.py` | `d6e201b6db7e4f51c71c6982adafb7e0d0dd574656ce7be7b9bf0c67fcaf0ec2` |
| `Basis_DE_S/__init__.py` | `46fd807c99aed48d54c886628dc4b4bfc7dd52505d1e4b0d186d91e5501b9ec7` |
| `Basis_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `behaviour_table.csv` | `3b2f52a40eb84e952938a33f2752fad5979c3440fa30cd016cf3a51e85ecac9d` |
| `charge_table.csv` | `73fb61f10fd3c74fcee720662b9760f08b0ce40f763ac89569840c9897a7edfd` |
| `model.md` | `8d44e3f3a870666a3aed02fa42d23b4aa81be4e25e4ff473ce11d354ad89b0b8` |
| `model_point_table.csv` | `946d8c0ee9ad1064a51cacd324ba3a1a96fec3db4782c83ce12dfad68f306786` |
| `mort_table.csv` | `8da618cf2abd5168e681a766df481ad3ac60cd6eff55679e30bae3d963c66e48` |
| `option_table.csv` | `f05de44ef951ee6453fa3b5fe0683abbb7f72838b689f7bb1a0856352ad59b69` |
| `product-spec.md` | `8fc46651d5d102959871ac43308f7c229f7447b378e706ec52d6e5d8b3ebc2fa` |
| `rentenfaktor_table.csv` | `7f1981335c5be227246b46fef69920f4464087886ee59614ba334a896897cfa5` |
| `run.py` | `7ed760bd645cd21b56488164c4fd7153ce43c4a88f0fa3541c015e640ebcbe86` |
| `sources.md` | `312b565298e2af60839955c8019472ff2314daddabfba61616e070c57bb85654` |
| `surplus_table.csv` | `c698bd0f2931ac3fd7d1ae56e0d2be20411ca87d78bc3f6eb245fe6d968315a7` |
| `technical-notes.md` | `95e66687a577bb20c32fe33eb029680503fb953816f63f4cce904bb38faa3dd4` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`); it adds no regular file. A changed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `Basis_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection` |
| `Basis_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; `input_dir` moved to the core and inherited from it; `model_point_table` moved to the core and inherited from it; Reference `mort_table_file` renamed `mort_file`; `mort_table` overrides the core with a reason (index columns); `rentenfaktor_table` moved to the core and inherited from it; docstring names `calendar_year`, was `cal_year` |
| `Basis_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core and inherited from it; Reference `mort_table_file` renamed `mort_file` in the header table; `entry_age` renamed `issue_age`; inline reads of the issue age call `issue_age()`, inherited from the core; inline read of `conclusion_year` calls `issue_year()`, inherited from the core; inline reads of `duration_init` call `duration_init()`, inherited from the core; `proj_year` moved to the core and inherited from it; `duration_mth` overrides the core with a reason (valuation-date clock); `duration` moved to the core and inherited from it; `duration_y` moved to the core and inherited from it; `policy_year` moved to the core and inherited from it; `age_y` overrides the core with a reason (projection year); `age` overrides the core with a reason (valuation-date clock); `proj_len_y` overrides the core with a reason (horizon); `proj_len` moved to the core and inherited from it; `cal_year_y` renamed `calendar_year_y`; `calendar_year_y` overrides the core with a reason (valuation-date clock); `cal_year` renamed `calendar_year`; `calendar_year` overrides the core with a reason (valuation-date clock) |
| `model.md` | Reference `mort_table_file` named `mort_file`; `entry_age` named `issue_age`; `conclusion_year` named `issue_year`; `cal_year_y` named `calendar_year_y` |
| `model_point_table.csv` | column `entry_age` renamed `issue_age`; column `conclusion_year` renamed `issue_year` |
| `technical-notes.md` | `entry_age` named `issue_age`; `conclusion_year` named `issue_year`; `cal_year_y` named `calendar_year_y`; `cal_year` named `calendar_year` |
| `sources.md` | `conclusion_year` named `issue_year`; `cal_year` named `calendar_year` |
| `run.py` | reads column `issue_year`, was `conclusion_year` |
| `Basis_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `Basis_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
