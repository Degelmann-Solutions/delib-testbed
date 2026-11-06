# The common core of phase 3: layout and conventions

Phase 3 moves the quantities the ten products share into one core. This file describes where the core lives, how a product reaches it, what the core holds of the time axis, the tariff basis, the decrement rates, the policy counts, the cash flows, the expense inflation, the outputs and checks, the contract data and charges, the parameter files and the formula literals, how the core quota is measured and bounded, and the conventions every core commit follows: commit trailers, the rules for measuring speed, the reason on a product override, and how a product's `UPSTREAM.md` names the files phase 3 changed. The tests that enforce the conventions are `tests/test_core.py`, `tests/test_provenance.py`, `tests/test_core_quota.py` and `tests/test_baseline_deviations.py` (with the tool `tools/baseline_deviations.py`).

## Layout

- `core/Core/` is a modelx model of its own, with the spaces `Data` and `Projection`. It holds the shared cells and nothing product-specific: no product folder name, model name or model prefix appears anywhere under `core/` (grep test in `tests/test_core.py`). Because it is a readable model, the tests can load it without a product. Beside it, `core/param_usage.py` is a plain Python module, the static usage scan of the parameter reads (section "The parameter files"); `mx.read_model` of `core/Core` does not see it.
- `core/Core/Projection` is parameterized by `point_id`, like every product's `Projection`; its cells are written against the product's names (`data`, `point_id`), which the product space provides. Its one Reference is the Module `types`, for the read-only `model_point()`; a product's `Projection` inherits it, under both engines.
- `core/Core/Data` holds the shared input loaders. Its cells use the product's References (`pd`, `model_point_file`, `param_file`, `mort_file`, `lapse_file`, `rentenfaktor_file`, `freq_loading_file`, `surplus_file`, `charge_file`, `hoechstrechnungszins_file`), which the product's `Data` defines; the core's `Data` defines no References. The scalar parameters are read through one lookup, `param("<item>")`, over the core file and the product's parameter files (section "The parameter files"). A loader reads its file at an index term (`mort_table_index()`, `lapse_table_index()`, `rentenfaktor_table_index()`, `surplus_table_index()`, `charge_table_index()`), the majority's index columns; a product whose file has other keys overrides the term with the literal it reads, not the loader.
- Beside each loader `<reader>()` stands a dict cell `<reader>_dict()`, the same table as plain Python dicts, built once per model from the loader's DataFrame, so that a lookup that runs many times per contract reads a dict rather than `DataFrame.at`. The model point table is held by row, `model_point_table_dict()[point_id][column]`; every other table by column, `<reader>_dict()[column][key]`, keyed as the loader indexes it (a tuple for several index columns, in the file's order). A dict cell derives from its loader by name, so a product's override of the loader or its index term flows through, and it is built only where something reads it. The loaders keep returning their DataFrames. The core's `Projection` reads its lookups through the dict cells (`model_point`, `prem_freq`, `prem_freq_load`, `instalments`, `lapse_rate_base`, `hoechstrechnungszins`), keyed and wrapped as before, and its parameters (`omega_age`, `unisex_mix_male`, `expense_infl`, `roll_fwd_tol`) through `param`; the products' own lookups move to them in entries 6–9 of the night-run epic.
- A product inherits every core cell, also one it has no use for: a product without a lapse table still has a derived `lapse_table`, which nothing evaluates. `CORE_CELLS` in `tests/test_core.py` lists, for every cell in the core, the products that derive it and those that override it with a reason.

## How a product reaches the core

modelx `bases` work only inside one model, and each product is its own model. The core therefore enters each product's model folder as two symlinks next to the product's own spaces:

```text
products/<product>/<Model>/CoreData       -> ../../../core/Core/Data
products/<product>/<Model>/CoreProjection -> ../../../core/Core/Projection
```

The product's `__init__.py` lists `CoreData` and `CoreProjection` in `_spaces` (before `Data` and `Projection`), and its `Data` and `Projection` name them as bases in the serialized format of `mx.write_model`, one leading dot for a sibling space:

```python
_bases = [
    ".CoreProjection"
]
```

`mx.read_model` follows the symlinks, so the product stays a self-contained modelx model: `run.py` and the runner `tools/run_baseline.py` read it unchanged, under `--engine export` and `--engine modelx`. A product cell that the product space does not define is derived from the core; under `--engine modelx` the trace shows the core's formula. `Data.input_dir()` resolves from the product's model path, so a core cell reads the product's own input files.

`shutil.copytree` follows symlinks by default, so a scratch copy of a product folder (tests, `tools/measure_marginal.py`) holds real copies of the core spaces and runs the same way.

A checkout without symlink support (Windows without developer mode or `core.symlinks`) is not supported. Composing the core into the product at load time in `tools/` was probed as an alternative and not built (Moritz, 2026-10-25).

## What enters the core

A quantity enters the core when at least two products compute it by the same procedure, also with different parameters or with terms that differ. The core formula is then built from term cells with neutral defaults (0 or 1), and a product overrides only the terms it differs in, each with its reason; the rest of the formula still derives from the core. A switch in the core formula is a last resort, and a choice that depends on the contract belongs in the data (a model-point column or `param_tariff_type.csv`), not in the code. A procedure no other product shares stays in the product. A unification that changes results is a commit of its own, one quantity at a time (Moritz, 2026-10-26).

## The time axis

The core's `Projection` builds every clock cell from one term, `clock_offset_mth()`, the policy months completed at `t = 0`: 0 on the inception clock most products use, where `t` counts policy months from issue.

- `duration_mth(t) = clock_offset_mth() + t`, `duration(t) = duration_mth(t) // 12`, `policy_year(t) = duration(t) + 1`.
- `duration_y(k) = duration(12 k)`, `policy_year_y(k) = duration_y(k) + 1`, `age_y(k) = issue_age() + duration_y(k)`, `calendar_year_y(k) = issue_year() + duration_y(k)`; `age(t) = issue_age() + duration(t)` and `calendar_year(t) = issue_year() + duration(t)` read the same at a month.
- `k_start() = duration_init() - clock_offset_mth() // 12` and `t_start() = 12 k_start()`: an in-force point on the inception clock opens its frame at its duration, one on the valuation clock at 0.
- `horizon_age() = issue_age() + policy_term()`, the attained age at which the projection ends; `proj_len() = 12 (horizon_age() - issue_age()) - clock_offset_mth()`, the frame's exclusive end, and `proj_len_y() = proj_len() // 12`.
- `omega_age()`, the limiting age ω from `param_tariff_type.csv`: the first age nobody reaches, the death rate is 1 at ω − 1. `ret_age()` is the age at *Rentenbeginn* from the model point, `k_conv() = ret_age() - age(0)` its projection year (negative on a point already in payment) and `t_conv() = 12 k_conv()` its month.

The integer arithmetic is exact for any offset, `(12 d + t) // 12 == d + t // 12`, so a product on another clock overrides only the offset. Basis and Riester count `t` from the valuation date (`products/basisrente/model.md:54`) and override `clock_offset_mth = 12 duration_init`, BU counts from the valuation month and overrides it with `duration_mth_init`; every other clock cell derives. Riester's model point carries no year of issue, so it overrides `issue_year() = valuation_year - duration_init()` (every point opens at 1 January 2027). BU floors `duration` at zero elapsed months before inception (a claim cohort's onset can precede it), and `policy_year` and `age` follow. The horizon is a term too: Basis, Riester, RV and Pflege end at `omega_age()` (lifelong annuities, a closed multi-state system), Index and FRV at `ret_age()` (the accumulation phase only), BU at its *Endalter* `cover_end_age()`; KLV and RLV derive the policy term. Basis and Riester read ω off their mortality table, one above its last age; RV, Pflege and Sofort carry it in `param_tariff_type.csv`.

Still per product: a frame start in months (`t_start` in FRV, Pflege and Sofort), Sofort's `proj_len` (two lives and the guarantee end) and second life (`issue_age`, `age`), and the deferments RV and Sofort state as years rather than an age (`aufschub_y`, `defer_years`), which are not `ret_age`. `CORE_CELLS` in `tests/test_core.py` lists every override.

## The tariff basis

The core's `Projection` holds the annual first-order equivalence that RLV and KLV share, and the parts of it that other products compute by the same procedure, built from term cells where the products differ in a part:

