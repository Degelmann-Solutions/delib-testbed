"""The stored per-product baseline of phase 1.

For every product the runner runs on the shipped model points and writes its
``result_cf.csv`` to a temporary folder. The tests pin the check cells, the recipe hash
the runner prints and the SHA-256 of ``baseline/<product>/result_cf.csv``, and read the
stored file back to the recipe hash, which proves that the file round-trips exactly.

A commit that moves a result changes these pins on purpose and updates them in the same
commit. The hashes are taken from raw 64-bit floats and have been confirmed on one machine.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tools" / "run_baseline.py"
BASELINE_DIR = ROOT / "baseline"

# product: (model points, check cells, recipe hash, SHA-256 of baseline/<product>/result_cf.csv)
BASELINE = {
    "basisrente": (
        14,
        ("check_annuity_roll_fwd", "check_av_roll_fwd", "check_conversion", "check_net_cf",
         "check_no_capital", "check_pols_roll_fwd"),
        "00edff73201b6dcf0c2144eba3112bf6d89515458049ceb8a46197ea1001eb57",
        "81b6329f2eed571172e8a46c987aebdc4df1f1a84837c607c812d7691b230f1f",
    ),
    "berufsunfaehigkeit": (
        13,
        ("check_cover_end", "check_dis_roll_fwd", "check_net_cf", "check_pols_roll_fwd",
         "check_prem_split", "check_runoff_roll_fwd", "check_states"),
        "6c8d5250f622e1c967bce96003ebe475f09d24519bab798710bb9d833e6d956b",
        "ef3ebf3eeed64f93049342cb22e50d85b98d5af659ebf30a3ddc37a9c927d0a3",
    ),
    "fondsgebundene_rentenversicherung": (
        13,
        ("check_acq_charge", "check_av_roll_fwd", "check_benefit_funding", "check_net_cf",
         "check_pols_roll_fwd", "check_prem_split", "check_units_roll_fwd"),
        "80d7ecd36b06a80876b3e48f8450df7453539e94e77071b7d62f4a5f34908552",
        "b53f1878a92a5bd554674870f278915bd76a12bf4548c0838c702902d031931b",
    ),
    "indexpolice": (
        13,
        ("check_av_roll_fwd", "check_index_credit", "check_lock_in", "check_net_cf",
         "check_pols_roll_fwd", "check_surplus_alloc"),
        "383d0b16c9feffdd233d1f471ed1aac9a06cdec0d75ae30d8ae71c6765b872a2",
        "822be82bf34333faf01f24a1baaebd66d784795185505441ffbf52fbc96705d6",
    ),
    "kapitallebensversicherung": (
        14,
        ("check_decrement_closure", "check_equivalence", "check_net_cf", "check_pols_roll_fwd",
         "check_rechnungszins_cap", "check_res_roll_fwd", "check_surplus_roll_fwd",
         "check_surr_floor", "check_surr_nonneg", "check_zillmer_cap"),
        "9adf0eebdedfe2c7cdea0ace568dc36cc6207bb3f2db7c2bb91fef536ccaea09",
        "56885e9c624422ef490107ec01258d7f9ec61a1de445837c3b88aab52b8d7687",
    ),
    "klassische_rentenversicherung": (
        14,
        ("check_annuity_conv", "check_annuity_guarantee", "check_av_roll_fwd",
         "check_av_sur_roll_fwd", "check_cv_floor", "check_decrement_closure", "check_net_cf",
         "check_pols_roll_fwd", "check_prem_split"),
        "03b48391201f1f63f793256c2a4a95577869b606ddbe138e5fa9fe72f43723aa",
        "16a75a454436dbc4b6e963d9e9f6d6ed501094f6df1b10acb8ac0b91b024c0be",
    ),
    "pflegerentenversicherung": (
        14,
        ("check_esc_ledger", "check_net_cf", "check_pols_roll_fwd", "check_prem_equiv",
         "check_states", "check_waiver"),
        "79e7fd6f38cf4c9bbfc557d0a669398201f783cbc826618b3074525f833e2c61",
        "2b86cb89d59979227ca3d5869b8fd60e45bf7bd6d831ec99f6baa9e69c9a9316",
    ),
    "riester_rente": (
        13,
        ("check_av_roll_fwd", "check_conversion", "check_guar_roll_fwd", "check_net_cf",
         "check_pols_roll_fwd", "check_zulage_lag"),
        "3950712ac294110e0c3262e918816837c918e83389ac014570fcc98e0defc991",
        "38f86fdece377378d61e38fb4a06d9e1b8db36e4d538128dae8f61cca26eefa0",
    ),
    "risikolebensversicherung": (
        14,
        ("check_net_cf", "check_no_cash_value", "check_pols_roll_fwd", "check_prem_split",
         "check_res_roll_fwd"),
        "cf60ccf6f67bc02709500df8e1e58e92316abea2a59fff0670268312abb980e9",
        "c405c8f807af32210fcb01b03c68b2add2e44e5f45cba6530a3499caf8824442",
    ),
    "sofortrente": (
        14,
        ("check_annuity_roll_fwd", "check_death_option_xor", "check_equivalence",
         "check_guarantee_certain", "check_lives_roll_fwd", "check_net_cf",
         "check_payment_factor", "check_refund_run_off", "check_tariff_int_rate"),
        "d9e07e5d60e3817dba588b6052d4be20f37dfb0b7fc0b599529e8c5bcf919950",
        "ca329dd71db4d50af24e649d0e6f3186c6200888f2e1cb5ce5969fe92eed6584",
    ),
}


def parse_output(stdout: str) -> dict[str, str]:
    return dict(line.split(": ", 1) for line in stdout.splitlines() if ": " in line)


def recipe_hash_of_csv(data: bytes) -> str:
    """The runner's hash recipe, recomputed from a stored ``result_cf.csv``."""
    lines = data.decode("ascii").split("\n")
    assert lines[-1] == "", "the file ends with a line end"
    header = lines[0].split(",")
    assert header[:2] == ["point_id", "t"]
    columns = header[2:]
    rows: dict[int, list[list[str]]] = {}
    for line in lines[1:-1]:
        fields = line.split(",")
        assert len(fields) == len(header)
        rows.setdefault(int(fields[0]), []).append(fields[1:])
    assert list(rows) == sorted(rows), "points are ascending"
    digest = hashlib.sha256()
    for point_id, point_rows in rows.items():
        index = np.array([int(r[0]) for r in point_rows], dtype="<i8")
        values = np.array([[float(v) for v in r[1:]] for r in point_rows], dtype="<f8")
        digest.update((f"point_id={point_id}\n"
                       f"columns={','.join(columns)}\n"
                       f"shape={values.shape[0]},{values.shape[1]}\n").encode("utf-8"))
        digest.update(index.tobytes())
        digest.update(values.tobytes(order="C"))
    return digest.hexdigest()


