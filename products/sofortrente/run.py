"""Run the Sofort_DE_S reference model and print its cash flow statement.

    python products/sofortrente/run.py            # anchor cell (point_id = 1)
    python products/sofortrente/run.py 9          # another model point

Output is ASCII-only so it prints on a Windows console under any code page.
"""
import sys
from pathlib import Path

import modelx as mx

model = mx.read_model(Path(__file__).parent / "Sofort_DE_S")
point_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

proj = model.Projection[point_id]
mp = proj.model_point()

print("model point {}: {} - Einmalbeitrag {:,.2f} EUR, {}{} born {}, entry {}".format(
    point_id, proj.policy_id(), proj.prem_gross_level_pp(), proj.sex(1), proj.issue_age(1),
    proj.birth_year(1), proj.issue_year()))
print("options: Aufschubzeit {} mth, Rentengarantiezeit {} y, refund {}, "
      "Hinterbliebenenrente {:.0%}".format(
          proj.defer_mths(), proj.guar_years(), proj.refund_form(), proj.surv_pct()))
print("payment: {} per year, {}, first instalment at t = {}, guarantee ends at t = {}".format(
    proj.ann_freq(), proj.payment_timing(), proj.first_pay_mth(),
    proj.guar_end_mth()))
print("tariff:  i = {:.4f} (cap {:.4f} for {}), alpha = {:.3f}, beta = {:.3f}, "
      "surplus = {}".format(
          proj.rechnungszins(), proj.hoechstrechnungszins(), proj.issue_year(),
          proj.data.param("load_acq_sp_once"), proj.data.param("load_admin_annval_once"),
          proj.surplus_form()))
print("frame:   t = {} ... {} ({} monthly rows, proj_len = {} exclusive)".format(
    proj.t_start(), proj.proj_len() - 1, proj.proj_len() - proj.t_start(),
    proj.proj_len()))
print()
print("net_single_prem  {:,.4f} EUR".format(proj.net_single_prem()))
print("annuity_factor   {:.6f}   (a12 = {:.6f})".format(
    proj.annuity_factor(), proj.annuity_factor() / proj.ann_freq()))
print("refund_pv        {:,.4f} EUR".format(proj.refund_pv()))
print("annuity_guar_pp  {:,.6f} EUR per instalment".format(
    proj.annuity_guar_pp(proj.t_start())))
print()

df = proj.result_cf()
print(df.head(13).round(4).to_string())
print()
print("totals over {} months:".format(len(df)))
for col in df.columns[1:]:
    print("  {:<18s} {:>18,.2f}".format(col, df[col].sum()))
print()
print("checks:")
for name in sorted(c for c, cells in model.Projection.cells.items()
                   if c.startswith("check_") and not c.endswith("_resid")
                   and not cells.parameters):
    print("  {:<26s} {}".format(name, getattr(proj, name)()))

model.close()