- `rechnungszins()` reads the model point's `rechnungszins` column. The rate used at conclusion applies for the whole term (§ 2 Abs. 2 DeckRV, `products/basisrente/sources.md:353`), so a book carries a stack of vintages and the rate is a contract attribute; every product with a *Rechnungszins* derives it (KLV, Riester, Sofort, RV, Index, Basis, RLV, BU and Pflege). RLV, BU and Pflege carry it as a model-point column, 1,00 % on every shipped point. `hoechstrechnungszins()` is the statutory cap in force at `issue_year()`, looked up by band in `hoechstrechnungszins_table()` (Sofort); KLV overrides it with its year-keyed `deckrv_table` (the split years at the higher rate). Both feed checks only.
- `disc_factor(y) = (1 + rechnungszins()) ** -y`, the annual factor to the start of policy year `y` (RLV, KLV), and `disc_factor_mth(t) = (1 + rechnungszins()) ** (-t / 12)`, the monthly factor (BU, Pflege). At `t = 12 y` the exponent `-t / 12` is exactly `-y`, so the two agree on year starts bit for bit.
- `mort_rate_tariff(t) = mort_load_tariff(t) * mort_rate_tariff_base(t)`, the first-order annual death rate in month `t`, with `mort_load_tariff(t) = 1` and `mort_rate_tariff_base(t) = mort_rate_tariff_at_age(age(t))` (FRV, KLV). RLV derives it and overrides the load, `(1 + m)` times the rating factor, and the base, its unisex blend over two lives. Sofort overrides it whole (generational, unisex, a second life), RV too (the trend-projected generational table at the attained age and the calendar year) and Pflege (the table rate times its prudence margin, the sexes blended; the rest of its `tar_` family keeps its names).
- `unisex_mix_male()` from `param_tariff_type.csv` and `unisex_blend(q_m, q_f) = w q_m + (1 - w) q_f`, the unisex tariff blend (KLV, Pflege). RLV's `sex_mix_male` blends before its load over two lives and Sofort's `mix_male` (0.45) a generational table; they stay.
- `pols_tariff(y)`, the tariff survivorship entering policy year `y`, mortality only: 1 for `y <= 0`, then `pols_tariff(y - 1) * (1 - mort_rate_tariff(12 (y - 1)))`. It starts at issue also on an in-force point, since the tariff was struck then (RLV, KLV).
- `tariff_annuity()`, the premium annuity-due `sum(disc_factor(y) * pols_tariff(y))` over `y < prem_term()` (RLV, KLV), and `tariff_term_annuity()`, the same over the cover term weighted by `tariff_schedule(y)`, the base of a sum-related loading (RLV, KLV). Pflege overrides `tariff_annuity` with the expected present value of its monthly premium in units of `P` on its multi-state tariff ledger.
- The benefit values from terms with neutral defaults: `tariff_death_pv() = tariff_death_sum() * sum(disc_factor(y + 1) * pols_tariff(y) * tariff_death_load(y) * mort_rate_tariff(12 y) * tariff_schedule(y))` over `y < proj_len_y()`, `tariff_maturity_pv() = tariff_maturity_sum() * disc_factor(n) * pols_tariff(n)`, and `tariff_benefit_pv()` their sum. The defaults are 1, 1, 1 and 0. RLV overrides `tariff_schedule(y) = benefit_pp(12 y)` (the benefit schedule); KLV overrides `tariff_death_sum = sum_death()`, `tariff_death_load = rating_factor()` (the *Risikozuschlag* on the death leg only) and `tariff_maturity_sum = sum_assured()`. Pflege overrides `tariff_benefit_pv` with its *Pflegerente* on the multi-state ledger.
- `prem_net_level_pp() = tariff_benefit_pv() / tariff_annuity()`, the net level premium, a pricing quantity and never a cash flow (RLV, KLV, Pflege).

The term positions carry the byte identity: `x * 1.0` and `x + 0.0` are exact, reassociation is not. So a neutral term stands where the product's own factor stood (KLV's rating factor between `p` and `q`, the death sum outside the sum), and RLV's `(1 + m) * rf` stays one load term.

Core cells that call a cell the product defines, its hook into the chain: `mort_rate_tariff_base` calls `mort_rate_tariff_at_age(x)` (FRV, KLV), `beitragssumme_prem` calls `prem_gross_pp()` (KLV) and `zillmer_amount` calls `alpha_rate()`, the product's *Zillmersatz* (KLV, FRV, Basis, RV, Pflege, Riester). A product without the hook inherits the core cell unused, as with every other core cell.

Still in the products, because unifying them changes results or adds a quantity (each a result-changing commit of its own, listed as open work):

- The gross premium. RLV, KLV, BU and Pflege solve the same first-order equivalence, `G = rho (A + cost PVs) / ((1 - beta) ae - alpha Beitragssumme - D)`, in different term orders and with different terms; it belongs in the core as a formula of term cells.
- The reserves. RLV's net reserve (`res_pp_at`, `res_zill_pp_at`) and KLV's (`res_net_pp`, `res_zill_pp`) are the same prospective procedure with different terms (maturity benefit, sum-insured schedule); KLV's paid-up and minimum reserves stay in KLV. RV's `av_pp` and Riester's `dk_pp` are the *Deckungskapital* rolled forward retrospectively, so the core's reserve has to offer the retrospective method beside the prospective one. BU and Pflege compute no *Deckungsrückstellung* (`products/berufsunfaehigkeit/technical-notes.md:975`, `products/pflegerentenversicherung/technical-notes.md:32`); adding one is a new quantity.
- The annuity present values of Sofort, Riester and RV (`annuity_factor`, `ann_factor`, `annuity_due_factor`): one sum of discount factor times survivorship, differing in payment frequency, the Woolhouse deduction, the guarantee period and a second life.
- Sofort's and RV's inline discounting with `v = 1 / (1 + i)` raised to month fractions, `disc_factor_mth` in another float order.
- RLV's and BU's acquisition charges, `(z k) G` and `(a G) BS_u`: the zillmered amount in another float order than `zillmer_amount`.

Not suited to the core: the multi-state first-order engines of BU (`*_first` ledgers) and Pflege (`tar_*` ledgers) and Sofort's monthly two-life survivorship (`tariff_lives`), which are different procedures, not one procedure with different terms.

## The decrement rates

The core's `Projection` holds the second-order (best-estimate) decrement rates, each the annual rate of the policy year a month falls in beside the monthly rate the recursion applies, built from term cells with neutral defaults:

- `mort_rate_base(t) = mort_rate_at_age(age(t))`, the annual table death rate before the best-estimate factor. `mort_rate_at_age(x)`, the product's table rate at an attained age, is the hook (BU, Riester with its ω guard, KLV, Index and Pflege at `(sex(), x)`). `mort_be_factor() = 1` is the step to the best estimate; Basis (0.85), FRV (0.75), KLV (0.75), RV (1.15) and Riester (0.80) override it from their `param_tariff_type.csv`, RLV derives it.
- `mort_rate(t) = min(1, mort_rate_base(t) * mort_be_factor())` (BU, FRV, Index, KLV, Pflege, RV). IEEE `*` commutes, so FRV's `factor * q` gives the same bits, and `min(1, q) == q` for `q <= 1`.
- `mort_rate_mth(t)`, the geometric twelfth `1 - (1 - q)^(1/12)` of `q = mort_rate(t)`, so twelve months compound back to the annual rate. An annual rate of 1 is a certainty, not a rate: it is placed in the anniversary month, 1 where `is_anniv(t)` and 0 in the eleven months before, so the cohort is paid its last year and dies at its end (Basis, Index, RV, Riester; BU, KLV and RLV had the plain twelfth, and their rate stays below 1 on every baseline point, so the branch never acts there).
- `lapse_rate_base(t)`, the table annual lapse rate at `policy_year(t)`, holding the table's last row for later years (BU, FRV, KLV, Pflege, RV, Riester, RLV). `lapse_factor(t) = 1` is the factor on it, and `lapse_rate(t) = lapse_rate_base(t) * lapse_factor(t)`, 0 without reading the table where the factor is 0 (BU, Index, Pflege, Riester, RLV).
- `lapse_rate_mth(t)`, the same shape on `lapse_rate(t)`: an annual rate of 1, a dated contractual act such as the § 165 VVG cash-out, falls whole in the anniversary month (BU, Index, KLV, Pflege, RV, Riester, RLV).

The monthly split is a product choice, not a contract attribute, so a product that splits otherwise overrides the cell with its reason rather than setting a switch in its data (Moritz, 2026-10-26). The certainty branch reads `is_anniv(t)`, `t % 12 == 11`; BU's `t` counts from the valuation month, where that is not the anniversary, but BU's rates never reach 1.

The overrides, each with its reason in the cell's docstring:

