# Upstream provenance: `Sofort_DE_S` (lifelib `delib`)

This folder is the sofortrente product of lifelib's `delib` library, copied whole and byte for byte at a pinned commit. At the import nothing was edited, added or removed; line endings are upstream's (LF). Later changes are listed under `## Changed in phase 3`.

This file describes the import. Byte identity with upstream holds for the commit of the import; a later commit that changes a file listed here says so, and the hashes below stay those of upstream.

- Upstream repository: https://github.com/lifelib-dev/lifelib
- Commit: `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1`
- Commit date: 2026-09-26
- Source path: `lifelib/libraries/delib/products/sofortrente/`
- Licence: MIT, "Copyright (c) 2022 lifelib Developers". The notice is `LICENSE-lifelib.txt`, copied from `LICENSE.txt` in the upstream repository root.

The `delib` tree, and with it this folder, is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10), the upstream head at the time of the import.

modelx, the engine that reads and runs the model, is not copied. It is an unmodified dependency installed from PyPI (see `pyproject.toml`).

The Markdown files and some tables cite insurers and rating agencies as sources. These citations come from upstream and stay byte-identical; the repository's rule against vendor and client names covers our own vendors and clients, not them.

## Files copied verbatim

Each file was byte-identical to upstream at the import; the hashes are upstream's. `tests/test_provenance.py` checks these SHA-256 values, except for the files listed under `## Changed in phase 3`, and that the folder holds no other file than these and this one, besides the symlinks listed there.

| File | SHA-256 |
|---|---|
| `LICENSE-lifelib.txt` | `f30a3558fa4b497b5dc70f2cf28b1f5309db42e4d405196f8cd621b8ca3d1d51` |
| `Sofort_DE_S/Data/__init__.py` | `32c927ad790528c6f4c7057134c008119d7caab86956ce3604b50f43fe147980` |
| `Sofort_DE_S/Projection/__init__.py` | `9dcb142ffc88c994f86fa8c29bdc59f3758142866436f3cd1a5148053be0c3c4` |
| `Sofort_DE_S/__init__.py` | `e3b0d7957a7ddf839980e4bd24d14f073ca257e44a0aeab2b1d08b8c949ad4e7` |
| `Sofort_DE_S/_system.json` | `bd2b0595635b2377009e5667654277b31f454e6be52b84cb59725e97d6409334` |
| `hoechstrechnungszins_table.csv` | `b8bb94b4175ab21bc033ad1241dc9d7d811e99c4accfb68daffad929f5b3411e` |
| `improvement_table.csv` | `8ca9bba1ff8033b9b7f3f99d37b3fa814a724d82d01198b3f46e8914c58332e1` |
| `model.md` | `de4554214d59cfc2c3af63c26e4ead54760b1907a2f7c1f6864946565d9084e5` |
| `model_point_table.csv` | `d66726039f0d84f6d3ba6f56ea1b61caa916fbd3393fdcc668b1a0fdef88b234` |
| `mort_table.csv` | `1ba5bc0bba7b2f9e6559ec4b5461453703e74ca146a99cd98644cca248adc2a5` |
| `product-spec.md` | `ef273a09c52f4677aed5afc0a28a155c3e5053e189ff25427342adc2217e09bd` |
| `run.py` | `734bcb642e7297a336aa919149ef4ed2187f9dfd24e368f7f4538e1b4b5eccc8` |
| `sources.md` | `2be0ea50841fbc1c477907ca6405f43573e2a64b7caa3b1ba7af982773f1f1f1` |
| `surplus_scale_table.csv` | `1a900a9dfc688321055e189784fe2fca686273bbc8106fbfaf1a9e46b3734d07` |
| `technical-notes.md` | `1fbd2fb790699131ee00c4d734879828b0f31e9be978791cc2567bdf04ad6694` |

