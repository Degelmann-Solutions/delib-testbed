# Performance: reference measurement of phase 2a, the phase-2b, phase-2c and phase-2d measurements next to it, the phase-3 per-cell profile and the phase-3 night measurement

The marginal time per contract of every product, measured with `tools/measure_marginal.py` on the unchanged phase-1 runner. Later phase-2 changes are measured with the same tool against this table.

The 2a reference was measured at `10c2ad8`, before the runner had per-contract cleanup. Since phase 2b the runner cleans up by default, since phase 2c it runs on the exported model by default, and since phase 2d it can run the points in worker processes and the tool measures at several worker counts with K = 32 by default; reproducing the 2a table with the current tool needs `--factor 2 --engine modelx --no-cleanup`, the 2b table `--factor 2 --engine modelx`, the 2c table `--factor 2 --workers 1`. The phase-2b, phase-2c and phase-2d measurements, the phase-3 per-cell profile (of the phase-2 state, before the core) and the phase-3 night measurement (the final code of epic-night-run, with a fresh profile) follow in their own sections below.

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

Assumptions: M = 500 mutants, P = 10,000 contracts, W = 1 worker, for each product on its own; the slope is taken from each product's shipped point mix; two sizes only, so linearity is assumed, not tested. This is a linear extrapolation without trace pruning, and a forecast, not a measurement: mutants exist only once the separate test-set repository generates them. The night is 10 h, the exit criterion of phase 2 in the README; it needs `t_marginal ≤ 7.2 ms` at W = 1.

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

No product fits the 10 h night: the gap is a factor of about 32 (`indexpolice`) to 579 (`klassische_rentenversicherung`), as in 2a. Memory no longer limits a run over the pool: one process stays at its peak RSS of 108 to 544 MB, so many processes fit side by side in 62.8 GiB. The remaining gap is time; it is what process parallelism (planned as 2c at the time, now phase 2d) addresses, even perfect scaling over the 24 logical CPUs (W = 24) would leave a factor of about 1.3 to 24.

# Phase 2c: export engine

The same measurement with the runner's export engine (the default since phase 2c): the runner reads the model with modelx, exports it with `mx.export_model` into a package in a temporary folder and runs the points and checks on the exported model, which computes the same formulas without modelx's per-cell trace and dependency graph. Per-contract cleanup is on, as in 2b. The export lands in `run_product` and so in `T` and the fixed cost.