- `mort_rate_base`: Basis, the generational first-order table at the attained age and the calendar year; RLV, the table on sex and smoker status, two lives combined to the first-death rate before loading; RV, `mort_rate_tariff(t)`, the trend-projected first-order table the best estimate is loaded on; FRV, `mort_rate_tariff(t)`, the first-order tariff table its flat factor stands on. Sofort inherits it unused.
- `mort_rate`: Basis, the absorbing terminal age (1 from `omega_age() - 1` whatever the factor, where the generational trend would carry the table's terminal rate below 1); Riester, the basis switch at `t_conv()` to the generational annuitant table and its own factor `annuity_mort_be_factor`; RLV, the *Risikozuschlag* and the selective-lapse loading; Sofort, the argument `life` on its generational surface.
- `mort_rate_mth`: FRV, the linear split `q / 12`, coupled to the *Risikobeitrag* struck on `q/12` times the *riskiertes Kapital*; Pflege, a published diagnostic of its force-based monthly step, the plain twelfth also at the limiting age; Sofort, the argument `life`.
- `lapse_rate_base`: Index, its table keyed on the 0-based policy year, read through `duration(t)`.
- `lapse_factor`: Index, 0 through the final policy year, which ends at *Rentenbeginn*; RLV, 0 through the final policy year, where cover expires, else `shock_lapse_factor(t)`; Pflege, 0 once the premium term has ended; Riester, 0 from `t_conv()`, a contract in payment cannot be surrendered.
- `lapse_rate`, each reading `lapse_rate_base(t)`: KLV, § 165 VVG turns a failed *Beitragsfreistellung* election into a surrender (rate 1 in that year) and the final year is 0, its end the *Ablauf*; RV, the § 165 cash-out (rate 1) and 0 from `aufschub_y`; FRV, the tax-threshold step, the additive dynamic lapse and the 40 % cap.
- `lapse_rate_mth`: FRV, 0 in the last projected month, whose end is *Rentenbeginn*.

KLV derives `lapse_rate_mth`. Its own branch put 1 in the anniversary month of a failed election year; the core's certainty branch does the same wherever `lapse_rate` is 1 there, which is every such year but the final policy year, where `lapse_rate` is 0 and the survivors mature. No shipped point elects in its final year.

Still in the products: the first-order and tariff rates (`mort_rate_tariff*`, Pflege's `tar_*`, BU's `*_first`), BU's disabled-lives and in-claim rates (`mort_rate_dis*`), Pflege's forces and care rates (`mort_force`, `mort_rate_care`), Riester's payout basis (`annuity_mort_rate`) and transfer rate, Basis's *Beitragsfreistellung* rate, and the surrender values and charges.

## The policy counts

The core's `Projection` holds the policy counts the monthly recursion is built from, on the rates above and the frame `t_start() .. proj_len()`:

- `pols_if_init()`, the policy count the model point stands for, from its `pols_if_init` column. The count is a contract-book attribute and so data: every product derives it, and RLV and BU, whose cell was the literal 1.0, carry the column, 1.0 on every shipped point.
- `pols_if(t)`, the count at the **start** of month `t` and the weight on that month's row: 0 outside `t_start() .. proj_len()`, `pols_if_init()` at `t_start()`, then `pols_if(t-1) - pols_death(t-1) - pols_lapse(t-1) - pols_maturity(t-1)`. Subtracting the exits makes `pols_if(proj_len()) = +0.0` exact where the survivors mature (RLV, Index).
- `pols_death(t) = pols_if(t) * mort_rate_mth(t)` (FRV, Index, KLV, RV, RLV), `pols_lapse(t) = pols_if_at(t, "AFT_DEATH") * lapse_rate_mth(t)` (FRV, Index, KLV, RV, RLV, Riester), the lapses taken from the survivors of the month's deaths, and `pols_maturity(t)`, 0 before the last month `proj_len() - 1` and the survivors of both decrements there, `pols_if_at(t, "AFT_DEATH") * (1 - lapse_rate_mth(t))` (KLV, FRV, Index, RLV); the lapse is closed in that month, so the factor is exactly 1.
- `pols_if_at(t, timing)` on one sequence of timings: `"BEF_DECR"`, the start of the month, `pols_if(t)`; `"AFT_DEATH"`, after the month's deaths, `pols_if(t) * (1 - mort_rate_mth(t))`; `"AFT_DECR"`, the end of the month after every exit, `pols_if(t + 1)`; any other timing raises `ValueError` (BU, Pflege, RLV, KLV, Riester). The products' labels for the same points were renamed to these: KLV `AFT_MORT` and `AFT_LAPSE`, RLV and RV `BEF_LAPSE`, BU and Pflege `BEG` and `END`. BU and Pflege read only `"BEF_DECR"` and `"AFT_DECR"`; the inherited `"AFT_DEATH"` is the single-decrement population, not the survivors of their ledgers, and nothing reads it there.

The float order carries the byte identity, as for the rates: a product derives a count only where the core expression gives its bits (`x - 0.0 == x`, `x * 1.0 == x`, `a - a == +0.0`). Index's and RV's `"AFT_DEATH"` subtracts the deaths, `pols_if(t) - pols_death(t)`, so they keep their `pols_if_at` and still derive `pols_lapse`, which reads it through their override. KLV's and Riester's `pols_if` read their own end-of-month expression, since the derived `"AFT_DECR"` is `pols_if(t + 1)`.

The overrides, each with its reason in the cell's docstring:

- `pols_death`: Basis, the deaths of the paying and the paid-up cohort summed; BU, the three ledgers' deaths summed; Pflege, every state at its own rate; Riester, zero outside the frame and in the conversion month of a commuted contract, where the *Kleinbetragsrenten-Abfindung* takes the whole cohort. Sofort has no such cell.
- `pols_if_at`: Basis, `"AFT_FREEZE"`, after the *Beitragsfreistellung* has moved policies between the cohorts; FRV, `"AFT_DECR"` is the cohort before the maturity sweep, not `pols_if(t + 1)`; Index, `"AFT_DEATH"` subtracts the deaths and `"AFT_LAPSE"` is the cohort before the maturity that `pols_surv_year_end` reads; RV, `"AFT_DEATH"` subtracts the deaths and `"AFT_DECR"` the commutation at *Rentenbeginn* too.
- `pols_lapse`: BU, from the *aktiv* ledger only; Pflege, from the active state's survivors and the month's reactivations.
- `pols_if`: Basis and Pflege, the sum of their ledgers; BU, death and lapse its only exits with no maturity, rolled forward so that `check_states` tests the ledgers against it; FRV and KLV, the multiplicative recursion `l(t) (1 - q^m) (1 - w^m)`, and KLV subtracts no maturity, so its `pols_if(proj_len())` is the maturing cohort its checks read; RV, the commutation exit; Riester, the transfer exit (*Anbieterwechsel*) and the *Abfindung*; Sofort, the probability that a payment obligation remains over two lives and the guarantee period, not a count.

Still in the products: the ledger counts (`pols_paying`, `pols_paidup`, `pols_actv`, `pols_dis`, `pols_act`, `pols_care`, `pols_pg`, `pols_karenz`, Sofort's `lives_if`), the exits other than death, lapse and maturity (RV's `pols_commutation`, Riester's `pols_transfer`, Basis's `pols_freeze`), `pols_tariff` of the tariff basis, the annuity counts (`pols_annuity`) and the surrender values.

Open work, each a result-changing commit of its own: FRV's and KLV's multiplicative `pols_if` and Basis's summed `pols_death` give other bits than the core form; Index's and RV's subtracted `"AFT_DEATH"` other bits than the core's product; KLV's `pols_if(proj_len())`, the maturing cohort, would become 0 with its checks rewritten on `pols_maturity`, and FRV's `"AFT_DECR"` at the last month would become `pols_if(proj_len()) = 0`.

## The cash flows

The core's `Projection` holds the monthly cash flows from the counts above, each a procedure of term cells with neutral defaults; a product overrides the terms that carry its own premium, benefit and cost amounts and derives the cell. The amounts themselves (the premium per policy, the death benefit, the surrender value, the annuity, the expense rates, `claim_expenses`, `surplus_credit`, `annuity_payments`, `zuzahlungen`, `zulagen`, FRV's charges and `death_strain`) stay in the products, and a term override delegates to them or holds the expression the product's cell had.