## Changed in phase 3

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`). Each row states the file as it is now against upstream, the import commit `c23e22e`; how it got there is its history in git (`docs/core.md`, section "Changed files in `UPSTREAM.md`"). Phase 3 adds two regular files: the tariff-type file `param_tariff_type.csv`, the product's scalar tariff parameters read by the core's `param`, and `ann_freq_table.csv`, the annuity payment frequencies the model point may carry. A changed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The added files and the symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `Sofort_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection`; the docstring counts seven input CSVs, was five |
| `Sofort_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; inherited from the core (removed here): `input_dir`, `model_point_table`, `mort_table` and `hoechstrechnungszins_table`, beside the core's `param` and dict cells; overrides the core: `mort_table_index` (a first- and a second-order basis, keyed by `basis`, `sex` and `age`); added: `ann_freq_table` with `ann_freq_table_keys`, its keys as a `frozenset`, `improvement_table_dict` and `surplus_scale_table_dict`, their tables as dicts by column, and `mort_table_ages` and `improvement_table_ages`, each table's age range, all built once per model; References: `mort_table_file` → `mort_file`, added `ann_freq_file` (`ann_freq_table.csv`) and `param_file` (`param_tariff_type.csv`); the docstrings list the seven input files and the dict cells and name `unisex_mix_male`, was `mix_male` |
| `Sofort_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; inherited from the core (removed here): `model_point`, `policy_id`, `duration_mth_init`, `pols_if_init`, `duration_mth`, `duration`, `policy_year`, `calendar_year`, `premiums`, `claims`, `expenses`, `check_net_cf`, `result_cf` and `result_pols`; renamed and inherited: `entry_year` → `issue_year`, `tariff_int_rate` → `rechnungszins`, `max_tariff_int_rate` → `hoechstrechnungszins`, `infl_factor` → `inflation_factor`; renamed and overriding the core: `entry_age` → `issue_age` (a second life, argument `life`); renamed product-only: `payment_freq` → `ann_freq`, checked against `ann_freq_table_keys()`, was a literal set, and `single_prem` → `prem_gross_level_pp` (the *Einmalbeitrag*, the premium at inception under its name in every product); added product-only: `prem_due`, `t == 0`, the month the single premium is due, which `prem_inst_pp` reads where upstream's `premiums` tested the month itself; overrides the core: `sex` and `age` (the second life, argument `life`), `t_start` (the elapsed duration in months), `proj_len` (the longest of the annuitant's survival, the guarantee period and the second life), `mort_rate_tariff` (generational and unisex at each life's birth cohort), `mort_rate` and `mort_rate_mth` (per life on the generational surface, the closing age stepping to zero), `pols_if` (the probability that a payment obligation remains, not a count), `net_cf` (`-liability_cf(t)`), `liability_cf` (the notes' outgo-positive stream), `check_net_cf_resid` (the instalment rebuilt through the single payment factor), and the added terms `prem_inst_pp` (the *Einmalbeitrag* at `t = 0`), `pols_prem` (`pols_if_init()`), `claim_kinds` and `claims_other` (`GUARANTEE`, `REFUND`), `expenses_acq`, `expenses_maint` and `expenses_claim` (the payment run), `check_net_cf_scale` (the single premium of the book), `result_cf_columns` and `result_pols_columns` (its columns); References removed: `expense_load_alpha` → `load_acq_sp_once`, `expense_load_beta` → `load_admin_annval_once`, `expense_acq_rate` → `expense_acq_sp_once`, `expense_acq_fixed` → `expense_acq_pp_once`, `expense_maint_pp` → `expense_admin_pp_ann`, `expense_pay_pp` → `expense_pay_pp_inst`, `mix_male` → `unisex_mix_male` (read through the core's `unisex_mix_male()`), and `mort_base_year` and `omega_age` (read through the core's `omega_age()`), items of `param_tariff_type.csv`; `expense_infl` (upstream 0.015) and `roll_fwd_tol` → `check_tol`, items of `core/Core/Data/param_core.csv`, read through the core's `expense_infl()` and `roll_fwd_tol()`; the solver settings, were `solve_tol` and `solve_max_iter`, are the literals 1e-10 and 200 of `annuity_pp_derived`; in the kept cells every parameter read goes through `data.param`, every table read through a dict cell of the core or `Data` with the age ranges of `mort_table_ages` and `improvement_table_ages`, and the checks close to `roll_fwd_tol()`; the docstrings' header table names the core cells and the files |
| `model.md` | names follow the renames above; the inputs table lists seven input CSVs with `ann_freq_table.csv` and `param_tariff_type.csv` (`param_file`), pointing to `tools/params.py` for the items; `expense_infl` 2,0 %, upstream 1,5 %, the house-wide rate of the core file, with the anchor figures it moves recomputed; the check tolerance is `check_tol` of the core file, and the refund solve's bisection tolerance 1e-10 and iteration cap 200 are literals of `annuity_pp_derived()` |
| `model_point_table.csv` | columns renamed: `entry_age` → `issue_age`, `entry_year` → `issue_year`, `tariff_int_rate` → `rechnungszins`, `payment_freq` → `ann_freq`, `single_prem` → `prem_gross_level_pp` (the premium before any *Ratenzahlungszuschlag* at inception, one name in every product); column added: `prem_form`, `single` on every point, the premium form as the other products state it; values as upstream |
| `run.py` | names follow the renames above (`issue_age()`, `issue_year()`, `rechnungszins()`, `hoechstrechnungszins()`, `ann_freq()`, `prem_gross_level_pp()`); reads `data.param("load_acq_sp_once")` and `data.param("load_admin_annval_once")`, were the References `expense_load_alpha` and `expense_load_beta`; lists only the `check_*` cells without parameters |
| `technical-notes.md` | names follow the renames above; the model-point attributes name `prem_form`, `single` on every point; the input files table lists `param_tariff_type.csv` and the scalar assumptions name their rows of it; `expense_infl` 2,0 %, upstream 1,5 %, the house-wide rate of the core file stepping at the policy anniversary, and the worked example recomputed on it; the check tolerance is `check_tol` of the core file and the tolerance of `check_net_cf` is stated; the refund solve's bisection tolerance 1e-10 and iteration cap 200 are literals of `annuity_pp_derived()`, solver settings and so code |
| `sources.md` | names follow the renames above (`rechnungszins`, `ann_freq`) |
| `param_tariff_type.csv` | added: the tariff-type file of the core's `param`, columns `item`, `value`, `basis` and `provenance`: the upstream References `omega_age` and `mort_base_year` of `Projection` at their values, and the renamed References `expense_load_alpha` → `load_acq_sp_once`, `expense_load_beta` → `load_admin_annval_once`, `expense_acq_rate` → `expense_acq_sp_once`, `expense_acq_fixed` → `expense_acq_pp_once`, `expense_maint_pp` → `expense_admin_pp_ann`, `expense_pay_pp` → `expense_pay_pp_inst` and `mix_male` → `unisex_mix_male` at their values, each with its basis and its provenance from the docstrings and notes |
| `ann_freq_table.csv` | added: the annuity payment frequencies `ann_freq` may take, 12, 4, 2 and 1 instalments a year, with their provenance; was the literal set of the cell `payment_freq` on `Projection` |
| `Sofort_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `Sofort_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
