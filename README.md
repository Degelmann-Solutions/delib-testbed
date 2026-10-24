# delib-testbed

delib-testbed is a multi-product life model built from the `delib` library of [lifelib](https://github.com/lifelib-dev/lifelib), with a real, growing commit history. It starts as upstream's standard products side by side, gets a faster runner, then a common core, and then new tariffs, tariff generations and products.

The repository serves two purposes:

1. **Test object.** A test-set builder, kept in a separate repository, mutates this model and measures the quality of its test sets against the real history recorded here.
2. **Data source.** Commits that change results, including those made by agents during the refactor, are realistic changes and are kept as material.

## What this repository is not

- It holds no test-set selection, no mutation tooling and no quality metric. Those live in the separate test-set repository.
- It is not the oracle of [DeltaRecon](https://github.com/Degelmann-Solutions/deltarecon). [delib-history](https://github.com/Degelmann-Solutions/delib-history) stays that oracle, with its pinned hashes.
- It is not a basis for a client-side calculator.

## Phases

| # | Phase | Done when |
|---|---|---|
| 1 | Import upstream `delib` at a pinned commit: all standard products side by side, unchanged. | Every product runs on its own model points and its results are stored as the per-product baseline. |
| 2 | Performance at runner level only: process parallelism, per-contract cleanup as a switch, and the like. Model-level fixes wait for phase 3. | The shipped model points of every product run as fast as possible with unchanged output values, and the linear extrapolation `N_mutants × N_pool × t_marginal / workers` fits in one night (about 10 h). |
| 3 | Build the common core, largely agent-driven. | Every product reproduces its phase-2 baseline under DeltaRecon's comparison rules (`decimals`, per-quantity bounds). |
| 4 | Add new tariffs, tariff generations and products: public product plans first, own products later. | Open-ended. This is the history the test-set builder measures against. |

[docs/roadmap.md](docs/roadmap.md) holds the measurement method for phase 2, the known facts to start from, and the open questions.

## Rules for the history

- **One change per commit.** The history is the measurement material.
- **Phase-2 commits leave the results of every product unchanged, and prove it.** A commit that changes results anyway is not reverted: it stays in the history and is labelled as result-changing.
- Refactor commits of phase 3 stay in the history, including those that break something unnoticed.
- The interpreter is pinned to its patch version, Python 3.12.13 (`.python-version`).
- Fund products run on one fixed scenario, without stochastics, at first.
- No names of our own vendors or clients appear anywhere in the repository; source citations that files copied byte for byte from upstream bring along, such as insurers and rating agencies, are exempt and stay unchanged.
- The model stays traceable: the trace per contract is not optimised away.

## Layout

- `products/<product>/`: the ten products of upstream `delib`, each a separate model folder (`Basis_DE_S`, `BU_DE_S`, …) with its input tables, `run.py` and upstream's Markdown documents, copied byte for byte. `UPSTREAM.md` records the provenance and the SHA-256 of every copied file; `LICENSE-lifelib.txt` is lifelib's licence notice.
- `tools/run_baseline.py`: the runner. It projects every shipped model point of one product, evaluates the product's built-in checks and prints one SHA-256 over all `result_cf` frames; with `--write` it stores them. By default it deletes each point's ItemSpace once its results and checks are read (per-contract cleanup); `--no-cleanup` keeps them all, as in phase 2a. Its first output line, `cleanup: on` or `cleanup: off`, names the mode; hash and written bytes are the same in both.
- `tools/measure_marginal.py`: the measuring tool of phase 2. It runs the runner in the chosen mode (per-contract cleanup by default, without it under `--no-cleanup`) on each product at two sizes, the shipped points and a replicated multiple in scratch copies, in fresh processes, and derives the fixed cost and the marginal time per contract; it checks that replicated points equal their originals and that the shipped points reproduce the baseline, and prints the night-run forecast with its assumptions.
- `docs/performance.md`: the reference measurement of all products with the measuring tool, with date, machine, commit and command.
- `baseline/<product>/result_cf.csv`: the baseline of each product, all points, columns `point_id,t,<result_cf columns>`, every value written so that it reads back exactly.
- `tests/`: provenance against the recorded hashes, the runner on scratch copies, and the baseline with its pinned hashes.

## Quick start

```sh
uv sync
uv run pytest -q                                          # about 2 min
uv run python tools/run_baseline.py basisrente            # one product: hash and checks
uv run python tools/run_baseline.py basisrente --write    # rewrite baseline/basisrente/
uv run python tools/run_baseline.py basisrente --no-cleanup  # without per-contract cleanup
uv run python tools/measure_marginal.py basisrente         # fixed cost, marginal time per contract, forecast
```

The runner exits 0 when every check of every point is true, 1 when a point raises or a check is false, and 2 on a usage error. A path instead of a product name runs a copy of a product folder.

## Licence

MIT, see [LICENSE](LICENSE). Files copied from lifelib keep lifelib's licence notice, which is stored next to them.

## Status

Phase 1 is done. The ten products are imported unchanged from lifelib at commit `fb1d195ab5423031cfd6d2548fe25a86b76cd0a1` (2026-09-26); the `delib` tree is identical at `b706d8bbab530cc9ef94e06600e9c9d1468d8cb1` (v0.17.2, 2026-10-10). Every product runs on its own shipped model points with all built-in checks true, and its results are stored as its baseline.

Wall time of one runner process per product, measured once on one machine, one product at a time (modelx 0.33.0); it covers the modelx import, the run, the checks and the hash:

| Product | Model | Points | Checks | Wall time |
|---|---|---:|---:|---:|
| basisrente | `Basis_DE_S` | 13 | 6 | 5.4 s |
| berufsunfaehigkeit | `BU_DE_S` | 13 | 7 | 5.0 s |
| fondsgebundene_rentenversicherung | `FRV_DE_S` | 13 | 7 | 5.0 s |
| indexpolice | `Index_DE_S` | 13 | 6 | 2.6 s |
| kapitallebensversicherung | `KLV_DE_S` | 14 | 10 | 7.0 s |
| klassische_rentenversicherung | `RV_DE_S` | 14 | 9 | 38.1 s |
| pflegerentenversicherung | `Pflege_DE_S` | 14 | 6 | 36.4 s |
| riester_rente | `Riester_DE_S` | 13 | 6 | 4.9 s |
| risikolebensversicherung | `RLV_DE_S` | 14 | 5 | 4.7 s |
| sofortrente | `Sofort_DE_S` | 14 | 9 | 5.8 s |
