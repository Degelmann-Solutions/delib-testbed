# The common core of phase 3: layout and conventions

Phase 3 moves the quantities the ten products share into one core. This file describes where the core lives, how a product reaches it, what the core holds of the time axis and the tariff basis, and the conventions every core commit follows: commit trailers, the reason on a product override, and how a product's `UPSTREAM.md` names the files phase 3 changed. The tests that enforce the conventions are `tests/test_core.py` and `tests/test_provenance.py`.

## Layout

- `core/Core/` is a modelx model of its own, with the spaces `Data` and `Projection`. It holds the shared cells and nothing product-specific: no product folder name, model name or model prefix appears anywhere under `core/` (grep test in `tests/test_core.py`). Because it is a readable model, the tests can load it without a product.
- `core/Core/Projection` is parameterized by `point_id`, like every product's `Projection`; its cells are written against the product's names (`data`, `point_id`), which the product space provides.
- `core/Core/Data` holds the shared input loaders. Its cells use the product's References (`pd`, `model_point_file`, `param_file`, `mort_file`, `lapse_file`, `rentenfaktor_file`, `freq_loading_file`), which the product's `Data` defines; the core defines no References.
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

A quantity enters the core when at least two products compute it by the same procedure, also with different parameters or with terms that differ. The core formula is then built from term cells with neutral defaults (0 or 1), and a product overrides only the terms it differs in, each with its reason; the rest of the formula still derives from the core. A switch in the core formula is a last resort, and a choice that depends on the contract belongs in the data (a model-point column or `param_table.csv`), not in the code. A procedure no other product shares stays in the product. A unification that changes results is a commit of its own, one quantity at a time (Moritz, 2026-10-26).

## The time axis

The core's `Projection` holds the time axis on the inception clock, which most products use: `t` counts policy months from issue, `duration_mth(t) = t`, `duration(t) = duration_mth(t) // 12`, `policy_year(t) = duration(t) + 1`, `age(t) = age_y(duration(t))`, `calendar_year(t) = calendar_year_y(duration(t))`, and an in-force point opens its frame at `t_start() = 12 * k_start()` with `k_start() = duration_init()`. The in-force duration stays two model-point columns, `duration_init` in years and `duration_mth_init` in months. Basis, Riester and BU count `t` from the valuation date (a documented frame choice, `products/basisrente/model.md:54`), so they override only the cells where that clock shows: `duration_mth`, and in Basis and Riester also `k_start` (0, the frame opens at the valuation date), `age_y`, `age`, `calendar_year_y` and `calendar_year`; there `duration`, `duration_y`, `policy_year` and `proj_len` still derive from the core. The other overrides of the time axis are a product's own horizon (`proj_len_y` or `proj_len`), a frame start in months (`t_start` in FRV, Pflege and Sofort), BU's floors for a negative `t` (`policy_year`, `age`) and Sofort's second life (`age`); `CORE_CELLS` in `tests/test_core.py` lists them.

## The tariff basis

The core's `Projection` holds the annual first-order equivalence that RLV and KLV share, and the parts of it that other products compute by the same procedure:

- `rechnungszins()` reads the model point's `rechnungszins` column. The rate used at conclusion applies for the whole term (§ 2 Abs. 2 DeckRV, `products/basisrente/sources.md:353`), so a book carries a stack of vintages and the rate is a contract attribute; every product with a *Rechnungszins* derives it (KLV, Riester, Sofort, RV, Index, Basis, RLV, BU and Pflege). RLV, BU and Pflege, which priced the whole book at one rate from `param_table.csv`, carry it as a model-point column, 1,00 % on every shipped point.
- `disc_factor(y) = (1 + rechnungszins()) ** -y`, the annual factor to the start of policy year `y` (RLV, KLV), and `disc_factor_mth(t) = (1 + rechnungszins()) ** (-t / 12)`, the monthly factor (BU, Pflege). At `t = 12 y` the exponent `-t / 12` is exactly `-y`, so the two agree on year starts bit for bit.
- `mort_rate_tariff(t) = mort_rate_tariff_at_age(age(t))`, the first-order annual death rate in month `t` (FRV, KLV). RLV overrides it (the unisex blend loaded by `1 + m` and the rating factor, over two lives), Sofort too (generational, unisex, a second life).
- `pols_tariff(y)`, the tariff survivorship entering policy year `y`, mortality only: 1 for `y <= 0`, then `pols_tariff(y - 1) * (1 - mort_rate_tariff(12 (y - 1)))`. It starts at issue also on an in-force point, since the tariff was struck then (RLV, KLV).
- `tariff_annuity()`, the premium annuity-due `sum(disc_factor(y) * pols_tariff(y))` over `y < prem_term()` (RLV, KLV). Pflege overrides it with the expected present value of its monthly premium in units of `P` on its multi-state tariff ledger.
- `prem_net_level_pp() = tariff_benefit_pv() / tariff_annuity()`, the net level premium, a pricing quantity and never a cash flow (RLV, KLV, Pflege).

