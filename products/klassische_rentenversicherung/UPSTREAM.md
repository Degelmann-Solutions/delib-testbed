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

Phase 3 changes these files and adds these symlinks to take shared cells from the common core (`docs/core.md`). Each row states the file as it is now against upstream, the import commit `c23e22e`; how it got there is its history in git (`docs/core.md`, section "Changed files in `UPSTREAM.md`"). Two upstream files are renamed, each listed as removed and added: upstream's `param_table.csv` is the tariff-type file `param_tariff_type.csv`, the product's scalar tariff parameters read by the core's `param`, and upstream's `freq_load_table.csv` is `prem_freq_table.csv`, the premium payment frequencies. A changed or removed file keeps upstream's hash in the table above; `tests/test_provenance.py` skips its hash check. The added files and the symlinks are not copied files and have no hash.

| Path | Change |
|---|---|
| `RV_DE_S/__init__.py` | `_spaces` lists `CoreData` and `CoreProjection` before `Data` and `Projection`; the docstring's names follow the renames below (`rechnungszins`, was `int_rate_guar`) |
| `RV_DE_S/Data/__init__.py` | `_bases` names `.CoreData`; inherited from the core (removed here): `input_dir`, `model_point_table`, `mort_table`, `lapse_table` (its column now `policy_year`), `rentenfaktor_table` and `charge_table`, beside the core's `param`, `prem_freq_table` and dict cells; renamed and inherited: `freq_load_table` → `prem_freq_table`; removed: upstream's `param_table`, the parameters read through the core's `param`; overrides the core: `charge_table_index` (keyed per item, by `charge_id` and `item`, so each number carries its own provenance); added: `decl_rate_table_dict`, its reader's table as dicts by column, and `decl_rate_years`, each scenario's calendar range, both built once per model; References: `freq_load_file` → `prem_freq_file` (`prem_freq_table.csv`), `param_file` names `param_tariff_type.csv`, was `param_table.csv`; the docstrings list the input files and the dict cells, and the docstring of `charge_table_index` names the six items of a charge set by the renames of `charge_table.csv` |
| `RV_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; inherited from the core (removed here): `model_point`, `omega_age`, `k_start`, `t_start`, `duration_mth`, `duration`, `policy_year`, `age`, `age_y`, `calendar_year`, `calendar_year_y`, `proj_len`, `proj_len_y`, `is_anniv`, `pols_if_init`, `roll_fwd_tol` (the item `check_tol` of `core/Core/Data/param_core.csv`), `expense_infl` (the item `expense_infl` there), `premiums`, `mort_rate`, `mort_rate_mth`, `lapse_rate_mth`, `pols_death`, `pols_lapse`, `claims`, `expenses`, `net_cf`, `liability_cf`, `check_net_cf_resid`, `result_cf` and `result_cf_annual`; renamed and inherited: `int_rate_guar` → `rechnungszins`, `freq_load` → `prem_freq_load`, `alpha_total_pp` → `zillmer_amount`; renamed and overriding the core: `beitragssumme_pp` → `beitragssumme` (the premium schedule up to the *Aufschubzeit*, the frequency loading inside it), `mort_rate_guar` → `mort_rate_tariff` (the generational first-order table at the attained age and the calendar year; the annual frame's column keeps the label `mort_rate_guar`); renamed product-only: `expense_acq_pp` → `expense_acq_pp_once`, `expense_maint_pp` → `expense_admin_pp_ann`, `expense_annuity_pp` → `expense_annuity_pp_ann`, `expense_claim_pp` → `expense_claim_pp_once`, each reading its item of `param_tariff_type.csv`; overrides the core: `mort_be_factor` (1.15, the best estimate above the first-order table, from `param_tariff_type.csv`), `lapse_rate` (the § 165 cash-out, a rate of 1, and no surrender from *Rentenbeginn*), `pols_if` (the commutation exit), `pols_if_at` (`"AFT_DEATH"` subtracts the deaths, `"AFT_DECR"` the commutation too), `check_net_cf` (also asserts `liability_cf(t) == -net_cf(t)`), `result_pols` (the annual state by policy year), and the added terms `horizon_age` (`omega_age()`, a life annuity has no term), `mort_rate_base` (`mort_rate_tariff(t)`, the trend-projected first-order table the factor loads), `prem_inst_pp` (the year's premium where `prem_due`), `claim_kinds` (death, lapse, commutation), `benefit_death_pp` and `benefit_lapse_pp` (`db_pp` and `cv_pp` at `duration(t)`), `claims_other` (the commutation capital), `expenses_acq`, `expenses_maint` and `expenses_claim`, `annuity_outgo` (`annuity_payments`), `net_cf_outgo_columns` (the annuity payments, no commission), `result_cf_columns` (its statement's columns) and `result_cf_counts` (`pols_annuity` beside `pols_if`); added product-only: `alpha_rate` (the charge set's `charge_acq_bsum_once`, the core's *Zillmer* hook) and `pols_exits_cum`, the running total of deaths, surrenders and commutations that `check_decrement_closure_resid` reads; in the kept cells the model-point reads go through the core's cells (`issue_age()`, `sex()`, `prem_term_y()`, `scenario_id()`, `prem_form()`), every parameter read goes through `data.param` (`bwr_rate`, was `val_reserve_rate`; the *Rentenfaktor* unit `rf_unit`, was the literal `10000.0`, in `pup_cashout`, `annuity_guar_mth_pp`, `check_annuity_conv_resid` and `check_annuity_conv`; the spread in `charge_acq_spread_pp` the core item `surr_spread_years`, was the charge-table item `alpha_spread_years`), every table read through a dict cell of the core or `Data` with the same keys, clamps and wrappers, no DataFrame lookup left, the charge-table items are read by their names in `charge_table.csv`, and `expenses_pp` inflates through the core's `inflation_factor`; the docstrings' header table names the core cells and the files, the premium form `single`, was `einmal`; the core hook `alpha_rate` and the cell `val_reserve_pp` keep their names |
| `model.md` | names follow the renames above; the inputs table names `param_tariff_type.csv` (`param_file`, `param()`), pointing to `tools/params.py` for the items, `prem_freq_table.csv` (`prem_freq_file`, `prem_freq_table()`) with its column `instalments`, and six items a charge set, was eight; the payout-phase administration charge has no item, was `annuity_admin_rate` recorded and not applied; the check tolerance is 1e-8, `check_tol` of the core file, and the expense inflation `expense_infl` an item of the core file |
| `model_point_table.csv` | columns renamed: `int_rate_guar` → `rechnungszins`, `decl_scenario_id` → `scenario_id`, `premium_form` → `prem_form`, its values `laufend` → `regular` and `einmal` → `single`; other values as upstream |
| `run.py` | names follow the renames above (`rechnungszins()`, `prem_freq_load()`, `beitragssumme()`, `zillmer_amount()`, the column `prem_form`) |
| `technical-notes.md` | names follow the renames above; the input files table names `param_tariff_type.csv` with its `basis` column, pointing to `tools/params.py` for the items, `check_tol` and `expense_infl` items of the core file, and `prem_freq_table.csv` with its column `instalments`; `prem_form` takes `regular` and `single`; the conversion formula names `rf_unit` a row of `param_tariff_type.csv`; the § 165 minimum-benefit row states there is no surrender from *Rentenbeginn*; the spread of the acquisition charge is the core item `surr_spread_years`; the payout-phase administration charge has no item |
| `sources.md` | names follow the renames above (`rechnungszins`, `zillmer_amount`, `mort_rate_tariff`, `surr_spread_years`) |
| `charge_table.csv` | items renamed in both charge sets: `alpha_rate` → `charge_acq_bsum_once`, `beta_rate` → `charge_admin_prem_inst`, `gamma_rate` → `charge_admin_av_ann`, `gamma_pup_rate` → `charge_admin_pup_av_ann`; removed: the rows of upstream's `alpha_spread_years`, the spread read from the core item `surr_spread_years` (5 = 5), and of upstream's `annuity_admin_rate`, which no cell read; values as upstream |
| `lapse_table.csv` | column renamed: `duration` → `policy_year`; values as upstream |
| `freq_load_table.csv` | removed: renamed to `prem_freq_table.csv` |
| `param_table.csv` | removed: renamed to `param_tariff_type.csv` |
| `param_tariff_type.csv` | added: upstream's `param_table.csv` renamed, the tariff-type file of the core's `param`, columns `item`, `value`, `basis` (new) and `provenance`; items renamed: `expense_acq_pp` → `expense_acq_pp_once`, `expense_maint_pp` → `expense_admin_pp_ann`, `expense_annuity_pp` → `expense_annuity_pp_ann`, `expense_claim_pp` → `expense_claim_pp_once`, `val_reserve_rate` → `bwr_rate`; removed: upstream's `roll_fwd_tol` 1e-09, now the item `check_tol` 1e-08 of `core/Core/Data/param_core.csv`, and upstream's `expense_infl` 0.020, now the item `expense_infl` 0.02 there, the same double; added: `rf_unit` 10000.0, the *Rentenfaktor* unit, a literal in the code upstream; every other value as upstream; `basis` `Setzung` on every row, each provenance with its source or reason (acceptance of 2026-11-09) |
| `prem_freq_table.csv` | added: upstream's `freq_load_table.csv` renamed, columns `freq_load` → `prem_freq_load` and `n_instalments` → `instalments`, `instalments` placed before `prem_freq_load`; values as upstream |
| `product-spec.md` | names the premium forms `regular` and `single`, were `laufend` and `einmal` |
| `RV_DE_S/CoreData` | added: symlink to the core space folder `core/Core/Data` |
| `RV_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
