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

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`). Each row states the file as it is now against upstream, the import commit `c23e22e`; how it got there is its history in git (`docs/core.md`, section "Changed files in `UPSTREAM.md`"). Phase 3 adds two regular files: the tariff-type file `param_tariff_type.csv`, the product's scalar tariff parameters read by the core's `param`, and `prem_freq_table.csv`, upstream's `freq_load_table.csv` renamed, listed as removed and added. A changed or removed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The added files and the symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `Index_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection`; the docstrings' names follow the renames below (`issue_age`, was `entry_age`; `duration_init`, was `dur_init`; `ret_age`, was `ann_start_age`) and count nine input CSVs, was eight |
| `Index_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; inherited from the core (removed here): `input_dir`, `model_point_table`, `mort_table` and `lapse_table`, beside the core's `param` and dict cells; renamed and inherited: `freq_load_table` → `prem_freq_table`; overrides the core: `lapse_table_index` (the table keyed by the model's 0-based `t`, not the 1-based policy year); added: `index_return_table_dict`, `index_param_table_dict`, `surplus_rate_table_dict` and `election_table_dict`, their tables as dicts by column, built once per model; References: `freq_load_file` → `prem_freq_file` (`prem_freq_table.csv`), added `param_file` (`param_tariff_type.csv`); the docstrings list the nine input files and the dict cells |
| `Index_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; inherited from the core (removed here): `model_point`, `policy_id`, `sex`, `pols_if_init`, `prem_form` (the value `regular`, was `level`), `prem_freq` (checked against `prem_freq_table.csv`), `prem_term_y`, `k_start`, `t_start`, `proj_len_y`, `proj_len`, `duration_mth`, `duration`, `is_anniv`, `policy_year`, `age_y`, `age`, `premiums`, `mort_rate`, `mort_rate_mth`, `lapse_rate`, `lapse_rate_mth`, `pols_if`, `pols_death`, `pols_lapse`, `pols_maturity`, `claims`, `expenses`, `net_cf`, `liability_cf`, `check_net_cf`, `result_cf` and `result_cf_annual`; renamed and inherited: `entry_age` → `issue_age`, `dur_init` → `duration_init`, `ann_start_age` → `ret_age`, `guar_rate` → `rechnungszins`, `freq_load` → `prem_freq_load`; renamed, one name per premium quantity in every product: `prem_base_pp` → `prem_gross_pp` (the year's premium before the *Ratenzahlungszuschlag*), `prem_gross_pp` → `prem_pp` (after it), `prem_paid_pp` → `prem_gross_cum_pp` and `prem_paid_init` → `prem_gross_cum_pp_init` (the premiums paid to date before it); overrides the core: `lapse_rate_base` (keyed on the 0-based policy year through `duration(t)`), `pols_if_at` (`"AFT_DEATH"` subtracts the deaths, `"AFT_LAPSE"` the cohort before the maturity that `pols_surv_year_end` reads), `check_net_cf_resid` (the kind-less claim total), and the added terms `horizon_age` (the accumulation phase only, to *Rentenbeginn*), `lapse_factor` (0 through the final policy year, which ends at *Rentenbeginn*), `prem_inst_pp` (the year's premium where `prem_due`), `benefit_death_pp`, `benefit_lapse_pp` and `benefit_maturity_pp` (`db_pp`, `cv_pp` and `mat_pp` at `duration(t)`), `expenses_maint` (the acquisition expense and a twelfth of the year's maintenance as one per-policy rate), `check_net_cf_scale` (the month's largest premium, claim or expense) and `result_cf_columns` (no commission, `liability_cf` before `net_cf`); added product-only: `mort_rate_at_age` (the table rate at an attained age, the core's hook); References removed: `acq_cost_rate` → `charge_acq_bsum_once`, `acq_expense_rate` → `expense_acq_bsum_once`, `zill_years` → `acq_spread_years`, `exp_prem_rate` → `charge_admin_prem_inst`, `exp_av_rate` → `charge_admin_av_ann`, `exp_fixed_pp` → `expense_admin_pp_ann`, `storno_rate` → `stornoabzug_rate`, and `rentenfaktor_guar` and `rentenfaktor_curr`, items of `param_tariff_type.csv`; `zill_cap_rate` → `zillmer_cap_bsum`, `exp_infl` → `expense_infl` (0.02, upstream 0.015, read through the core's `expense_infl()`) and `roll_fwd_tol` → the core's `roll_fwd_tol()` (the item `check_tol`), items of `core/Core/Data/param_core.csv`; in the kept cells every parameter read goes through `data.param`, the literal `5` of `prem_charge_acq_min_pp` reads the core item `surr_spread_years` and the *Rentenfaktor* unit `10000.0` of `ann_monthly_pp` the item `rf_unit`, every table read goes through a dict cell of the core or `Data` with the same keys and `float()` wrappers, no DataFrame lookup by label left, `exp_maint_pp` inflates through the core's `inflation_factor(12 * k)`, and the checks close to `roll_fwd_tol()`; the docstrings' header table names the core cells and the files, and `exp_maint_pp` gives `expense_infl` 2.0 % |
| `model.md` | names follow the renames above; the file tree and the Reference table list nine input CSVs with `prem_freq_table.csv` (`prem_freq_file`, `prem_freq_table()`) and `param_tariff_type.csv` (`param_file`), pointing to `tools/params.py` for the items and to the core file for the house-wide, technical and statutory ones (`zillmer_cap_bsum` among them); the check tolerance is 1e-8, `check_tol` of the core file; the expense inflation is 2,0 %, upstream 1,5 %, the house-wide `expense_infl` |
| `model_point_table.csv` | columns renamed: `entry_age` → `issue_age`, `dur_init` → `duration_init`, `guar_rate` → `rechnungszins`, `ann_start_age` → `ret_age`, `prem_gross_pp` → `prem_gross_level_pp` (the annual premium before the *Ratenzahlungszuschlag* at inception), `prem_paid_init` → `prem_gross_cum_pp_init` (the premiums paid to date before the *Ratenzahlungszuschlag*); the `prem_form` value `regular`, was `level`; other values as upstream |
| `run.py` | names follow the renames above: calls `issue_age()`, `rechnungszins()` and `ret_age()`, was `entry_age()`, `guar_rate()` and `ann_start_age()`, and `prem_gross_pp(k)` and `prem_pp(k)`, was `prem_base_pp(k)` and `prem_gross_pp(k)` |
| `technical-notes.md` | names follow the renames above (the items of `param_tariff_type.csv` in the expense table and the conversion formula with `rf_unit`, the `prem_form` value `regular`, the column `instalments` of `prem_freq_table.csv`); the timings `"AFT_DEATH"` and `"AFT_LAPSE"` of `pols_if_at` and the tolerance of `check_net_cf` are stated; the expense inflation `expense_infl` is 2,0 %, upstream 1,5 %, the house-wide rate of the acceptance of 2026-11-09, an item of the core file, and the worked example is recomputed on it |
| `sources.md` | names follow the renames above (`rechnungszins`, was `guar_rate`) |
| `product-spec.md` | names follow the renames above (`rechnungszins`, was `guar_rate`); the *Stückkosten* inflate at 2,0 %, upstream 1,5 %, the house-wide `expense_infl` (acceptance of 2026-11-09) |
| `freq_load_table.csv` | removed: renamed to `prem_freq_table.csv` |
| `param_tariff_type.csv` | added: the tariff-type file of the core's `param`, columns `item`, `value`, `basis` and `provenance`: the upstream References of `Projection` at their values, renamed `acq_cost_rate` → `charge_acq_bsum_once`, `acq_expense_rate` → `expense_acq_bsum_once`, `zill_years` → `acq_spread_years`, `exp_prem_rate` → `charge_admin_prem_inst`, `exp_av_rate` → `charge_admin_av_ann`, `exp_fixed_pp` → `expense_admin_pp_ann`, `storno_rate` → `stornoabzug_rate`, and `rentenfaktor_guar` and `rentenfaktor_curr`; and `rf_unit` 10000.0, upstream's literal in `ann_monthly_pp`; each a `Setzung` with its provenance from the docstrings and notes |
| `prem_freq_table.csv` | added: upstream's `freq_load_table.csv` renamed, the frequencies `annual`, `half_yearly`, `quarterly` and `monthly`; column `freq_load` → `prem_freq_load`, values as upstream; column `instalments` added (1, 2, 4, 12) |
| `Index_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `Index_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
