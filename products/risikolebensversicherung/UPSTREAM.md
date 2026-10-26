# Upstream provenance: `RLV_DE_S` (lifelib `delib`)

This folder is the risikolebensversicherung product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/risikolebensversicherung/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `RLV_DE_S/Data/__init__.py` | `c51a19b29c94dc99f0ee41d7594f5c117cc08eb719a75d2676e486e5e445aac8` |
| `RLV_DE_S/Projection/__init__.py` | `543b58a57764014b52f28f6da203a96c4bbf0f03958950e5db50693a2f43bf6a` |
| `RLV_DE_S/__init__.py` | `01d307c7587d9ba0718f4a0c55e94e0e319e4adb5fd83fcbbf35b71c4fab6071` |
| `RLV_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `benefit_schedule.csv` | `903b8faea3a6881bb5d03aa1d99773d5b2afe55c974d2511980ce8afe253060a` |
| `freq_loading_table.csv` | `4335fcc62821819668931a41cc9270c74ef63bbec35c9666e29c7d006e67fcf8` |
| `lapse_table.csv` | `d9e0d24e56b66900243183ea2cd7a9d937fb503c66a74b953eba4a1c126d4247` |
| `model.md` | `15aad8e91e344cf3be99e07ad2bbbbcdbf6c53c5485b168835ef9e8bd389852d` |
| `model_point_table.csv` | `dfc9fae39993a6d60b388650340d0a851c46a3d452bbf0c3a90936b70bf0414a` |
| `mort_table.csv` | `f0f35b93f071c580fa424114645990321e604e06295f2d85d7159c23c8867df2` |
| `nvg_schedule.csv` | `bddb7779f4727058494e1e055fa07dd69ee4e98ad673423e3474b88d2ec27397` |
| `product-spec.md` | `8d685bbde0bace039f4a002078871cf3a5ab64c4180174ee273065db8908c830` |
| `run.py` | `b49e4d68d5ce0279869e4510269c97accf20b501d7fbb8a0eac33035eacc5944` |
| `sources.md` | `aff8670905cc626607707d636342493ac22daece85b09890482cd4d8c26a745d` |
| `technical-notes.md` | `391c621f2cfe991d026cef53a618969d143c0ab9e998911bdc32a6e10fc0f799` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`); it adds no regular file. A changed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `RLV_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection`; docstring names `duration_init`, was `duration_y`; docstring counts `param_table.csv` among the input CSVs; docstring names `mort_rate_tariff`, was `mort_rate_tar`; docstring no longer counts `param_table.csv`, removed again |
| `RLV_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; `input_dir` moved to the core and inherited from it; `model_point_table` moved to the core and inherited from it; Reference `mort_table_file` renamed `mort_file`; `mort_table` overrides the core with a reason (index columns); `lapse_table` moved to the core and inherited from it; `freq_loading_table` moved to the core and inherited from it; Reference `param_file` added, `param_table` inherited from the core; header table names `param_table.csv`; docstring names `mort_rate_tariff`, was `mort_rate_tar`; `mort_table` no longer overrides the core, derived from it; `mort_table_index` added, overrides the core with a reason (index columns); Reference `param_file` removed again with `param_table.csv`; header table no longer names it |
| `RLV_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core and inherited from it; Reference `mort_table_file` renamed `mort_file` in the header table; `issue_age` moved to the core and inherited from it; `sex` moved to the core and inherited from it; `smoker` overrides the core with a reason (code `R`); `policy_term` moved to the core and inherited from it; `prem_term` overrides the core with a reason (range check); `duration_y` renamed `duration_init`; `duration_init` moved to the core and inherited from it; `proj_start` renamed `t_start`; `t_start` moved to the core and inherited from it; `duration_mth` moved to the core and inherited from it; `duration` moved to the core and inherited from it; `policy_year` moved to the core and inherited from it; `age` moved to the core and inherited from it; `proj_len_y` moved to the core and inherited from it; `proj_len` moved to the core and inherited from it; Reference `rechnungszins` replaced by the cell `rechnungszins`, which reads `param_table.csv` and overrides the core with a reason (book-wide rate); `disc_factor` moved to the core and inherited from it; `mort_rate_tar` renamed `mort_rate_tariff` (the output column keeps the label `mort_rate_tar`); `mort_rate_tariff` overrides the core with a reason (loaded unisex blend, two lives); `pols_tariff` moved to the core and inherited from it; `tariff_annuity` moved to the core and inherited from it; `tariff_claims_pv` renamed `tariff_benefit_pv`; `prem_net_level_pp` moved to the core and inherited from it; header table names `param_table.csv`; Reference `mort_be_factor` (1.0) removed, `mort_be_factor` inherited from the core; `smoker` no longer overrides the core, derived from it; `smoker_codes` added, overrides the core with a reason (`R` for a smoker); `smoker2` checks `smoker_codes()`; `prem_term` no longer overrides the core, derived from it (the core checks the range); `rechnungszins` no longer overrides the core, derived from it: the rate is the model-point column `rechnungszins`; header table no longer names `param_table.csv`; `mort_rate_tariff` no longer overrides the core, derived from it; `mort_load_tariff` and `mort_rate_tariff_base` added, each overrides the core with a reason (the load `(1 + m) x rf`, the unisex blend); header table names them; `policy_id` moved to the core and inherited from it; `sum_assured` moved to the core and inherited from it; `rating_factor` moved to the core and inherited from it; `prem_freq` moved to the core and inherited from it (checked against the frequency loading table); `prem_freq_load` moved to the core and inherited from it; `instalments` moved to the core and inherited from it; `tariff_benefit_pv` moved to the core and inherited from it; `tariff_schedule` added, overrides the core with a reason (`benefit_pp`); `tariff_sum_pv` renamed `tariff_term_annuity`; `tariff_term_annuity` moved to the core and inherited from it; header table names `tariff_term_annuity` and `tariff_schedule`; `mort_rate_base` overrides the core with a reason (sex, smoker, two lives); `mort_rate` overrides the core with a reason (rating, selective lapse); `mort_rate_mth` moved to the core and inherited from it; `lapse_rate_base` moved to the core and inherited from it; `lapse_factor` added, overriding the core with a reason (0 in the final policy year, else `shock_lapse_factor`); `lapse_rate` reads `lapse_rate_base(t) * lapse_factor(t)`, 0 where the factor is 0; header table names `lapse_factor`; `lapse_rate` moved to the core and inherited from it; `lapse_rate_mth` moved to the core and inherited from it |
| `model.md` | Reference `mort_table_file` named `mort_file`; `duration_y` named `duration_init`; `proj_start` named `t_start`; names `param_table.csv`; `mort_rate_tar` named `mort_rate_tariff`; `param_table.csv` no longer named; `rechnungszins` stated as a model-point column |
| `model_point_table.csv` | column `duration_y` renamed `duration_init`; column `rechnungszins` added (0.01 on every point), moved from `param_table.csv` |
| `technical-notes.md` | `duration_y` named `duration_init`; names `param_table.csv`; `mort_rate_tar` named `mort_rate_tariff`; states that every model point is priced at the one `rechnungszins` of `param_table.csv`; states the first-death rule of `mort_rate_tariff` over two lives; `mort_be_factor` named the core's neutral factor; `param_table.csv` no longer named; `rechnungszins` a row of the model-point attributes, with its provenance |
| `run.py` | calls `duration_init()`, was `duration_y()`; calls `t_start()`, was `proj_start()` |
| `sources.md` | `mort_rate_tar` named `mort_rate_tariff` |
| `RLV_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `RLV_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
