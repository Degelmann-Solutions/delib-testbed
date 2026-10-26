# Upstream provenance: `Index_DE_S` (lifelib `delib`)

This folder is the indexpolice product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/indexpolice/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `Index_DE_S/Data/__init__.py` | `377516657c0e29695874a44b307de4bcbde9dd603e4ec635d92a2e3fbd417df4` |
| `Index_DE_S/Projection/__init__.py` | `b8da7c03d47dbefc6b710fa05e75e9e97023b02835a1352203717469de7fdddb` |
| `Index_DE_S/__init__.py` | `ff81dce15093d3ef306071e8f5977a7af0bf3cab0d10c0b640441d8255281cc1` |
| `Index_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `election_table.csv` | `403bd1e45edfa4e3b560a025e8aa184d0d8695d0208b22cfb828f5bc39786a6f` |
| `freq_load_table.csv` | `d4065b67f60aeca9a6709518424b9a6c2402427344eb499221bd71d425c75881` |
| `index_param_table.csv` | `3bea9e0881a55e9a607b3a257d64850501524691b557a661fc1be731265fca3e` |
| `index_return_table.csv` | `03fe8ef95217bc667be5155a155cca0326776a00c11a291afca53af1aaf415b7` |
| `lapse_table.csv` | `860db5c85661699778df6a93ac1ea8acdeff3760d90c35ef243abd0932634230` |
| `model.md` | `1ae897fcf3fdd48145514a733e74120af8aab14f990d7a479c1dbbf2dbdd36ab` |
| `model_point_table.csv` | `6a86e585c66e6431e394207558a18cd0f95fedb0816d69dc2f9fe7984f30b770` |
| `mort_table.csv` | `10191827008472d69ba2b7cbe7615686cb56e0550ee003988f804cfc2f3db0d8` |
| `product-spec.md` | `512bf3c1bf2e064af7201cbb8c49d8fd0606cce284b4339e0a8dff503591faec` |
| `run.py` | `63f2bc3a1d9939a6e62c5e0d1f68c524e24da45d5e253fbc6d69a8623b9abc0d` |
| `sources.md` | `5702de55d261be56d9bf7b9eb8b001df0c649851ec8966f3fd7a2d8bf83ad1db` |
| `surplus_rate_table.csv` | `97d0e38fd22ad8e4463a401a493690d0101376bb1901da9e15353c5d7c29dba9` |
| `technical-notes.md` | `94b5b5b2a394353116872798d6a700107dcb741c6e9e01f2013bd9b25488ec93` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`); it adds no regular file. A changed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `Index_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection`; docstring names `issue_age`, was `entry_age`; docstring names `duration_init`, was `dur_init`; docstring names `ret_age`, was `ann_start_age` |
| `Index_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; `input_dir` moved to the core and inherited from it; `model_point_table` moved to the core and inherited from it; `mort_table` moved to the core and inherited from it; `lapse_table` overrides the core with a reason (index column); Reference `freq_load_file` renamed `freq_loading_file`; cell `freq_load_table` renamed `freq_loading_table`; `freq_loading_table` moved to the core and inherited from it; `lapse_table` no longer overrides the core, derived from it; `lapse_table_index` added, overrides the core with a reason (0-based `t`) |
| `Index_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core and inherited from it; Reference `freq_load_file` renamed `freq_loading_file`; reads `data.freq_loading_table()`, was `data.freq_load_table()`; `entry_age` renamed `issue_age`; `issue_age` moved to the core and inherited from it; `sex` moved to the core and inherited from it; `prem_term_y` moved to the core and inherited from it; `dur_init` renamed `duration_init`; `duration_init` moved to the core and inherited from it; `k_start` moved to the core and inherited from it; `t_start` moved to the core and inherited from it; `duration_mth` moved to the core and inherited from it; `duration` moved to the core and inherited from it; `policy_year` moved to the core and inherited from it; `age_y` moved to the core and inherited from it; `age` moved to the core and inherited from it; `proj_len_y` overrides the core with a reason (horizon); `proj_len` moved to the core and inherited from it; `guar_rate` renamed `rechnungszins`; `rechnungszins` moved to the core and inherited from it; `is_anniv` moved to the core and inherited from it; `ann_start_age` renamed `ret_age`; `ret_age` moved to the core and inherited from it; `proj_len_y` no longer overrides the core, derived from it; `horizon_age` added, overrides the core with a reason (`ret_age()`); `policy_id` moved to the core and inherited from it; `prem_freq` moved to the core and inherited from it (checked against the frequency loading table) |
| `model.md` | Reference `freq_load_file` named `freq_loading_file`; cell `freq_load_table` named `freq_loading_table`; `entry_age` named `issue_age`; `dur_init` named `duration_init`; `ann_start_age` named `ret_age` |
| `model_point_table.csv` | column `entry_age` renamed `issue_age`; column `dur_init` renamed `duration_init`; column `guar_rate` renamed `rechnungszins`; column `ann_start_age` renamed `ret_age` |
| `run.py` | calls `issue_age()`, was `entry_age()`; calls `rechnungszins()`, was `guar_rate()`; calls `ret_age()`, was `ann_start_age()` |
| `technical-notes.md` | `entry_age` named `issue_age`; `dur_init` named `duration_init`; `guar_rate` named `rechnungszins`; `ann_start_age` named `ret_age` |
| `sources.md` | `guar_rate` named `rechnungszins` |
| `product-spec.md` | `guar_rate` named `rechnungszins` |
| `Index_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `Index_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
