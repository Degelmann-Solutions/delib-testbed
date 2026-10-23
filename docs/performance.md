# Performance: reference measurement of phase 2a

The marginal time per contract of every product, measured with `tools/measure_marginal.py` on the unchanged phase-1 runner. Later phase-2 changes are measured with the same tool against this table.

**Timings depend on the machine.** They compare changes on one machine; they are not a property of the model.

- Date: 2026-10-23
- Commit: `10c2ad819fc00cf967dc0993d1be3a85a96c0682`, clean tree
- Machine: 12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62 GB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4
- Command: `uv run python tools/measure_marginal.py --all --json /tmp/phase2a.json` (defaults: factor K = 2, repeats R = 3, M = 500, P = 10,000, W = 1); exit 0, every run verified, wall time 27 min

## Method

Each product runs at two sizes in scratch copies: its shipped `n` points and `K·n` points whose ids `n+1 … K·n` repeat ids `1 … n`. Every (size, repeat) is a fresh process, one at a time, sizes alternating. `T` is the median time of `run_product` (`read_model`, `result_cf`, all checks, hashing); the import of the runner and modelx is timed separately.

- `t_marginal = (T(K·n) − T(n)) / ((K−1)·n)`
- `fixed = import + T(n) − n·t_marginal`
- `MB/contract = (RSS(K·n) − RSS(n)) / ((K−1)·n)`, from the median peak RSS

Every run is verified: no point failed, every id present, every replicated point's `result_cf` equal to its original's, and points `1 … n` reproduce `baseline/<product>/result_cf.csv` byte for byte.

## Result

| Product | n | K·n | T(n) s | T(K·n) s | import s | fixed s | t_marginal ms | RSS(n) MB | RSS(K·n) MB | MB/contract |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 13 | 26 | 7.00 | 13.83 | 0.10 | 0.27 | 525 | 516 | 944 | 32.9 |
| berufsunfaehigkeit | 13 | 26 | 6.85 | 12.19 | 0.09 | 1.59 | 411 | 640 | 1194 | 42.6 |
| fondsgebundene_rentenversicherung | 13 | 26 | 6.40 | 14.02 | 0.10 | −1.13 | 586 | 487 | 886 | 30.7 |
| indexpolice | 13 | 26 | 3.09 | 6.08 | 0.10 | 0.19 | 230 | 231 | 373 | 10.9 |
| kapitallebensversicherung | 14 | 28 | 10.45 | 17.04 | 0.10 | 3.96 | 471 | 731 | 1374 | 46.0 |
| klassische_rentenversicherung | 14 | 28 | 56.58 | 114.04 | 0.10 | −0.78 | 4105 | 4583 | 9076 | 320.9 |
| pflegerentenversicherung | 14 | 28 | 47.93 | 97.13 | 0.10 | −1.17 | 3514 | 2416 | 4756 | 167.1 |
| riester_rente | 13 | 26 | 5.32 | 10.40 | 0.10 | 0.33 | 391 | 465 | 842 | 29.0 |
| risikolebensversicherung | 14 | 28 | 5.02 | 9.92 | 0.10 | 0.22 | 350 | 460 | 833 | 26.6 |
| sofortrente | 14 | 28 | 6.14 | 12.64 | 0.10 | −0.27 | 465 | 499 | 909 | 29.3 |

Status `ok` for all ten products.

Observations:

- The run is almost entirely per-contract cost. The fixed cost (import and `read_model`) is a fraction of a second to about 4 s; for four products it comes out slightly negative, that is, `T(K·n)` is a little more than twice `T(n)`. That is within noise of the medians or a first hint that time per contract grows with `n` while every ItemSpace stays alive; two sizes cannot tell which.
- Memory grows linearly with the contracts held: 11 to 46 MB per contract for eight products, 167 MB for `pflegerentenversicherung` and 321 MB for `klassische_rentenversicherung`.

## Forecast

Assumptions: M = 500 mutants, P = 10,000 contracts, W = 1 worker, for each product on its own; the slope is taken from each product's shipped point mix; two sizes only, so linearity is assumed, not tested. This is a linear extrapolation without trace pruning, and a forecast, not a measurement: mutants exist only after phase 4. The night is 10 h, the exit criterion of phase 2 in the README; it needs `t_marginal ≤ 7.2 ms` at W = 1.

| Product | M·P·t_marginal/W | M·(fixed + P·t_marginal)/W | MB/contract × P, one process |
|---|---:|---:|---:|
| basisrente | 729.3 h | 729.4 h | 321.5 GB |
| berufsunfaehigkeit | 571.1 h | 571.3 h | 416.0 GB |
| fondsgebundene_rentenversicherung | 814.5 h | 814.3 h | 299.5 GB |
| indexpolice | 319.7 h | 319.8 h | 106.9 GB |
| kapitallebensversicherung | 653.6 h | 654.1 h | 448.7 GB |
| klassische_rentenversicherung | 5700.7 h | 5700.6 h | 3134.1 GB |
| pflegerentenversicherung | 4880.4 h | 4880.3 h | 1631.9 GB |
| riester_rente | 543.6 h | 543.6 h | 283.0 GB |
| risikolebensversicherung | 486.0 h | 486.0 h | 260.0 GB |
| sofortrente | 645.4 h | 645.4 h | 286.2 GB |

No product fits the 10 h night: the gap is a factor of about 32 (`indexpolice`) to 570 (`klassische_rentenversicherung`). For every product the extrapolated memory of one process exceeds the machine's 62.8 GB, so a run over the pool needs per-contract cleanup before anything else.
