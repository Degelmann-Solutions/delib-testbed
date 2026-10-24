# Performance: reference measurement of phase 2a

The marginal time per contract of every product, measured with `tools/measure_marginal.py` on the unchanged phase-1 runner. Later phase-2 changes are measured with the same tool against this table.

The 2a reference was measured at `10c2ad8`, before the runner had per-contract cleanup. Since phase 2b the runner cleans up by default; reproducing the 2a table with the current tool needs `--no-cleanup`. The phase-2b measurement follows in its own section below.

**Timings depend on the machine.** They compare changes on one machine; they are not a property of the model.

- Date: 2026-10-23
- Commit: `10c2ad819fc00cf967dc0993d1be3a85a96c0682`, clean tree
- Machine: 12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4
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

No product fits the 10 h night: the gap is a factor of about 32 (`indexpolice`) to 570 (`klassische_rentenversicherung`). For every product the extrapolated memory of one process exceeds the machine's 62.8 GiB, so a run over the pool needs per-contract cleanup before anything else.

# Phase 2b: per-contract cleanup

The same measurement with the runner's per-contract cleanup on (the default since phase 2b): after a point's `result_cf` and checks are read, its ItemSpace is deleted (`del model.Projection[point_id]`). Nothing else changed; how cells are computed and traced is the same.

