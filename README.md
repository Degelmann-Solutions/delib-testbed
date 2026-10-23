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
- No vendor or client names appear anywhere in the repository.
- The model stays traceable: the trace per contract is not optimised away.

## Status

Phase 1 has not started. The repository holds this description only.