- Date: 2026-10-24
- Commit: `eb36f86d0684cb3950566c3a7007194a9fd9ee04`, clean tree (measured as `5160484`; rebasing a docstring-only rewording into the runner commit gave it this hash, the code is identical)
- Machine: the same as for 2a and 2b (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Command: `uv run python tools/measure_marginal.py --all --json /tmp/phase2c.json` (defaults: engine export, cleanup on, factor K = 2, repeats R = 3, M = 500, P = 10,000, W = 1); exit 0, every run verified, wall time 4.2 min

## Result

| Product | n | K·n | T(n) s | T(K·n) s | import s | fixed s | t_marginal ms | RSS(n) MB | RSS(K·n) MB | MB/contract |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 13 | 26 | 2.23 | 3.35 | 0.10 | 1.20 | 86 | 127 | 138 | 0.8 |
| berufsunfaehigkeit | 13 | 26 | 2.17 | 3.21 | 0.09 | 1.22 | 80 | 233 | 254 | 1.6 |
| fondsgebundene_rentenversicherung | 13 | 26 | 2.07 | 2.87 | 0.09 | 1.37 | 61 | 122 | 134 | 0.9 |
| indexpolice | 13 | 26 | 1.91 | 2.69 | 0.09 | 1.23 | 60 | 120 | 121 | 0.1 |
| kapitallebensversicherung | 14 | 28 | 2.31 | 3.25 | 0.10 | 1.46 | 67 | 123 | 124 | 0.0 |
| klassische_rentenversicherung | 14 | 28 | 2.96 | 4.51 | 0.09 | 1.50 | 111 | 132 | 135 | 0.2 |
| pflegerentenversicherung | 14 | 28 | 10.24 | 18.43 | 0.09 | 2.14 | 585 | 141 | 142 | 0.1 |
| riester_rente | 13 | 26 | 1.84 | 2.34 | 0.10 | 1.43 | 39 | 126 | 142 | 1.2 |
| risikolebensversicherung | 14 | 28 | 1.52 | 1.90 | 0.10 | 1.24 | 27 | 120 | 120 | −0.0 |
| sofortrente | 14 | 28 | 2.05 | 2.83 | 0.10 | 1.37 | 56 | 127 | 146 | 1.3 |

Status `ok` for all ten products: replicas equal their originals and points `1 … n` reproduce `baseline/` byte for byte. Separately, for every product the runner's sha256 and `--write` bytes are identical in the export and the modelx engine, and equal to `baseline/`.

The single runs are close together: the spread of `T` within a size is at most 0.3 s, except `pflegerentenversicherung` n (9.55 to 12.48 s).

**Memory.** Peak RSS stays between 120 and 254 MB. Unlike in 2b, `RSS(K·n)` lies above `RSS(n)` by the same amount in every repeat for five products (11 to 21 MB: `basisrente`, `berufsunfaehigkeit`, `fondsgebundene_rentenversicherung`, `riester_rente`, `sofortrente`). Checked on `basisrente` with `--repeats 1` (2026-10-24):

- In the exported code every ItemSpace sits in a reference cycle (`_mx_roots` in `modelx/export/exporter.py`), so `del Projection[point_id]` frees a point only when Python's cyclic garbage collector runs: over the 13 points the live `Projection` instances go 2, 3, 4, 2, … up to 9 without, and stay at 2 with a `gc.collect()` after each delete.
- The peak RSS grows with the points, but sublinearly: at n = 13 against K·n it is 127 / 137 MB at K = 2, 126 / 152 MB at K = 8, 126 / 170 MB at K = 16, about 0.2 MB per contract beyond 26 points rather than the 0.8 to 1.6 MB of the table's `MB/contract`, so the tool's linear `MB/contract × P` overstates it.
- A `gc.collect()` after each delete does not stop the growth (121 / 153 MB at K = 16) and raises `t_marginal` from about 83 to 129 ms, so the runner does not do it.

The remaining cause of the growth was open for phase 2d, and 2d answers it: it is the CSV lines the runner collected for every point of the run, whether or not they were written (a `tracemalloc` probe on `basisrente` at K = 16 showed +24.8 MiB from `csv_lines` between point 40 and point 207, with the count of Python objects flat), not the export engine; under modelx in 2b the same growth was hidden in the noise. Since 2d the runner collects the lines only with `--write`, and the measuring tool's child only those of the shipped points, comparing replicas by a digest per point. Checked by hand on `basisrente` without `--write` (2026-10-24): peak RSS 128 MB at 13 points, 138 MB at 26, 140 MB at 104, 142 MB at 208 and 142 MB at 832; it no longer grows with the points.

## Comparison with 2b

| Product | t_marginal 2b ms | t_marginal 2c ms | 2b / 2c | fixed 2b s | fixed 2c s |
|---|---:|---:|---:|---:|---:|
| basisrente | 654 | 86 | 7.6× | 0.31 | 1.20 |
| berufsunfaehigkeit | 597 | 80 | 7.5× | 0.36 | 1.22 |
| fondsgebundene_rentenversicherung | 635 | 61 | 10.4× | 0.04 | 1.37 |
| indexpolice | 228 | 60 | 3.8× | 0.27 | 1.23 |
| kapitallebensversicherung | 785 | 67 | 11.7× | 1.19 | 1.46 |
| klassische_rentenversicherung | 4166 | 111 | 37.7× | 14.86 | 1.50 |
| pflegerentenversicherung | 4005 | 585 | 6.8× | −3.70 | 2.14 |
| riester_rente | 452 | 39 | 11.6× | 0.26 | 1.43 |
| risikolebensversicherung | 384 | 27 | 14.2× | 0.24 | 1.24 |
| sofortrente | 528 | 56 | 9.4× | 0.28 | 1.37 |

- **Time per contract:** the export engine cuts `t_marginal` by a factor of 3.8 (`indexpolice`) to 38 (`klassische_rentenversicherung`); eight products now take 27 to 111 ms per contract, `pflegerentenversicherung` 585 ms. This confirms that most of the 2b cost was modelx's per-cell machinery, not the formulas.
- **Fixed cost:** it rises to 1.2 to 2.1 s, which is the export (about 1 s) plus `read_model`. The 2b fixed costs were noisy (from −3.7 to 14.9 s); the 2c ones are consistent.

## Forecast

Assumptions as in 2a and 2b: M = 500 mutants, P = 10,000 contracts, W = 1 worker, each product on its own, slope from the shipped point mix, linearity assumed, not tested; a linear extrapolation without trace pruning and a forecast, not a measurement. The night needs `t_marginal ≤ 7.2 ms` at W = 1.

| Product | M·P·t_marginal/W | M·(fixed + P·t_marginal)/W | gap to 10 h | gap at W = 24 |
|---|---:|---:|---:|---:|
| basisrente | 119.9 h | 120.0 h | 12× | 0.5× |
| berufsunfaehigkeit | 111.2 h | 111.4 h | 11× | 0.5× |
| fondsgebundene_rentenversicherung | 85.2 h | 85.4 h | 9× | 0.4× |
| indexpolice | 83.1 h | 83.3 h | 8× | 0.3× |
| kapitallebensversicherung | 93.5 h | 93.7 h | 9× | 0.4× |
| klassische_rentenversicherung | 153.7 h | 153.9 h | 15× | 0.6× |
| pflegerentenversicherung | 812.6 h | 812.9 h | 81× | 3.4× |
| riester_rente | 54.1 h | 54.3 h | 5× | 0.2× |
| risikolebensversicherung | 37.6 h | 37.7 h | 4× | 0.2× |
| sofortrente | 77.9 h | 78.1 h | 8× | 0.3× |

Still no product fits the 10 h night with one worker: the gap is a factor of about 4 (`risikolebensversicherung`) to 15 (`klassische_rentenversicherung`), and 81 for `pflegerentenversicherung`, against 32 to 579 in 2b. Under perfect scaling over the 24 logical CPUs (W = 24, phase 2d) nine products would fit, `pflegerentenversicherung` would not (factor 3.4). Perfect scaling is an assumption: 24 logical CPUs are not 24 full cores. The memory growth noted above is a point to watch in 2d, where it would add up over the workers.

# Phase 2d: process parallelism

The same measurement with the runner's worker processes (`--workers W`, new in 2d): the parent reads and exports the model once and forks `W` workers, which run single points on the exported model with per-contract cleanup; the parent takes their results in point order. The tool now runs every product at W = 1, 4, 8, 12, 16 and 24, each (W, size, repeat) in a fresh child, and `t_marginal(W)` is wall time per contract across all workers. Two further changes since 2c: the runner no longer collects the CSV lines of every point (see the memory paragraph of 2c), and every process runs with one BLAS/OpenMP thread.

- Date: 2026-10-24
- Commit: `433004b791e03f8382e6b12c7d4cce04139476d5`, clean tree
- Machine: the same as for 2a to 2c (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Command: `uv run python tools/measure_marginal.py --all --json /tmp/phase2d.json` (defaults: engine export, cleanup on, workers W = 1, 4, 8, 12, 16, 24, factor K = 32, repeats R = 3, M = 500, P = 10,000); exit 0, every run verified, wall time 63 min

K is 32 instead of 2: with many workers, the slope of the export engine is small against its fixed cost of about 1.4 s, and K·n = 416 or 448 points gives every worker at W = 24 about 18 points. At a large W, `T(n)` is a single wave of 13 or 14 points in parallel, so `t_marginal(W)` and `fixed(W)` are biased slightly low there; this is stated, not corrected.

**Memory figure: `mem`.** For W = 1 it is the peak RSS of the one process. For W > 1 it is the parent's peak RSS plus, summed over the workers, each worker's largest Pss after a point (read from `/proc/self/smaps_rollup` after every point's cleanup), so pages the workers share copy-on-write with the parent are not counted once per worker. Two biases are stated, not corrected: the Pss after a point's cleanup understates a worker's true peak during the point, and the pages the workers share with the parent are counted close to twice (fully in the parent's RSS, plus each worker's share in its Pss), so at W > 1 `mem` overstates by up to the parent's shared footprint (about 100 MB). `MB/contract` is given at W = 1 only.

## Result

Speed-up is `t_marginal(1) / t_marginal(W)` of the same product.

| Product | W | T(n) s | T(K·n) s | fixed s | t_marginal ms | speed-up | mem(n) MB | mem(K·n) MB | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| basisrente | 1 | 2.37 | 35.56 | 1.40 | 82.4 | 1.0× | 130 | 141 | ok |
| basisrente | 4 | 1.65 | 10.92 | 1.45 | 23.0 | 3.6× | 287 | 443 | ok |
| basisrente | 8 | 1.48 | 7.99 | 1.37 | 16.2 | 5.1× | 317 | 724 | ok |
| basisrente | 12 | 1.51 | 7.16 | 1.42 | 14.0 | 5.9× | 362 | 996 | ok |
| basisrente | 16 | 1.47 | 6.52 | 1.40 | 12.5 | 6.6× | 360 | 1254 | ok |
| basisrente | 24 | 1.54 | 6.14 | 1.49 | 11.4 | 7.2× | 340 | 1762 | ok |
| berufsunfaehigkeit | 1 | 2.14 | 30.11 | 1.33 | 69.4 | 1.0× | 238 | 262 | ok |
| berufsunfaehigkeit | 4 | 1.72 | 10.27 | 1.54 | 21.2 | 3.3× | 406 | 924 | ok |
| berufsunfaehigkeit | 8 | 1.48 | 7.59 | 1.37 | 15.2 | 4.6× | 432 | 1649 | ok |
| berufsunfaehigkeit | 12 | 1.48 | 6.60 | 1.41 | 12.7 | 5.5× | 479 | 2385 | ok |
| berufsunfaehigkeit | 16 | 1.55 | 6.43 | 1.49 | 12.1 | 5.7× | 475 | 3081 | ok |
| berufsunfaehigkeit | 24 | 1.62 | 6.08 | 1.57 | 11.1 | 6.3× | 454 | 4375 | ok |
| fondsgebundene_rentenversicherung | 1 | 2.07 | 28.37 | 1.32 | 65.3 | 1.0× | 123 | 146 | ok |
| fondsgebundene_rentenversicherung | 4 | 1.46 | 9.30 | 1.30 | 19.5 | 3.4× | 250 | 457 | ok |
| fondsgebundene_rentenversicherung | 8 | 1.40 | 6.79 | 1.32 | 13.4 | 4.9× | 300 | 734 | ok |
| fondsgebundene_rentenversicherung | 12 | 1.38 | 6.10 | 1.32 | 11.7 | 5.6× | 344 | 1016 | ok |
| fondsgebundene_rentenversicherung | 16 | 1.40 | 5.56 | 1.36 | 10.3 | 6.3× | 343 | 1204 | ok |
| fondsgebundene_rentenversicherung | 24 | 1.47 | 5.31 | 1.44 | 9.5 | 6.9× | 322 | 1471 | ok |
| indexpolice | 1 | 1.87 | 24.75 | 1.23 | 56.8 | 1.0× | 121 | 122 | ok |
| indexpolice | 4 | 1.37 | 8.50 | 1.23 | 17.7 | 3.2× | 235 | 347 | ok |
| indexpolice | 8 | 1.28 | 5.87 | 1.22 | 11.4 | 5.0× | 285 | 537 | ok |
| indexpolice | 12 | 1.24 | 5.23 | 1.20 | 9.9 | 5.7× | 327 | 720 | ok |
| indexpolice | 16 | 1.26 | 4.75 | 1.23 | 8.7 | 6.6× | 324 | 897 | ok |
| indexpolice | 24 | 1.32 | 4.47 | 1.31 | 7.8 | 7.3× | 305 | 1226 | ok |
| kapitallebensversicherung | 1 | 2.21 | 30.22 | 1.40 | 64.5 | 1.0× | 123 | 124 | ok |
| kapitallebensversicherung | 4 | 1.54 | 10.49 | 1.34 | 20.6 | 3.1× | 243 | 359 | ok |
| kapitallebensversicherung | 8 | 1.52 | 7.80 | 1.42 | 14.5 | 4.5× | 295 | 557 | ok |
| kapitallebensversicherung | 12 | 1.50 | 6.89 | 1.42 | 12.4 | 5.2× | 337 | 746 | ok |
| kapitallebensversicherung | 16 | 1.51 | 6.17 | 1.46 | 10.7 | 6.0× | 348 | 939 | ok |
| kapitallebensversicherung | 24 | 1.48 | 5.82 | 1.43 | 10.0 | 6.4× | 326 | 1270 | ok |
| klassische_rentenversicherung | 1 | 3.05 | 53.33 | 1.52 | 115.9 | 1.0× | 133 | 136 | ok |
| klassische_rentenversicherung | 4 | 1.79 | 15.77 | 1.43 | 32.2 | 3.6× | 357 | 426 | ok |
| klassische_rentenversicherung | 8 | 1.67 | 11.06 | 1.46 | 21.6 | 5.4× | 460 | 694 | ok |
| klassische_rentenversicherung | 12 | 1.76 | 10.69 | 1.57 | 20.6 | 5.6× | 399 | 944 | ok |
| klassische_rentenversicherung | 16 | 1.66 | 9.42 | 1.51 | 17.9 | 6.5× | 389 | 1201 | ok |
| klassische_rentenversicherung | 24 | 1.68 | 8.51 | 1.56 | 15.7 | 7.4× | 366 | 1687 | ok |
| pflegerentenversicherung | 1 | 10.75 | 294.06 | 1.71 | 652.8 | 1.0× | 141 | 143 | ok |
| pflegerentenversicherung | 4 | 4.50 | 79.71 | 2.16 | 173.3 | 3.8× | 416 | 453 | ok |
| pflegerentenversicherung | 8 | 3.69 | 55.71 | 2.10 | 119.9 | 5.4× | 635 | 731 | ok |
| pflegerentenversicherung | 12 | 3.84 | 50.94 | 2.41 | 108.5 | 6.0× | 772 | 1007 | ok |
| pflegerentenversicherung | 16 | 3.76 | 46.95 | 2.47 | 99.5 | 6.6× | 770 | 1277 | ok |
| pflegerentenversicherung | 24 | 3.57 | 43.33 | 2.38 | 91.6 | 7.1× | 752 | 1794 | ok |
| riester_rente | 1 | 1.45 | 10.94 | 1.23 | 23.5 | 1.0× | 126 | 146 | ok |
| riester_rente | 4 | 1.31 | 4.24 | 1.29 | 7.3 | 3.2× | 351 | 460 | ok |
| riester_rente | 8 | 1.20 | 3.13 | 1.22 | 4.8 | 4.9× | 309 | 759 | ok |
| riester_rente | 12 | 1.24 | 2.93 | 1.26 | 4.2 | 5.6× | 359 | 1040 | ok |
| riester_rente | 16 | 1.26 | 2.86 | 1.29 | 4.0 | 5.9× | 354 | 1311 | ok |
| riester_rente | 24 | 1.31 | 2.80 | 1.34 | 3.7 | 6.4× | 335 | 1594 | ok |
| risikolebensversicherung | 1 | 1.18 | 9.27 | 1.00 | 18.6 | 1.0× | 120 | 122 | ok |
| risikolebensversicherung | 4 | 1.05 | 3.62 | 1.05 | 5.9 | 3.2× | 233 | 360 | ok |
| risikolebensversicherung | 8 | 1.10 | 2.72 | 1.13 | 3.7 | 5.0× | 282 | 565 | ok |
| risikolebensversicherung | 12 | 1.07 | 2.62 | 1.10 | 3.6 | 5.2× | 322 | 741 | ok |
| risikolebensversicherung | 16 | 1.08 | 2.53 | 1.12 | 3.3 | 5.6× | 333 | 912 | ok |
| risikolebensversicherung | 24 | 1.11 | 2.46 | 1.15 | 3.1 | 6.0× | 313 | 1263 | ok |
| sofortrente | 1 | 1.70 | 23.09 | 1.09 | 49.3 | 1.0× | 129 | 150 | ok |
| sofortrente | 4 | 1.29 | 7.66 | 1.17 | 14.7 | 3.4× | 318 | 473 | ok |
| sofortrente | 8 | 1.16 | 5.33 | 1.12 | 9.6 | 5.1× | 302 | 796 | ok |
| sofortrente | 12 | 1.18 | 4.84 | 1.14 | 8.4 | 5.8× | 343 | 1093 | ok |
| sofortrente | 16 | 1.18 | 4.57 | 1.16 | 7.8 | 6.3× | 356 | 1396 | ok |
| sofortrente | 24 | 1.19 | 4.27 | 1.17 | 7.1 | 6.9× | 335 | 1830 | ok |

Status `ok` for all 60 (product, W) pairs: replicas equal their originals by digest and points `1 … n` reproduce `baseline/` byte for byte at every W. Separately, for every product the runner's sha256 and `--write` bytes are identical at W = 1 and W = 8, and equal to `baseline/`.

The single runs are close together: at W = 24 the three `T(K·n)` of a product lie within 0.2 s of each other (`pflegerentenversicherung` 42.5 to 44.6 s); at W = 1 the spread is up to 5 s for most products and 40 s for `pflegerentenversicherung` (264 to 304 s).

Observations:

- **Scaling:** every product gains from every step in W, but less than linearly: about 3.1 to 3.8× at W = 4, 4.5 to 5.4× at W = 8 and 6.0 to 7.4× at W = 24. The 24 logical CPUs are 16 cores (8 performance cores with two threads each and 8 efficiency cores), so W = 24 cannot give 24×; the gain from 16 to 24 workers is 7 to 14 %. The best W is 24 for every product.
- **W = 1 against 2c:** `t_marginal(1)` lies between −40 % (`riester_rente` 23.5 against 39 ms, `risikolebensversicherung` 18.6 against 27 ms) and +12 % (`pflegerentenversicherung` 653 against 585 ms) of the 2c value. 2c used K = 2, where the slope of nine products rested on a difference `T(K·n) − T(n)` of 0.4 to 1.6 s (`pflegerentenversicherung` 8 s); K = 32 measures it on a difference of 8 to 283 s. The effect of the single BLAS thread is not separable from this; it is not a large speed-up at W = 1.
- **Memory:** at W = 1 the peak RSS no longer grows with the points: `MB/contract` is 0.00 to 0.06, against 0.0 to 1.6 in 2c. With workers, `mem` grows with W, not with the points: each worker adds about 45 to 80 MB of its own (`berufsunfaehigkeit` about 170 MB), so `mem(K·n)` at W = 24 is 1.2 to 1.8 GB (`berufsunfaehigkeit` 4.4 GB), far below the machine's 62.8 GiB. `mem(n)` is lower than `mem(K·n)` because at n most workers have run one point or none.

## Forecast

Assumptions: M = 500 mutants, P = 10,000 contracts, each product on its own, slope from the shipped point mix, linearity assumed, not tested; a linear extrapolation without trace pruning and a forecast, not a measurement. Unlike in 2a to 2c, the forecast does not divide by W: `t_marginal(W)` is measured with W workers. The night is 10 h, which needs `t_marginal(W) ≤ 7.2 ms`.

| Product | t_marginal(1) ms | best W | t_marginal(best) ms | speed-up | M·P·t_marginal(1) | M·P·t_marginal(best) | M·(fixed + P·t_marginal), best | gap to 10 h, best W | mem(K·n) at best W MB | MB/contract at W = 1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 82.4 | 24 | 11.4 | 7.2× | 114.4 h | 15.8 h | 16.1 h | 1.58× | 1762 | 0.03 |
| berufsunfaehigkeit | 69.4 | 24 | 11.1 | 6.3× | 96.4 h | 15.4 h | 15.6 h | 1.54× | 4375 | 0.06 |
| fondsgebundene_rentenversicherung | 65.3 | 24 | 9.5 | 6.9× | 90.6 h | 13.2 h | 13.4 h | 1.32× | 1471 | 0.06 |
| indexpolice | 56.8 | 24 | 7.8 | 7.3× | 78.9 h | 10.9 h | 11.0 h | 1.09× | 1226 | 0.00 |
| kapitallebensversicherung | 64.5 | 24 | 10.0 | 6.4× | 89.7 h | 13.9 h | 14.1 h | 1.39× | 1270 | 0.00 |
| klassische_rentenversicherung | 115.9 | 24 | 15.7 | 7.4× | 160.9 h | 21.9 h | 22.1 h | 2.19× | 1687 | 0.01 |
| pflegerentenversicherung | 652.8 | 24 | 91.6 | 7.1× | 906.7 h | 127.3 h | 127.6 h | 12.73× | 1794 | 0.00 |
| riester_rente | 23.5 | 24 | 3.7 | 6.4× | 32.7 h | 5.1 h | 5.3 h | 0.51× | 1594 | 0.05 |
| risikolebensversicherung | 18.6 | 24 | 3.1 | 6.0× | 25.9 h | 4.3 h | 4.5 h | 0.43× | 1263 | 0.00 |
| sofortrente | 49.3 | 24 | 7.1 | 6.9× | 68.5 h | 9.9 h | 10.0 h | 0.99× | 1830 | 0.05 |

With process parallelism at the best worker count, three products fit the 10 h night by the forecast: `risikolebensversicherung` (4.3 h), `riester_rente` (5.1 h) and, just, `sofortrente` (9.9 h, 10.0 h with the fixed cost per mutant). Six miss it by a factor of 1.1 (`indexpolice`) to 2.2 (`klassische_rentenversicherung`), and `pflegerentenversicherung` by a factor of 12.7. Against 2c at W = 1 (factor 4 to 15, `pflegerentenversicherung` 81) this is the gain of the workers; it is smaller than the "perfect scaling over 24 CPUs" of the 2c forecast (gap at W = 24 of 0.2 to 0.6, `pflegerentenversicherung` 3.4), because the measured speed-up at W = 24 is about 7×, not 24×.

This is as fast as the runner gets at runner level (export engine, per-contract cleanup, process parallelism), which is phase 2's exit criterion in the README. The remaining gap is documented here and is not a condition of phase 2; closing it needs changes to the model (phase 3) or trace pruning, more cores, or fewer mutants or contracts per night.

# Phase 3: per-cell profile

Where the per-point time of every product goes, cell by cell: the map epic-night-run's optimisations start from. Read-only: no model, runner, tool or test changed; the profiling script is the command below and is not part of the repo. The profile is of the phase-2 state: the branch's base `73c7c75` (merge of PR #6), before the common core of PR #7.

- Date: 2026-10-25
- Commit: `73c7c751318b89bf631bcb5c5a7b70595bb5ae94`, clean tree
- Machine: the same as for 2a to 2d (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Command: the script below, run from the repository root; exit 0, `ok` for all ten products, wall time about 45 s

```sh
uv run python - <<'EOF'
import importlib, sys, time
from collections import defaultdict
sys.path.insert(0, "tools")
import run_baseline as rb

def run(product, profile):
    """One run_product at W = 1; returns n, ok, loop seconds, exclusive ns and calls."""
    excl, calls, stack, mark = defaultdict(int), defaultdict(int), [], {}
    real_import = importlib.import_module

    def timed(key, f):
        def g(self, *a):
            stack.append(0); t0 = time.perf_counter_ns()
            try:
                return f(self, *a)
            finally:
                el = time.perf_counter_ns() - t0; child = stack.pop()
                excl[key] += el - child; calls[key] += 1
                if stack: stack[-1] += el
        return g

    def hook(name, *a, **k):
        mod = real_import(name, *a, **k)
        if name.startswith("_delib_export_"):
            if profile:
                classes = real_import(name + "._mx_classes")
                for cname, cls in list(vars(classes).items()):
                    if cname.startswith("_c_") and isinstance(cls, type):
                        for attr, f in list(vars(cls).items()):
                            if attr.startswith("_f_") and callable(f):
                                setattr(cls, attr, timed((cname[3:], attr[3:]), f))
            mark["t0"] = time.perf_counter()
        return mod

    importlib.import_module = hook
    try:
        n, _checks, _sha, failures, lines, _d = rb.run_product(rb.resolve_product(product), keep_lines=True)
    finally:
        importlib.import_module = real_import
    loop = time.perf_counter() - mark.get("t0", 0.0)
    expected = (rb.BASELINE_DIR / product / rb.CSV_NAME).read_bytes()
    ok = not failures and ("\n".join(lines) + "\n").encode("ascii") == expected
    return n, ok, loop, excl, calls

names = rb.product_names()
order = ["pflegerentenversicherung"] + sorted(p for p in names if p != "pflegerentenversicherung")
bad = []
for p in order:
    n, ok0, loop0, _, _ = run(p, profile=False)
    n, ok, loop, excl, calls = run(p, profile=True)
    if not (ok and ok0):
        print(f"{p}: FAILED"); bad.append(p); continue
    point = {k: v for k, v in excl.items() if k[0] != "Data"}
    data = {k: v for k, v in excl.items() if k[0] == "Data"}
    tot = sum(point.values())
    print(f"\n{p}: ok  n={n}  spaces={sorted({k[0] for k in excl})}")
    print(f"  point loop ms/point: unprofiled {loop0 / n * 1e3:.1f}, profiled {loop / n * 1e3:.1f}"
          f"  | per-point cells: {tot / n / 1e6:.1f} ms/point, {sum(calls[k] for k in point) / n:.0f} calls/point"
          f"  | Data cells, once per run: {sum(data.values()) / 1e6:.1f} ms")
    cum, cap = 0, 15 if p == "pflegerentenversicherung" else 10
    for i, (k, v) in enumerate(sorted(point.items(), key=lambda kv: -kv[1])):
        if i == cap or cum >= 0.8 * tot:
            break
        cum += v
        print(f"  {k[0]}.{k[1]:<32} {v / n / 1e6:7.2f} ms/pt {v / tot:6.1%}  cum {cum / tot:6.1%}  {calls[k] / n:6.0f} calls/pt")
print("\nFAILED: " + ", ".join(bad) if bad else "\nall ok")
sys.exit(1 if bad else 0)
EOF
```

## Method

For each product, `pflegerentenversicherung` first and then alphabetically, the script calls the runner's `run_product` twice at W = 1 on the export engine with cleanup: once unprofiled, once profiled. For the profiled run it wraps `importlib.import_module`; when the runner imports the exported package (`_delib_export_…`), every formula method `_f_<cell>` of every space class in `_mx_classes` is replaced by a timer. Item spaces `Projection[i]` are instances of the same class, so this covers every point.

- **What is timed:** each evaluation of a cell's formula, that is each cache miss. The cache lookup of a hit is not a call; it costs the calling cell, inside whose formula it happens. `calls/pt` counts formula evaluations over all argument values of the cell, per point.
- **Exclusive time:** a cell's own time minus the time of the cells it calls (a stack of child times, `perf_counter_ns`). Nested cells are not counted twice, and pandas/numpy time is attributed to the cell that calls pandas or numpy, which cProfile's per-function `tottime` would not do. Checks are cells too and run per point; they are reported like other cells.
- **Per point and Data apart:** cells of `Projection` (the only per-point space in all ten products) make up the per-point time, which is what `t_marginal` measures; their exclusive time summed over the run is divided by n. Cells of `Data` run once per run, mostly on the first point, and are given as one total per run.
- **Point loop:** wall time from the import of the exported package to the end of `run_product` (all points with their checks, hashing, CSV lines, cleanup), divided by n; `read_model` and the export are not in it. It is not `t_marginal`: n is 13 or 14 and nothing is replicated. The per-point cell time is 92 to 99 % of the profiled point loop; the rest is the runner's hashing, CSV lines and cleanup.
- **Verified:** both runs of every product must have no failures and their CSV lines must equal `baseline/<product>/result_cf.csv` byte for byte, else the script prints `FAILED` for the product and exits 1.

**Overhead caveat.** The timer adds about 0.3 to 0.8 µs per formula evaluation: the profiled point loop is 12 to 49 % slower than the unprofiled one (summary table), most where cells are many and cheap (`riester_rente`, `risikolebensversicherung`). Part of this overhead lands in the exclusive time of the calling cells, so cells with many cheap callees are overstated somewhat; the shares of the big lookup cells are not changed in substance. Garbage-collection pauses are attributed to whichever cell triggers them: in an earlier trial run of `berufsunfaehigkeit` about 6 ms per point moved between `pv_rente_first` and `mort_rate_dis_first_mth_year`. The overhead and the unprofiled ms/pt rest on a single unprofiled and a single profiled run per product, back to back, so they carry run-to-run noise of the same order as the overhead itself and are indicative only; in one rerun on a loaded machine the unprofiled loop of two products was slower than the profiled one. Several full runs of the command gave the same top cells per product, only adjacent cells of nearly equal share swapping places, and cells near the 80 % cut-off can change places (in one rerun the 13th row of `pflegerentenversicherung` was `p_pg_death`, 1.3 %, instead of `expenses`, 1.4 %); the tables below are from the first run.

## Summary

| Product | n | point loop ms/pt, unprofiled | point loop ms/pt, profiled | overhead | per-point cells ms/pt | calls/pt | Data ms/run | top cell | share | rows to 80 % |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| pflegerentenversicherung | 14 | 554.7 | 618.7 | +12 % | 614.8 | 100,834 | 7.2 | `tar_mort_rate_care` | 31.1 % | 13 |
| basisrente | 13 | 69.9 | 89.7 | +28 % | 86.5 | 26,460 | 5.5 | `expenses` | 21.3 % | 10 |
| berufsunfaehigkeit | 13 | 57.4 | 64.7 | +13 % | 62.4 | 25,720 | 5.8 | `dis_cohorts_first` | 12.9 % | > 10 (72.0 %) |
| fondsgebundene_rentenversicherung | 13 | 59.6 | 69.4 | +16 % | 67.1 | 24,953 | 3.5 | `fund_return_gross_ann` | 35.4 % | 6 |
| indexpolice | 13 | 51.9 | 58.7 | +13 % | 57.3 | 8,990 | 6.1 | `index_return` | 39.0 % | 4 |
| kapitallebensversicherung | 14 | 62.0 | 70.8 | +14 % | 69.5 | 13,036 | 5.7 | `mort_rate_base` | 29.2 % | > 10 (77.2 %) |
| klassische_rentenversicherung | 14 | 101.7 | 121.7 | +20 % | 118.6 | 31,191 | 6.8 | `check_decrement_closure_resid` | 41.3 % | > 10 (75.3 %) |
| riester_rente | 13 | 25.1 | 37.5 | +49 % | 34.6 | 22,964 | 6.4 | `check_net_cf_resid` | 33.8 % | > 10 (76.1 %) |
| risikolebensversicherung | 14 | 18.1 | 24.1 | +33 % | 22.8 | 12,800 | 4.6 | `benefit_factor` | 23.5 % | > 10 (75.5 %) |
| sofortrente | 14 | 48.7 | 59.5 | +22 % | 57.4 | 23,203 | 4.4 | `mort_rate_at_age` | 40.4 % | 7 |

The unprofiled point loop per point, a single run per product and indicative only, is in the same order as `t_marginal(1)` of phase 2d (for example 555 against 653 ms for `pflegerentenversicherung`, 18.1 against 18.6 ms for `risikolebensversicherung`), as it should be; it is a different measurement (see Method). Data cells take 3.5 to 7.2 ms per run, against a point loop of 0.25 to 8 s: they do not matter for `t_marginal`.

## Top cells per product

Cells in descending exclusive time per point until they cover at least 80 % of the per-point cell time, at most 10 rows (15 for `pflegerentenversicherung`). All cells are in `Projection`. Share and cumulative share are of the per-point cell time.

**pflegerentenversicherung** (n = 14; 614.8 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `tar_mort_rate_care` | 191.22 | 31.1 % | 31.1 % | 2,962 |
| `rec_rate` | 68.29 | 11.1 % | 42.2 % | 3,493 |
| `mort_force_care` | 38.02 | 6.2 % | 48.4 % | 3,553 |
| `tar_mort_rate` | 37.30 | 6.1 % | 54.5 % | 592 |
| `tar_inc_rate` | 35.75 | 5.8 % | 60.3 % | 581 |
| `tar_det_rate` | 24.07 | 3.9 % | 64.2 % | 2,919 |
| `mort_rate` | 22.16 | 3.6 % | 67.8 % | 711 |
| `tar_rec_rate` | 20.96 | 3.4 % | 71.2 % | 2,919 |
| `check_prem_equiv_resid` | 15.74 | 2.6 % | 73.8 % | 593 |
| `inc_rate` | 15.24 | 2.5 % | 76.2 % | 696 |
| `tar_p_pg` | 11.67 | 1.9 % | 78.1 % | 2,962 |
| `p_pg_better` | 9.42 | 1.5 % | 79.7 % | 3,553 |
| `expenses` | 8.55 | 1.4 % | 81.1 % | 711 |

Ten rows reach 76.2 %, thirteen 81.1 %. The point is dominated by the care-grade rates: about 100,000 formula evaluations per point, of which the ones with a grade argument `g` (care grades 1 to 5) run about five times per month. `tar_mort_rate_care` alone is 65 µs per evaluation: five scalar `DataFrame.at` lookups (two into the `(sex, age)` MultiIndex of `mort_table`, the others into `basis_table` and `care_table`), evaluated for every month `t` and grade `g`, although the `mort_table` values depend only on `age(t)`, which changes once a year. The nine rate cells in the table (all but `check_prem_equiv_resid`, `tar_p_pg`, `p_pg_better` and `expenses`), each a few scalar table lookups and a little arithmetic, are 73.7 % of the point.

**basisrente** (n = 13; 86.5 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `expenses` | 18.38 | 21.3 % | 21.3 % | 877 |
| `commissions` | 13.21 | 15.3 % | 36.5 % | 877 |
| `check_net_cf_resid` | 13.12 | 15.2 % | 51.7 % | 877 |
| `ann_bonus_rate` | 7.51 | 8.7 % | 60.4 % | 54 |
| `result_cf` | 4.94 | 5.7 % | 66.1 % | 1 |
| `claims` | 3.20 | 3.7 % | 69.8 % | 3,508 |
| `decl_rate` | 3.20 | 3.7 % | 73.5 % | 18 |
| `bf_rate` | 3.08 | 3.6 % | 77.1 % | 18 |
| `check_no_capital_resid` | 1.50 | 1.7 % | 78.8 % | 877 |
| `mort_rate_at_age` | 1.37 | 1.6 % | 80.4 % | 72 |

**berufsunfaehigkeit** (n = 13; 62.4 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `dis_cohorts_first` | 8.06 | 12.9 % | 12.9 % | 352 |
| `dis_cohorts` | 7.48 | 12.0 % | 24.9 % | 339 |
| `mort_rate_dis_first_mth_year` | 7.37 | 11.8 % | 36.7 % | 351 |
| `lapse_rate` | 6.58 | 10.5 % | 47.2 % | 338 |
| `dis_exits_first` | 4.95 | 7.9 % | 55.2 % | 351 |
| `dis_exits` | 4.72 | 7.6 % | 62.7 % | 338 |
| `result_cf` | 2.12 | 3.4 % | 66.1 % | 1 |
| `claims` | 1.69 | 2.7 % | 68.8 % | 1,353 |
| `pv_rente_first` | 1.17 | 1.9 % | 70.7 % | 1 |
| `pv_claim_cost_first` | 0.84 | 1.3 % | 72.0 % | 1 |

**fondsgebundene_rentenversicherung** (n = 13; 67.1 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `fund_return_gross_ann` | 23.78 | 35.4 % | 35.4 % | 339 |
| `fund_ter_ann` | 22.33 | 33.3 % | 68.7 % | 339 |
| `result_cf` | 2.87 | 4.3 % | 73.0 % | 1 |
| `lapse_rate_base` | 2.77 | 4.1 % | 77.1 % | 338 |
| `av_pp_at` | 1.66 | 2.5 % | 79.6 % | 1,355 |
| `fund_return_net_ann` | 0.73 | 1.1 % | 80.7 % | 339 |

**indexpolice** (n = 13; 57.3 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `index_return` | 22.32 | 39.0 % | 39.0 % | 279 |
| `mort_rate` | 19.39 | 33.9 % | 72.9 % | 279 |
| `lapse_rate_base` | 3.70 | 6.5 % | 79.3 % | 267 |
| `elect_index` | 1.73 | 3.0 % | 82.3 % | 23 |

**kapitallebensversicherung** (n = 14; 69.5 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `mort_rate_base` | 20.29 | 29.2 % | 29.2 % | 277 |
| `check_decrement_closure_resid` | 4.52 | 6.5 % | 35.7 % | 277 |
| `lapse_rate` | 4.36 | 6.3 % | 42.0 % | 276 |
| `expenses_pp` | 4.17 | 6.0 % | 48.0 % | 277 |
| `check_net_cf_resid` | 3.73 | 5.4 % | 53.4 % | 277 |
| `commissions` | 3.64 | 5.2 % | 58.6 % | 277 |
| `inflation_factor` | 3.36 | 4.8 % | 63.4 % | 23 |
| `decl_rate` | 3.25 | 4.7 % | 68.1 % | 23 |
| `mort_rate_at_age` | 3.20 | 4.6 % | 72.7 % | 24 |
| `ans_rate` | 3.09 | 4.5 % | 77.2 % | 23 |

**klassische_rentenversicherung** (n = 14; 118.6 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `check_decrement_closure_resid` | 48.97 | 41.3 % | 41.3 % | 863 |
| `check_net_cf_resid` | 12.02 | 10.1 % | 51.4 % | 863 |
| `mort_rate_guar` | 9.46 | 8.0 % | 59.4 % | 863 |
| `mort_rate_at_age` | 5.10 | 4.3 % | 63.7 % | 72 |
| `result_cf` | 3.74 | 3.2 % | 66.8 % | 1 |
| `lapse_rate` | 3.10 | 2.6 % | 69.4 % | 863 |
| `claims` | 1.91 | 1.6 % | 71.1 % | 3,453 |
| `charge_prem_pp` | 1.75 | 1.5 % | 72.5 % | 72 |
| `surr_charge_pp` | 1.66 | 1.4 % | 73.9 % | 72 |
| `check_net_cf` | 1.64 | 1.4 % | 75.3 % | 1 |

**riester_rente** (n = 13; 34.6 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `check_net_cf_resid` | 11.69 | 33.8 % | 33.8 % | 727 |
| `result_cf` | 4.32 | 12.5 % | 46.3 % | 1 |
| `mort_rate_at_age` | 3.26 | 9.4 % | 55.7 % | 16 |
| `claims` | 1.47 | 4.3 % | 59.9 % | 4,364 |
| `lapse_rate` | 1.26 | 3.7 % | 63.6 % | 195 |
| `transfer_rate` | 1.12 | 3.2 % | 66.8 % | 195 |
| `mort_rate` | 0.93 | 2.7 % | 69.5 % | 727 |
| `pols_if_at` | 0.93 | 2.7 % | 72.2 % | 727 |
| `zulage_entitlement_pp` | 0.78 | 2.3 % | 74.4 % | 16 |
| `check_net_cf` | 0.57 | 1.7 % | 76.1 % | 1 |

**risikolebensversicherung** (n = 14; 22.8 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `benefit_factor` | 5.37 | 23.5 % | 23.5 % | 267 |
| `check_net_cf_resid` | 3.47 | 15.2 % | 38.7 % | 267 |
| `lapse_rate_base` | 1.82 | 8.0 % | 46.7 % | 255 |
| `lapse_cum` | 1.67 | 7.3 % | 54.0 % | 267 |
| `result_cf` | 1.47 | 6.5 % | 60.5 % | 1 |
| `mort_rate_at_age` | 1.35 | 5.9 % | 66.4 % | 46 |
| `benefit_paid_pp` | 0.62 | 2.7 % | 69.1 % | 267 |
| `claims` | 0.57 | 2.5 % | 71.6 % | 1,066 |
| `pols_if_at` | 0.45 | 2.0 % | 73.5 % | 533 |
| `sum_uplift_y` | 0.45 | 2.0 % | 75.5 % | 23 |

**sofortrente** (n = 14; 57.4 ms per point in cells)

| Cell | ms/pt | share | cum | calls/pt |
|---|---:|---:|---:|---:|
| `mort_rate_at_age` | 23.20 | 40.4 % | 40.4 % | 213 |
| `improve_rate_at_age` | 13.33 | 23.2 % | 63.6 % | 104 |
| `annuity_payments` | 4.36 | 7.6 % | 71.2 % | 1,921 |
| `result_cf` | 2.38 | 4.1 % | 75.3 % | 1 |
| `claims` | 1.19 | 2.1 % | 77.4 % | 1,921 |
| `annuity_factor` | 0.87 | 1.5 % | 78.9 % | 1 |
| `pols_if` | 0.85 | 1.5 % | 80.4 % | 640 |

## Observations

- **Scalar table lookups dominate.** In seven of the ten products the top cells read one value from an input table per month or per age with `DataFrame.at` or `.loc`, often on a MultiIndex, at about 10 to 130 µs per evaluation, against about 1 µs or less for a cell of plain arithmetic: `pflegerentenversicherung` (the care-grade rates, 73.7 %), `fondsgebundene_rentenversicherung` (`fund_return_gross_ann` and `fund_ter_ann` on `(scenario, policy year)`, 68.7 %), `indexpolice` (`index_return` and `mort_rate`, 72.9 %), `sofortrente` (`mort_rate_at_age` and `improve_rate_at_age`, 63.6 %, which also take the min and max of the age level of the index on every evaluation), `kapitallebensversicherung` (`mort_rate_base`, 29.2 %), `risikolebensversicherung` (`benefit_factor`, 23.5 %), `basisrente` (`expenses` and `commissions`, which select the tariff's row of `charge_table` on every month, 36.5 %) and the lapse-rate cells of several products. The values looked up depend on few inputs (sex, age, policy year, scenario, grade), so precomputing them once per run or per point as arrays or dicts is the obvious lever; it stays byte-identical only if the same floats come out.
- **Checks are a large part of the point.** The `check_*_resid` cells run every point and are part of `t_marginal`. `check_net_cf_resid`, which takes the row `result_cf().loc[t]` as a Series for every month, is 33.8 % of `riester_rente`, 15.2 % of `basisrente` and `risikolebensversicherung`, 10.1 % of `klassische_rentenversicherung` and 5.4 % of `kapitallebensversicherung`. `check_decrement_closure_resid` of `klassische_rentenversicherung` sums the exits over all months up to `t` for every `t`, quadratic in the projection length: 41.3 % of the product's point; the same cell in `kapitallebensversicherung` has the same form at 6.5 %.
- **Python loops elsewhere.** `berufsunfaehigkeit` is the one product without a dominant lookup: its disability cohorts (`dis_cohorts*`, `dis_exits*`, `mort_rate_dis_first_mth_year`) are list and tuple loops in Python, together 52 % of the point, spread over many cells (10 rows reach 72.0 %).
- **`result_cf` itself** (building the DataFrame from per-month lists) is 2 to 7 % of most products and 12.5 % of `riester_rente`, the cheapest point.
- **Shared across products, candidates for the core:** `mort_rate_at_age` is in the top cells of six products (`basisrente`, `kapitallebensversicherung`, `klassische_rentenversicherung`, `riester_rente`, `risikolebensversicherung`, `sofortrente`), `check_net_cf_resid` of five, a `lapse_rate` or `lapse_rate_base` of seven, `result_cf` of seven, `claims` of six, `decl_rate` of two (`basisrente`, `kapitallebensversicherung`), `check_decrement_closure_resid` of two. The same name is not the same formula: `mort_rate_at_age` is an `.at` on `(sex, age)` in `klassische_rentenversicherung`, on `(table, sex, smoker, age)` in `risikolebensversicherung`, a clamped `.loc` on `(basis, sex, age)` in `sofortrente` and a row `.loc` with a trend factor in `basisrente`. A fast table lookup and a cheaper net-cash-flow check built once in the core would reach most products; `pflegerentenversicherung`, which is 91.6 of the 171 ms of the W = 24 forecast sum, needs its own care-grade rates made cheap first.

# Phase 3: night measurement

The closing measurement of epic-night-run on its final code: after the core (epic-common-core), the performance commits of entries 2.3 to 2.10 and 2.14 to 2.16, the harvest of the four-hour experiment (PR #32) and the refactor sweep (PR #34). It gives the combined forecast for all ten products at the new M (`docs/roadmap.md`, "The new M"), a fresh per-cell profile and the trace check under `--engine modelx`. Read-only: no model, runner, tool or test changed.

- Date: 2026-10-31
- Commit: `94294d6fd387348a4c8a6f85aaa125da42973111` (merge of PR #34), clean tree
- Machine: the same as for 2a to 2d (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4); load average about 1 at the start
- Commands, one after the other on the otherwise idle machine:
  - `uv run python tools/measure_marginal.py --all --workers 24 --json /tmp/night311.json` (defaults: engine export, cleanup on, transform cache off, factor K = 32, repeats R = 3, M = 5,300, P = 10,000); exit 0, every run verified, wall time 2 min
  - `for p in $(ls products); do uv run python tools/run_baseline.py $p --engine modelx > /tmp/trace-$p.txt || echo FAIL $p; done`; no `FAIL`, so exit 0 for each of the ten
  - the profile script of the phase-3 per-cell profile above, unchanged; exit 0, `all ok`, wall time 34 s

## Result at W = 24

| Product | n | K·n | T(n) s | T(K·n) s | fixed s | t_marginal ms | mem(K·n) MB | status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| basisrente | 13 | 416 | 1.00 | 1.59 | 1.07 | 1.47 | 570 | ok |
| berufsunfaehigkeit | 13 | 416 | 1.13 | 2.31 | 1.20 | 2.93 | 699 | ok |
| fondsgebundene_rentenversicherung | 13 | 416 | 0.99 | 1.40 | 1.08 | 1.01 | 525 | ok |
| indexpolice | 13 | 416 | 1.01 | 1.21 | 1.10 | 0.50 | 482 | ok |
| kapitallebensversicherung | 14 | 448 | 0.97 | 1.45 | 1.05 | 1.11 | 485 | ok |
| klassische_rentenversicherung | 14 | 448 | 1.12 | 1.80 | 1.19 | 1.56 | 593 | ok |
| pflegerentenversicherung | 14 | 448 | 1.25 | 2.76 | 1.29 | 3.47 | 953 | ok |
| riester_rente | 13 | 416 | 1.07 | 1.66 | 1.14 | 1.46 | 594 | ok |
| risikolebensversicherung | 14 | 448 | 0.94 | 1.31 | 1.02 | 0.86 | 513 | ok |
| sofortrente | 14 | 448 | 1.00 | 1.56 | 1.07 | 1.27 | 529 | ok |

Status `ok` for all ten: replicas equal their originals by digest and points `1 … n` reproduce `baseline/` byte for byte. Σ t_marginal = 15.7 ms and Σ fixed = 11.21 s, against 137.8 ms and 20.3 s with the core on 2026-10-28 (`docs/roadmap.md`, "Where the common core stands") and 171 ms in phase 2d: `t_marginal` fell by a factor of about 9, the fixed cost by about 1.8. `pflegerentenversicherung` is no longer half of the marginal time but 3.47 of 15.7 ms (72.0 ms on 2026-10-28). `mem(K·n)` is 0.5 to 1.0 GB, against 1.2 to 4.4 GB in phase 2d.

## Forecast and the R9 verdict

The combined line of the command, verbatim:

> all 10 products together, W = 24: M_core·(Σ f + P·Σ t) + Σ M_p·(f_p + P·t_p) = 186·(11.21 s + 1,000·15.7 ms) + Σ M_p·(…) = 1.4 h + 4.1 h = 5.5 h (fits the 10 h night), M = 5,300 (M_core = 186, Σ M_p = 5,114), P = 1,000 per product, fixed cost included

All ten products together, at the new M = 5,300, P = 10,000 (1,000 per product), W = 24, fixed cost included, are forecast at **5.5 h, within the 10 h night** (36.2 h on 2026-10-28; the target Σ t_marginal ≈ 25.6 ms of "The new M" is met at 15.7 ms). R9 holds; no decision on the trace rule or the criterion is needed (epic-night-run, N6). The assumptions of the command apply: a linear extrapolation without trace pruning, the coverage filter ignored, `M_core` and `M_p` the counts at `f07f003`, a forecast, not a measurement.

Run-to-run spread: the same command on the same code content, in the description of PR #34 (2026-10-31, before its merge), gave Σ t 12.9 ms, Σ fixed 10.25 s and 4.7 h. This run is 22 % higher in Σ t, with eight of ten products up, most `kapitallebensversicherung` (0.41 → 1.11 ms), `pflegerentenversicherung` (2.90 → 3.47), `berufsunfaehigkeit` (2.41 → 2.93), `risikolebensversicherung` (0.57 → 0.86) and `indexpolice` (0.34 → 0.50); only `fondsgebundene_rentenversicherung` and `sofortrente` came down. The cause is not established: this run started at load average about 1, and no code changed between the two. The figure recorded here is the higher, conservative one; both lie well within the night.

## Trace check under `--engine modelx`

Each product runs on the modelx engine, point by point with its own ItemSpace, so the trace per contract stays available (epic-night-run, N5):

| Product | points | check cells | checks | sha256 equal to the pin in `tests/test_baseline.py` | wall time s |
|---|---:|---:|---|---|---:|
| basisrente | 13 | 6 | all true | yes | 6.6 |
| berufsunfaehigkeit | 13 | 7 | all true | yes | 6.5 |
| fondsgebundene_rentenversicherung | 13 | 7 | all true | yes | 5.6 |
| indexpolice | 13 | 6 | all true | yes | 2.0 |
| kapitallebensversicherung | 14 | 10 | all true | yes | 2.8 |
| klassische_rentenversicherung | 14 | 9 | all true | yes | 8.6 |
| pflegerentenversicherung | 14 | 6 | all true | yes | 10.8 |
| riester_rente | 13 | 6 | all true | yes | 6.7 |
| risikolebensversicherung | 14 | 5 | all true | yes | 4.7 |
| sofortrente | 14 | 9 | all true | yes | 5.7 |

## Fresh per-cell profile

The script and method of the phase-3 per-cell profile above, on this commit: W = 1, export engine with cleanup, one unprofiled and one profiled run per product, exclusive time per cell. Below are the summary and the three top cells per product; shares are of the per-point cell time.

| Product | point loop ms/pt, unprofiled | point loop ms/pt, profiled | per-point cells ms/pt | calls/pt | top cells (share) |
|---|---:|---:|---:|---:|---|
| pflegerentenversicherung | 29.0 | 45.9 | 41.0 | 38,132 | `pols_ledger` 19.4 %, `result_cf` 9.3 %, `tar_ledger` 7.0 % |
| basisrente | 19.2 | 28.2 | 24.2 | 37,720 | `result_cf` 16.6 %, `claims` 8.1 %, `net_cf` 4.7 % |
| berufsunfaehigkeit | 20.9 | 34.2 | 31.0 | 28,596 | `dis_exits` 8.3 %, `dis_exits_first` 8.1 %, `result_cf` 6.9 % |
| fondsgebundene_rentenversicherung | 8.8 | 26.1 | 23.3 | 28,998 | `pols_maturity` 21.7 %, `result_cf` 13.2 %, `av_pp_at` 5.7 % |
| indexpolice | 4.5 | 10.0 | 8.2 | 13,528 | `result_cf` 13.9 %, `claims` 8.1 %, `net_cf` 5.5 % |
| kapitallebensversicherung | 5.2 | 12.5 | 10.7 | 17,088 | `result_cf` 12.9 %, `claims` 6.2 %, `net_cf` 3.5 % |
| klassische_rentenversicherung | 18.9 | 33.8 | 29.8 | 45,987 | `result_cf` 12.6 %, `claims` 7.8 %, `net_cf` 4.9 % |
| riester_rente | 12.4 | 28.2 | 24.2 | 39,077 | `result_cf` 19.2 %, `claims` 10.8 %, `net_cf` 5.1 % |
| risikolebensversicherung | 7.1 | 13.9 | 12.2 | 16,109 | `lapse_cum` 14.1 %, `result_cf` 12.7 %, `benefit_paid_pp` 4.1 % |
| sofortrente | 15.0 | 27.6 | 24.9 | 30,257 | `mort_rate_tariff_mth` 20.0 %, `result_cf` 10.0 %, `annuity_payments` 6.8 % |

Observations:

- **No dominant lookup is left.** The scalar `DataFrame.at`/`.loc` lookups that were 23 to 74 % of seven products in the pre-core profile no longer appear among the top cells; ten rows now cover only 40 to 58 % of the point (Pflege 61 % with fifteen rows), so the time is spread over many cheap cells. The unprofiled point loop is 4.5 to 29.0 ms per point, against 18.1 to 554.7 ms pre-core.
- **What remains is the core's frame.** `result_cf` (building the result DataFrame, once per point) is among the top three cells of all ten products, `claims` and `net_cf` of five each (Basis, Index, KLV, RV, Riester); they are the next common lever, in the core.
- **Product-specific remainders:** Pflege's ledgers (`pols_ledger`, `tar_ledger`, 26 %), FRV's `pols_maturity` (21.7 %), Sofort's `mort_rate_tariff_mth` (20.0 %), RLV's `lapse_cum` (14.1 %) and BU's disability exits and cohorts (`dis_exits*`, `dis_cohorts*`, together 27 %).
- **The overhead caveat is larger now.** The profiled point loop is 47 to 197 % slower than the unprofiled one (+12 to +49 % pre-core): with lookups gone, a point is many cells of about 1 µs, where the timer's 0.3 to 0.8 µs per evaluation weighs most. Shares of cheap cells with many callees are overstated accordingly; single runs, indicative only.

# Phase 3: night forecast remeasured

The night forecast of "Phase 3: night measurement" (above) used the mutant counts of `f07f003`, and its Σ t was 22 % above the same command on the same code in PR #34 without a known cause (epic-night-run retrospective). This measurement repeats the command at the recounted M (`docs/roadmap.md`, "The new M": M = 5,305, M_core = 186, Σ M_p = 5,119, counted at `790706b`), alternating with a control on `main` in the same session. The branch changes no timed path (no file under `core/`, `products/` or `tools/run_baseline.py`; only the counts `tools/measure_marginal.py` holds, its tests and docs), so both sides measure the same model and their runs give the run-to-run spread directly. Read-only: no model or runner changed for it.

- Date: 2026-11-02, 11:58 to 12:08
- Commits: branch `a49940c` (phase-3-night-run-new-m-remeasure, after the recount on `790706b`), clean tree; the runs were on an earlier version of the same branch that differed from it in `docs/` only; control `790706b` (`main`, merge of PR #38) in the worktree `/tmp/s219-main`, the same installed packages
- Machine: the same as for 2a to 2d (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Commands, six runs one after the other, branch and control in turn, `uptime` before each:
  - `uv run python tools/measure_marginal.py --all --workers 24 --json /tmp/s219-<side>-<i>.json` (defaults: engine export, cleanup on, transform cache off, factor K = 32, repeats R = 3, P = 10,000; M = 5,305 on the branch, 5,300 on `main`); exit 0 and status `ok` for all ten products in every run, wall time 89 to 93 s each
- Load: the 1-minute load average before each run is that of the run before it, since the runs followed each other directly: 2.98 before the first, 8.6 to 9.5 before the other five.

## The six runs at W = 24

| Run | Side | Commit | load (1 min) | Σ t_marginal ms | Σ fixed s | forecast h |
|---|---|---|---:|---:|---:|---:|
| 1 | branch | `a49940c` | 2.98 | 14.61 | 9.78 | 5.01 |
| 2 | `main` | `790706b` | 9.48 | 14.63 | 9.83 | 5.02 |
| 3 | branch | `a49940c` | 9.30 | 14.81 | 9.77 | 5.04 |
| 4 | `main` | `790706b` | 8.59 | 14.86 | 9.90 | 5.09 |
| 5 | branch | `a49940c` | 8.98 | 14.99 | 9.94 | 5.11 |
| 6 | `main` | `790706b` | 9.48 | 15.70 | 9.93 | 5.26 |

The forecast on the branch is at M = 5,305, on `main` at M = 5,300 (0.1 % less, below the spread).

`t_marginal` per product in ms, runs 1 to 6 in the order above, and each side's mean:

| Product | 1 b | 2 m | 3 b | 4 m | 5 b | 6 m | branch mean | `main` mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 1.42 | 1.32 | 1.45 | 1.33 | 1.38 | 1.36 | 1.42 | 1.34 |
| berufsunfaehigkeit | 2.58 | 2.73 | 2.61 | 2.57 | 2.52 | 2.68 | 2.57 | 2.66 |
| fondsgebundene_rentenversicherung | 0.94 | 0.96 | 1.02 | 1.08 | 0.97 | 1.16 | 0.98 | 1.07 |
| indexpolice | 0.52 | 0.59 | 0.53 | 0.54 | 0.47 | 0.63 | 0.51 | 0.59 |
| kapitallebensversicherung | 0.71 | 0.65 | 0.67 | 0.61 | 0.62 | 0.63 | 0.67 | 0.63 |
| klassische_rentenversicherung | 1.70 | 1.58 | 1.67 | 1.66 | 1.79 | 1.83 | 1.72 | 1.69 |
| pflegerentenversicherung | 3.28 | 3.39 | 3.29 | 3.55 | 3.42 | 3.61 | 3.33 | 3.52 |
| riester_rente | 1.40 | 1.38 | 1.28 | 1.27 | 1.33 | 1.40 | 1.34 | 1.35 |
| risikolebensversicherung | 0.86 | 0.79 | 0.87 | 0.83 | 1.01 | 0.81 | 0.91 | 0.81 |
| sofortrente | 1.21 | 1.24 | 1.41 | 1.41 | 1.48 | 1.59 | 1.37 | 1.41 |

One product's branch mean lies more than 10 % above its control (N4): `risikolebensversicherung`, 0.91 against 0.81 ms (+12 %), its highest run 1.01 ms at load 8.98. The code is the same on both sides, so the rise is noise: the same session shows per-product spreads of that size on one side alone (`sofortrente` 1.24 to 1.59 ms and `fondsgebundene_rentenversicherung` 0.96 to 1.16 ms on `main`, `sofortrente` 1.21 to 1.48 ms on the branch), and in the other direction `indexpolice` and `fondsgebundene_rentenversicherung` are 13 % and 8 % lower on the branch.

## Forecast

The combined line of branch run 1, verbatim:

> all 10 products together, W = 24: M_core·(Σ f + P·Σ t) + Σ M_p·(f_p + P·t_p) = 186·(9.78 s + 1,000·14.6 ms) + Σ M_p·(…) = 1.3 h + 3.8 h = 5.0 h (fits the 10 h night), M = 5,305 (M_core = 186, Σ M_p = 5,119), P = 1,000 per product, fixed cost included

All ten products together, at the recounted M = 5,305, P = 10,000 (1,000 per product), W = 24, fixed cost included, are forecast at **5.1 h** (branch mean 5.06 h, min–max 5.01 to 5.11 h over three runs), within the 10 h night; the `main` control on the same code gave 5.02 to 5.26 h at M = 5,300, so the session's same-code spread is 5.0 to 5.3 h. Σ t_marginal is 14.8 ms (14.61 to 14.99), below the recounted target of 25.0 ms (`s` ≈ 5.51 over 2026-10-28), Σ fixed 9.83 s (9.77 to 9.94). R9 holds as before. The assumptions of the command apply: a linear extrapolation without trace pruning, the coverage filter ignored, `M_core` and `M_p` the counts at `790706b`, a forecast, not a measurement.

## The +22 % of the night measurement

Within this session the same code (`790706b`, branch and `main` control) gave Σ t from 14.61 to 15.70 ms over six runs, a spread of 7.5 % (2.6 % on the branch alone), at load averages from 3 to 9.5. The two earlier figures were measured on the content of `94294d6`, not on this code: PRs #37 and #38 changed timed code since (the core's `Projection`, BU, FRV, Pflege and `tools/run_baseline.py`), so this measurement does not repeat them. Those two, 12.9 ms (PR #34, before its merge; its description gives load ≈ 4.5 for its alternating runs) and 15.7 ms (night measurement, load about 1), lie 22 % apart, more than the 7.5 % spread on `790706b`, so in-session noise of that size does not account for the gap. The load at the start does not order the figures: 12.9 ms at about 4.5, 15.7 ms at about 1, 14.6 to 15.7 ms here at 3 to 9.5. The cause of the 22 % stays open; this measurement cannot separate a change in the code from a condition that differs between sessions. The higher figures stay the recorded ones; at every figure measured the forecast lies within the night.

# Parameter tables: night forecast after the alignment

Entry 13 of epic-parameter-files (its rule R11: the night forecast after the alignment is compared with 5.1 h, and a rise above 10 % needs a reason against a `main` control): after the renames, core moves and value alignment of entries 11 and 12, the night forecast is measured at the code and M of the commit it runs on, `d849151` (branch `parameter-files-alignment`), M = 5,249 (M_core = 190, Σ M_p = 5,059, the pins of `tools/measure_marginal.py`, unchanged by the alignment), against 5.1 h, the forecast of "Phase 3: night forecast remeasured". The branch changes timed paths (parameter values, the core file the loader reads, the core and product `Projection` code that reads the renamed and moved items), so a `main` control on `e16c935` runs alternately in the same session (docs/core.md, "Measuring rules"). Read-only: no model or runner changed for it.

- Date: 2026-11-09, 16:34 to 16:44 (all-products runs), 16:47 to 17:04 (the targeted runs below)
- Commits: branch `d849151`, clean tree; control `e16c935` (`main`, merge of PR #51) in the worktree `/tmp/s113-main`, the same installed packages
- Machine: the same as for 2a to 2d (12th Gen Intel Core i7-12800HX, 24 logical CPUs, 62.8 GiB RAM, Linux 6.6 under WSL2; Python 3.12.13, modelx 0.33.0, pandas 3.1.0, numpy 2.5.4)
- Commands, six runs one after the other, branch and control in turn, `uptime` before each:
  - `uv run python tools/measure_marginal.py --all --workers 24 --json /tmp/s113-<side>-<i>.json` (defaults: engine export, cleanup on, transform cache off, K = 32, R = 3, P = 10,000, M = 5,249 on both sides); exit 0 and status `ok` for all ten products in every run, wall time 96 to 109 s each
- Load: the runs followed each other directly, so the load rose from 1.42 before the first to 10.21 before the last.

## The six runs at W = 24

| Run | Side | Commit | load (1 min) | Σ t_marginal ms | Σ fixed s | forecast h |
|---|---|---|---:|---:|---:|---:|
| 1 | branch | `d849151` | 1.42 | 15.34 | 10.43 | 5.28 |
| 2 | `main` | `e16c935` | 3.43 | 14.79 | 10.38 | 5.16 |
| 3 | branch | `d849151` | 6.28 | 15.31 | 10.98 | 5.38 |
| 4 | `main` | `e16c935` | 8.66 | 16.23 | 10.82 | 5.55 |
| 5 | branch | `d849151` | 9.65 | 17.74 | 11.47 | 5.99 |
| 6 | `main` | `e16c935` | 10.21 | 16.70 | 11.76 | 5.77 |

`t_marginal` per product in ms, runs 1 to 6 in the order above, and each side's mean:

| Product | 1 b | 2 m | 3 b | 4 m | 5 b | 6 m | branch mean | `main` mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 1.44 | 1.38 | 1.43 | 1.44 | 1.88 | 1.44 | 1.58 | 1.42 |
| berufsunfaehigkeit | 2.69 | 2.58 | 2.73 | 2.68 | 3.23 | 2.83 | 2.89 | 2.70 |
| fondsgebundene_rentenversicherung | 1.06 | 1.00 | 1.09 | 1.23 | 1.23 | 1.18 | 1.13 | 1.14 |
| indexpolice | 0.58 | 0.53 | 0.51 | 0.57 | 0.62 | 0.84 | 0.57 | 0.64 |
| kapitallebensversicherung | 0.64 | 0.64 | 0.75 | 0.62 | 0.71 | 0.94 | 0.70 | 0.73 |
| klassische_rentenversicherung | 1.80 | 1.72 | 1.87 | 1.71 | 2.02 | 1.72 | 1.89 | 1.72 |
| pflegerentenversicherung | 3.47 | 3.44 | 3.26 | 3.89 | 3.95 | 3.67 | 3.56 | 3.67 |
| riester_rente | 1.40 | 1.34 | 1.40 | 1.56 | 1.55 | 1.56 | 1.45 | 1.49 |
| risikolebensversicherung | 0.85 | 0.84 | 0.91 | 0.96 | 0.97 | 1.11 | 0.91 | 0.97 |
| sofortrente | 1.42 | 1.30 | 1.36 | 1.57 | 1.56 | 1.41 | 1.45 | 1.43 |

Two products' branch means lie more than 10 % above their control (N4): `basisrente`, 1.58 against 1.42 ms (+11 %), and `klassische_rentenversicherung`, 1.89 against 1.72 ms (+10 %). Both branch means lie outside the control's spread of these six runs, which ran back to back with the load rising to 10, so they were measured again alone, branch and `main` in turn, each run started only once the 1-minute load was below 3:

- `uv run python tools/measure_marginal.py basisrente klassische_rentenversicherung --workers 24`, five runs a side (load 2.15 to 2.95, wall time 20 to 35 s): in the three runs at 20 to 21 s wall, `basisrente` gives 1.56, 1.42, 1.47 ms on the branch against 1.45, 1.70, 1.60 ms on `main`, so the branch is not slower; runs 4 and 5 are not used on either side: three of the four were disturbed (29 to 35 s wall, `main`'s `basisrente` 5.52 ms in run 5), and `main`'s run 4 (21 s; 1.81 and 1.99 ms) is dropped with its pair. The load before the run did not show the disturbance; wall time did. `klassische_rentenversicherung` gave 1.89, 1.75, 2.16 against 1.84, 1.69, 1.59 ms in those three runs, still higher, so it was measured once more on its own.
- `uv run python tools/measure_marginal.py klassische_rentenversicherung --workers 24`, six runs a side, `main` first (load 2.50 to 2.96, wall 10 to 11 s after a disturbed first pair, 2.62 and 4.52 ms at 17 and 21 s, not used): `main` 1.73, 1.85, 1.81, 1.76, 1.89 ms (mean 1.81), branch 1.84, 1.83, 1.92, 1.89, 1.84 ms (mean 1.86), +2.9 %; the two sides overlap from 1.83 to 1.89 ms, and only the branch's highest run, 1.92 ms, lies above every control run, by 2 %.

At low load neither product is more than 10 % slower than its control. For `basisrente` the rise of the back-to-back runs comes from one run at load 9.65 (1.88 ms; 1.44 and 1.43 ms otherwise). For `klassische_rentenversicherung` load does not explain it (the control stayed at 1.71 to 1.72 ms up to load 10.21); alone, the branch is 2.9 % higher and within the control's spread, so a small cost is not excluded by these runs, but none above 10 %. The code gives no reason for one: for both products the alignment changes no formula a contract runs, only parameter values (`klassische_rentenversicherung`: the check tolerance and the text of its expense inflation; `basisrente`: its best-estimate factor and check tolerance) and where the loader finds an item, a dictionary built once per model (`core/Core/Data/__init__.py`, `param_dict`).

## Forecast

All ten products together at M = 5,249, P = 10,000 (1,000 per product), W = 24, fixed cost included, are forecast at **5.6 h** on the aligned code (branch mean 5.55 h, min–max 5.28 to 5.99 h over three runs), within the 10 h night; the `main` control gave 5.16 to 5.77 h (mean 5.49 h) in the same session.

R11 compares with 5.1 h, the forecast of "Phase 3: night forecast remeasured": the branch mean is 8.9 % higher, below 10 %. Against the unrounded 5.06 h it is 9.7 %, which three runs spreading 13 % (5.28 to 5.99 h; 5.33 h, +5.4 %, without the run at load 9.65, which alone is 18 % higher) cannot tell from 10 %, so the reason R11 would ask for is given anyway. The branch mean is 1.1 % above the control's (5.55 against 5.49 h; the pairs +2.4 %, −3.0 %, +3.9 %), within the control's own spread of 12 % (5.16 to 5.77 h), so the six runs show no cost of the alignment; they cannot exclude a small one, and the branch ran at the lower load in every pair. The 8.5 % between the control (`e16c935`) and 5.06 h is not separated by this session: 5.06 h was measured on `790706b`, and the epic's earlier entries (PRs #41 to #51: the layered loader, the `param` reads, the moved literals) changed timed code since, beside a session that may differ; the section below, on another day, gives 4.83 h for the same control, so most of it is the session. Per product, against the phase 3 table five branch means are 10 to 15 % higher (`fondsgebundene_rentenversicherung` 1.13 against 0.98 ms, `berufsunfaehigkeit` 2.89 against 2.57 ms, `indexpolice` 0.57 against 0.51 ms, `basisrente` 1.58 against 1.42 ms, `klassische_rentenversicherung` 1.89 against 1.72 ms; the last two are the targeted runs above); against this session's control `fondsgebundene_rentenversicherung` and `indexpolice` are −1 % and −11 %, and `berufsunfaehigkeit` is +7 % (2.70 ms), above the control's highest run (2.83 ms) only through the branch's run at load 9.65 (3.23 ms; 2.69 and 2.73 ms in the other two, within the control's 2.58 to 2.83 ms). The 5.06 h were forecast at M = 5,305 (M_core = 186, Σ M_p = 5,119), this one at M = 5,249 (M_core = 190, Σ M_p = 5,059), the counts of the commit measured (epic decision of 2026-11-03): 1 % fewer mutants, but four more in the core, which run all ten products. With the phase 3 counts the branch mean would be 5.57 h, 10.1 % above 5.06 h, so the counts account for 0.3 points and "below 10 %" holds at the commit's own M only. The figure stands for `d849151`; the commits after it are measured in the section below. The assumptions of the command apply: a linear extrapolation without trace pruning, the coverage filter ignored, M the pinned counts, a forecast, not a measurement.

# Parameter tables: night forecast on the final code

The forecast above stands for `d849151`. After it the branch renamed the cost columns of four products' tables and their readers in `Projection` (entry 17, `24a6fe8` to `29ab771`) and aligned the expense inflation of `kapitallebensversicherung` and `basisrente` to the core item (`e47bfa2`, `0478e53`, which remove the two override cells), all timed paths, so the measurement is repeated on the branch head, again alternating with the `main` control. Two things differ from the session above: each run started only once the 1-minute load was below 3, and the order is `main`, branch, branch, `main`, `main`, branch, so that neither side runs first in every pair. Read-only: no model or runner changed for it.

- Date: 2026-11-10, 10:17 to 10:31
- Commits: branch `02b20b1`, clean tree (measured before a check of its two value commits corrected five figures in product docs and docstrings and one provenance text; no timed path differs); control `e16c935` (`main`, merge of PR #51) in the worktree `/tmp/s113h-main`, run with the branch's virtual environment, so the same installed packages
- Machine: the same as above
- Command: `python tools/measure_marginal.py --all --workers 24 --json /tmp/s113h-<i>-<side>.json` (defaults as above, M = 5,249, M_core = 190 on both sides: the pins are unchanged at `02b20b1`); exit 0 and status `ok` for all ten products in every run, wall time 84 to 86 s each
- Load: the 1-minute load average before each run is in the table; after each run it stood at 5.5 to 10.4.

## The six runs at W = 24

| Run | Side | Commit | load (1 min) | Σ t_marginal ms | Σ fixed s | forecast h |
|---|---|---|---:|---:|---:|---:|
| 1 | `main` | `e16c935` | 0.71 | 14.00 | 9.61 | 4.83 |
| 2 | branch | `02b20b1` | 2.94 | 13.81 | 9.52 | 4.78 |
| 3 | branch | `02b20b1` | 2.74 | 13.53 | 9.49 | 4.72 |
| 4 | `main` | `e16c935` | 2.72 | 14.29 | 9.57 | 4.91 |
| 5 | `main` | `e16c935` | 2.84 | 13.71 | 9.39 | 4.74 |
| 6 | branch | `02b20b1` | 2.99 | 13.73 | 9.43 | 4.74 |

`t_marginal` per product in ms, runs 1 to 6 in the order above, and each side's mean:

| Product | 1 m | 2 b | 3 b | 4 m | 5 m | 6 b | branch mean | `main` mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| basisrente | 1.32 | 1.26 | 1.24 | 1.34 | 1.31 | 1.26 | 1.25 | 1.32 |
| berufsunfaehigkeit | 2.39 | 2.46 | 2.34 | 2.50 | 2.37 | 2.43 | 2.41 | 2.42 |
| fondsgebundene_rentenversicherung | 1.05 | 0.95 | 0.99 | 1.03 | 0.92 | 0.88 | 0.94 | 1.00 |
| indexpolice | 0.51 | 0.51 | 0.46 | 0.49 | 0.44 | 0.49 | 0.48 | 0.48 |
| kapitallebensversicherung | 0.66 | 0.57 | 0.59 | 0.66 | 0.58 | 0.63 | 0.59 | 0.63 |
| klassische_rentenversicherung | 1.54 | 1.63 | 1.48 | 1.65 | 1.61 | 1.55 | 1.55 | 1.60 |
| pflegerentenversicherung | 3.13 | 3.15 | 3.21 | 3.40 | 3.14 | 3.12 | 3.16 | 3.23 |
| riester_rente | 1.35 | 1.28 | 1.26 | 1.33 | 1.33 | 1.24 | 1.26 | 1.34 |
| risikolebensversicherung | 0.77 | 0.77 | 0.74 | 0.71 | 0.79 | 0.85 | 0.79 | 0.75 |
| sofortrente | 1.27 | 1.23 | 1.22 | 1.19 | 1.22 | 1.28 | 1.24 | 1.23 |

No product's branch mean lies more than 10 % above its control (N4); the largest rise is `risikolebensversicherung`, 0.79 against 0.75 ms (+4.4 %), its highest branch run 0.85 ms against the control's 0.79 ms. `klassische_rentenversicherung` and `basisrente`, the two products of the targeted runs above, are 2.8 % and 5.1 % lower on the branch here.

## Forecast

All ten products together at M = 5,249, P = 10,000 (1,000 per product), W = 24, fixed cost included, are forecast at **4.7 h** on the branch head (branch mean 4.75 h, min–max 4.72 to 4.78 h over three runs), within the 10 h night; the `main` control gave 4.74 to 4.91 h (mean 4.83 h). Σ t_marginal is 13.7 ms on the branch (13.53 to 13.81) against 14.0 ms on `main` (13.71 to 14.29), Σ fixed 9.48 s against 9.52 s.

Against 5.1 h (R11) the branch mean is 6.9 % lower, against the unrounded 5.06 h 6.1 % lower; with the phase 3 counts (M_core = 186, Σ M_p = 5,119) it would be 4.77 h, 5.8 % lower. R11 is met without a reason to give. The branch mean is 1.6 % below the control's, within the control's spread of 3.6 %, so this session shows no cost of the epic's entries 11 to 18 either, and no gain it could tell from the spread. The same control, `e16c935`, gave 5.49 h in the session above and 4.83 h here, 12 % less at loads below 3 instead of 3 to 10: the session accounts for more than the 9.7 % that the section above reports against phase 3. This figure is the recorded forecast of the branch; the 5.6 h above stays as the measurement of `d849151` on a loaded machine. The assumptions of the command apply: a linear extrapolation without trace pruning, the coverage filter ignored, M the pinned counts, a forecast, not a measurement.

# Runner wall time per product

The wall time of one runner process per product, one product at a time, on its shipped model points: the modelx import, the run, the checks and the hash. Phase 1 ran the traced modelx model without per-contract cleanup; today's runner runs by default on the exported model with cleanup, at W = 1. One run per product on each side, so the figures show the order of magnitude, not a measurement to compare changes with (for that, `tools/measure_marginal.py` above).

- Phase 1: the table of the README from 2026-10-23 (commit `bee4cb6`), modelx 0.33.0, "measured once on one machine"
- Today: 2026-11-10, commit `586e831`, clean tree, the same machine and packages as above; `uv run python tools/run_baseline.py <product>`, timed in the shell, so `uv`'s start is included

| Product | Model | Points | Checks | Phase 1 | Today |
|---|---|---:|---:|---:|---:|
| basisrente | `Basis_DE_S` | 13 | 6 | 5.4 s | 2.7 s |
| berufsunfaehigkeit | `BU_DE_S` | 13 | 7 | 5.0 s | 2.5 s |
| fondsgebundene_rentenversicherung | `FRV_DE_S` | 13 | 7 | 5.0 s | 2.1 s |
| indexpolice | `Index_DE_S` | 13 | 6 | 2.6 s | 2.1 s |
| kapitallebensversicherung | `KLV_DE_S` | 14 | 10 | 7.0 s | 2.1 s |
| klassische_rentenversicherung | `RV_DE_S` | 14 | 9 | 38.1 s | 2.3 s |
| pflegerentenversicherung | `Pflege_DE_S` | 14 | 6 | 36.4 s | 2.7 s |
| riester_rente | `Riester_DE_S` | 13 | 6 | 4.9 s | 2.3 s |
| risikolebensversicherung | `RLV_DE_S` | 14 | 5 | 4.7 s | 2.0 s |
| sofortrente | `Sofort_DE_S` | 14 | 9 | 5.8 s | 2.2 s |

Points and checks are unchanged since phase 1. Today a run is about 2 s whatever the product: the import and the export dominate, while the points themselves take milliseconds (the tables above).
