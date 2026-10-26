# Upstream provenance: `KLV_DE_S` (lifelib `delib`)

This folder is the kapitallebensversicherung product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/kapitallebensversicherung/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `KLV_DE_S/Data/__init__.py` | `c952017976e41db770e63186b45e36f9bc2ec3bf32303abfd591ca6a5633474a` |
| `KLV_DE_S/Projection/__init__.py` | `2aeb5bb351c3c38802a62ad1a4361f4046c99f164e2aecb7db478b5cf1ce03e1` |
| `KLV_DE_S/__init__.py` | `eb8209a13147bcbaaa52f8e46a41db003faa8868a978d307110d40e50333df06` |
| `KLV_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `cost_table.csv` | `33ffc90ca41ceb06177bee2f1372bbe3dd4bfc2df092bfb466620ed0c559cdd3` |
| `deckrv_table.csv` | `aacdf5f2732ae2b8eb91c30fc660e986e585f794cd452ec2f89b18fe7c8f28e3` |
| `freq_loading_table.csv` | `5aed2d050f5b7d39b443e6f940e0495a7749c402aa4cfc2d4953e32a1427cb3b` |
| `lapse_table.csv` | `b3d35ee990cf356621ff42da1039ce30e656879826094b391f7bd42604c5a854` |
| `model.md` | `5995cc471c404f202c11052c9a835ee0800d24a8045a69ec7326fc665f7d34c5` |
| `model_point_table.csv` | `e495bd27bd190e8dcc7f103a8f28707fb7af011ecb0d784745a1ee2bdd73e834` |
| `mort_table.csv` | `5525a88610ad942a6216a70333ed55753d756a554dffd849ee5632b55c3167f2` |
| `product-spec.md` | `bfe6341c4790d716fd61432a7d587d8db8927977739a17e096ab2fc096f85def` |
| `run.py` | `8ad00e278f0f2f74d7866c601a72b043f89c6df15d34a77e2544492f3158e38e` |
| `sources.md` | `6bce9950e81c9b3ae3b5fc7c21cbb659d5c200d7f1fff22805b177a181aead4c` |
| `surplus_rate_table.csv` | `b3e3165100cf6a3cb2c6cc7f24c3e4d516293e770bd3915c73885e85b2243bbb` |
| `technical-notes.md` | `bfdaceff340b69dfa6d66c75a618845310b16363da024c1118c154eb706b7bd1` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`); it adds no regular file. A changed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `KLV_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection` |
| `KLV_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; `input_dir` moved to the core and inherited from it; `model_point_table` moved to the core and inherited from it; Reference `mort_table_file` renamed `mort_file`; `mort_table` moved to the core and inherited from it; `lapse_table` moved to the core and inherited from it; `freq_loading_table` moved to the core and inherited from it |
| `KLV_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core and inherited from it; Reference `mort_table_file` renamed `mort_file` in the header table; `issue_age` moved to the core and inherited from it; `sex` moved to the core and inherited from it; `smoker` moved to the core and inherited from it; `policy_term` moved to the core and inherited from it; `prem_term` moved to the core and inherited from it; `issue_year` moved to the core and inherited from it; `duration_init` moved to the core and inherited from it; `k_start` moved to the core and inherited from it; `t_start` moved to the core and inherited from it; `duration_mth` moved to the core and inherited from it; `duration` moved to the core and inherited from it; `policy_year` moved to the core and inherited from it; `age_y` moved to the core and inherited from it; `age` moved to the core and inherited from it; `proj_len_y` moved to the core and inherited from it; `proj_len` moved to the core and inherited from it; `rechnungszins` moved to the core and inherited from it; `disc_factor_1st` renamed `disc_factor`; `disc_factor` moved to the core and inherited from it; `mort_rate_at_age` renamed `mort_rate_tariff_at_age`; `mort_rate_tariff` inherited from the core |
| `model.md` | Reference `mort_table_file` named `mort_file`; `mort_rate_at_age` named `mort_rate_tariff_at_age` |
| `technical-notes.md` | `mort_rate_at_age` named `mort_rate_tariff_at_age` |
| `sources.md` | `mort_rate_at_age` named `mort_rate_tariff_at_age` |
| `KLV_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `KLV_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
