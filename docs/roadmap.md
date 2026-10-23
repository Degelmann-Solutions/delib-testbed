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

## Open questions

- Visibility of this repository: private for now. The licence is MIT, like upstream lifelib and delib-history.
- Order of the products in phase 3.
- Contract pool for the night-run criterion: size and generator.