- `premiums(t) = prem_inst_pp(t) * pols_prem(t)`, the premium collected per policy at the start of the month times the count it is collected from, with `prem_inst_pp(t) = 0` and `pols_prem(t) = pols_if(t)`. All ten derive it and override `prem_inst_pp`: KLV and RLV with their instalment, BU `prem_gross_pp(t)`, Pflege `premium_pp(t)`, FRV `prem_pp(t) + topup_pp(t)`, Index, RV and Basis the year's premium where `prem_due(t)`, Riester the *Eigenbeitrag* and the extra contribution where due, Sofort `single_prem()` at `t = 0`. `pols_prem` is overridden by BU (*Beitragsbefreiung*: the *aktiv* ledger plus the disabled inside the *Karenzzeit*), Pflege (the waived lives taken out), Basis (`pols_paying(t)`) and Sofort (`pols_if_init()`, its `pols_if` being a probability). A month with nothing due gives `0 * pols = +0.0`.
- `claims(t, kind=None)`: the total `sum(claims(t, k) for k in claim_kinds())`, with `claim_kinds() = ("DEATH", "LAPSE", "MATURITY")`; `"DEATH"`, `"LAPSE"` and `"MATURITY"` are `benefit_death_pp(t) * pols_death(t)`, `benefit_lapse_pp(t) * pols_lapse(t)` and `benefit_maturity_pp(t) * pols_maturity(t)`, each benefit 0 by default; any other kind is `claims_other(t, kind)`, which raises `ValueError` in the core. Derived by RLV (`benefit_death_pp = benefit_paid_pp`; lapse and maturity exactly 0 from the neutral benefits), KLV (its death and maturity benefit, `surr_value_pp`, kinds `DEATH, MATURITY, LAPSE`), Index (`db_pp`, `cv_pp`, `mat_pp` at `duration(t)`), RV (`db_pp`, `cv_pp`, kinds `DEATH, LAPSE, COMMUTATION`, the *Kapitalabfindung* in `claims_other`), Riester (`db_pp`, `cv_pp` at `proj_year(t)`, its six kinds, transfer, lump sum, commutation and annuity in `claims_other`), BU (kinds `BU_RENTE, REINTEGRATION, LAPSE`, the first two in `claims_other`, the lapse 0) and Sofort (kinds `GUARANTEE, REFUND`, both in `claims_other`).
- `expenses(t) = expenses_acq(t) + expenses_maint(t) + expenses_claim(t)`, excluding commission, each term 0 by default. RLV, RV, Sofort and Riester override all three terms (Sofort's claim term is the payment run, Riester's maintenance term the accumulation maintenance plus the annuity expense); Basis overrides acquisition and maintenance, each with the frame guard, and derives the claim term 0; KLV and Index override `expenses_maint` with their per-policy rate, which carries the acquisition expense of the opening month, and KLV `expenses_claim = claim_expenses(t)`.
- `commissions(t) = comm_init(t) + comm_renew(t)`: `comm_init(t) = comm_init_rate() * beitragssumme() * pols_if(t)` in the frame's first month on new business (`duration_init() == 0`), else 0, and 0 without reading the *Beitragssumme* where `comm_init_rate() = 0`; `comm_renew(t) = 0`. KLV (the cost table's rate), Riester (`comm_rate_init`) and Basis (its charge table) override the rate and `comm_renew`; Riester's renewal is 0 in the month of the initial commission. RLV (`comm_init_pp()`) and FRV (`comm_acq_pp(t) * pols_if(t)`) override both terms. BU, Index, RV, Pflege and Sofort pay none and inherit exactly 0.
- `net_cf(t)`, income positive: `premiums(t) + income_other(t)`, less `claims(t, kind)` for each kind of `claim_kinds()` in turn, less `annuity_outgo(t)`, `expenses(t)` and `commissions(t)`, with `income_other(t) = annuity_outgo(t) = 0`. Derived by RLV, KLV, Index, RV (`annuity_outgo = annuity_payments(t)`), Basis (`income_other = zuzahlungen(t)`) and Riester (`income_other = zulagen(t)`). Basis overrides `claim_kinds` with `DEATH, ANNUITY, SURVIVOR` for it.
- `liability_cf(t) = -net_cf(t)`, the same stream outgo positive (all but Sofort).

The float order carries the byte identity: `x - 0.0 == x`, `0.0 + x == x` for `x != -0.0` and `a * b == b * a`, so a neutral term adds nothing and a product whose order the core formula keeps derives the cell. Subtracting the kinds one by one is the majority's order (KLV, Index, RV, Basis, Riester); RLV's `p - claims(t)` gives the same bits because its lapse and maturity claims are +0.0. Python's `sum` over floats is compensated (Python 3.12), so the core's claim total equals a product's `sum` over the same kinds, not a product's left-to-right `A + L + D`.

The overrides, each with its reason in the cell's docstring:

- `claims`: Basis, the death benefit releases the reserve of two cohorts weighted by the survivor's eligibility; FRV, the surrender value formed as count times fund times `(1 - sigma)`, another float order, and no total; Pflege, its total `A + L + D` added left to right.
- `expenses`: BU, the acquisition charge added to the proportional administration before the flat one, `(acq + prop) + flat`, which the core's `acq + (prop + flat)` would reassociate; FRV, five expenses added left to right (the per-event surrender and annuitisation expenses among them); Pflege, the *Zillmerung* allowance added after the two administration terms.
- `net_cf`: BU, the *Beitragsverrechnung* before the claim total and the *Leistungsbearbeitungskosten* after the expenses; Pflege, the claim total at once and the claims-handling cost; FRV, the non-unit cash flow, charges and *Stornoabzug* less expenses, commissions and the death strain; Sofort, `-liability_cf(t)`.
- `liability_cf`: Sofort, the notes' outgo-positive stream, annuity payments, claims and expenses less the premium.

A product inherits every term also where it has no use for it: Pflege and FRV inherit `claim_kinds` and the benefits unused, and the core's `claims(t, "DEATH")` on Sofort, which has no deaths of that form, is not evaluated. A kind outside a product's `claim_kinds()` but among the core's three (RV's `"MATURITY"`, Riester's `"MATURITY"`) gives the core's product of a neutral benefit and a count rather than a `ValueError`.

Still in the products: the per-policy amounts named above. The expense inflation the cost terms multiply follows in the next section, the result frames and `check_net_cf` after it.

