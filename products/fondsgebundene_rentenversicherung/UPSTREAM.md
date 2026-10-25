# Upstream provenance: `FRV_DE_S` (lifelib `delib`)

This folder is the fondsgebundene_rentenversicherung product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/fondsgebundene_rentenversicherung/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `FRV_DE_S/Data/__init__.py` | `54d0f165fb60eb5c63804a202a67411ca1d0a0c1f795e7b240300bb0970a9757` |
| `FRV_DE_S/Projection/__init__.py` | `a3eaf66ca8b9c8fd522f7f4ecc74fb61bc36e863285369705ca837894770f409` |
| `FRV_DE_S/__init__.py` | `bf81359d2a2acdd8fbfa9d2d53078c120fccfdb1788f7a89f4e56bc343779689` |
| `FRV_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `charge_table.csv` | `341412f0607e17ec3b877680cfef58a875dc9a012c95cfa09ed6fce1c1b0698e` |
| `fund_scenario_table.csv` | `055ac29241200fdf043343948813c80ffaa3e64a64bac92a80064a6ffd4e615a` |
| `lapse_table.csv` | `c7e8ab34ae1d726028b6fcb57cb31591f57047f2cbd2dcb2ade7a5a06b7f1370` |
| `model.md` | `ae1cba7aeec2f58a55d72aca5588371a3fc0e91343989428be11cdd029710cbe` |
| `model_point_table.csv` | `62fc62ffcfaac17b4ac7e499efae48731ba25e3906036f60fc821e89ec71e2f8` |
| `mort_table.csv` | `ae945ef318070c47c529cdff82afa61fe74bf61da46665d52ae024a39eb2e071` |
| `product-spec.md` | `068d70c76f46f587ff1e374360279b67876f52c38b433d594c70eaba1f0a3a50` |
| `rentenfaktor_table.csv` | `7765d701126a9ef4e98c66da4277e625129415459ab25527ff57708778cec9b0` |
| `run.py` | `3f8035807e6106ebf9a8d45ca6c1a42b043a8186d043d55136798488e4bb7193` |
| `sources.md` | `a6cb5f3f099581f3dd06d05ce1379de7e7fe6bef84d95797a3470a7899ffb555` |
| `technical-notes.md` | `0d20e330b9fcbd23a7bbb0bf07a3410a6700335221dc8ceb8266fa71c4e66667` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`); it adds no regular file. A changed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `FRV_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection`; docstring names `issue_age`, was `entry_age` |
| `FRV_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; `input_dir` moved to the core and inherited from it; `model_point_table` moved to the core and inherited from it; `mort_table` overrides the core with a reason (index columns); `lapse_table` moved to the core and inherited from it; `rentenfaktor_table` overrides the core with a reason (index columns) |
| `FRV_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core and inherited from it; `entry_age` renamed `issue_age`; `issue_age` moved to the core and inherited from it; `sex` moved to the core and inherited from it; `prem_term_y` moved to the core and inherited from it |
| `model.md` | `entry_age` named `issue_age` |
| `model_point_table.csv` | column `entry_age` renamed `issue_age` |
| `run.py` | calls `issue_age()`, was `entry_age()` |
| `sources.md` | `entry_age` named `issue_age` |
| `technical-notes.md` | `entry_age` named `issue_age` |
| `FRV_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `FRV_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