Two core cells call a cell the product defines, its hook into the chain: `mort_rate_tariff` calls `mort_rate_tariff_at_age(x)`, the product's first-order rate at an attained age (FRV, KLV), and `prem_net_level_pp` calls `tariff_benefit_pv()`, the present value of the product's benefits on its tariff basis (RLV's death benefits, KLV's death and maturity benefits, Pflege's *Pflegerente*). A product without the hook inherits the core cell unused, as with every other core cell.

Still in the products, because unifying them changes results or adds a quantity (each a result-changing commit of its own, listed as open work):

- The gross premium. RLV, KLV, BU and Pflege solve the same first-order equivalence, `G = rho (A + cost PVs) / ((1 - beta) ae - alpha Beitragssumme - D)`, in different term orders and with different terms; it belongs in the core as a formula of term cells.
- The reserves. RLV's net reserve (`res_pp_at`, `res_zill_pp_at`) and KLV's (`res_net_pp`, `res_zill_pp`) are the same prospective procedure with different terms (maturity benefit, sum-insured schedule); KLV's paid-up and minimum reserves stay in KLV. RV's `av_pp` and Riester's `dk_pp` are the *Deckungskapital* rolled forward retrospectively, so the core's reserve has to offer the retrospective method beside the prospective one. BU and Pflege compute no *Deckungsrückstellung* (`products/berufsunfaehigkeit/technical-notes.md:974`, `products/pflegerentenversicherung/technical-notes.md:32`); adding one is a new quantity.
- The annuity present values of Sofort, Riester and RV (`annuity_factor`, `ann_factor`, `annuity_due_factor`): one sum of discount factor times survivorship, differing in payment frequency, the Woolhouse deduction, the guarantee period and a second life.
- Sofort's and RV's inline discounting with `v = 1 / (1 + i)` raised to month fractions, `disc_factor_mth` in another float order.
- First-order rates under their own names: RV's `mort_rate_guar(t)`, Pflege's `tar_mort_rate(t)` (its `tar_` family), Basis's `mort_rate_base(t)`. Renaming them to `mort_rate_tariff` is byte-identical and makes each a reasoned override of the core cell; it is left for a later entry.

Not suited to the core: the multi-state first-order engines of BU (`*_first` ledgers) and Pflege (`tar_*` ledgers) and Sofort's monthly two-life survivorship (`tariff_lives`), which are different procedures, not one procedure with different terms.

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
- **Performance commit** (epic-night-run): `Performance: byte-identical`. Results stay byte-identical; the trailer marks the commit as a speed-up rather than a refactor.
- **Fix forward**: a commit that repairs an earlier commit is not a revert; it names the repaired commit with its full SHA:

  ```text
  Fixes: 0123456789abcdef0123456789abcdef01234567
  ```

  The repaired commit stays in the history, as the README's rules for the history require.

## Override reason

A product cell that redefines a cell of a core base is an override. Its docstring carries one line with the reason and the document that gives it:

```python
def model_point():
    """The selected model point as a Series.

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

As a rule a product adds no regular file, since an added file has no upstream hash; the paths phase 3 adds are symlinks to core space folders. There are two exceptions. A product whose scalar tariff parameter moves into the core gets its first `param_table.csv` (columns `item, value, provenance`, the provenance from the docstring or notes that justified the old Reference) and a `param_file` Reference in its `Data`; Basis, FRV, KLV and Riester got theirs for `mort_be_factor` and Sofort for `omega_age`, listed as `added: …`. RLV and BU had one for the *Rechnungszins* until it moved to the model point; it was removed again with its `added:` row. The other is a merge of input files, decided for each case (epic Notes): Pflege's `basis_table.csv` and `expense_table.csv` merge into one `param_table.csv`, so that RV and Pflege share the core's `param_table` loader. Such a merge is listed with two kinds of change:

```markdown
| `param_table.csv` | added: merged from `basis_table.csv` and `expense_table.csv` |
| `basis_table.csv` | removed: merged into `param_table.csv` |
| `expense_table.csv` | removed: merged into `param_table.csv` |
```

A change starting `added:` that is no symlink names a regular file that must be present and is not in the hash table. A change starting `removed:` names a file of the hash table that must be absent; its row with upstream's hash stays. The folder then holds exactly the hash table's files without the removed ones, plus the added ones and `UPSTREAM.md`.