Open work, each a result-changing commit of its own: Pflege's claim total in the compensated `sum`; FRV's lapse claim as amount times count and its five expenses, and Pflege's expenses, in the core's three terms; BU's expenses in the core's three terms; BU's, Pflege's and FRV's net cash flow from the core's terms (`surplus_credit` and `claim_expenses` as outgo terms, FRV's charges as income); Sofort's `liability_cf` as `-net_cf`.

## The expense inflation

The core's `Projection` holds the expense inflation the cost terms of the cash flows multiply, as a rate and a factor built from one term:

- `expense_infl()`, the annual expense inflation rate, the row `expense_infl` of `param_tariff_type.csv` (RV's form); a product without the row raises `KeyError`. RV had the cell and Pflege read the row inline; FRV (0.02), Riester (0.02), RLV (0.02) and Sofort (0.015) had a Reference and got the row, and Index's Reference `exp_infl` (0.015), the same rate under another name, became the row `expense_infl`.
- `inflation_factor(t) = (1 + expense_infl()) ** inflation_years(t)`, with the term `inflation_years(t) = duration(t)`: the completed policy years, so the factor counts from issue and steps on the policy anniversary, flat across a policy year's twelve months. RLV, Sofort (its `infl_factor`, `t // 12` on the inception clock), RV, Riester, KLV and Index derive both; KLV's `expenses_pp` reads `inflation_factor(t)` where it read its own `inflation_factor(duration(t))`, and Index's year-indexed `exp_maint_pp(k)` reads `inflation_factor(12 k)`, `duration(12 k) == k` on its inception clock.

The overrides, each with its reason in the cell's docstring:

- `expense_infl`: KLV, a column of `cost_table.csv` at `cost_id()`; Basis, a column of `charge_table.csv` at the tariff. The rate belongs to the cost basis there, beside the levels it inflates.
- `inflation_years`: FRV and Pflege, `t / 12`, inflation compounding continuously from inception (`1.02^(t/12)`, `(1 + f) ** (t / 12)`); Basis, `proj_year(t)`, the projection years from the valuation date, its `t` running on the valuation clock; its year-indexed `unit_cost_pp(k)` reads `inflation_factor(12 k)`, `proj_year(12 k) == k`.

The power is the same subexpression in the same place as in each product's own form, so every product's results are byte-identical. BU has no expense inflation (a German *Verwaltungskostenzuschlag* is fixed in the tariff, `products/berufsunfaehigkeit/technical-notes.md:339`) and inherits the three cells unused.

## The outputs and checks

The core's `Projection` holds the result frames and the cash-flow reconciliation, each a procedure of term cells: the core holds how a frame is built and checked, the product the columns it publishes and the scale it is checked on.

- `roll_fwd_tol()`, the tolerance the `check_*` identities close to, the row `roll_fwd_tol` of `param_tariff_type.csv` (RV's form); a product without the row raises `KeyError`. Every product derives it: Basis 1e-9, BU 1e-10, FRV 1e-10, Index 1e-8, KLV 1e-10, RV 1e-9, Pflege 1e-10, Riester 1e-9, RLV 1e-10, Sofort 1e-8. RV had the cell and Pflege read the row inline; the other eight had a Reference and got the row, BU, Index and RLV with their first `param_table.csv`. `val_tol` stays a product item of its own: a row of FRV's and RLV's `param_tariff_type.csv`.
- `result_cf()`, one column per `(label, cell)` pair of `result_cf_columns()`, each cell evaluated over `t_start() .. proj_len() - 1`, index named `t`. The default columns are the statement the core's cells make: `pols_if`, `premiums`, a `claims_<kind>` column per kind of `claim_kinds()` in its order, `expenses`, `commissions`, `net_cf`, `liability_cf`. KLV derives both. The other nine override `result_cf_columns` with their statement's columns in their order, a column that is not a cell of `t` alone (a claim kind) as a lambda of `t`, the frame's docstring moved to the term: Basis (the paying count, the *Zuzahlungen*, its three kinds), BU (three state counts, the paying count, the *Beitragsverrechnung*, the claims-handling cost, `liability_cf` before `net_cf`), FRV (the premium split into the unit fund, the charges, the *Stornoabzug*, the unit-fund outgo, the death strain), Index (no commission, `liability_cf` before `net_cf`), RV (the annuity count and payments, the *Kapitalabfindung*, no commission), Pflege (the state counts, the claims-handling cost, no commission), Riester (the paying annuity count, the *Zulagen*, six kinds), RLV (the guaranteed premium and the *Beitragsverrechnung* beside the billed premium) and Sofort (the annuity payments, two kinds, no commission).
- `result_cf_annual()`, RV's form: `result_cf` grouped by `policy_year = duration(t) + 1`, the flows summed and each column of `result_cf_counts()` (default `("pols_if",)`) taken at the year's start and placed first. Index, KLV, RLV and RV derive it; RV overrides the counts with `pols_if, pols_annuity`.
- `result_pols()` and `result_states()`, the monthly frame of `result_cf` over `result_pols_columns()` and `result_states_columns()`, both `()` by default. RLV and Sofort derive `result_pols` and override its columns (RLV's reserves through `res_pp_at` and Sofort's two lives as lambdas); Pflege derives `result_states` and overrides its columns (the grade ledgers and the sums over grades and *Karenz* months as lambdas).
- `result_cf_dict()`, `result_cf()` as plain dicts by column, `{label: {t: value}}`, in the frame's column order with the frame's values, built once per point; `check_net_cf_resid` reads it instead of a pandas row per month (epic-night-run, entry 6), and every product derives it.
- `check_net_cf_resid(t)`, the reconciliation KLV and RLV publish: on the frame's values at month `t`, read through `result_cf_dict()`, the columns of `net_cf_income_columns()` (default `premiums`) added left to right, less each column of `net_cf_outgo_columns()` in turn (default a `claims_<kind>` column per kind, then `expenses` and `commissions`), and the residual `net_cf` less that. KLV and RLV derive both terms; Riester overrides the income with `premiums, zulagen` (its kinds give the outgo); RV overrides the outgo with its three claims, `annuity_payments` and `expenses` and derives the income.
- `check_net_cf()`, every `abs(check_net_cf_resid(t))` within `check_net_cf_tol(t)` over `t_start() .. proj_len() - 1`, with `check_net_cf_tol(t) = roll_fwd_tol() * check_net_cf_scale(t)` and `check_net_cf_scale(t) = 1`. The scale overrides: BU `max(1, abs(bu_rente_pp(t)))`, Index `max(abs(premiums(t)), abs(claims(t)), abs(expenses(t)), 1)`, KLV `max(sum_assured(), 1)`, Pflege `max(pols_if_init() * max(rente_mth(), 1), 1)`, Riester `max(1, guar_pp(k_conv() + 1))`, Sofort `max(single_prem() * pols_if_init(), 1)`. FRV and RLV check against `val_tol` and override the tolerance: FRV `val_tol * max(1, abs(net_cf(t)))`, RLV `val_tol * max(sum_assured(), 1)`. The two terms take `t`, so `tools/run_baseline.py` does not list them as checks.

The float order carries the byte identity as before: the core rebuilds the residual in the products' order (income first, then each outgo subtracted), a scale multiplies the tolerance where the product's own expression did, and `float(a) - float(b)` equals `float(a - b)` for RV. A frame's index is set by name (`frame.index.name = "t"`, a `Series` named `policy_year` as the annual grouper), since the grep test reads `Index` as a product prefix.

The overrides, each with its reason in the cell's docstring:

- `result_cf`, `result_states`, `check_net_cf`: BU, whose model point carries no `duration_init`, so the core's `t_start()` is not defined there; its frames run from the valuation month `t = 0` over its own column terms, its check over its tolerance term.
- `result_cf_annual`: Basis and Riester, indexed by the projection year `k` of the valuation clock and summed over each year's twelve-month slice.
- `result_pols`: Basis and RV, the annual state by projection or policy year.
- `check_net_cf_resid`: Basis (the rebuilt flow less `net_cf`, the reverse of the core's sign, with the *Zuzahlungen* as income), BU (the premium leg from the *Zahlbeitrag* billed times the paying count), FRV (the first two charges as premiums less the premium to the unit fund), Index (the kind-less claim total), Pflege (from the cells of its claim kinds and the claims-handling cost), Sofort (the instalment through the single payment factor); each rebuilds by another route on purpose, its docstring naming the boundary it crosses.
- `check_net_cf`: Basis (one scale over the run, the largest `abs(net_cf)`), RV (also asserts `liability_cf(t) == -net_cf(t)`).

A product inherits every frame also where it has none: the core's `result_cf_annual`, `result_pols` and `result_states` are derived in products that do not publish them, and nothing evaluates them there.

Still in the products: the product frames of their own (`result_surplus`, `result_fund`, `result_index`, `result_acct`) and every check but `check_net_cf`, also those two or more products share (`check_pols_roll_fwd`, `check_av_roll_fwd`, `check_prem_split`, `check_decrement_closure`, `check_res_roll_fwd`, `check_equivalence`, `check_annuity_roll_fwd`, `check_conversion`, `check_states`). The runner lists every cell of a product's `Projection` whose name starts with `check_` and that takes no parameter, inherited ones included, so a core `check_pols_roll_fwd` would add a check to Sofort's pinned list, which has `check_lives_roll_fwd` instead; the pinned check lists must not change.

Open work: BU's frames and check derive once its time axis defines `t_start()` (its model point has no `duration_init`); Basis's and Riester's annual frames and `result_pols` of Basis and RV are annual-step views of their own, and the five residuals that cross another boundary stay by design.

## The core quota

The core quota of a product is the share of its executed formulas that come from the core (R8). An executed formula is a cell of the point's `Projection` ItemSpace that holds a value (`len(cell) > 0`) after `result_cf()` and every runner check (`run_baseline.check_names`) for every shipped point, the union over the points, with the model read by `mx.read_model` (the modelx engine, whose cells keep their values). An executed cell counts as core when the product's static `Projection` cell of that name is derived from the core base (`_is_derived()`); an override of a core cell and a product-only cell count as product. `Data` cells, the loaders, are not counted. The quota counts distinct formulas, not calls: a cell evaluated in every month counts once.

The lower bound is 20 % for every product, and a product passes at quota >= 20 % (Moritz, 2026-10-28; epic-common-core Notes), with one exception: BU carries its own bound at its measured quota, 28 of 148 (Moritz, 2026-10-29, epic-night-run Notes, variant c, as recorded in `a5a4781`), since its cohort index, its *Leistungsdynamik* step and its per-claim-year rate arrays keyed by age are product cells of its `Projection`, inside the mutation domain. `LOWER_BOUND` and `PRODUCT_BOUNDS` in `tools/core_quota.py` hold them, `bound_for(product)` gives a product's bound, and `tests/test_core_quota.py` fails for any product below its bound.

| Product | `18a18fa` (merge base) | after the expense inflation |
|---|---|---|
| basisrente | 36 / 106 = 33.96 % | 37 / 109 = 33.94 % |
| berufsunfaehigkeit | 28 / 140 = 20.00 % | 28 / 140 = 20.00 % |
| fondsgebundene_rentenversicherung | 32 / 135 = 23.70 % | 34 / 138 = 24.64 % |
| indexpolice | 47 / 128 = 36.72 % | 50 / 131 = 38.17 % |
| kapitallebensversicherung | 74 / 166 = 44.58 % | 76 / 168 = 45.24 % |
| klassische_rentenversicherung | 48 / 150 = 32.00 % | 51 / 152 = 33.55 % |
| pflegerentenversicherung | 33 / 130 = 25.38 % | 35 / 132 = 26.52 % |
| riester_rente | 49 / 153 = 32.03 % | 52 / 156 = 33.33 % |
| risikolebensversicherung | 64 / 122 = 52.46 % | 67 / 124 = 54.03 % |
| sofortrente | 17 / 89 = 19.10 % | 20 / 91 = 21.98 % |

Sofort was below the bound at the merge base and rises above it with the expense inflation in the core. BU stood exactly at the bound and passed by `>=`; since story 2.16 it is below 20 % at its own bound (above).

To measure:

```text
uv run python tools/core_quota.py risikolebensversicherung
uv run python tools/core_quota.py --all --json /tmp/quota.json
```

The tool prints `<product>: executed <n>, from core <c>, quota <q>` per product, writes the figures and the sorted cell names with `--json`, and exits 1 if any product is below its bound (`bound_for`), each named on stderr with its bound, 2 on a usage error.

## Contract data and charges

`model_point()` is the selected point's row as a dict by column, `model_point_table_dict()[point_id]`; a cell reads a column as `model_point()["<column>"]`. The row is shared with the table's dict cell and is read-only: a cell that assigned into it would change the point for every later read, so `model_point()` returns it as a `types.MappingProxyType` and such an assignment raises `TypeError`. FRV's `charge_row()`, its shared row of `charge_table.csv`, is read-only the same way, and BU's cached `cohort_year_idx(n)` and `cohort_anniv_step(n)` are arrays with `setflags(write=False)`. The core's `Projection` reads the model-point attributes at least two products share, each in the form they had: `policy_id`, `sum_assured`, `rating_factor` (the *Risikozuschlag*; what it multiplies stays the product's), `scenario_id`, `karenz_months`, `smoker` (checked against `smoker_codes()`, `N` and `S`; RLV overrides the codes with `N` and `R`) and `prem_term` (checked against `1 <= prem_term <= policy_term`). Naming equivalents were renamed with their model-point column (BU `risk_factor`, Basis `surplus_scenario_id`, RV `decl_scenario_id`, Riester `rentenbeginn_age`, FRV `annuity_age`, Index `ann_start_age`).

The payment frequency and its loading: `prem_freq()` reads the model point, checked against the keys of the product's `freq_loading_table` (KLV, Index, Riester, RLV, RV, BU); `prem_freq_load()` and `instalments()` read that table at it. Pflege (frequencies with `single` and no loading, checked against the keys of its own `prem_mode_table.csv`) and Basis (the loading is a factor of `option_table.csv`) override `prem_freq`; KLV (1 for an *echt* sub-annual payment) and Basis override `prem_freq_load`. FRV's `prem_mode_months` and Sofort's `payment_freq` count months or instalments directly, without a loading, and stay product cells; each checks the model point against the keys of a table of its own (section "Formula literals").

The *Beitragssumme* and the acquisition charge on it: `beitragssumme() = beitragssumme_prem() * beitragssumme_years()`, the annual premium times the paying years (`prem_gross_pp()`, `prem_term()`; KLV). FRV and Pflege override the two terms for their premium form (instalments, a single premium counted once, Pflege's age-85 cap); Basis and RV (schedule sums with *Dynamik*) and Riester (a model-point column) override `beitragssumme`. `zillmer_amount() = zillmer_on() * alpha_rate() * beitragssumme()` with `zillmer_on() = 1`; KLV overrides `zillmer_on` from its model point, FRV's `alpha_rate` is the *Zuzahlungskosten* rate on a single premium (its `beitragssumme()` is then the premium once), and Riester spreads it over five years. BU's `beitragssumme_unit` (per euro of premium) stays.

The shared loaders in the core's `Data` beside the tables of entry 2: `surplus_table()` (Basis, Riester's `surplus_scenario.csv`), `charge_table()` (FRV; Basis, RV and KLV's `cost_table.csv` override its index term) and `hoechstrechnungszins_table()` (Sofort). KLV's and Index's `surplus_rate_table` and RV's `decl_rate_table` have other keys and stay.

## The parameter files

A scalar parameter, a rate, factor, amount or tolerance with one value per tariff, is a row of a parameter file and is read through one lookup in the core's `Data`, `param("<item>")`, always called with the item's name as a string literal, so that a scan of the code finds every item read (`data.param("<item>")` from a `Projection`). Three layers hold the items, each item in exactly one of them for a tariff:

- the core file `core/Core/Data/param_core.csv`, the technical and house-wide quantities with one value for every tariff type. It holds one item, `rate_cap_eps` (1e-12): Pflege's eleven guards cap a decrement probability at `1 - rate_cap_eps` before taking its force `-ln(1 - q)`, so that the force stays finite at the limiting age (section "Formula literals");
- the tariff-type file in the product folder, named by the product's Reference `param_file`: `param_tariff_type.csv` in all ten products, each renamed from the product's `param_table.csv` (RLV first, the other nine together);
- the tariff file `param_tariff.csv` in the product folder, optional: it appears only at the first value in which a tariff deviates from its tariff type, and the loader skips the layer where it is absent.

Every layer file has the columns `item`, `value`, `basis` and `provenance`. `provenance` says where the value comes from, in the vocabulary of the product's documents; `basis` will say whether it rests on a `source` or a `Setzung` and stays empty until the acceptance decides it. A value whose text is an integer literal (`text.lstrip("+-").isdigit()`) is read as a Python `int`, any other as a Python `float`, `float(text)`, which is correctly rounded and so the value the same decimal literal had as a Python Reference: a parameter moves from a Reference into a file byte-identically.

`param_layers()` reads the three layers in turn, `param_core_path()`, `input_dir() / param_file` and `param_tariff_path()` where it exists, as text (`dtype=str`, `keep_default_na=False`), and returns them once per model as `{"core": {...}, "tariff_type": {...}, "tariff": {...}}`, the `"tariff"` layer only where its file exists. `param_dict()` merges the layers in that order into one dict `{item: value}`; `param(item)` is `param_dict()[item]`, a dict lookup behind one cell, and an unknown item raises `KeyError` naming it. A missing core file raises on the first `param` call; it is not silently skipped. The two path cells are term cells, which a product may override like any core term.

The loader checks the files as it reads them, and a broken file raises `ValueError` on the first `param` call, naming the item and the file or files: an item standing twice in one file; an item of the core file in the tariff-type or the tariff file (the core lock: a core item has one value for every tariff, and a product does not override it); an item standing in both the tariff-type and the tariff file (uniqueness: a later layer never silently replaces an item of an earlier one). `tests/test_core.py` breaks a scratch copy of RLV for each case.

Whether every item is read and every call names an item is checked statically, by the usage scan `core/param_usage.py`, not in a run. `scan(model)` reads a product's modelx model, the formula sources of its `Projection` and `Data` cells only, evaluates no `Projection` cell (of the loader only `param_layers()` and `param_indirect()`), and returns the layers, the items read with the cells reading them, the reachable cells, the declared indirect reads and a list of problems. A call counts for a product only where its cell is reachable: the roots are the product's own cells (`_is_defined()`) in `Projection` and `Data` and every cell named `result_*` or `check_*`, the edges every `ast.Name` id and `ast.Attribute` attr in a cell's source that names a cell of either space. Counting every inherited core cell instead would flag the core's `omega_age`, `unisex_mix_male` and `expense_infl` in the products that inherit them unused. The edges are meant to over-approximate what a run evaluates; `tests/test_core_quota.py` checks that every `Projection` cell the core quota records as executed is reachable (`Data` cells are not compared). A cell that reads parameters other than by a literal `param("<item>")`, a table factory reading its items by a computed name, declares them in the term `param_indirect()`, `{cell: (item, ...)}`, empty in the core; the declared items count as read by the cell. The problems: a call or declared item naming an item no layer holds, an item of the tariff-type or the tariff file that no reachable cell reads, an undeclared indirect read, a declared cell that does not exist, and a cell other than the loader cells (`param`, `param_dict`, `param_layers`) referencing the readers behind `param`. An item of the core file is checked across all ten products together, `unused_core_items(usages)`: it is used if any product reads it. `tests/test_core.py` runs the scan on every product, which reports no problem, and on the core file, which has no unused item, and breaks a scratch copy of RLV for each problem. The parameter tool (entry 14 of epic-parameter-files) builds on the scan.

The core file lives beside the core's loaders rather than at `core/param_core.csv`, and `param_core_path()` finds it as `_model.path / "CoreData" / "param_core.csv"`, through the product's `CoreData` symlink: `param_file` resolves against `input_dir()`, the product folder, and a scratch copy of a product folder (tests, `tools/measure_marginal.py`) copies the `CoreData` folder through the symlink and with it the core file, so a copy reads its own core file and a test can give it a fixture item without touching the core (Moritz, 2026-11-04). `mx.read_model` ignores a CSV file in a space folder, and `tests/test_provenance.py` does not descend into the symlinked folder, so the file adds no cell and no product file.

Every parameter read goes through `param`: the core's parameter cells `omega_age`, `unisex_mix_male`, `expense_infl` and `roll_fwd_tol` and the products' own reads (RV, Pflege, Basis, FRV, KLV, Riester) call `data.param("<item>")`, each in the `int` or `float` wrapper it had. The former DataFrame and dict readers `param_table()` and `param_table_dict()` had no reader left and are gone; `tests/test_core.py` fails on a source that still names them.

## Formula literals

Every numeric literal in a formula cell of the core's `Projection` and the ten products' `Projection` spaces was reviewed (epic-parameter-files, entry 8, and its follow-ups of 2026-11-06): the cells "The new M" counts in `docs/roadmap.md` (module-level `def`s and non-underscore `name = lambda`, walked whole), with the literals inside a subscript and in the arguments of `range(...)` included and the values 0, 1, 0.0 and 1.0 excluded; docstrings hold no formula. The `Data` spaces and the products' `__init__.py` hold no such literal. A literal is actuarial when it states an assumption or a statutory term a tariff could set otherwise; then a parameter mutant on it was a code change, and it became a row of a parameter file. Three further rules decide the rest (Moritz, 2026-11-06):

- **A table's length is read from the table, never written as a literal.** A cap at a table's last row, its last index or its row count is a `Data` cell computed once per model from the table's index, which the formula reads in the literal's place.
- **Payment frequencies are parameters, not code.** A set of allowed frequencies, or a map from a frequency to its months or instalments, is a table of the product's own: a CSV with a `provenance` column, its Reference and reader in `Data`, and a dict or keys cell built once per model that the cell checks the model point against, as the core's `freq_loading_table` and `freq_loading_table_dict` serve `prem_freq`. A single frequency, such as an annual annuity paid in twelve instalments, is a row of the tariff-type file.
- **Units are parameters.** A unit a value is quoted in is a row of the tariff-type file; one quantity has one item name and one type in every product.

What stays code: the calendar (months per year, the last month of a policy year, the months of a year), solver iteration counts and bisection midpoints, and structure indices.

The actuarial literals moved byte-identically, each row's value the literal's text (an `int` stays an `int`), each read a literal `data.param("<item>")` in the literal's place:

- FRV, rows of its `param_tariff_type.csv`: in `lapse_tax_step` the 12/62 rule of EStG § 20 Abs. 1 Nr. 6 Satz 2 with § 52 Abs. 28, `tax_step_min_year` 13 and `tax_step_age` 62, and the step's magnitude `tax_step_factor` 2.5; in `irr_ann` the bisection bracket `irr_lo` -0.99 and `irr_hi` 5.0. The bracket is no actuarial assumption but a row because it bounds the yields the measure can report, and a tariff with other charges could need another one (the ticket names it); the midpoints `0.5` and the iteration count `range(200)` only carry out the bisection inside whatever bracket it is given and stay structural.
- Index: in `prem_charge_acq_min_pp` the five-year spread of § 169 Abs. 3 VVG, `surr_spread_years` 5.
- KLV: in `res_min_pp` the same spread, `surr_spread_years` 5, an `int` as in Index (the literal was `5.0`; `k / 5` is the same true division), and in `benefit_death_pp` the three-year *Selbsttötung* window of § 161 VVG, `suicide_years` 3 (RLV's row of that name has the same value).
- Pflege's eleven guards `1.0 - 1e-12`, which cap a decrement probability below 1 before `-ln(1 - q)`, read `1.0 - data.param("rate_cap_eps")`: the epsilon is technical with one value for every tariff type, so it is the item of the core file (section "The parameter files"); the subtraction stays in the cell.

The table lengths read from their tables, each the table's largest key as an `int`:

- BU: `claim_duration_last_year()` (11), the last `dur_year` of `claim_duration_table.csv`, the ultimate row. `claim_year` caps the claim year at it (was `min(11, …)`), `cohort_year_idx` the index at it minus 1 (was `10`), and `recov_rates` and `mort_dis_sel_factors` read claim years `range(1, claim_duration_last_year() + 1)` (was `range(1, 12)`).
- Pflege: `surrender_table_last_year()` (40), the last `policy_year` of `surrender_table.csv`; `rkw_pp` caps the policy year at it (was `min(policy_year(t), 40)`).

The payment frequencies, each a table of the product's own with its `Data` Reference and reader:

- FRV: `prem_mode_table.csv`, keyed by `prem_mode_months` (1, 3, 6, 12); `prem_mode_months` checks the model point against `prem_mode_table_keys()`, the keys as a `frozenset` of `int` (was the set `(1, 3, 6, 12)`). The table has no column beside its key and the provenance, so a keys cell takes the dict cell's place.
- Pflege: `prem_mode_table.csv`, keyed by `prem_mode` with the column `prem_mode_months` (1, 3, 6, 12, and 0 for `single`); `prem_freq` checks the model point against the keys of `prem_mode_table_dict()` (was a tuple of the five names) and `prem_mode_months` reads it at `prem_freq()` (was a literal dict).
- Sofort: `payment_freq_table.csv`, keyed by `payment_freq` (12, 4, 2, 1); `payment_freq` checks against `payment_freq_table_keys()` (was the set `(1, 2, 4, 12)`).
- Riester: the annuity is paid monthly and its *Rentenfaktor* quoted in euro a month, so the twelve instalments a year are the row `ann_freq` 12, an `int` as Basis' row of that name; `rentenfaktor_curr`, `annuity_pp` and `check_conversion_resid` read it (was `12.0` four times; `12 * x` is `12.0 * x`).

The units, rows of the tariff-type files:

- `rf_unit` 10000.0, the *Rentenfaktor* per 10,000 of capital, as Basis' row: FRV (`annuity_mth_pp`), Index (`ann_monthly_pp`), RV (`pup_cashout`, `annuity_guar_mth_pp`, `check_annuity_conv_resid`, `check_annuity_conv`) and Riester (`rentenfaktor_curr`, `annuity_month_pp`, `is_kleinbetrag`, `check_conversion_resid`).
- `permille_unit` 1000.0, Pflege's per mille of `acq_permille`: `alpha_rate`, `premium_mth_pp` and `check_prem_equiv_resid`.

Each moving commit took its literals out of O6 (and a table length read through `+ 1` or `- 1` added that operator to O3) and updated the counts of `tools/measure_marginal.py` and `tests/test_measure_marginal.py` to the output of the roadmap's command: in entry 8 Pflege 822 to 811, FRV 428 to 421, Index 346 to 344, KLV 422 to 419, M 5,305 to 5,282; in the follow-ups BU 507 to 506, FRV 421 to 414, Pflege 811 to 802, Sofort 485 to 479, Riester 598 to 590, Index 344 to 343, RV 586 to 582, M 5,282 to 5,246; M_core 186 unchanged. The roadmap's section records the counts at `790706b` and stays as it is.

The structural literals, by class and place:

- The calendar: `12` and `12.0` (months per year) in the core and every product, `11`, the last month of a policy year (`t % 12 == 11` in the core's `is_anniv`, `12 k + 11` in Index and KLV), and `13` in Index' `range(1, 13)`, the twelve months of a year. Every `12` was checked against the payment-frequency rule: it converts between months and years on the monthly grid (an annual rate or amount to a month and back, a policy year's months, a premium due on the policy anniversary, `12 // instalments()` months between instalments, a monthly discount or survival step), and none counts the instalments of a payment but Riester's four, now `ann_freq`.
- Structure indices and counts: the second life `2` (RLV's `lives` and `smoker2`, Sofort throughout); Pflege's care grades and ledger positions `2` to `6`; BU's tuple and array positions `2`; RV's `pup - 2`, the row of the year before the paid-up year.
- Numerics: the bisection midpoints `0.5` (FRV, Sofort) and FRV's iteration count `range(200)`.

Sofort's `solve_max_iter` is a row beside `solve_tol` and FRV's bracket `irr_lo`, `irr_hi` rows, against the rule that iteration counts are code; Moritz decides them separately.

`STRUCTURAL_LITERALS` in `tests/test_core.py` lists, for the core and each product, the reprs of the structural literals its formula cells hold, and `test_formula_literals_are_listed_as_structural` walks every formula cell as above and fails on a literal not listed for its space, naming space, cell, line and value, and on a listed value its space no longer holds. The test catches a new literal whose value is not yet listed for its space, which is then either listed here and there as structural or moved into a parameter file or a table; a new literal of a value already listed for its space passes it and is a matter for review.

## Commit trailers

Every commit that touches the core or a product model follows these rules from the first phase-3 commit on. Trailers stand in the last paragraph of the commit message, before `Co-Authored-By`.

- **Byte-identical commit** (refactor, unification without result change, reasoned override, tests, docs): no result trailer. A commit without `Result-Change` claims that every product's results are byte-identical to the commit before; the `pytest` gate (`tests/test_baseline.py` with its pinned hashes) proves it.
- **Result-changing commit**: one trailer naming every product whose results change, the reason, and the agent check:

  ```text
  Result-Change: risikolebensversicherung, kapitallebensversicherung
  Reason: products/kapitallebensversicherung/technical-notes.md, section …
  Checked-By: <agent>: <verdict>
  ```

  `Reason` points to the document and place that justify the change (product docs, a decision); `Checked-By` names the agent that checked the change and its verdict. The same commit updates the affected baselines and their pins. Every deviation from the tag `phase-2-baseline` leads to exactly one such commit.

  The listing of every deviation:

  ```bash
  uv run python tools/baseline_deviations.py
  uv run python tools/baseline_deviations.py --json /tmp/deviations.json
  ```

  The tool reads git only. A deviation is a commit in `phase-2-baseline..HEAD` that changes the content of a product's `baseline/<product>/result_cf.csv` (a mode-only change does not count), adding or removing it included: two commits that change one product's baseline are two deviations, and a change reverted later is still one. A merge counts only for content no parent brings (an evil merge); a PR's change is listed at its branch commit. The tool lists every marked deviation (product, commit, subject, `Reason`), prints `no baseline deviation from phase-2-baseline (<sha>)` when there is none, and exits 1 with each problem on stderr: a deviation whose `Result-Change` does not name the product (`UNMARKED`), a `Result-Change` without a non-empty `Reason` or `Checked-By` (`INCOMPLETE`), a `Result-Change` naming a product whose baseline that commit does not change (`NO CHANGE`), a `Performance: within-rounding` commit that changes a value of a product beyond the tolerance or whose baselines are not comparable (`OUT OF TOLERANCE`, naming the worst breach). It reads the trailers from the trailing paragraphs of the message that consist only of `Key: value` lines, the result trailers' paragraph before the `Co-Authored-By` paragraph included. A missing tag exits 2; fetch it with `git fetch --tags`. A failing git call also exits 2, with `error:` and git's message on stderr. `tests/test_baseline_deviations.py` runs the tool on the repository, so `pytest` fails on an unmarked deviation, and checks every case on a throwaway repository.
- **Performance commit** (epic-night-run), in one of two forms:
  - `Performance: byte-identical`. Results stay byte-identical; the trailer marks the commit as a speed-up rather than a refactor.
  - `Performance: within-rounding`. The commit changes results within rounding and is also a result-changing commit: it rewrites the affected baselines and their pins and carries `Result-Change`, `Reason` and `Checked-By`, with `Performance` in the same trailer block (the trailing paragraphs of `Key: value` lines). Every changed value stays within the tolerance: a euro amount by less than one cent (`|new − old| < 0.005`, taken exactly from the written decimals), every other column (`point_id`, `t`, the `pols_*` counts) only by floating-point noise (`|new − old| ≤ 1e-12 · max(|old|, |new|)`, so zero stays zero and the keys stay equal). Which `result_cf` columns are euro amounts is fixed per product in `EURO_COLUMNS` in `tools/baseline_deviations.py`: every column except `point_id`, `t` and the `pols_*` columns; `tests/test_baseline_deviations.py` pins the map to the baseline headers, so a new column fails until it is classified. `tools/baseline_deviations.py` compares every cell of each affected product's `result_cf.csv` at the commit with its first parent, lists the deviation with the largest euro and relative changes, and exits 1 with `OUT OF TOLERANCE` for a breach, a changed header or row count, an added or removed baseline, or a product missing from the map.
- **Fix forward**: a commit that repairs an earlier commit is not a revert; it names the repaired commit with its full SHA:

  ```text
  Fixes: 0123456789abcdef0123456789abcdef01234567
  ```

  The repaired commit stays in the history, as the README's rules for the history require.

## Measuring rules

Rules for a story or experiment that measures speed (`tools/measure_marginal.py`), learnt in epic-night-run:

- **A rise above 10 % is reasoned with a control.** If a product's `t_marginal` on the branch lies more than 10 % above `main` (epic-night-run, N4), the rise is explained only with alternating runs of a `main` control in the same session: a worktree of `main` (`git worktree add /tmp/<story>-main main`), the same command run in turn on the branch and in the worktree, at least three times each, `uptime` before every run. The plan records the figures of every run and the load average they ran at. A rise that stays within the control's own spread is noise; one beyond it has a cause to name before the commit lands.
- **Every measured figure carries its load average**, the `uptime` taken just before the run; a figure without one cannot reason a rise (N4); older figures without one are compared only with that caveat stated.
- **A failing test is recorded with its name** in the plan, and whether it passed on rerun; "one flaky test" is not a record.
- **Measure again after a review patch that touches a timed path.** A figure stands only for the code it was measured on; a patch to a cell, the runner or the export after the measurement makes the figure stale, and the measurement is repeated on the patched code before it is recorded.
- **A commit harvested from an experiment gets a story's checks.** A commit carried over from a time-boxed experiment branch passes the same mutation-domain check as a story's commit: no business logic moves out of `Projection` (epic-night-run, N1), where mutants could no longer reach it. The harvested commit is cited by its SHA on `main`, not by its SHA on the experiment branch, which other clones do not have.

## Override reason

A product cell that redefines a cell of a core base is an override. Its docstring carries one line with the reason and the document that gives it:

```python
def model_point():
    """The selected model point as a dict by column.

    Override reason: <reason>, <doc ref>
    """
```

The line starts with `Override reason:` and is not empty after the colon. `tests/test_core.py` loads every product that has a core base and fails, naming product and cell, for an override without it. A cell that the product does not define is inherited and needs no reason.

## Changed files in `UPSTREAM.md`

The hash table of a product's `UPSTREAM.md` stays upstream's: it lists every copied file with its upstream SHA-256, also after phase 3 changes the file. A product whose folder phase 3 changes gets a section below the hash table that names every changed file and every added symlink:

```markdown
## Changed in phase 3

| Path | Change |
|---|---|
| `RLV_DE_S/Projection/__init__.py` | `_bases` names `.CoreProjection`; `model_point` moved to the core |
| `RLV_DE_S/CoreProjection` | added: symlink to the core space folder `core/Core/Projection` |
```

`tests/test_provenance.py` skips the hash check for a listed file, requires every listed changed file to stay in the hash table, and requires every symlink in a product folder to be listed and to resolve to a core space folder under `core/`. A changed file that is not listed fails the hash check as before.

As a rule a product adds no regular file, since an added file has no upstream hash; the paths phase 3 adds are symlinks to core space folders. There are two exceptions. A product whose scalar tariff parameter moves into the core gets its first `param_table.csv` (columns `item, value, provenance`, the provenance from the docstring or notes that justified the old Reference; renamed to `param_tariff_type.csv` with a `basis` column it became the tariff-type layer, section "The parameter files", in all ten products, the added file's row naming the rename; RV's `param_table.csv` is upstream's, so it is listed `removed: renamed to param_tariff_type.csv` and `param_tariff_type.csv` as `added:`) and a `param_file` Reference in its `Data`; Basis, FRV, KLV and Riester got theirs for `mort_be_factor` and Sofort for `omega_age`, listed as `added: …`. RLV and BU had one for the *Rechnungszins* until it moved to the model point; it was removed again with its `added:` row. BU, Index and RLV got one for `roll_fwd_tol`, and the other products took the row into the table they had. The other is a merge of input files, decided for each case (epic Notes): Pflege's `basis_table.csv` and `expense_table.csv` merge into one `param_table.csv`, so that RV and Pflege share the core's `param_table` loader. Such a merge is listed with two kinds of change:

```markdown
| `param_table.csv` | added: merged from `basis_table.csv` and `expense_table.csv` |
| `basis_table.csv` | removed: merged into `param_table.csv` |
| `expense_table.csv` | removed: merged into `param_table.csv` |
```

A change starting `added:` that is no symlink names a regular file that must be present and is not in the hash table. A change starting `removed:` names a file of the hash table that must be absent; its row with upstream's hash stays. The folder then holds exactly the hash table's files without the removed ones, plus the added ones and `UPSTREAM.md`.