@pytest.fixture(scope="session")
def runs(tmp_path_factory):
    """Run every product with ``--write`` to a temporary folder, all in parallel processes."""
    out = tmp_path_factory.mktemp("baseline")
    processes = {
        product: subprocess.Popen(
            [sys.executable, str(RUNNER), product, "--write", "--out", str(out / product)],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for product in BASELINE}
    results = {}
    for product, process in processes.items():
        stdout, stderr = process.communicate(timeout=900)
        results[product] = (process.returncode, parse_output(stdout), stderr,
                            out / product / "result_cf.csv")
    return results


def test_every_product_has_a_baseline():
    assert {p.name for p in (ROOT / "products").iterdir() if p.is_dir()} == set(BASELINE)
    assert {p.name for p in BASELINE_DIR.iterdir()} == set(BASELINE)
    for product in BASELINE:
        assert [p.name for p in (BASELINE_DIR / product).iterdir()] == ["result_cf.csv"]


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_runner_finds_the_pinned_checks(runs, product):
    _, checks, _, _ = BASELINE[product]
    assert runs[product][1]["check cells"] == ",".join(checks)


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_product_runs_with_all_checks_true_and_the_pinned_hash(runs, product):
    points, _, recipe_hash, _ = BASELINE[product]
    code, output, stderr, _ = runs[product]
    assert code == 0, stderr
    assert output["checks"] == "all true"
    assert int(output["model points"]) == points
    assert output["sha256"] == recipe_hash


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_written_file_equals_the_stored_baseline(runs, product):
    _, _, _, file_hash = BASELINE[product]
    stored = (BASELINE_DIR / product / "result_cf.csv").read_bytes()
    assert hashlib.sha256(stored).hexdigest() == file_hash
    assert runs[product][3].read_bytes() == stored


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_stored_baseline_reads_back_to_the_recipe_hash(product):
    points, _, recipe_hash, _ = BASELINE[product]
    stored = (BASELINE_DIR / product / "result_cf.csv").read_bytes()
    assert b"\r" not in stored
    assert recipe_hash_of_csv(stored) == recipe_hash
    assert len({line.split(b",", 1)[0] for line in stored.split(b"\n")[1:-1]}) == points


@pytest.mark.parametrize("product", sorted(BASELINE))
def test_run_script_prints_without_error(product):
    """Each product's ``run.py``, the hand-run demo, exits 0 and prints its checks.

    No other test runs these scripts; Sofort's crashed at its check loop for nine days
    because it called the core's ``check_net_cf_tol(t)`` without ``t``.
    """
    done = subprocess.run([sys.executable, str(ROOT / "products" / product / "run.py")],
                          capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr
    assert "checks" in done.stdout