- Date: 2026-10-24
- Commit: `822591f20093968c7d809524b765f5fb0d865f58`, clean tree
- Machine: the same as for 2a (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Command: `uv run python tools/measure_marginal.py --all --json /tmp/phase2b.json` (defaults: cleanup on, factor K = 2, repeats R = 3, M = 500, P = 10,000, W = 1); exit 0, every run verified, wall time 28 min

## Result

| Product | n | K·n | T(n) s | T(K·n) s | import s | fixed s | t_marginal ms | RSS(n) MB | RSS(K·n) MB | MB/contract (noise) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 13 | 26 | 8.71 | 17.21 | 0.10 | 0.31 | 654 | 139 | 142 | 0.2 |
| berufsunfaehigkeit | 13 | 26 | 8.01 | 15.77 | 0.10 | 0.36 | 597 | 157 | 159 | 0.2 |
| fondsgebundene_rentenversicherung | 13 | 26 | 8.19 | 16.45 | 0.10 | 0.04 | 635 | 141 | 143 | 0.1 |
| indexpolice | 13 | 26 | 3.15 | 6.11 | 0.10 | 0.27 | 228 | 107 | 108 | 0.1 |
| kapitallebensversicherung | 14 | 28 | 12.09 | 23.08 | 0.10 | 1.19 | 785 | 144 | 144 | −0.0 |
| klassische_rentenversicherung | 14 | 28 | 73.09 | 131.42 | 0.10 | 14.86 | 4166 | 542 | 544 | 0.1 |
| pflegerentenversicherung | 14 | 28 | 52.28 | 108.36 | 0.10 | −3.70 | 4005 | 389 | 395 | 0.4 |
| riester_rente | 13 | 26 | 6.04 | 11.92 | 0.09 | 0.26 | 452 | 136 | 139 | 0.2 |
| risikolebensversicherung | 14 | 28 | 5.52 | 10.89 | 0.09 | 0.24 | 384 | 149 | 150 | 0.1 |
| sofortrente | 14 | 28 | 7.57 | 14.95 | 0.09 | 0.28 | 528 | 132 | 134 | 0.1 |

Status `ok` for all ten products: replicas equal their originals and points `1 … n` reproduce `baseline/` byte for byte, as in 2a. Separately, for every product the runner's sha256 and `--write` bytes are identical with and without `--no-cleanup`.

**Memory figure under cleanup: peak RSS per size.** With cleanup, at most one point's ItemSpace is alive, so the peak RSS hardly depends on the number of points: `RSS(n)` and `RSS(K·n)` differ by 0 to 6 MB. `MB/contract` is the difference of two nearly equal medians divided by `n`, that is noise (it even comes out slightly negative for `kapitallebensversicherung`), and so is its extrapolation `MB/contract × P` in the tool's forecast lines. The peak RSS of one process is the figure to use, and it is not expected to grow with P.

## Comparison with 2a

| Product | t_marginal 2a ms | t_marginal 2b ms | change | RSS(n) 2a MB | RSS(n) 2b MB | RSS(K·n) 2a MB | RSS(K·n) 2b MB | RSS(K·n) 2a / 2b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 525 | 654 | +25 % | 516 | 139 | 944 | 142 | 6.7× |
| berufsunfaehigkeit | 411 | 597 | +45 % | 640 | 157 | 1194 | 159 | 7.5× |
| fondsgebundene_rentenversicherung | 586 | 635 | +8 % | 487 | 141 | 886 | 143 | 6.2× |
| indexpolice | 230 | 228 | −1 % | 231 | 107 | 373 | 108 | 3.5× |
| kapitallebensversicherung | 471 | 785 | +67 % | 731 | 144 | 1374 | 144 | 9.5× |
| klassische_rentenversicherung | 4105 | 4166 | +1 % | 4583 | 542 | 9076 | 544 | 16.7× |
| pflegerentenversicherung | 3514 | 4005 | +14 % | 2416 | 389 | 4756 | 395 | 12.0× |
| riester_rente | 391 | 452 | +16 % | 465 | 136 | 842 | 139 | 6.1× |
| risikolebensversicherung | 350 | 384 | +10 % | 460 | 149 | 833 | 150 | 5.5× |
| sofortrente | 465 | 528 | +13 % | 499 | 132 | 909 | 134 | 6.8× |

- **Memory:** peak RSS at K·n falls by a factor of 3.5 (`indexpolice`) to 17 (`klassische_rentenversicherung`); every product now peaks between 108 and 544 MB, against 373 to 9,076 MB in 2a, and no longer grows with the points held. The extrapolated RAM blocker of 2a is gone.
- **Time:** cleanup does not make the run faster. `t_marginal` lies between −1 % and +67 % of the 2a value; the large changes come with a large spread of the single runs (`kapitallebensversicherung` K·n: 21.8, 23.1 and 28.9 s; `klassische_rentenversicherung` n: 63.8 to 88.8 s). A same-day control with both modes back to back on three products (R = 3, not committed as a table) gave with/without cleanup: `risikolebensversicherung` 395 / 324 ms, `kapitallebensversicherung` 506 / 567 ms, `berufsunfaehigkeit` 473 / 463 ms. The effect of cleanup on time is therefore within the noise of this measurement, perhaps a small cost for the cheap products; it is not a speed-up. So the time per contract is not driven by the memory that the live ItemSpaces held in 2a.

## Forecast

Assumptions as in 2a: M = 500 mutants, P = 10,000 contracts, W = 1 worker, each product on its own, slope from the shipped point mix, linearity assumed, not tested; a linear extrapolation without trace pruning and a forecast, not a measurement. The night needs `t_marginal ≤ 7.2 ms` at W = 1.

| Product | M·P·t_marginal/W | M·(fixed + P·t_marginal)/W | gap to 10 h |
|---|---:|---:|---:|
| basisrente | 908.0 h | 908.0 h | 91× |
| berufsunfaehigkeit | 828.7 h | 828.8 h | 83× |
| fondsgebundene_rentenversicherung | 881.9 h | 881.9 h | 88× |
| indexpolice | 317.2 h | 317.3 h | 32× |
| kapitallebensversicherung | 1090.8 h | 1091.0 h | 109× |
| klassische_rentenversicherung | 5786.5 h | 5788.6 h | 579× |
| pflegerentenversicherung | 5563.2 h | 5562.7 h | 556× |
| riester_rente | 627.9 h | 628.0 h | 63× |
| risikolebensversicherung | 532.8 h | 532.9 h | 53× |
| sofortrente | 732.7 h | 732.7 h | 73× |

No product fits the 10 h night: the gap is a factor of about 32 (`indexpolice`) to 579 (`klassische_rentenversicherung`), as in 2a. Memory no longer limits a run over the pool: one process stays at its peak RSS of 108 to 544 MB, so many processes fit side by side in 62.8 GiB. The remaining gap is time; it is what process parallelism (phase 2c) addresses, even perfect scaling over the 24 logical CPUs (W = 24) would leave a factor of about 1.3 to 24.
