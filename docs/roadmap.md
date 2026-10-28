# Roadmap and working notes

## Phase 1: first step

Import upstream `delib` with all standard products at a pinned commit. Then run every product once on its own model points and store the baseline results.

- Upstream as of `fb1d195` has ten products. Each is a separate model with its own tables and `product-spec.md`; they share no code.
- Check whether upstream has moved on (lifelib release 2026-10-10) and pin the start commit explicitly.
- Record provenance per product as in delib-history: upstream commit, source path, SHA-256 of every copied file, and lifelib's licence notice.

## Phase 2: how to measure

- Measure the **marginal** time per contract (the slope), not the average. Run each product at two sizes, for example all shipped points and a replicated multiple, so that fixed costs (model load, export) separate from the per-contract cost.
- State these assumptions with the estimate: the projected number of mutants (from the operator list, scaled to the code size after phase 3) and the pool size. A linear extrapolation without trace-pruning is conservative.
- Mutants exist only after phase 4, so the night-run criterion is a forecast, not a measurement.
- Rough order of magnitude, an estimate only: the term life product alone yields about 500 code mutants with the chosen operators, without parameter cells. 500 mutants × 10,000 contracts in 10 h needs about 7 ms per contract-run across all workers. Today a run takes about 230 ms per contract (82 s for 350 points).

## Known facts to start from

- Term life performance, measured 2026-10-21 in delib-history: about 130 s and 8.2 GB per run of 350 points. Deleting `Projection[pid]` after each point gives 82 s and 155 MB. `mx.export_model` takes about 9.5 s and is bit-identical on 35 states.
- modelx 0.33.0, checked in its source: a formula change marks the space dirty and deletes **all** `Projection[pid]` itemspaces. Caching across mutants therefore does not work at cell level.
- modelx ships a memory-optimised run (`execute_actions` / `get_calcsteps` in `core/model.py`). Look at it before building per-contract cleanup.
- For the test-set repository later: recording the trace per contract allows pruning mutants at positions that are never called. Keep the model traceable.

## Where phase 2 ended

Measured in phase 2d (2026-10-24, details and the earlier steps in [performance.md](performance.md)): with the export engine, per-contract cleanup and 24 worker processes, `t_marginal` is 3.1 to 15.7 ms per contract, and 91.6 ms for `pflegerentenversicherung`; the 230 ms above are the phase-1 starting point. By the forecast (M = 500, P = 10,000), `risikolebensversicherung`, `riester_rente` and, just, `sofortrente` fit the 10 h night; six products miss it by a factor of 1.1 to 2.2, `pflegerentenversicherung` by 12.7. Peak memory no longer grows with the points run.

Speed stays a goal beyond phase 2: faster is always better, and phase 3, which may change the model, closes the remaining gap in its night-run part (below).

## Where the common core stands

The common core of phase 3 is delivered on `main` (PRs #7 and #9 to #19; layout and conventions in [core.md](core.md)). All ten products inherit `core/Core/` through modelx `bases` and override only what is their own, each override with its reason; the groups moved in the dependency order of the RLV graph, from the contract data through the time axis, the tariff basis and present values, the decrement rates, the policy counts and the cash flows to the outputs and checks. `uv run python tools/baseline_deviations.py` finds no baseline deviation from the tag `phase-2-baseline` (`73c7c75`): every product's results are byte-identical to phase 2, and every built-in check is true. The core quota is at least 20 % in every product, from 20.0 % (`berufsunfaehigkeit`, at the bound) and 22.0 % (`sofortrente`) to 54.0 % (`risikolebensversicherung`). Shared quantities whose unification would change results (the gross premium, reserves and annuity present values as one formula, among others) are not unified yet; [core.md](core.md) lists them as open work, each a result-changing commit of its own.

The night run is open (epic-night-run): all ten products together in one 10 h night at M = 500 and P = 10,000 contracts, 1,000 per product, and the new M. Measured with the core on 2026-10-28 (export engine, per-contract cleanup, W = 24, `tools/measure_marginal.py --all --workers 24`), `t_marginal` is 2.5 to 14.1 ms per contract, and 72.0 ms for `pflegerentenversicherung` (91.6 ms in phase 2d); the sum over the ten products is 137.8 ms (171 ms in phase 2d). All ten together, 1,000 contracts each, take 500 × 1,000 × 137.8 ms ≈ 19.1 h and miss the night by a factor of about 1.9 (2.4 in phase 2d); `pflegerentenversicherung` alone is half of it.

## Decisions

- Phase 3 goes through all ten products together, not product by product: one commit unifies one quantity in every product, and one PR is one group of quantities (2026-10-25, reported to the strategist the same day). It replaces the product order of 2026-10-24, which started with `risikolebensversicherung` and ended with `pflegerentenversicherung`; `risikolebensversicherung` stayed the probe for the first core cell.
- Lower bound of the core quota: 20 % for every product, no exception (2026-10-28).
- Contract pool for the night-run criterion: P = 10,000 contracts for now.

## Open questions

- Visibility of this repository: private for now. The licence is MIT, like upstream lifelib and delib-history.
- Contract pool for the night-run criterion: the generator.
