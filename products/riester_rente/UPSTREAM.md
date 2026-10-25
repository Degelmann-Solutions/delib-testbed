# Upstream provenance: `Riester_DE_S` (lifelib `delib`)

This folder is the riester_rente product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/riester_rente/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `Riester_DE_S/Data/__init__.py` | `7b9afe933cac39073d0e2a1c09888d4d7544f021067e9b90dca1410497bdb78d` |
| `Riester_DE_S/Projection/__init__.py` | `5e5ede9ba28f99e78d594a4bd68352b644553a5479bb0f5cd3e414b26562a8a3` |
| `Riester_DE_S/__init__.py` | `9ce9da4e2f14cb17094aba791d485571d8c266c9f0bc6fafec7c3141b1761637` |
| `Riester_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `annuity_mort_table.csv` | `b780800953918db07f2e728045a905191ca20409fc729815c81e24a6f876bf5a` |
| `freq_loading.csv` | `9ae76ff50d7f8679101b41a5a28569320af3a4a08971916dbeb16b007d4d7ea9` |
| `income_schedule.csv` | `bafa2d0b0d4e0059150d48c46a869ed5ac7e9f493a0abda0cb7cf340003336b0` |
| `lapse_table.csv` | `2aaa0945e5b34019954491a42bdc0bdb7f7ea059e03f3f3a5ff480eb32f149de` |
| `model.md` | `8c43d4405ec5808b6de50e4a8024deecf788ae8c454f305814dfba4be729a486` |
| `model_point_table.csv` | `efa41bbcc96db66b98560708ad46274c28111b57d2527329be6df78040c38c67` |
| `mort_table_accum.csv` | `b71714d541de87044647240ae17074a69ce075a9b84f2463ccfb16900fed8664` |
| `product-spec.md` | `06bb636272b180cba238e649171f76eaf923e16b509bf3a39771c19220a461e5` |
| `run.py` | `7bb5f661c58169d5685ab40ce9476c2276b1cf6ef1621fe02f1a6c4abc920a25` |
| `sources.md` | `d34bbde087b5a7f22c4a86722714f57c7299fed414d618c484c3e8b01eb81691` |
| `surplus_scenario.csv` | `7d346758efe4d3a00fcd61ae44a5f248caf129ba3e3a18c96c567bc07b9c9a5e` |
| `technical-notes.md` | `29dc988575b999d4cbb1b45faac84babe55358eccf516e60f1331ed3465ae53c` |
| `zulage_schedule.csv` | `9ac0848bd3682eb0f5b7948b893aee013123a747280185c4f63e16be43e22984` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`); it adds no regular file. A changed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `Riester_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection` |
| `Riester_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; `input_dir` moved to the core and inherited from it; `model_point_table` moved to the core and inherited from it; `lapse_table` overrides the core with a reason (index column); cell `freq_loading` renamed `freq_loading_table`; `freq_loading_table` moved to the core and inherited from it; cell `mort_table_accum` renamed `mort_table` and Reference `mort_accum_file` renamed `mort_file`; `mort_table` overrides the core with a reason (index column) |
| `Riester_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core and inherited from it; reads `data.freq_loading_table()`, was `data.freq_loading()`; `issue_age` moved to the core and inherited from it; `sex` moved to the core and inherited from it; reads `data.mort_table()`, was `data.mort_table_accum()`; Reference `mort_accum_file` renamed `mort_file` in the header table; `duration_init` moved to the core and inherited from it; `proj_year` moved to the core and inherited from it; `duration_mth` overrides the core with a reason (valuation-date clock); `duration` moved to the core and inherited from it; `duration_y` moved to the core and inherited from it; `age_y` overrides the core with a reason (projection year); `age` overrides the core with a reason (valuation-date clock); `proj_len_y` overrides the core with a reason (horizon) |
| `model.md` | cell `freq_loading` named `freq_loading_table`; Reference `mort_accum_file` named `mort_file`, cell `mort_table_accum` named `mort_table` |
| `technical-notes.md` | cell `freq_loading` named `freq_loading_table`; cell `mort_table_accum` named `mort_table` |
| `Riester_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `Riester_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
