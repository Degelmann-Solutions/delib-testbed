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

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`). Each row states the file as it is now against upstream, the import commit `c23e22e`; how it got there is its history in git (`docs/core.md`, section "Changed files in `UPSTREAM.md`"). Phase 3 adds two regular files: the tariff-type file `param_tariff_type.csv`, the product's scalar tariff parameters read by the core's `param`, and `prem_freq_table.csv`, the premium payment frequencies, moved out of `option_table.csv`. A changed or removed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The added files and the symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `Basis_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection`; the docstrings' names follow the renames below (`rechnungszins`, was `gtd_rate`) and count nine input CSVs, was seven |
| `Basis_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; inherited from the core (removed here): `input_dir`, `model_point_table`, `mort_table`, `surplus_table`, `rentenfaktor_table` and `charge_table`, beside the core's `param`, `prem_freq_table` and dict cells; overrides the core: `mort_table_index` (the unisex first-order table with a generational `trend` column, keyed by `age` alone) and `charge_table_index` (one row per tariff, keyed by `tariff_id`); added: `behaviour_table_dict` and `option_table_dict`, their tables as dicts by column, `behaviour_table_durs`, each behaviour table's last policy year, and `surplus_table_years`, each surplus scenario's last `t`, all built once per model; References: `mort_table_file` → `mort_file`, added `prem_freq_file` (`prem_freq_table.csv`) and `param_file` (`param_tariff_type.csv`); `option_table` reads `option_key` as text, its keys without the frequency rows; the docstrings list the nine input files and the dict cells, name the columns by the renames of `charge_table.csv`, and state that `mort_be_factor` steps up from the first-order table to the best estimate |
| `Basis_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; inherited from the core (removed here): `model_point`, `pols_if_init`, `proj_year`, `duration`, `duration_y`, `duration_mth`, `policy_year`, `age`, `age_y`, `proj_len`, `proj_len_y`, `is_anniv`, `prem_freq_load` (from `prem_freq_table.csv`, 1 on a single premium), `mort_rate_mth`, `premiums`, `expenses`, `commissions`, `net_cf`, `liability_cf` and `result_cf`; renamed and inherited: `cal_year_y` → `calendar_year_y`, `cal_year` → `calendar_year`, `ret_y` → `k_conv`, `ret_t` → `t_conv`, `alpha_total_pp` → `zillmer_amount`; renamed and overriding the core: `beitragssumme_pp` → `beitragssumme` (the premiums escalate with the *Beitragsdynamik*, the sum runs over the schedule); overrides the core: `omega_age` (read off the mortality table, one above its last age), `mort_rate_base` (the generational first-order table at the attained age and the calendar year), `mort_rate` (the terminal age absorbing, 1 from `omega_age() - 1`), `pols_if` (the sum of the paying and the paid-up ledger), `pols_if_at` (the timing `"AFT_FREEZE"`), `pols_death` (summed over the two cohorts), `claims` (the death benefit releases two cohorts' reserves weighted by the survivor's eligibility; the annuity kinds), `check_net_cf_resid` (the *Zuzahlungen* as income, the rebuilt flow less `net_cf`), `check_net_cf` (one tolerance over the run), `result_cf_annual` and `result_pols` (by projection year `k`), and the added terms `clock_offset_mth` (the valuation-date clock), `horizon_age` (lifelong, to the end of the table), `mort_be_factor` (1.15 from `param_tariff_type.csv`), `expense_infl` (the charge table's column at `tariff_id`), `inflation_years` (`proj_year(t)`), `prem_inst_pp` (the year's premium where `prem_due`), `pols_prem` (`pols_paying`), `claim_kinds` (death, annuity, survivor), `expenses_acq` and `expenses_maint` (each with the frame guard), `comm_init_rate` (the charge table's `comm_acq_bsum_once`), `comm_renew`, `income_other` (`zuzahlungen`) and `result_cf_columns` (its statement's columns); added product-only: `alpha_rate` (the charge table's `charge_acq_bsum_once`, the core's *Zillmer* hook); References removed: `mort_be_factor` (upstream 0.85, now the cell above), `elig_surv_prob`, `mort_base_year`, `rf_unit` and `ann_freq`, items of `param_tariff_type.csv`, `zill_spread_y` → the item `acq_spread_years` there, and `roll_fwd_tol` (upstream 1e-09) → the core's `roll_fwd_tol()`, the item `check_tol` 1e-08 of `core/Core/Data/param_core.csv` (acceptance of 2026-11-09); in the kept cells the model-point reads go through the core's cells (`issue_age()`, `issue_year()`, `duration_init()`, `ret_age()`, `scenario_id()`, `prem_form()`, `rechnungszins()`), every parameter read goes through `data.param`, every table read through a dict cell of the core or `Data` with the same keys, clamps and `float()` wrappers, no `DataFrame.at` or `.loc` left but the `iloc` slices of `result_cf_annual`, the charge-table columns are read by their names in `charge_table.csv`, `unit_cost_pp` and `expenses_maint` inflate through the core's `inflation_factor`, the checks close to `roll_fwd_tol()`, `zuz_take_up` and `result_pols` call `policy_year_y`, and `check_net_cf_resid` reads `result_cf_dict()`; the docstrings' header table names the core cells and the files, and `mort_be_factor` 1.15 is the step up from the annuitant table; the cells `unit_cost_pp` and `comm_init_rate` keep their names |
| `model.md` | names follow the renames above; the inputs table lists nine input CSVs with `prem_freq_table.csv` (`prem_freq_file`) and `param_tariff_type.csv` (`param_file`), pointing to `tools/params.py` for the items, and `option_table.csv` no longer holds the *Ratenzahlungszuschlag*; the limiting age is the last age 121, `omega_age()` 122 one above the table end; `mort_be_factor` 1.15, upstream 0.85, the step up from the annuitant table as RV's, with the anchor figures it moves recomputed; the check tolerance is 1e-8, `check_tol` of the core file |
| `model_point_table.csv` | columns renamed: `entry_age` → `issue_age`, `conclusion_year` → `issue_year`, `gtd_rate` → `rechnungszins`, `surplus_scenario_id` → `scenario_id`, `prem_mode` → `prem_freq`; values as upstream |
| `technical-notes.md` | names follow the renames above; the input files table lists `prem_freq_table.csv` with its columns and `param_tariff_type.csv`, the scalar assumptions its rows, pointing to `tools/params.py`, and `option_table.csv` no longer holds the *Ratenzahlungszuschlag*; the limiting age `omega_age` is one above the table end; `mort_be_factor` 1.15, upstream 0.85, with its reason, and the worked example recomputed on it; the timing `AFT_FREEZE` of `pols_if_at` is stated; the check tolerance is 1e-8, `check_tol` of the core file |
| `sources.md` | names follow the renames above (`issue_year`, `calendar_year`, `rechnungszins`, `acq_spread_years`) |
| `run.py` | names follow the renames above (`k_conv()`, `t_conv()`, `beitragssumme()`, `zillmer_amount()`, the columns `issue_year` and `prem_freq`); prints the last age as `omega_age() - 1`; reads `data.param("acq_spread_years")`, was the Reference `zill_spread_y` |
| `param_tariff_type.csv` | added: the tariff-type file of the core's `param`, columns `item`, `value`, `basis` and `provenance`: `mort_be_factor` 1.15, upstream's Reference 0.85, a `Setzung` of the acceptance of 2026-11-09, and the upstream References `elig_surv_prob`, `mort_base_year`, `rf_unit` and `ann_freq` of `Projection` at their values, `acq_spread_years` renamed from `zill_spread_y`, each with its basis and its provenance from the docstrings and notes |
| `charge_table.csv` | columns renamed: `zill_rate` → `charge_acq_bsum_once`, `alpha_zuz_rate` → `charge_acq_sp_once`, `beta_prem` → `charge_admin_prem_inst`, `gamma_av` → `charge_admin_av_ann`, `unit_cost_pp` → `charge_admin_pp_ann`, `acq_expense_pp` → `expense_acq_pp_once`, `maint_expense_pp` → `expense_admin_pp_ann`, `annuity_admin_pp` → `expense_annuity_pp_ann`, `comm_init_rate` → `comm_acq_bsum_once`, `comm_renew_rate` → `comm_renew_prem_inst`; values as upstream, the provenance text names the new columns |
| `option_table.csv` | the four rows of the upstream option `prem_mode` removed, their factors now in `prem_freq_table.csv` |
| `prem_freq_table.csv` | added: the premium payment frequencies `annual`, `half_yearly`, `quarterly` and `monthly` with `instalments` (1, 2, 4, 12) and the *Ratenzahlungszuschlag* `prem_freq_load`, the factors of upstream's `prem_mode` rows of `option_table.csv`, with their provenance |
| `Basis_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `Basis_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
