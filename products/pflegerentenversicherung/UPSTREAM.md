# Upstream provenance: `Pflege_DE_S` (lifelib `delib`)

This folder is the pflegerentenversicherung product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/pflegerentenversicherung/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `Pflege_DE_S/Data/__init__.py` | `4e56cc6311571bdd3dd30ced4415085ae9645d8e9bded609dbfee485a6ea3af2` |
| `Pflege_DE_S/Projection/__init__.py` | `12e77ac00c6e2c911ab80aa470dafb0471f0bdb4282305dae9982b0f4ed0f878` |
| `Pflege_DE_S/__init__.py` | `d085014ce3e2d46e0e0c58ebaef2b9f8065132763e8cb6cf70dde70b887e13c9` |
| `Pflege_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `basis_table.csv` | `d4aa72822660802d89b8da5427947c011d438ddc45e2ced6ba98fbd1da300f0e` |
| `benefit_scale_table.csv` | `0a73bc3c463d15c2f136685ad7d6ee60c55118f3af3d5860ce2a7603c7753568` |
| `care_table.csv` | `e68a746fca1222bd4527dd57fd64e9c1b2f574719f2b84cd5d61445cea9d81cb` |
| `expense_table.csv` | `e390b5809b518b9f46f0b99de7a9dcbbdfbad504fcc5a529d26d0df90fb17a9b` |
| `incidence_table.csv` | `4023b4e2d6b1b826ed79804578bbf879917d6826557e659d55d903483c5351f9` |
| `lapse_table.csv` | `03fccaadd41f41ec0936a3ad07ad4b94b9e9db622cb0dd75feb083023a77903b` |
| `model.md` | `6d8ce1ee9992b2cfa124ff117d60cb91374f0008732dcb08c8044a9dfd160f71` |
| `model_point_table.csv` | `b4f98b583c2c8bb676d9592cf87948e27ec47b5cb98df9edffc2a175f462b6ae` |
| `mort_table.csv` | `7f424338ae842f206df1758e4e5dd0332f401fa2ccfeab8f46ce808a36d1965a` |
| `product-spec.md` | `fd906445345847e58027ff471fc6ea265fb84d8bbc9c96e1ddae5a5136c64a53` |
| `run.py` | `0526596c4d82803b0d71af8d9448a2e2bac6a30ba5905b6e0311787fdd5c5854` |
| `sources.md` | `79619015bc6840e7119f27cf5d3fdf9894f3195e7355d6e28d3da4c94ecb646d` |
| `surrender_table.csv` | `7a028403d04a050ce573ed2d05e882fbf407caad332c4cd3637858f945752059` |
| `technical-notes.md` | `5fb0da9038ee2d09b835bf9243215f30c57be4a2eb3e0cdffbf281b0af58e0b0` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`). It adds one regular file, `param_table.csv`, merged from the two files it removes (`docs/core.md`, section on changed files). A changed or removed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The added file and the symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `Pflege_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection`; docstring: eight input CSVs; docstring names `issue_age`, was `age_at_entry` |
| `Pflege_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; `input_dir` moved to the core and inherited from it; `model_point_table` moved to the core and inherited from it; `basis_table` and `expense_table` replaced by `param_table`, inherited from the core; References `basis_file` and `expense_file` replaced by `param_file`; docstring updated; Reference `mort_table_file` renamed `mort_file`; `mort_table` moved to the core and inherited from it; `lapse_table` moved to the core and inherited from it; docstring names `rechnungszins` a model-point column |
| `Pflege_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core and inherited from it; `data.basis_table()` and `data.expense_table()` read as `data.param_table()`; header table and docstrings name `param_table.csv`; Reference `mort_table_file` renamed `mort_file` in the header table; `age_at_entry` renamed `issue_age`; `issue_age` moved to the core and inherited from it; `sex` moved to the core and inherited from it (the `str()` around the read dropped); `duration_mth_init` moved to the core and inherited from it; `duration_mth` moved to the core and inherited from it; `policy_year` moved to the core and inherited from it; `age` moved to the core and inherited from it; `proj_len` overrides the core with a reason (horizon); `t_start` overrides the core with a reason (duration in months); inline frame-start reads of `duration_mth_init()` call `t_start()`; docstrings of `pols_act` and `pols_pg` name `t_start()`; `rechnungszins` overrides the core with a reason (book-wide rate); `disc_factor` renamed `disc_factor_mth`; `disc_factor_mth` moved to the core and inherited from it; `epv_prem_units` renamed `tariff_annuity`; `tariff_annuity` overrides the core with a reason (monthly premium units); `epv_benefits` renamed `tariff_benefit_pv`; `prem_net_level_pp` moved to the core and inherited from it; `omega_age` moved to the core and inherited from it; `proj_len` no longer overrides the core, derived from it; `horizon_age` added, overrides the core with a reason (`omega_age()`); `rechnungszins` no longer overrides the core, derived from it: the rate is the model-point column `rechnungszins`; `policy_id` moved to the core and inherited from it; `rating_factor` moved to the core and inherited from it; `karenz_months` moved to the core and inherited from it; `prem_mode` renamed `prem_freq`, which overrides the core with a reason (no frequency table, `single`); `tariff_benefit_pv` overrides the core with a reason (the Pflegerente on the multi-state ledger); `tar_mort_rate`, `tar_mort_rate_care` and `tar_inc_rate` call `unisex_blend`, inherited from the core, for their inline blend at `unisex_mix_male`; `beitragssumme` moved to the core and inherited from it; `beitragssumme_prem` and `beitragssumme_years` added, each overrides the core with a reason (monthly or single premium, the age-85 cap) |
| `model.md` | `basis_table.csv` and `expense_table.csv` named as `param_table.csv`; Reference `mort_table_file` named `mort_file`; `age_at_entry` named `issue_age`; `disc_factor` named `disc_factor_mth`; `rechnungszins` no longer named a row of `param_table.csv` |
| `technical-notes.md` | `basis_table.csv` and `expense_table.csv` named as `param_table.csv`; `age_at_entry` named `issue_age`; `epv_prem_units` named `tariff_annuity`; `epv_benefits` named `tariff_benefit_pv`; states that every model point is priced at the one `rechnungszins` of `param_table.csv`; `rechnungszins` a row of the model-point attributes, with its provenance, no longer a row of `param_table.csv` |
| `sources.md` | `basis_table.csv` and `expense_table.csv` named as `param_table.csv` |
| `param_table.csv` | added: merged from `basis_table.csv` (column `param` renamed `item`, empty `unit`) and `expense_table.csv`, same values, without `rechnungszins`, which moved to `model_point_table.csv` |
| `basis_table.csv` | removed: merged into `param_table.csv` |
| `expense_table.csv` | removed: merged into `param_table.csv` |
| `model_point_table.csv` | column `age_at_entry` renamed `issue_age`; column `rechnungszins` added (0.01 on every point), moved from `param_table.csv` |
| `run.py` | calls `issue_age()`, was `age_at_entry()`; calls `t_start()` for the frame start, was `duration_mth_init()`; calls `tariff_annuity()`, was `epv_prem_units()`; calls `tariff_benefit_pv()`, was `epv_benefits()`; calls `prem_freq()`, was `prem_mode()` |
| `Pflege_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `Pflege_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
