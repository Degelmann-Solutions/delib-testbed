# Upstream provenance: `RV_DE_S` (lifelib `delib`)

This folder is the klassische_rentenversicherung product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/klassische_rentenversicherung/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `RV_DE_S/Data/__init__.py` | `f54b4770dc154dcb46b24cdd3087646660355bdb4701d1882f3f35ea5a4869b4` |
| `RV_DE_S/Projection/__init__.py` | `b7aa270c4d6df629b897ba7d269aa3fe7046fc31cefbece3d149b54eb47dcb5c` |
| `RV_DE_S/__init__.py` | `5c3d1533d4812cf68c4b78526bdff7969d5f31005830d810a06ddf85877f1e5d` |
| `RV_DE_S/_system.json` | `36acc4a594d285cc8e02921166c41c817c2db1e788fa24cdec5b57802ce21b90` |
| `charge_table.csv` | `c58dec5c5a496160ac33e481212154bd60226187b1685cb31f15c59e4c752f75` |
| `decl_rate_table.csv` | `5c9e271e8a5d2686ee3362f9e3ff77572b055105a2679631957227e50f7d6015` |
| `freq_load_table.csv` | `55fc3c5b36d3350362493626973b6437678b0629544ca8dbb042b7c85bd9d985` |
| `lapse_table.csv` | `539a00ef39faf4c052af68a3209bab331250920f618ddffcfa148b3c4cb7fea2` |
| `model.md` | `27f76836141d4ba5d000b313035215386c29062b231a3fa9ae8f1e656bb06b8c` |
| `model_point_table.csv` | `2d4eb9a134128f1626025e917b39c8eeb1b39d8395154f896427e6553edfb913` |
| `mort_table.csv` | `689adf95f32c33fccea66294ca5dabccb2558d45ba8c42eaf891318100c02a7c` |
| `param_table.csv` | `dee23cba4f02b55fcd6621c79d347fd96059bb9b7299265daaaa9af5ba38f1d7` |
| `product-spec.md` | `ed5deca272995edae3bac28deb1fd91eb79f4a7b82ef4c67fe5c33530ba2c8e4` |
| `rentenfaktor_table.csv` | `768fa994be2d6e176aa9f5833bd793c16b3d404c73670a90fd4cc3d71f213700` |
| `run.py` | `c35ca3619baa3ea2c9c7e8c07a0147305145de240809d7335702f12b6e362f98` |
| `sources.md` | `a418bda1caacfc793fad8fdc09af3a7b833c3944ab96f8f8f1196cd8134476e0` |
| `technical-notes.md` | `0b25e75f1638ccbc92a6554cbd136e4607bcc1d59dc26a5b80b9ad1c929a0b0c` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`); it adds no regular file. A changed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `RV_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection` |
| `RV_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; `input_dir` moved to the core and inherited from it; `model_point_table` moved to the core and inherited from it; `param_table` moved to the core and inherited from it; `mort_table` moved to the core and inherited from it; `lapse_table` overrides the core with a reason (index column); `rentenfaktor_table` moved to the core and inherited from it; Reference `freq_load_file` renamed `freq_loading_file`; cell `freq_load_table` renamed `freq_loading_table`; `freq_loading_table` moved to the core and inherited from it |
| `RV_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core and inherited from it; Reference `freq_load_file` renamed `freq_loading_file`; reads `data.freq_loading_table()`, was `data.freq_load_table()`; inline reads of `issue_age` call `issue_age()`, inherited from the core; inline reads of `sex` call `sex()`, inherited from the core; inline reads of `prem_term_y` call `prem_term_y()`, inherited from the core; inline reads of `issue_year` call `issue_year()`, inherited from the core; inline read of `duration_init` calls `duration_init()`, inherited from the core; `k_start` moved to the core and inherited from it; `t_start` moved to the core and inherited from it; `duration_mth` moved to the core and inherited from it; `duration` moved to the core and inherited from it; `policy_year` moved to the core and inherited from it; `age_y` moved to the core and inherited from it; `age` moved to the core and inherited from it; `proj_len_y` overrides the core with a reason (horizon); `proj_len` moved to the core and inherited from it; `calendar_year_y` moved to the core and inherited from it |
| `model.md` | Reference `freq_load_file` named `freq_loading_file`; cell `freq_load_table` named `freq_loading_table` |
| `RV_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `RV_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
