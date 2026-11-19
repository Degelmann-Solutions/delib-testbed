# Technical Notes

**Status:** Drafted 2026-08-29 with no document retrieved; **re-verified against the primary
documents on 2026-08-30**, when 19 of this product's 32 source entries were opened and read.

**Scope note.** These notes specify a reference liability cash-flow projection model — model name
**`Sofort_DE_S`**, **monthly** grid — for the representative composite German *sofortbeginnende
private Rentenversicherung* defined in `product-spec.md` (same directory). This is not any single
insurer's product; the clause evidence behind it comes from four condition sets covering the
immediate annuity — [S4], [S2], [S6] and the GDV template [S1]. [S#] and [R#] tags refer to
`sources.md` (numbering carried from `_research/sofortrente.md`; frozen); [REG-R#] tags the
cross-product reference library `references/regulatory-and-actuarial-references.md` (its own frozen
R1–R56 numbering). **[std]** marks standardizations introduced for the reference implementation;
[unverified] marks claims no retrieved document corroborates. Parameter values are identical to
those in `product-spec.md`. Cells names, model-point columns and CSV headers are English `lower_snake_case`;
German terms of art keep their German form in prose.

**Retrieval conditions.** These notes were **drafted** under a policy that blocked all egress, with
the `WebSearch` budget exhausted before work on this product began, so **not one search was run for
the *Sofortrente*** and the draft rested on the authoring model's own knowledge of German practice.
The citations have since been **re-verified against the primary documents**: 19 of the 32 entries in
`sources.md` read `Retrieved: yes` and 12 read `no`, and the clause-level mechanics below are now
quoted from documents that were opened and read. The **levels** are not. One carrier's guaranteed
annuity scale [S8] and one carrier group's surplus declaration [S10] reached the corpus, neither was
used to fit anything, and every level in class (b) and class (c) below is therefore still **[std]**,
as are several in class (a). That is stated once here and tagged at every occurrence rather than
repeated in prose.

---

## Model scope and conventions

- **Purpose.** Project gross best-estimate liability cash flows for one *Sofortrente* — the
  *Einmalbeitrag* in, the guaranteed annuity and the *Überschussrente* out, the guaranteed
  instalments continuing to beneficiaries inside a *Rentengarantiezeit*, the *Kapitalrückgewähr* on
  death, the *Hinterbliebenenrente*, and insurer expenses — on an expected, probability-weighted
  basis, for a single model point. **Undiscounted.** Discounting, the *Deckungsrückstellung*
  recursion, the *Zinszusatzreserve*, the Solvency II best estimate and risk margin and the IFRS 17
  measurement are **out of scope** and are cited, not computed (see *Valuation and reserve
  pointers*).
- **Mortality is the model.** After *Rentenbeginn* the contract has **no premium stream, no
  surrender value, no lapse decrement, no paid-up state and no policyholder option of any kind**
  [R1] [R2] [R5] [REG-R28]. The only decrement is death; where a *Hinterbliebenenrente* is in force
  there are two lives and the liability runs to the second death. **There is no lapse machinery
  anywhere in this model, and that is a cited product feature rather than an omission.**
- **Projection frequency and origin.** **Monthly grid**, `t = t_start() … proj_len() − 1`, counted
  in complete months from *Vertragsbeginn*. Month `t` is the civil month beginning at the `t`-th
  month-start after inception. The index is **0-based**, which is the library-wide convention: the
  first month of a new-business point is `t = 0`, `policy year = t // 12 + 1`, and `proj_len()` is
  the **exclusive end** of the frame, so the frame is `range(t_start(), proj_len())`, its last month
  index is `proj_len() − 1` and it carries `proj_len() − t_start()` rows. `t = 0` is both the month
  the *Einmalbeitrag* is received and — under the representative *vorschüssig* convention — the
  month the first instalment is paid. An in-force model point opens at `t = duration_mth_init()`,
  the number of months the contract has already run.
- **The model carries duration, not the calendar.** Every step in this product falls on a **policy
  anniversary**: the *Überschussrente* increase [S15], the expense inflation index, the attained-age
  step. Nothing happens on 31 December, so — unlike `frlib`'s `Rente_FR_S`, where revalorisation is
  a calendar event — no cells needs the civil month. `issue_year` is carried all the same, for two
  reasons that are not cash flows: it is the **cohort key** of the generational mortality surface,
  and it selects the **contract's own *Höchstrechnungszins* vintage** [REG-R14] [REG-R15].
- **Timing conventions [std].** The *Einmalbeitrag* arrives at the **start of month 0**. Instalments
  are paid at the **start** of a payment month; under `advance` (*vorschüssig*) the first falls at
  `t = defer_mths()`, under `arrears` (*nachschüssig*) at `t = defer_mths() + 12/ann_freq`. A
  payment is made if the payee is alive at the **start** of that month — the same instant — so the
  survival index of a payment is always `t` and the two timings differ **only in which months carry
  an instalment**. Deaths fall **during** month `t`, so a life dying in month `t` has already
  received the instalment due at `t`; the *Kapitalrückgewähr* is settled net of it. Expenses accrue
  at the start of the month.
- **Age basis and generation [std].** `age(t, life) = issue_age(life) + t // 12`: age last birthday
  at inception, incrementing at each 12-month multiple of it. The **birth year is a separate model
  point attribute and is never derived from the projection year**, because the mortality surface is
  generational and the cohort is its key [REG-R49]. The shipped model points satisfy
  `issue_year == birth_year(1) + issue_age(1)`, which is a **[std]** internal-consistency
  convention, not a contract fact; a real book will carry a fractional offset of up to a year.
- **Unisex pricing.** The tariff annuity factor is computed on a **unisex blend** of the sex-distinct
  proxy tables, at a **[std]** portfolio male share; the model point's own `sex` drives only the
  best-estimate decrement path [REG-R34] [REG-R49]. Letting `sex` reach the annuity factor
  reproduces a tariff unlawful in Germany since 21 December 2012 and is pitfall 10.
- **Currency, sign and rounding.** EUR throughout. `net_cf(t)` is **income-positive** (the
  *Einmalbeitrag* +, annuity payments, death benefits and expenses −), with the outgo-positive
  orientation of these notes published as `liability_cf(t) = −net_cf(t)`. No intermediate rounding;
  displayed cash flows to the cent and probabilities to six decimals **[std]**.
- **Out of scope and said so.** The *Bewertungsreserven* share, which continues in the payout phase
  [S3] [REG-R24] but is path- and balance-sheet-dependent on the HGB accounts [REG-R9] [REG-R18]; a
  commuted settlement of the *Restgarantiezeit*, whose basis was not established (research gap 10);
  taxation, which falls on the annuitant rather than on the insurer's liability [REG-R41]; and any
  management action on the declared surplus.

---

## Model point attributes

| Attribute | Type | Meaning | Exercised by |
|---|---|---|---|
| `point_id` | int | Key; `Projection` is parameterized by it | all |
| `policy_id` | str | Reference, reporting only | all |
| `prem_gross_level_pp` | EUR | The *Einmalbeitrag*, `SP`; beside it `prem_form`, `single` on every point, which Sofort's own cells do not read | all |
| `issue_age` | int | Annuitant's age last birthday at *Vertragsbeginn* | all |
| `issue_year` | int | Calendar year of *Vertragsbeginn*; the *Höchstrechnungszins* vintage | 10 |
| `birth_year` | int | Annuitant's *Geburtsjahr* — the generational table key | all |
| `sex` | enum {M, F} | **Decrement only**; the tariff is unisex [REG-R34] | 11, 12 (F) |
| `defer_years` | int | *Aufschubzeit*, 0 for a pure *Sofortrente* | 6 |
| `guar_years` | int | *Rentengarantiezeit*, 0 = none | 1, 5, 7–10, 12–14 |
| `refund_form` | enum {none, full} | *Kapital-/Beitragsrückgewähr* | 3, 6 |
| `surv_pct` | float 0–1 | *Hinterbliebenenrente* as a fraction of the annuitant's annuity; 0 = rider off | 4, 5 |
| `surv_age` | int | Second life's age last birthday at *Vertragsbeginn* | 4, 5 |
| `surv_birth_year` | int | Second life's *Geburtsjahr* | 4, 5 |
| `surv_sex` | enum {M, F} | Second life's sex, decrement only | 4, 5 |
| `ann_freq` | int, a key of `ann_freq_table.csv` {12, 4, 2, 1} | Instalments per year, `m` | 7 (4), 8 (1), 11 (2) |
| `payment_timing` | enum {advance, arrears} | *vorschüssig* / *nachschüssig* **[std]** | 9 |
| `rechnungszins` | float | The tariff *Rechnungszins* `i`, at or below the vintage cap | 10, 13 |
| `surplus_form` | enum {none, konstant, teildynamisch, volldynamisch} | *Überschussverwendung* | 5, 8, 11, 13 (konstant); 6, 12 (voll); 14 (none) |
| `annuity_pp_init` | EUR | Guaranteed instalment carried on an in-force point; **0 = derive by equivalence** | 10 |
| `duration_mth_init` | int | Months already elapsed at the valuation date; the frame's first `t` | 10 |
| `pols_if_init` | float | Policies the point represents | all |

**Two configurations, not two premium forms.** A *Sofortrente* has exactly one premium form — a
single *Einmalbeitrag* — so the pair of shapes this model must serve is not `level`/`revisable` but
**derived** against **given**: a new-business point (`annuity_pp_init == 0`) whose guaranteed annuity
the model strikes from `prem_gross_level_pp` by equivalence on the tariff basis, and an in-force point
(`annuity_pp_init > 0`) whose annuity was struck years ago on a basis the model does not reproduce
and is therefore carried. Model point 10 is the second kind. On it the pricing identity
`check_equivalence()` is not asserted, and the notes say so rather than letting the check pass
vacuously without explanation.

`surv_age`, `surv_birth_year` and `surv_sex` are ignored where `surv_pct == 0`, and the shipped table
carries zeros there. `sex` is carried but **must not** enter the annuity factor [REG-R34].

**The fourteen shipped model points.** Between them they exercise every option, all four payment
frequencies, both payment timings, all four *Überschussverwendung* forms, both derived and given
annuities, two tariff vintages with three tariff rates and both ends of the issue-age envelope.
Every point opens at the valuation date 1 January 2027 (decision of 2026-11-11): the thirteen
new-business points are business of 2027, and the in-force point 10, issued in 2012, opens
fifteen years in. Model point 1 is the worked example's anchor cell.

| # | `SP` | age / year / cohort / sex | options | `m` / timing | `i` | surplus | what it is for |
|---|---|---|---|---|---|---|---|
| 1 | 100,000 | 65 / 2027 / 1962 / M | guar 10 y | 12 / adv | 1,00 % | teildyn. | **anchor**; the representative design |
| 2 | 100,000 | 65 / 2027 / 1962 / M | none | 12 / adv | 1,00 % | teildyn. | the plain *Leibrente*, against which every option's price is read |
| 3 | 100,000 | 65 / 2027 / 1962 / M | refund `full` | 12 / adv | 1,00 % | teildyn. | the implicit solve |
| 4 | 100,000 | 65 / 2027 / 1962 / M | surv 60 %, life 2 aged 62 / 1965 / F | 12 / adv | 1,00 % | teildyn. | the joint-life leg, and a **longer second-life horizon** |
| 5 | 150,000 | 68 / 2027 / 1959 / F | guar 20 y **and** surv 100 %, life 2 aged 70 / 1957 / M | 12 / adv | 1,00 % | konstant | the combined option, and the `(1 − γ)` gate |
| 6 | 100,000 | 62 / 2027 / 1965 / M | defer 5 y, refund `full` | 12 / adv | 1,00 % | volldyn. | the *Aufschubzeit* and its *Beitragsrückgewähr* |
| 7 | 100,000 | 65 / 2027 / 1962 / M | guar 10 y | **4** / adv | 1,00 % | teildyn. | quarterly instalments |
| 8 | 200,000 | 72 / 2027 / 1955 / M | guar 15 y | **1** / adv | 1,00 % | konstant | annual instalments |
| 9 | 100,000 | 65 / 2027 / 1962 / M | guar 10 y | 12 / **arr** | 1,00 % | teildyn. | *nachschüssig*, the timing switch of research gap 11 |
| 10 | 100,000 | 65 / **2012** / 1947 / M | guar 15 y | 12 / adv | **1,75 %** | konstant | **in force** at fifteen years: `annuity_pp_init = 430.00`, `duration_mth_init = 180`, `pols_if_init = 0.918857`, the guarantee just run out |
| 11 | **25,000** | **85** / 2027 / 1942 / F | none | **2** / adv | 1,00 % | konstant | boundary: oldest entry, smallest ticket, half-yearly |
| 12 | **500,000** | **60** / 2027 / 1967 / F | guar 30 y | 12 / adv | 1,00 % | volldyn. | boundary: youngest entry, largest ticket, longest guarantee |
| 13 | 250,000 | 70 / 2027 / 1957 / M | guar 10 y | 12 / adv | **0,25 %** | konstant | the 0,25 % of the 2022–2024 *Höchstrechnungszins* vintage, kept on a 2027 issue below that year's 1,00 % cap (decision of 2026-11-11) [REG-R15] |
| 14 | 100,000 | 65 / 2027 / 1962 / M | guar 10 y | 12 / adv | 1,00 % | **none** | surplus off, so the *Überschussrente*'s contribution is isolatable |

Point 10's `annuity_pp_init` is **[std]**: no *Standmitteilung* was located at any carrier [S15], so
the in-force annuity is a round figure of the right order for a 2012 tariff at 1,75 %, and its
*Überschussrente* is reconstructed from the form and the elapsed duration rather than carried.
Its `pols_if_init = 0.918856527011293` is no level of its own but the model's roll-forward of the
point to the valuation date (decision of 2026-11-11): the second-order probability that the
annuitant, alive at the start of month 156 (1 January 2025), is alive at the start of month 180,
the 15-year guarantee having run out at that month. It was rolled forward on the basis before the
switch to the table factory and is kept, with `annuity_pp_init`, as contract data: the switched
basis would give 0,946156 over the same months, and the point is not re-struck or re-rolled on it.

---

## State variables

| Variable | Description | Updated |
|---|---|---|
| `t_start()` | First projected month = `duration_mth_init()`; 0 for new business | once |
| `proj_len()` | **Exclusive end** of the frame, so `result_cf().index[-1] == proj_len() − 1` | once |
| `horizon_mths(life)` | `12 × (omega_age − issue_age(life))`, the month at which that life's survival reaches zero | once |
| `age(t, life)` | Attained age = `issue_age(life) + t // 12` | monthly |
| `duration(t)` | Completed policy years = `t // 12`; 0 through the first policy year | monthly |
| `policy_year(t)` | Contractual, 1-based policy year = `t // 12 + 1` | monthly |
| `calendar_year(t)` | `issue_year() + t // 12`; reporting and the cohort cross-check | monthly |
| `mort_rate(t, life)` | **Annual** second-order rate at `age(t, life)` for that life's cohort and sex | monthly |
| `mort_rate_mth(t, life)` | `1 − (1 − mort_rate)^(1/12)` **[std]** | monthly |
| `mort_rate_tariff(t, life)` | **Annual** first-order rate on the **unisex** blend, used only for pricing | monthly |
| `lives_if(t, life)` | Second-order probability alive at the **start** of month `t`; `lives_if(t₀) = 1` | recursion |
| `lives_death(t, life)` | `lives_if(t) − lives_if(t + 1)`, deaths **during** month `t` | monthly |
| `tariff_lives(k, life)` | First-order survival to the start of month `k`, used only inside the pricing sums | recursion |
| `first_pay_mth()` | `defer_mths()` under `advance`, `defer_mths() + pay_period_mths()` under `arrears` | once |
| `guar_end_mth()` | `first_pay_mth() + 12 × guar_years()`; the first month after the guarantee | once |
| `certain_floor(t)` | 1 while the *Rentengarantiezeit* runs, else 0 | monthly |
| `is_payment_mth(t)` | Whether an instalment falls due at the start of month `t` | monthly |
| `annuity_pp_derived()` | The guaranteed instalment struck by equivalence from `SP` | once |
| `annuity_guar_pp(t)` | The *garantierte Rente* in force in month `t`; level for life | monthly |
| `annuity_surp_pp(t)` | The *Überschussrente* instalment in month `t`; steps at the anniversary | monthly |
| `annuity_pp(t)` | `annuity_guar_pp(t) + annuity_surp_pp(t)`, the total instalment | monthly |
| `cum_annuity_guar_pp(t)` | Cumulative **guaranteed** instalments paid to and including month `t` | recursion |
| `refund_pp(t)` | `max(SP − cum_annuity_guar_pp(t), 0)` where the refund is elected, else 0 | monthly |
| `payment_factor(t)` | `max(certain_floor, l_a) + δ (1 − l_a) l_s (1 − certain_floor)` at the payment instant | monthly |
| `inflation_factor(t)` | `(1 + expense_infl)^(t // 12)`, the core's factor at `inflation_years(t) = duration(t)` **[std]**, stepping at the policy anniversary | monthly |
| `pols_if(t)` | Probability that any payment obligation remains at the start of month `t` | monthly |

There is **no account value, no surrender-value, no paid-up and no lapse state variable**, and no
`av_pp_at` / `lapse_rate` / `lapse_rate_mth` cells anywhere in the model. That is a statutory fact
about the product [R1] [R2] [R5] [REG-R28], not a modeling simplification, and it is asserted by
pitfall 17 rather than left to inspection.

`pols_if(t)` is **not a policy count**: it is the probability that a payment obligation of any kind
still stands — the guarantee period running, the annuitant alive, or the survivor's annuity in
payment — and it is the weight the maintenance expense is carried on. It keeps the library's name
for the expense weight, and its docstring says what it is so the shared conventions suite can apply
the payout-product exemption. At the frame's first row it is `pols_if_init()` exactly, on a
new-business point and on an in-force one alike.

---

## Assumption inputs

Three classes. Class (a) is contractual or statutory and is cited where the corpus supports it;
class (b) is the insurer's current discretionary scale, revisable annually within the statutory
minimum [REG-R18] [REG-R24]; class (c) is the modeller's view of experience.

### (a) Contractual / guaranteed elements (cited)

| Input | Value | Basis |
|---|---|---|
| Premium | One *Einmalbeitrag* at `t = 0`; no premium stream | [S2] [S4] [S6]; structural |
| *Nettoeinmalbeitrag* | `SP × (1 − α)`; the AVB charge clause is "Bei Verträgen gegen Einmalbeitrag werden von uns die Abschluss- und Vertriebskosten vollständig zu Vertragsbeginn mit diesem verrechnet" | [S4]; α **[std]**, class (c) |
| Equivalence | `SP_net = R × ä × (1 + β) + PV(refund)` on the **first-order** basis at the tariff `i` | [S2] [S4] [R10] |
| Mortality basis, pricing | A first-order annuitant table, generational, unisex tariff: DAV 2004R (Aggregattafel) at one carrier [S2] [S3], "NÜRNBERGER Tafel 2013 R" at another [S4]. DAV 2004 R is the profession's reference, not a mandate | [S2] [S4] [R10] [REG-R34] [REG-R49] |
| Tariff *Rechnungszins* | Model-point attribute; **1,00 %** for 2025–2027 business, at or below the vintage cap. Every retrieved tariff prices **at** its vintage's cap; no below-cap pricing was observed | [S2] [S3] [S4] [S6]; [REG-R14] [REG-R15] |
| Guarantee | The *garantierte Rente* is immutable for life; § 163 VVG is the only channel and it is narrow — and narrower here, Abs. 1 re-setting a *premium* this product does not have | [R4] [REG-R27] |
| Payment frequency and timing | Monthly, *vorschüssig*, first instalment at inception. Frequencies read at four sources; **timing contradicted — two AVB pay in arrears**, and the model's convention is retained in this pass | [S1] [S2] [S6] [S7]; timing **[std]**, contradicted by [S4] [S6] |
| *Rentengarantiezeit* | `guar_years × ann_freq` instalments payable **regardless of survival** from *Rentenbeginn*: "Stirbt die versicherte Person während der Rentengarantiezeit, so wird die monatliche Rente bis zum Ablauf der Rentengarantiezeit weiter gezahlt" | [S4]; also [S1] [S5] [S6] [S8] [R23] |
| *Kapital-/Beitragsrückgewähr* | `max(SP − guaranteed instalments already paid, 0)` on death — and two AVB confirm the netting is on the **guaranteed** annuity, so this is no longer a **[std]** argument | [S2] [S6] [R23] |
| *Hinterbliebenenrente* | `surv_pct` of the annuitant's annuity to a named second life, from the annuitant's death, for that life's remaining lifetime; lapses if the second life predeceases; and it begins only **after** any *Rentengarantiezeit* has expired | [S1] [S9]; percentages [unverified] — the model conditions state none |
| Death-benefit exclusivity | The refund is **not** combined with a guarantee period or a survivor's annuity | **[std]**, research gap 10 |
| Surrender / paid-up / lapse | **None**, once the *Rentenbezug* has begun — "Eine sofort beginnende Rentenversicherung können Sie nicht kündigen" [S4], "Sie können Ihren Vertrag nicht kündigen. Die Rückzahlung des Einmalbeitrages können Sie nicht verlangen" [S1]. § 168 Abs. 1 and 2 VVG never engage on a single-premium *Leibrente*, and § 169 falls with them | [S1] [S2] [S4]; [R1] [R2] [R5] [REG-R28] |
| *Überschussbeteiligung* | A statutory entitlement continuing through the payout phase, *Bewertungsreserven* *hälftig* under § 153 Abs. 3 VVG; method not prescribed. In payment the surplus is "jeweils nur für ein Versicherungsjahr zugesagt" [S2] | [S2] [S3] [S4] [S10] [REG-R24] |
| Limiting age | `omega_age() = 121`, the end age of the table factory's `dav2004r_proxy`, which closes with `q = 1` at attained age 120 | **[std]** |

### (b) Insurer-discretionary current elements

**One carrier group's declaration is now read and one carrier's realised increase with it, but
neither is this model's scale.** Bayern-Versicherung declares, for *Einzel-Rentenversicherungen* of
tariff generations 2015–2025, a *Zinsüberschussanteil* **während des Rentenbezugs** of "3,35 %
(2,5 %) abzüglich Rechnungszins" — 2,35 % over a 1,00 % tariff rate for 2026 — with "Ein Risiko- oder
Verwaltungskostenüberschussanteil wird nicht gewährt" in the payout phase, allotted "am Ende des
Versicherungsjahres", and with **no *Schlussüberschussbeteiligung* and no *Mindestbeteiligung* at the
*Bewertungsreserven* for immediate annuities** [S10]. Debeka reports the resulting increase on its own
*Sofortrente*: 0,75 % for 2024 [S8]. Five carriers' 2026 *laufende Verzinsung* run 2,4 %–3,0 % [R21]
[R22]. **The figures below are not calibrated to any of these** and remain **[std]**: they were chosen
to make the worked example reproduce, they use a two-component shape the one retrieved declaration
does not, and recalibrating them would move the golden tests. The gap between the two is recorded
rather than closed. The class is labelled (b) rather than (a) precisely because the insurer may
reduce it — the *konstante Überschussrente* included, "Falls wir in einem Jahr nicht ausreichend
Überschüsse erwirtschaften, kann die Zusatzrente reduziert werden" [S6] [R21].

| Input | Snapshot value | Basis |
|---|---|---|
| `surplus_init_pct` — *Überschussrente* at outset, as a fraction of the *garantierte Rente* | `none` 0 %; `konstant` **20 %**; `teildynamisch` **10 %**; `volldynamisch` **0 %** | **[std]** (b1) |
| `surplus_growth` — annual increase in the *Überschussrente* | `none` 0 %; `konstant` **0 %**; `teildynamisch` **1,0 %**; `volldynamisch` **2,0 %** | **[std]** (b1) |
| Crediting mechanic | The *Bonusrente* ratchet: an increment, once bought, is not taken back, so `annuity_pp(t)` is non-decreasing — "Die jeweils erreichte Rentenhöhe kann nicht mehr sinken" [S4] | [S4]; levels **[std]** |
| Increase date | The **policy anniversary**, not a calendar date: "erstmals zum Ende des ersten Versicherungsjahres" [S4], "am Ende des Versicherungsjahres" [S10], "jeweils für den Monat vor dem Jahrestag der Versicherung" for the *Bewertungsreserven* [S10] | [S4] [S6] [S10] [S15] |
| *Bewertungsreserven* share | **Excluded**, explicitly — though at one carrier an immediate annuity receives no *Mindestbeteiligung* at all [S10] | [S3] [S10] [REG-R24]; see *Model scope* |
| Reduction of a declared *Überschussrente* | **Not modelled**; the projection is a central estimate, and the sensitivity section prices the downside instead. The contracts permit reduction: [S6] on the *Zusatzrente*, [S2] on the *Garantie-PLUS-Rente* | [S2] [S6] [R21]; **[std]** |

(b1) The market's own description gives the *shape*: the constant (or *flexible*) form is highest at
outset and flat only "so lange die Überschüsse so hoch sind, wie bei Rentenbeginn prognostiziert"
[R19], the volldynamic form lowest at outset and rising with each declaration and unable to fall
[R19] [S4], the teildynamic form intermediate on both axes and able to fall [R19] [R21]; the
rating house's own treatment of the choice is titled "Die Qual der Wahl" [R20]. **The
opening 20 % for the constant form stays [unverified] and stays [std]**: the 15 %–25 % gap between
guaranteed and total annuity is not stated in any of the five retrieved insurer packs, nor in either
consumer source, so there is still no observed range behind it. The growth rates are round numbers
consistent with a *Zinsüberschuss* of one to two points over a 1,00 % *Rechnungszins* — a shape the
one retrieved declaration supports at 2,35 % for 2026 [S10] without validating these numbers, which
were not derived from it. **The three forms are not calibrated to equal present value in this
implementation**, and a user who needs them to be must do that calibration; asserting equality is a
wrong test, not a right one.

### (c) Behavioural / experience assumptions (modeller's view)

**The behavioural set is empty, and that is the product.** There is no lapse rate, no paid-up rate,
no dynamic surrender formula and no option take-up rate, because there is no option to take up after
*Rentenbeginn* [R1] [R2] [R5]. What remains in class (c) is the **basis** — mortality and expenses —
and every level in it is **[std]**.

**Mortality — the table factory's [std] proxy.** DAV 2004 R and DAV 2004 R-Bestand are DAV property,
are not public and are **not redistributed here** [REG-R47] [REG-R49]. The death rates come from the
core's table factory (`core/Core/Tables`): the item `mort_table` of `param_tariff_type.csv` chooses
`dav2004r_proxy`, a **[std]** proxy with the structure of the real table and none of its values,
whose parameters are rows of `core/Core/Data/param_tables.csv`, each with its provenance. It is a
generational table by sex over attained ages 0 to 120, built as follows **[std]**:

    q_base(x, M) = 0.008 × 1.11^(x − 65)          q_base(x, F) = 0.6 × q_base(x, M)
    tr(x)        = 0.025 up to age 75, linear to 0.0125 at 90, linear to 0 at 120      (both sexes)
    q(x, s, g)   = min( 1, q_base(x, s) × (1 − tr(x))^(g + x − 2005) ),      q(120, s, g) = 1

so the base rates are the period rates of the table's base year 2005, and `q(x, s, g)` is the rate of
the calendar year `g + x` for the birth year `g`. The end age 121 is `omega_age()`. For the anchor
cohort, born 1962, the unisex tariff blend below reads `0.003575` at 65, `0.007881` at 75 and
`0.024836` at 85, a cohort life expectancy of about 28,9 years at 65. The values package of
epic-table-factory, accepted 2026-11-18, records the choice and its reasons
(`_bmad-output/parameter-tables/epic-table-factory/values-package-table-factory.md`, section
"Sofort"; open points 2, 5, 8 and 9): the level of the table was redrawn (open point 9), the base
year moved from Sofort's former 2025 to the table's 2005 (open point 8), the best-estimate factor is
1.20 (open point 5), and the end age is guarded (open point 2, below). **Before the switch** the
product shipped its own proxy, `mort_table.csv` in four series `{FIRST, SECOND} × {M, F}` over ages
50 to 120 — the research file's Gompertz–Makeham law `q_base(x) = 1 − exp(−(A + B·c^x·(c − 1)/ln c))`,
`A = 0.0002`, `B = 1.5e-5`, `c = 1.10`, life expectancy 24,29 years at 65, split by sex at
`1.250000` and `0.795455` so that the 45 % / 55 % blend of the first-order series reproduced it,
with `SECOND = 1.20 × FIRST` — and `improvement_table.csv`; both files are gone, and with them the
anchor identity that traced the research file's annuity factors into the model.

**How far the proxy is from a real tariff basis — measured against a carrier quotation.** Debeka
publishes a *Berechnungsbeispiel* for its own *Sofortrente* on tariff **S1**, Stand 01.01.2025:
50 000 € single premium, 20-year *Rentengarantiezeit*, guaranteed **151 € a month at age 65** [S8] —
302 € per 100 000 €. This model, on the same age, the same 1,00 % tariff rate and the same guarantee
period, net of both **[std]** charges, produces **308,06 €** (154,03 € on 50 000 €), about **2 %
higher**; on its former file proxy it produced 335,13 €, about 11 % higher, and the research file's
own construction gives 349 €, about 16 % (`product-spec.md`, *Rentenhöhe*). What remains of the
difference is attributable to the proxy's mortality, to α = 2,5 % and β = 2,0 %, or to both; **the
corpus does not separate them**, because no carrier's charge parameter was established [S11] [S12].
**The proxy was not fitted to the quotation**: the table's level was redrawn for the table factory
as a whole (open point 9), not to hit 302 €, and one carrier at one vintage is not a market. A build
that wants a market-consistent annuity should replace the first-order basis and the loadings with
company data.

**The generational surface.** A period table is the wrong object for a forty-year annuity [REG-R49].
The trend `tr(x)` lives **inside** the table: the model reads `q(x, s, g)` at each life's own birth
year and never applies an improvement on top of a period rate. The exponent `g + x − 2005` is the
calendar year in which the life attains age `x`, less the base year; it would be **negative** for a
cohort attaining an age before 2005, which is correct and is not floored. No shipped point reads one:
every frame opens at the valuation date 1 January 2027, so the smallest exponent read is 22 — the
1962 anchor cohort at 65, and point 10's 1947 cohort at 80.

**The *Sicherheitszuschlag* is two-dimensional and both dimensions are shipped.** For an annuity,
prudence means **lighter** mortality **and a stronger assumed improvement trend**, so a proxy
reproducing only the level is not a proxy for the table [REG-R47]. The tariff reads the table rate
itself; the best estimate is the own sex's table rate times `mort_be_factor = 1.2` **[std]** and a
trend term `T = ((1 − 0.8 tr(x)) / (1 − tr(x)))^(g + x − 2005)` at `mort_be_trend_factor = 0.8`
**[std]**, so below the cap it is `1.2 × q_base(x, s) × (1 − 0.8 tr(x))^(g + x − 2005)`: the table is
lighter than the best estimate by the factor 1.2 in level and improves 1.25 times as fast, the
best estimate at 0.8 of the table's trend. Both are **[std]** with no observed range (research gap
12), carried over from the ratios of Sofort's former two bases. The wedge between the two bases is
the systematic *Risikoüberschuss* this product's surplus is largely financed from [REG-R47]
[REG-R18]; collapsing them destroys both halves of the mechanic and is pitfall 9.

**Unisex blend.** `q(x, "U", g) = ρ_M · q(x, "M", g) + (1 − ρ_M) · q(x, "F", g)`, the core's
`unisex_blend`, with `ρ_M = unisex_mix_male = 0.45` **[std]**. The direction is argued rather than
observed: a unisex tariff struck on sex-distinct tables is a better deal for women than for men, so
the realised female share of a voluntary annuitant portfolio sits above the population share
[REG-R34]. **No German carrier publishes a portfolio mix** (research gap 13).

**Expenses and loadings.** The two *loadings* are tariff parameters and enter the pricing identity;
the two *expenses* are best-estimate cash flows and do not. Keeping them apart is the point of the
three-class split, and confusing them is pitfall 12's neighbour.

| Input | Value | Basis |
|---|---|---|
| `load_acq_sp_once` α — acquisition loading in the tariff | **2,5 %** of `SP`, a row of `param_tariff_type.csv` | **[std]** (c1) |
| `load_admin_annval_once` β — administration loading on the annuity value | **2,0 %**, a row of `param_tariff_type.csv` | **[std]** (c1) |
| `expense_acq_sp_once`, `expense_acq_pp_once` — acquisition expense actually incurred at `t = 0` | **2,0 %** of `SP` **plus 200 €**, two rows of `param_tariff_type.csv` | **[std]** (c1) |
| `expense_admin_pp_ann` — maintenance expense per annum, per unit of `pols_if` | **60 €**, a row of `param_tariff_type.csv`, accrued monthly | **[std]** (c1) |
| `expense_pay_pp_inst` — cost of running one instalment | **1,50 €** per instalment paid, a row of `param_tariff_type.csv` | **[std]** (c1) |
| `expense_infl` — expense inflation | **2,0 %** p.a., the house-wide rate (acceptance of 2026-11-09; was 1,5 %), an item of the core file `param_core.csv`, stepping at the policy anniversary | **[std]** (c1) |
| `unisex_mix_male` ρ_M | **0.45**, a row of `param_tariff_type.csv` | **[std]** |
| `mort_table` | **`dav2004r_proxy`**, a row of `param_tariff_type.csv`, the table of the core's table factory both lives read; its end age 121 is `omega_age()` and its base year 2005 replaces the former item `mort_base_year` 2025 | **[std]** |
| `mort_be_factor`, `mort_be_trend_factor` | **1.2** and **0.8**, two rows of `param_tariff_type.csv`: the best estimate's level over the table rate and the share of the table's trend it improves at | **[std]** |
| `check_tol` | **1e-8**, an item of the core file `param_core.csv`, the tolerance every `check_*` closes to | **[std]** |
| Bisection tolerance and iteration cap | **1e-10**, **200**, literals in `annuity_pp_derived()` — the bisection controls for the refund solve, solver settings and so code | **[std]** |

(c1) **No charge or expense parameter was established at any carrier** (research gap 8), so none of
these has an observed range. The loadings are argued in `product-spec.md` footnote 6. The incurred
expenses are sized so that the tariff **over-recovers modestly**, which is the right direction and
the source of the *Kostenüberschuss*: on the anchor cell the acquisition loading takes 2 500 € against
2 200 € incurred, and the β loading collects roughly 2 % of the *Nettoeinmalbeitrag* against a
maintenance-plus-payment stream of about 78 € a year. A user with real expense data should replace all
six numbers; the two loadings and the four expenses must be replaced **together**, because moving one
without the other silently changes the modelled profit rather than the modelled cost.

### Input files

Inputs are **external CSVs in the model folder's parent**, read once per model by an unparameterized
`Data` Space — the `annuallife/TradLife_A` layout. Five files, and every one of them is read:

| File | Index columns | Value columns | Read by |
|---|---|---|---|
| `model_point_table.csv` | `point_id` | the 21 attributes above | `Data.model_point_table()` |
| `surplus_scale_table.csv` | `surplus_form` | `surplus_init_pct`, `surplus_growth` | `Data.surplus_scale_table()` |
| `hoechstrechnungszins_table.csv` | `year_from` | `year_to`, `max_rate` | `Data.hoechstrechnungszins_table()` |
| `ann_freq_table.csv` | `ann_freq` | — | `Data.ann_freq_table()` |
| `param_tariff_type.csv` | `item` | `value` | `Data.param()`, the core's loader |

No mortality file is read here: the death rates come from the core's table factory, the table
`mort_table` chooses, read through the Reference `tables` of `Projection`. It holds the sexes `M` and
`F`; the unisex blend is a model construction, not a table of its own, because no real table carries
one. The two mortality files of the product before the switch, `mort_table.csv` and
`improvement_table.csv`, are gone. Every file **except**
`model_point_table.csv` carries a final `provenance` column, one tag per row, per the library's second
ruling; a model point is a configuration rather than an assumption and is the only exemption. The
scalar assumptions of class (c) are rows of `param_tariff_type.csv`, each with its `provenance`, and are
tagged in the tables above.

---

## Cash flow components and recursions

### Notation (defined once, used throughout)

| Symbol | Cells | Meaning |
|---|---|---|
| `t` | — | month index from *Vertragsbeginn*, 0-based, `t = t₀ … n − 1` |
| `t₀`, `n` | `t_start`, `proj_len` | first projected month index; **exclusive end** of the frame |
| `m`, `p` | `ann_freq`, `pay_period_mths` | instalments per year; months between them, `p = 12/m` |
| `D`, `G` | `defer_mths`, `guar_years` | deferment in months; guarantee period in years |
| `SP`, `SP_net` | `prem_gross_level_pp`, `net_single_prem` | *Einmalbeitrag*; `SP(1 − α)` |
| `α`, `β` | `load_acq_sp_once`, `load_admin_annval_once` | acquisition and annuity-administration loadings |
| `i`, `v` | `rechnungszins` | tariff *Rechnungszins*; `v = 1/(1 + i)` |
| `R` | `annuity_pp_derived`, `annuity_guar_pp(t)` | the *garantierte Rente* per instalment |
| `U(t)`, `A(t)` | `annuity_surp_pp`, `annuity_pp` | *Überschussrente* instalment; total instalment `R + U(t)` |
| `u₀`, `ψ` | `surplus_init_pct`, `surplus_growth` | opening surplus fraction; its annual growth |
| `x_a(t)`, `x_s(t)` | `age(t, 1)`, `age(t, 2)` | attained ages of annuitant and second life |
| `g_a`, `g_s` | `birth_year(1)`, `birth_year(2)` | birth years — the generational keys |
| `tr(x)`, `T` | `tables.trend`, `mort_be_trend` | the table's annual improvement trend at age `x`; the best-estimate trend term |
| `q⁽¹⁾`, `q⁽²⁾` | `mort_rate_tariff`, `mort_rate` | annual first-order and second-order rates |
| `l_a`, `l_s` | `lives_if(t, 1)`, `lives_if(t, 2)` | second-order survival to the **start** of month `t` |
| `l̃` | `tariff_lives` | first-order survival, used only in the pricing sums |
| `d_a`, `d_s` | `lives_death(t, life)` | deaths during month `t`, `= l(t) − l(t + 1)` |
| `γ(t)` | `certain_floor` | 1 while the *Rentengarantiezeit* runs, else 0 |
| `δ` | `surv_pct` | survivor's percentage; 0 when the rider is off |
| `F(t)` | `payment_factor` | expected instalments payable at `t`, per unit of `pols_if_init` |
| `C(t)`, `K(t)` | `cum_annuity_guar_pp`, `refund_pp` | cumulative guaranteed instalments; the refund then due |
| `ä` | `annuity_factor` | value at `t = 0` of one unit of instalment on the tariff basis |
| `ω`, `ρ_M` | `omega_age`, `unisex_mix_male` | limiting age; portfolio male share |
| `c_e`, `c_p`, `π` | `expense_admin_pp_ann`, `expense_pay_pp_inst`, `expense_infl` | maintenance p.a.; per-instalment cost; inflation |
| `E₀` | — | acquisition expense incurred at `t = 0` |

`q`, `tr`, `T`, `l`, `γ`, `F` are dimensionless; `SP`, `R`, `U`, `A`, `K`, `C` and every cash flow are EUR;
`ä` is dimensionless (a value per unit of instalment). Note that `ä` is **not** the market's `a12`:
`a12 = ä / m`, so the research file's `a12(65, 1,00 %) = 20.426` corresponds to `ä = 245.11`.

### The projection frame, `t` and `proj_len()`

    horizon_mths(life) = 12 × ( omega_age − issue_age(life) )
    t_start()          = duration_mth_init()
    proj_len()         = max( horizon_mths(1),
                              first_pay_mth() + 12 × guar_years(),
                              horizon_mths(2)   if surv_pct > 0 )

`proj_len()` is the **exclusive end** of the frame, counted in months from *Vertragsbeginn*, so
`result_cf()` is indexed `range(t₀, n)`, `result_cf().index[-1] == proj_len() − 1` and the frame
carries `proj_len() − t₀` rows — the library's 0-based `range(proj_len())` ruling, asserted for
every model point. The three terms are the annuitant's survival horizon, the guarantee period's own
end, and the second life's horizon where a *Hinterbliebenenrente* is in force. **All three are
needed.** Stopping on the annuitant's horizon alone truncates a younger survivor's tail
(pitfall 18); stopping on the guarantee alone truncates the life annuity. On the anchor cell
`horizon_mths(1) = 12 × (121 − 65) = 672`, the guarantee ends at month 120, and `proj_len() = 672`,
so the frame carries **672 rows**, `t = 0 … 671`.

The frame **starts** at `t₀`, which is a product fact and is not asserted by the conventions suite:
a new-business point opens at 0 and an in-force point at the duration it has already run. What is
asserted is **contiguity** — a gap in `t` means a period was dropped, and no reading of `proj_len()`
would catch it.

### Generational mortality construction

    q(x, s, g)                  = tables.q( mort_table, s, x, g )  for x < omega_age(),  = 1 from omega_age() on
    q(x, "U", g)                = ρ_M · q(x, "M", g) + (1 − ρ_M) · q(x, "F", g)
    T(t, life)                  = ( (1 − 0.8 tr(x)) / (1 − tr(x)) )^( g + x − 2005 ),   x = x(t, life),  g = g(life)
    mort_rate(t, life)          = min( 1, mort_be_factor · T(t, life) · q(x, sex(life), g) ),  = 1 where q = 1   — projection
    mort_rate_tariff(t, life)   = q( x(t, life), "U", g(life) )                                                — pricing
    mort_rate_mth(t, life)      = 1 − (1 − mort_rate(t, life))^(1/12)                  **[std]**
    lives_if(t, life)           = lives_if(t − 1, life) × (1 − mort_rate_mth(t − 1, life)),  lives_if(t₀) = 1
    lives_death(t, life)        = lives_if(t, life) − lives_if(t + 1, life)
    tariff_lives(k, life)       = tariff_lives(k − 1, life) × (1 − mort_rate_tariff_mth(k − 1, life)),  = 1 at k = 0

Three properties matter and each is a test. **`q` depends on `t` only through the attained age and on
the model point only through the cohort**, so two points with the same entry age and different birth
years read different rates at the same age (pitfall 7). **The improvement is inside the surface**, not
applied on top of a period rate as a separate factor keyed to the projection year — that would walk
diagonally across cohorts and is the classic error (pitfall 8). And **the pricing basis and the
projection basis are different objects**: `mort_rate_tariff` is the table rate, first order and
unisex; `mort_rate` the best estimate, own sex, whose ratio to the own sex's table rate is
`1.2 T > 1.2` wherever the calendar year `g + x` lies after 2005 and the trend is positive — 1,34293
at `t = 0` on the anchor and 1,38327 at `t = 240` (pitfall 9). Because the tariff blends the sexes,
the best estimate does **not** lie above the tariff rate for every life: below the cap a man's is 1,5
to 1,9 times it (1,59 to 1,84 at the shipped points' ages), a woman's 0,9 to 1,1 of it (0,95 to 1,12),
above it at the main ages of the later cohorts and slightly below for older cohorts and at the
highest ages — born 1942, 0,99 of it at 85.

The table closes with `q = 1` at attained age 120 and its trend is 0 there, and the rate reaches the
cap of 1 before that: the table rate from age 113 or 114 for men and 117 or 118 for women on the
shipped cohorts 1942 to 1967, the best estimate, which is 1 wherever the table rate is, from 112 for
men and 116 for women. So `lives_if` reaches zero **before** `horizon_mths(life)` — the monthly
conversion of `q = 1` is 1, so the life dies in the first month of the age at which the rate first
reaches 1 and the path is zero from the next: on the anchor from `t = 565` (death in `t = 564`, the
first month of age 112), and the tariff path from `k = 637`, age 118 — and the decrements close: `Σ_t lives_death(t, life) = lives_if(t₀, life)` with
`lives_if(n, life) = 0`. That is `check_lives_roll_fwd()`. The horizon is an upper bound and no cash
flow depends on how far inside it the path ends. From `omega_age()` on the rate is 1 without reading
the table, which holds no age above 120: on the joint-life points 4 and 5 the frame runs to the
younger life's horizon, so the older life's attained age passes 120 while its survival is already
zero (open point 2 of the values package). No age is clamped below; the table holds every age
from 0.

### Payment months, the certain floor and the payment factors

    pay_period_mths()   = 12 // ann_freq()                                      ( p )
    first_pay_mth()     = defer_mths()                    under `advance`
                        = defer_mths() + pay_period_mths()  under `arrears`
    is_payment_mth(t)   = ( t ≥ first_pay_mth() )  and  ( (t − first_pay_mth()) mod p == 0 )
    guar_end_mth()      = first_pay_mth() + 12 × guar_years()
    certain_floor(t)    = 1 if first_pay_mth() ≤ t < guar_end_mth() else 0

    payment_factor(t)   = max( γ(t), l_a(t) )  +  δ · (1 − l_a(t)) · l_s(t) · (1 − γ(t))

**The survival index of a payment is `t` under both timings.** With month starts as the payment
instants, an advance instalment for month `t` and an arrears instalment covering `[t − p, t)` are both
paid at the start of month `t` and both require the payee to be alive then. So the two conventions
differ **only in which months carry an instalment**, and a `G`-year guarantee covers `G × m`
instalments under either — which is exactly what `guar_end_mth()` encodes, since `G · m · p = 12G`
regardless of `m` (pitfall 13).

**The `max` is what makes the *Rentengarantiezeit* a certain floor rather than a second stream.**
While the guarantee runs the full instalment is payable whether the annuitant is alive or not [R23];
an additive `γ + l_a` would pay `1 + l_a` for the whole guarantee, nearly doubling the outgo in the
first years (pitfall 3). The survivor leg is gated by `(1 − γ(t))` for the same reason: inside the
guarantee the full instalment already goes out, so adding the survivor's percentage on top would pay
`1 + δ` (pitfall 4).

The survivor gate is `(1 − l_a(t)) · l_s(t)` — the probability that the annuitant is dead and the
second life alive at the payment instant, **assuming independence [std]**. The *Anwartschaft* lapsing
on the second life's prior death needs no separate rule: `l_s(t)` is already zero then.

### Conversion — the guaranteed annuity struck at inception

    ä  =  Σ over payment months k  of  v^(k/12) · F̃(k)

where `F̃(k)` is `payment_factor(k)` computed on the **first-order** survival path `l̃` rather than on
`l`. Then, where the refund is not elected,

    net_single_prem() = SP × (1 − α)
    annuity_pp_derived() = SP_net / ( ä × (1 + β) )

and `annuity_guar_pp(t) = annuity_pp_init()` where that is positive, else `annuity_pp_derived()`,
level for the whole of the annuity's life [S6] [REG-R27].

`ä` is a **pricing quantity and must stay acyclic**: it depends on the tariff basis, the elected
options and the tariff interest rate, and on nothing that depends on the path. In particular it does
**not** depend on `surplus_form` — the *Überschussrente* is financed out of surplus actually earned,
not priced into the guarantee (pitfall 1's neighbour), so `annuity_pp_derived()` is invariant to
`surplus_form` and `check_equivalence()` closes on every derived point regardless of it.

`check_tariff_int_rate()` asserts `rechnungszins() ≤ hoechstrechnungszins() + roll_fwd_tol`, the cap
being read from `hoechstrechnungszins_table.csv` at `issue_year()` [REG-R14] [REG-R15]. The cap binds
the *reserving* rate and, through § 138 Abs. 1 VAG, the rate a new tariff may be priced at [REG-R8];
a carrier may price below it and one is observed doing so [S6], which is why the check is an
inequality.

### The *Kapitalrückgewähr* and its implicit equation

Where `refund_form == "full"`, the death benefit at a death during month `t` is

    C(t) = C(t − 1) + ( R  if is_payment_mth(t) else 0 ),   for t > t₀
    C(t₀) = R · ( (t₀ − first_pay_mth()) // p + 1 )  if t₀ ≥ first_pay_mth() else 0
    K(t) = max( SP − C(t), 0 )

The recursion opens at the frame's first month `t₀` rather than one month before it: on a
new-business point `t₀ = 0`, `first_pay_mth() = 0` under *vorschüssig* and the opening value is the
single instalment paid at `t = 0`; on an in-force point it is the instalments the contract has
already been paid by the valuation date. Nothing is ever indexed at `t = −1`.

— the *Einmalbeitrag* less the **guaranteed** instalments already paid, floored at zero **[std]**
(research gap 10). `C(t)` includes the instalment due at `t` itself, because that instalment was paid
at the start of the month in which the death occurred.

The pricing equation is then **implicit in `R`**, because `K` depends on `R` and the point at which
`K` reaches zero depends on `R` too:

    g(R) = R · ä · (1 + β)  +  Σ_t v^(t/12) · d̃_a(t) · max( SP − n(t)·R, 0 )   =   SP_net

with `n(t)` the number of instalments paid by month `t` and `d̃_a` the first-order death density.
`g` is increasing in `R` on `(0, R_max]` where `R_max = SP_net / (ä (1 + β))` is the no-refund
annuity, and `g(0) = SP · Σ v^(t/12) d̃_a(t) < SP_net` on any basis with a positive interest rate, so
a root exists and **bisection on `[0, R_max]` converges**. The reference implementation bisects to
a bracket of `1e-10` in at most `200` steps, evaluating the sum inline from the cached
`tariff_lives` path rather than through a cells parameterized by the trial `R`.

**Computing `R_max` and then subtracting a refund cost is a different — and wrong — answer** (pitfall
5). `refund_pv()` is published so the identity can be seen: `check_equivalence()` asserts
`SP_net == annuity_pp_derived() · ä · (1 + β) + refund_pv()` to `roll_fwd_tol`.

During an *Aufschubzeit* no instalment has been paid, so `C(t) = 0` and `K(t) = SP`: the same
machinery gives the *Beitragsrückgewähr* on death before *Rentenbeginn* without a second mechanic,
and `refund_form == "none"` on a deferred point gives the pure deferred annuity in which the fund of
those who die is forfeited to the survivors.

### The *Überschussrente*

    U(t) = R · u₀ · (1 + ψ)^( duration(t) − D / 12 )                for t ≥ first_pay_mth()
         = 0                                                        otherwise
    A(t) = R + U(t)

with `u₀` and `ψ` read from `surplus_scale_table.csv` at `surplus_form()`. Two properties are
asserted. **It steps at the policy anniversary, not monthly**: `U(t)` is constant across each block of
twelve months (pitfall 14). And **it ratchets**: `A(t) ≥ A(t − 1)` at every `t`, which is what the
*Bonusrente* crediting mechanic means arithmetically — an increment bought as paid-up annuity does not
come back off [R23] (pitfall 15). Both are `check_annuity_roll_fwd()`.

`U(t)` is an **insurer-discretionary current** quantity, never a guaranteed cash flow. A projection is
a central estimate of a stream the insurer may reduce [R21]; the sensitivity section prices the
downside rather than the model reserving for it.

### Expected cash flows in month `t`

**Premium.** One inflow, and only on a new-business point, because an in-force point's frame does not
contain `t = 0`:

    premiums(t) = SP × pols_if_init      if prem_due(t), t == 0,  else 0

**Annuity payments and guarantee claims.** The instalment splits into a payment to a living payee and
a payment to a beneficiary inside the guarantee:

    annuity_payments(t, "ANNUITANT") = pols_if_init · A(t) · l_a(t)                        · 1{payment month}
    annuity_payments(t, "SURVIVOR")  = pols_if_init · A(t) · δ (1 − l_a(t)) l_s(t) (1 − γ(t)) · 1{payment month}
    claims(t, "GUARANTEE")           = pols_if_init · A(t) · γ(t) · (1 − l_a(t))            · 1{payment month}

so that, at every payment month,

    annuity_payments(t) + claims(t, "GUARANTEE") = pols_if_init · A(t) · payment_factor(t)

which is `check_payment_factor()`, and inside the guarantee `payment_factor(t) = 1` exactly, which is
`check_guarantee_certain()`. Splitting the stream this way is not cosmetic: it separates annuity outgo
from death outgo, which is the shape of the product, and it makes the two commonest errors — the
additive certain floor and the survivor paid on top of the guarantee — visible in a column rather than
buried in a total.

**Refund claims.**

    claims(t, "REFUND") = pols_if_init · K(t) · lives_death(t, 1)

**Expenses.**

    expenses(t) = 1{t = 0} · pols_if_init · ( expense_acq_sp_once · SP + expense_acq_pp_once )
                + ( c_e / 12 ) · inflation_factor(t) · pols_if(t)
                + 1{payment month} · c_p · inflation_factor(t) · pols_if_init · payment_factor(t)

The acquisition term appears only at `t = 0` and therefore only on a new-business point. The
per-instalment term is weighted by `payment_factor(t)`, not by `pols_if(t)`: a survivor's annuity in
payment is a **second** payment run, and inside the guarantee the beneficiary's instalment costs the
same to pay as the annuitant's.

**Obligation weight and the net flow.**

    pols_if(t)      = pols_if_init · min( 1, max( γ(t), l_a(t) ) + 1{δ > 0} (1 − l_a(t)) l_s(t) )
    liability_cf(t) = annuity_payments(t) + claims(t) + expenses(t) − premiums(t)
    net_cf(t)       = − liability_cf(t)

`net_cf` is **income-positive**, the library-wide convention, and `liability_cf` carries these notes'
outgo-positive orientation; both are published as columns rather than one standing for the other.

`result_cf()` publishes, indexed by `t`, in this order: **`pols_if`, `premiums`, `annuity_payments`,
`claims_guarantee`, `claims_refund`, `expenses`, `liability_cf`, `net_cf`**. A second frame
`result_pols()` publishes `lives_if_1`, `lives_if_2`, `certain_floor`, `payment_factor`,
`annuity_guar_pp`, `annuity_surp_pp`, `annuity_pp`, `refund_pp`, `cum_annuity_guar_pp` and `pols_if`.

### Published `check_*` identities

Nine, each returning a `bool` over all `t` and, where a per-period residual exists, publishing it at
`check_*_resid(t)`. The library's first ruling makes `check_net_cf()` mandatory; the rest are this
product's own roll-forward and pricing identities.

| Check | Identity |
|---|---|
| `check_net_cf` | `net_cf(t) == premiums(t) − 1{payment month}·pols_if_init·A(t)·payment_factor(t) − claims(t,"REFUND") − expenses(t)`. The instalment term carries the payment-month indicator, because `payment_factor(t)` is defined at every `t` and only some `t` carry an instalment on a quarterly, half-yearly or annual point. **Not a restatement of the definition**: it rebuilds the annuity outgo through the `max()` payment factor rather than through the two published legs, so it asserts that the split into `annuity_payments` and `claims_guarantee` is exhaustive and non-overlapping; to `roll_fwd_tol()` times `max(prem_gross_level_pp() × pols_if_init(), 1)` |
| `check_lives_roll_fwd` | `lives_if(t + 1, life) == lives_if(t, life)·(1 − mort_rate_mth(t, life))`, and `Σ_t lives_death(t, life) + lives_if(n, life) == lives_if(t₀, life)` for each life in scope |
| `check_annuity_roll_fwd` | `annuity_surp_pp(t) == annuity_surp_pp(t − 1) · (1 + ψ)^{1 if t % 12 == 0 else 0}` inside the payment phase, and `annuity_pp(t) ≥ annuity_pp(t − 1)` at every `t` — the *Bonusrente* ratchet |
| `check_refund_run_off` | `refund_pp(t) == max(refund_pp(t − 1) − R·1{payment month}, 0)`, non-increasing and reaching zero at `⌈SP / R⌉` instalments; identically zero where `refund_form == "none"` |
| `check_payment_factor` | `annuity_payments(t) + claims(t,"GUARANTEE") == pols_if_init · A(t) · payment_factor(t)` at every payment month, and zero at every other |
| `check_guarantee_certain` | `payment_factor(t) == 1.0` at every payment month with `t < guar_end_mth()`, whatever `δ` — the instalment is certain inside the *Rentengarantiezeit* [R23] |
| `check_equivalence` | `net_single_prem() == annuity_pp_derived()·ä·(1 + β) + refund_pv()` to `roll_fwd_tol` scaled by `net_single_prem()` — the identity is an equality between euro amounts of the order of 10⁵ and the refund solve converges on `R` rather than on the residual. Returns `True` where `annuity_pp_init() > 0`, the annuity having been struck on a basis this model does not reproduce; the notes say so rather than letting it pass silently |
| `check_death_option_xor` | `refund_form() == "none"` **or** (`guar_years() == 0` **and** `surv_pct() == 0`) — the **[std]** exclusivity of research gap 10, asserted rather than assumed |
| `check_tariff_int_rate` | `rechnungszins() ≤ hoechstrechnungszins() + roll_fwd_tol`, the cap read at `issue_year()` [REG-R14] [REG-R15]. An inequality, not an equality: a carrier may price below the cap and one is observed doing so [S6] |

### Monthly processing order

For `t = t₀ … n − 1`, in this order:

1. **Once, before the loop:** read the model point; check `rechnungszins()` against the vintage cap
   [REG-R15]; compute `first_pay_mth()`, `guar_end_mth()` and `pay_period_mths()`; build the tariff
   survival path `l̃` on the first-order unisex basis; compute `ä`; and strike `R` — directly where
   `annuity_pp_init() > 0`, by `SP_net / (ä (1 + β))` where no refund is elected, and by bisection on
   the implicit equation where one is.
2. Set the attained ages `x_a(t)`, `x_s(t)` from `issue_age + t // 12`, and read `q⁽²⁾` from the
   generational surface at each life's own cohort and sex.
3. Advance the second-order survival: `l_a(t)`, `l_s(t)` from `l(t − 1)` and `mort_rate_mth(t − 1)`.
4. Set `γ(t)` and `is_payment_mth(t)`.
5. Set the instalment: `U(t)` from the surplus form and the completed policy year `duration(t)`, then
   `A(t) = R + U(t)`. Accumulate `C(t)` and set `K(t) = max(SP − C(t), 0)`.
6. Compute `payment_factor(t)` at the payment instant `t`.
7. **Start of month — premium.** At `t = 0` only, `premiums(0) = SP · pols_if_init`.
8. **Start of month — instalments.** `annuity_payments(t, ·)` and `claims(t, "GUARANTEE")` on the
   factors of step 6.
9. **During the month — deaths.** `lives_death(t, life) = l(t) − l(t + 1)`; settle
   `claims(t, "REFUND")` on `K(t)`, which is already net of the instalment paid at step 8.
10. **Expenses.** Acquisition at `t = 0`; maintenance on `pols_if(t)`; the per-instalment cost on
    `payment_factor(t)` where step 4 found a payment month.
11. Form `liability_cf(t)` and `net_cf(t)`; roll `l`, `C` and `U` forward to `t + 1`.

At `t = n − 1` the projection ends with no maturity payment and no tail state: `l_a(n) = 0` and the
guarantee has expired, so nothing remains to be paid.

---

## Known modeling pitfalls

These are the specific ways an implementation of *this* product looks right and is wrong. Each one
becomes a test.

1. **Projecting only the guaranteed annuity.** The *Überschussrente* is not guaranteed — in payment
   the RfB-funded part is "jeweils nur für ein Versicherungsjahr zugesagt" [S2] — but it **is** a
   projected cash flow, on typical market designs 15 % to 25 % of the payment [unverified] [R21]. A
   model publishing only `annuity_guar_pp` models less than the payment. Assert `annuity_pp(t) >
   annuity_guar_pp(t)` at every `t` on any point with `surplus_form != "none"`, and exact equality on
   model point 14, which switches surplus off.
2. **Decrementing the guaranteed instalments during the *Rentengarantiezeit*.** Inside the guarantee
   the payment is **certain**: "Stirbt die versicherte Person während der Rentengarantiezeit, so wird
   die monatliche Rente bis zum Ablauf der Rentengarantiezeit weiter gezahlt" [S4]. Assert `annuity_payments(t) + claims(t, "GUARANTEE") ==
   pols_if_init() × annuity_pp(t)` for every payment month with `t < guar_end_mth()`, exactly.
3. **Adding the certain floor instead of taking a max.** `γ + l_a` pays `1 + l_a` for the whole
   guarantee — on the anchor cell, nearly double the outgo for ten years. Assert `payment_factor(t)
   == 1.0` inside the guarantee where `surv_pct == 0`, and `≤ 1 + surv_pct` everywhere.
4. **Paying the survivor's annuity on top during the guarantee.** The survivor leg carries a
   `(1 − γ(t))` gate. Assert `annuity_payments(t, "SURVIVOR") == 0` for every `t < guar_end_mth()` on
   model point 5, and `> 0` for some `t` after it.
5. **Evaluating the *Kapitalrückgewähr* instead of solving it.** The equation is implicit in `R`.
   Assert `check_equivalence()` on model point 3, and that `annuity_pp_derived()` there differs from
   the naive `SP_net/(ä(1 + β))` less a refund cost computed at that annuity — the two answers are
   not the same number and the difference is not a rounding.
6. **Measuring the refund against the total annuity.** It is netted against the **guaranteed**
   instalments [std]. Assert `refund_pp(t)` is invariant to `surplus_form` — compare model point 3
   against a copy of it with the surplus switched off.
7. **Indexing the mortality surface by projection year instead of by birth year.** A period-table
   implementation reads age 66 in calendar year 2028 and walks diagonally across cohorts; a
   generational one reads `(g = 1962, x = 66)` whatever the projection year. Assert that two points
   with the same `issue_age` and different `birth_year` give **different** `mort_rate` at the same
   attained age.
8. **Shipping a period-table proxy at all.** A period proxy applied to a forty-year annuity
   understates the liability by a margin that dwarfs every other assumption [REG-R49]. Assert
   `mort_rate_gen(x, s, g)` differs from the table's base rate at `x` wherever `g + x != 2005` and
   the trend at `x` is positive, and that `ä` computed on the period table of the valuation year 2027
   is strictly smaller than `ä`.
9. **Applying the first-order margin to the level only.** For an annuity, prudence reaches the
   **trend** as well [REG-R47]. Assert `mort_be_trend(t, life) > 1` — the best estimate above
   `mort_be_factor` times the own sex's table rate — wherever `g + x` lies after 2005, the trend is
   positive and the cap does not bind; a level-only margin would hold the ratio at `mort_be_factor`.
10. **Letting `sex` into the tariff.** German new business has been unisex since 21 December 2012
    [REG-R34]. Assert that two points identical but for `sex` produce the **same**
    `annuity_pp_derived()` and **different** `lives_if`.
11. **Counting the *Einmalbeitrag* on an in-force model point.** Assert `premiums(t) == 0` for every
    `t` in model point 10's frame, and `Σ premiums == prem_gross_level_pp() × pols_if_init()` on model
    point 1.
12. **Opening an in-force point at `t = 0`.** The frame starts at the duration already run. Assert
    `result_cf().index[0] == duration_mth_init()` and `pols_if(t_start()) == pols_if_init()` on model
    point 10, and that the acquisition expense appears nowhere in its frame.
13. **Getting the arrears offset wrong.** Under `arrears` the first instalment falls at
    `defer_mths() + p`, and a `G`-year guarantee still covers `G × m` instalments. Assert that model
    point 9 has no payment at `t = 0`, has one at `t = 1`, and carries the **same number** of
    guaranteed instalments as model point 1.
14. **Compounding the *Überschussrente* monthly.** It steps at the policy anniversary [S15]. Assert
    `annuity_surp_pp(t) == annuity_surp_pp(t − 1)` whenever `t % 12 != 0`, and that the step at
    `t % 12 == 0` is exactly `(1 + surplus_growth)`.
15. **Letting the total annuity fall.** The *Bonusrente* ratchets [R23]. Assert `annuity_pp(t) ≥
    annuity_pp(t − 1)` at every `t` — `check_annuity_roll_fwd()`.
16. **Discounting the published cash flows at the tariff *Rechnungszins*.** `i` reaches the projection
    **only** through `ä` and `refund_pv()`; the model publishes undiscounted flows and a best estimate
    discounts at the EIOPA curve [REG-R4]. Assert that `net_cf` for a given `annuity_pp_init` is
    invariant to `rechnungszins`, which isolates the one legitimate channel.
17. **Inventing a lapse, a surrender value or a paid-up state.** There are none [R1] [R2] [R5]
    [REG-R28]. Assert that no `lapse_rate`, `lapse_rate_mth`, `av_pp_at`, `cv_pp` or surrender cells
    exists, and that the decrements close: `Σ_t lives_death(t, life) + lives_if(n, life) ==
    lives_if(t₀, life)` for each life in scope.
18. **Running the projection past the annuitant but not past the second life.** `proj_len()` takes the
    **maximum** of the two horizons and the guarantee's end. Assert that on model point 4 — annuitant
    65, second life 62 — `proj_len() == 12 × (omega_age − surv_age)`, the survivor's horizon and
    not the annuitant's, and that `annuity_payments(proj_len() − 1)` is finite and non-negative there.

---

## Policyholder behaviour modelling

**There is none to model, and this is a cited product feature.** Once the *Rentenbezug* has begun the
policyholder has no right of termination, no *Rückkaufswert*, no *Beitragsfreistellung*, no capital
option and no transfer [R1] [R2] [R5] [REG-R28]. Every option this product has is elected **once, at
inception** and is thereafter a parameter rather than a decision: the *Rentengarantiezeit*, the
*Kapitalrückgewähr*, the *Hinterbliebenenrente*, the payment frequency and the *Überschussverwendung*
form. The model therefore carries **no lapse decrement, no dynamic behaviour formula and no
take-up rate**, and that absence is the reason its result depends more purely on the mortality basis
and the surplus assumption than any other model in this library.

Behaviour enters the **basis**, not the projection, as selection effects **[std]**:

- **Annuitisation anti-selection.** A *Sofortrente* is bought voluntarily, disproportionately by
  people who expect to live long, and the German market does **not** medically underwrite it
  (`product-spec.md` footnote 4, still [unverified] — no retrieved condition set says so either way,
  though [S5] lists "keine Möglichkeit unsererseits zur Risikoprüfung" as a defining feature of an
  immediate-annuity tariff). DAV 2004 R is an annuitant-experience table understood
  to carry *Selektionsfaktoren* for exactly that [REG-R49], so the effect belongs inside the basis
  rather than beside it — which is why this model applies **no annuitant adjustment factor** on top of
  the first-order table. A projection applying population mortality to an annuity book overstates
  deaths by a wide margin [REG-R52].
- **Sex self-selection and the direction of `ρ_M`.** A unisex tariff struck on sex-distinct tables is
  a better deal for women, so the realised female share of a voluntary annuitant portfolio sits above
  the population share. That is the direction, not the magnitude, of `ρ_M = 0.45`; **no carrier
  publishes a portfolio mix** (research gap 13).
- **Option selection.** The *Rentengarantiezeit* and the *Kapitalrückgewähr* are chosen
  disproportionately by buyers who expect to die early, the *Hinterbliebenenrente* by those with a
  younger spouse. Both push realised experience away from the tariff basis and **no source quantifies
  either** [unverified].
- **Two behaviours at the boundary, handled outside the projection.** *Proof of life*: failure to
  return the annual certificate suspends payment until it arrives — a timing effect on an unchanged
  obligation, **not modelled [std]**. And the *Aufschubzeit* window, in which a surrender right may
  survive because the termination bar has not yet bitten [R1] [R2]: **no carrier's terms were
  established, and the corpus's one candidate turned out to be a hybrid unit-linked deferred annuity
  rather than a short-deferment *Sofortrente*** [S14] (research gap 17 closes as a negative). The base
  run switches the deferment off.

---

## Worked example

**Configuration.** Model point 1, the anchor cell, is the representative design of `product-spec.md`
with every attribute stated: `policy_id = SOF-000001`; `prem_form = single`; `prem_gross_level_pp = 100,000.00 €`;
`issue_age = 65`; `issue_year = 2027`; `birth_year = 1962`; `sex = M`; `defer_years = 0`, so
`defer_mths() = 0` and `first_pay_mth() = 0`; `guar_years = 10`, so `guar_end_mth() = 120` and the
first 120 monthly instalments are certain; `refund_form = none`; `surv_pct = 0.00`, with `surv_age`,
`surv_birth_year` and `surv_sex` unused and carried as zeros; `ann_freq = 12` and
`payment_timing = advance`, so an instalment falls at the start of every month from `t = 0`;
`rechnungszins = 0.0100`, the *Höchstrechnungszins* in force for 2027 business, 1,00 % since 2025 [REG-R15];
`surplus_form = teildynamisch`; `annuity_pp_init = 0.00`, so the guaranteed annuity is **derived by
equivalence**; `duration_mth_init = 0`, so the frame opens at `t = 0`, the valuation date 1 January 2027; and
`pols_if_init = 1.0`.
Hence `horizon_mths(1) = 12 × (121 − 65) = 672`, `proj_len() = 672`, and the frame runs
`t = 0 … 671` — **672 monthly rows**, the whole of the projection.

**Assumptions, each tagged.** *Tariff.* Acquisition loading `α = 2,5 %` of the *Einmalbeitrag*
**[std]** and annuity administration loading `β = 2,0 %` of the annuity value **[std]**, so
`net_single_prem() = 97,500.00 €`. Tariff *Rechnungszins* `i = 1,00 %` [REG-R15], discounting monthly
at `v^(k/12)` with `v = 1/1.01`. *Mortality.* The table factory's `dav2004r_proxy` **[std]**: base
rates `0.008 × 1.11^(x − 65)` for men and 0.6 of them for women, trend 2,5 % a year to age 75, linear
to 1,25 % at 90 and to zero at 120, base year 2005, so the annuitant's cohort exponent at age 65 is
`1962 + 65 − 2005 = 22` and the anchor's first-year table rates are the base rates times
`(1 − 0.025)²²`; the tariff reads the `unisex_mix_male = 0.45` **[std]** blend of the two sexes, the
best estimate the own sex's rate times `mort_be_factor = 1.2` and the trend term at
`mort_be_trend_factor = 0.8` **[std]**; limiting age `omega_age() = 121`, the table's end age, with
`q = 1` at attained age 120. Monthly rates by `1 − (1 − q)^(1/12)` **[std]**. The tariff factor `ä` is computed
on the **first-order unisex** path and the projection decrements on the **second-order male** path
[REG-R34] [REG-R47]. *Surplus.* `surplus_form = teildynamisch` gives `surplus_init_pct = 10 %` and
`surplus_growth = 1,0 %` p.a. **[std]**, so the *Überschussrente* opens at a tenth of the *garantierte
Rente* and steps up 1 % at each policy anniversary, ratcheting under the *Bonusrente* mechanic [R23].
*Expenses.* Acquisition `2,0 % of prem_gross_level_pp + 200 € = 2,200.00 €` at `t = 0` **[std]**; maintenance
`60 €` a year accrued monthly on `pols_if(t)` **[std]**; `1,50 €` per instalment paid **[std]**; all
three inflating at `expense_infl = 2,0 %` p.a., stepping at the policy anniversary.
*Decrements.* Death only — no lapse, no surrender, no paid-up, no option exercise [R1] [R2] [R5].
*Tolerances.* `roll_fwd_tol()` = 1e-8 (`check_tol`, the core file `param_core.csv`); the refund solve is not exercised on this cell.

All amounts in euros; `pols_if` and the survival probabilities to six decimals, cash flows to the
cent, and every total summed **at full precision and then rounded** rather than accumulated from
rounded cells.

### The derived quantities

Everything below follows from four numbers, and the first three of them a reader can check with
a calculator.

| Quantity | Cells | Value |
|---|---|---|
| *Nettoeinmalbeitrag* `SP_net = SP (1 − α)` | `net_single_prem()` | 97,500.0000 € |
| Tariff annuity factor `ä` | `annuity_factor()` | 299.8501045469 |
| the same as the market's `a12 = ä / m` | — | 24.9875087122 |
| PV of the refund leg | `refund_pv()` | 0.0000 € — no refund elected |
| *garantierte Rente* `R = SP_net / (ä (1 + β))` | `annuity_pp_derived()` | **318.7867332531 €** per month |
| *Überschussrente* at outset `U(0) = R u₀` | `annuity_surp_pp(0)` | 31.8786733253 € |
| Total instalment at outset `A(0)` | `annuity_pp(0)` | **350.6654065784 €** per month |

So the anchor configuration buys a **guaranteed 318,79 € a month for life** per 100 000 € of
*Einmalbeitrag*, with a ten-year *Rentengarantiezeit*, and a **total 350,67 € a month at outset**
of which a tenth is the non-guaranteed *Überschussrente*.

**This is 16,4 % below the 381 € the research file's own arithmetic gives**, and the whole of the
difference is the annuity factor: `a12 = 24.9875` here against `20.897` there, `+19.6 %`, and
`1 / 1.19575 = 0.8363`. The research file computes `a12` from a **period** table on its own
Gompertz–Makeham law with `a12 = a_due − 11/24`; this model reads the table factory's
**generational** surface, so the same annuitant is priced on mortality that improves for the whole
of the fifty-six-year projection. Read as the period table of the valuation year 2027 the same
table gives `a12 = 23.3419`, `+11.7 %` over the research file — its lighter level and the monthly
summation — and the generational reading adds the remaining `+7.05 %`. That last part is the
*Trendfunktion* [REG-R49], it is one-sided, and it is the reason a period-table proxy is pitfall 8
rather than a simplification.

### The frame

672 monthly rows, `t = 0 … 671`. The table shows the first policy year in full and the first
month of the second, where the *Überschussrente* steps, then the two months either side of the
guarantee's expiry and one row every ten years to the horizon. Money
to the cent, `pols_if` to six decimals; the **Total** row is summed over all 672 rows at full
precision and then rounded.

| `t` | `pols_if` | `premiums` | `annuity_payments` | `claims_guarantee` | `claims_refund` | `expenses` | `liability_cf` | `net_cf` |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.000000 | 100,000.00 | 350.67 | 0.00 | 0.00 | 2,206.50 | −97,442.83 | 97,442.83 |
| 1 | 1.000000 | 0.00 | 350.49 | 0.18 | 0.00 | 6.50 | 357.17 | −357.17 |
| 2 | 1.000000 | 0.00 | 350.30 | 0.36 | 0.00 | 6.50 | 357.17 | −357.17 |
| 3 | 1.000000 | 0.00 | 350.12 | 0.54 | 0.00 | 6.50 | 357.17 | −357.17 |
| 4 | 1.000000 | 0.00 | 349.94 | 0.72 | 0.00 | 6.50 | 357.17 | −357.17 |
| 5 | 1.000000 | 0.00 | 349.76 | 0.90 | 0.00 | 6.50 | 357.17 | −357.17 |
| 6 | 1.000000 | 0.00 | 349.58 | 1.08 | 0.00 | 6.50 | 357.17 | −357.17 |
| 7 | 1.000000 | 0.00 | 349.40 | 1.26 | 0.00 | 6.50 | 357.17 | −357.17 |
| 8 | 1.000000 | 0.00 | 349.22 | 1.44 | 0.00 | 6.50 | 357.17 | −357.17 |
| 9 | 1.000000 | 0.00 | 349.05 | 1.62 | 0.00 | 6.50 | 357.17 | −357.17 |
| 10 | 1.000000 | 0.00 | 348.87 | 1.80 | 0.00 | 6.50 | 357.17 | −357.17 |
| 11 | 1.000000 | 0.00 | 348.69 | 1.98 | 0.00 | 6.50 | 357.17 | −357.17 |
| 12 | 1.000000 | 0.00 | 348.82 | 2.16 | 0.00 | 6.63 | 357.61 | −357.61 |
| 60 | 1.000000 | 0.00 | 339.56 | 12.73 | 0.00 | 7.18 | 359.47 | −359.47 |
| 119 | 1.000000 | 0.00 | 322.60 | 31.05 | 0.00 | 7.77 | 361.42 | −361.42 |
| 120 | 0.911197 | 0.00 | 322.56 | 0.00 | 0.00 | 7.22 | 329.78 | −329.78 |
| 121 | 0.910106 | 0.00 | 322.18 | 0.00 | 0.00 | 7.21 | 329.39 | −329.39 |
| 240 | 0.709466 | 0.00 | 253.77 | 0.00 | 0.00 | 6.85 | 260.62 | −260.62 |
| 360 | 0.307217 | 0.00 | 111.14 | 0.00 | 0.00 | 3.62 | 114.75 | −114.75 |
| 480 | 0.015585 | 0.00 | 5.71 | 0.00 | 0.00 | 0.22 | 5.93 | −5.93 |
| 600 | 0.000000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | −0.00 |
| 671 | 0.000000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | −0.00 |
| **Total** | **297.747605** | **100,000.00** | **104,170.44** | **1,633.28** | **0.00** | **4,763.63** | **10,567.35** | **−10,567.35** |

**The Total row is summed at full precision and then rounded, and here that visibly matters.**
Adding the 672 *rounded* `net_cf` cells gives **−10 567,31 €** against the **−10 567,35 €** above —
4 cents apart, because 672 half-cent roundings do not cancel. The same happens in the other
columns: `annuity_payments` accumulates to 104 170,39 € from the rounded cells against
104 170,44 € at full precision, and `expenses` to 4 763,78 € against 4 763,63 €. Any test
of this table must sum the model's own values, not the printed ones.

Reading the frame in four steps. **Month 0** takes in the whole *Einmalbeitrag*, pays the first
instalment and the acquisition expense, and is the only positive `net_cf` in the projection.
**Months 0 to 119** are inside the *Rentengarantiezeit*: `pols_if` is exactly 1.000000, and
`annuity_payments + claims_guarantee` is exactly the instalment, the split between them moving
from the annuitant to the beneficiaries as survival falls — 350,49 € against 0,18 € in month 1,
322,60 € against 31,05 € in month 119. **Month 120** is the discontinuity: the guarantee expires,
`claims_guarantee` goes to zero for the rest of the projection, and the outgo drops by almost a
tenth in one step, from 361,42 € to 329,78 €. **Months 120 to 671** are the pure *Leibrente*: the
instalment keeps rising with the *Überschussrente* while survival falls faster, so the cash flow
decays to nothing by about month 555, and survival is zero from month 565, the first of age 112.

The state behind those rows:

| `t` | `lives_if_1` | `certain_floor` | `payment_factor` | `annuity_guar_pp` | `annuity_surp_pp` | `annuity_pp` | `cum_annuity_guar_pp` |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.000000 | 1.000000 | 1.000000 | 318.79 | 31.88 | 350.67 | 318.79 |
| 11 | 0.994356 | 1.000000 | 1.000000 | 318.79 | 31.88 | 350.67 | 3,825.44 |
| 12 | 0.993845 | 1.000000 | 1.000000 | 318.79 | 32.20 | 350.98 | 4,144.23 |
| 119 | 0.912201 | 1.000000 | 1.000000 | 318.79 | 34.87 | 353.65 | 38,254.41 |
| 120 | 0.911197 | 0.000000 | 0.911197 | 318.79 | 35.21 | 354.00 | 38,573.19 |
| 240 | 0.709466 | 0.000000 | 0.709466 | 318.79 | 38.90 | 357.68 | 76,827.60 |
| 360 | 0.307217 | 0.000000 | 0.307217 | 318.79 | 42.97 | 361.75 | 115,082.01 |
| 671 | 0.000000 | 0.000000 | 0.000000 | 318.79 | 55.10 | 373.89 | 214,224.68 |

`annuity_surp_pp` is flat across `t = 0 … 11` and steps at `t = 12`, which is the anniversary rule
of pitfall 14; `payment_factor` is exactly 1 up to `t = 119` and equals `lives_if_1` from `t = 120`,
which is the certain floor of pitfall 3.

### Three independent checks

Each rebuilds a cell of the table a **different way** from the way the model builds it.

**1. The guaranteed instalment, from the annuity factor alone.** The model builds `ä` by summing
672 discounted survival-weighted payment months. A reader with the printed `ä` does one division:

    R = 97,500.00 / (299.8501045469 x 1.02) = 97,500.00 / 305.8471066379 = 318.7867332531

and in the market's own unit, `100,000 x 0.975 / (12 x 24.9875087122 x 1.02) = 318.79 €`. The
opening total instalment is then `318.7867332531 x 1.10 = 350.6654065784`, the 1.10 being
`1 + u₀` with the *teildynamisch* opening share of 10 % and the growth exponent still zero in
the first policy year (`duration(0) − D / 12 = 0`).

**2. Month 1, rebuilt from the mortality table.** The annuitant is 65 and born in 1962, so the
cohort exponent is `1962 + 65 − 2005 = 22` and the table returns the base rate `0.008` times
`(1 − tr(65))²² = 0.975²² = 0.572929976008`: `q(65, M, 1962) = 0.004583439809`. The best estimate
takes it times `mort_be_factor = 1.2` and the trend term `T = (0.98 / 0.975)²² = 1.119108308036`, so
`q⁽²⁾ = 1.2 x 1.119108308036 x 0.004583439809 = 0.006155238684`, which is `1.2 x 0.008 x 0.98²²`,
the best estimate improving at 0.8 of the table's 2,5 %; monthly,
`1 − (1 − 0.006155238684)^(1/12) = 0.000514389345`; hence

    lives_if(1) = 1 − 0.000514389345 = 0.999485610655          -> 0.999486
    annuity_payments(1) = 350.6654065784 x 0.999485610655 = 350.4850280297   -> 350.49
    claims_guarantee(1) = 350.6654065784 x 0.000514389345 =   0.1803785487   ->   0.18

and the two add back to `350.6654065784` exactly, because inside the *Rentengarantiezeit*
`payment_factor(1) = max(1, 0.999486) = 1`. The **unisex tariff rate** at the same age comes off
the same table: the woman's rate is 0.6 of the man's, `0.002750063885`, and
`0.45 x 0.004583439809 + 0.55 x 0.002750063885 = 0.003575083051`, `0.78` times the man's table
rate and 0,58082 of his best estimate.

**3. Month 0's expense and cash flow, from the parameter list.** No survival enters either:

    expenses(0)  = 0.02 x 100,000 + 200            (acquisition)
                 + 60 / 12                          (one month's maintenance, pols_if = 1)
                 + 1.50                             (one instalment run)
                 = 2,000.00 + 200.00 + 5.00 + 1.50 = 2,206.50
    net_cf(0)    = 100,000.00 − 350.67 − 0.00 − 2,206.50 = 97,442.83

and the *Kostenüberschuss* the tariff is designed to earn is visible in the same two lines: the
acquisition **loading** takes `α x SP = 2,500.00 €` and the acquisition **expense** incurred is
2 200,00 €, a 300,00 € margin at inception **[std]**.

### Two closure identities

**The decrements close.** Death is the only decrement in this product, so the whole cohort must be
accounted for by deaths plus survivors:

    sum over t = 0 … 671 of lives_death(t, 1)  =  1.000000000000
    lives_if(672, 1)                            =  0.000000000000
    total                                       =  1.000000000000  =  lives_if(0, 1)

That is `check_lives_roll_fwd()`, and it closes to the last printed digit because the rate reaches
1 at attained age 112 and forces the survival path to zero inside the `omega_age() = 121` horizon.

**The cash flow statement closes.** Summing the columns at full precision,

    100,000.0000000000            premiums
  − 104,170.4354408219            annuity_payments
  −   1,633.2778997492            claims_guarantee
  −       0.0000000000            claims_refund
  −   4,763.6318345556            expenses
  = − 10,567.3451751266           net_cf

which is the printed Total to the cent. That is `check_net_cf()` summed rather than asserted
per month.

**And a third, which is the one worth having.** Inside the *Rentengarantiezeit* the outgo does
not depend on mortality **at all**, so the first ten years of this projection can be computed in
closed form with no table:

    120 R                                            = 120 x 318.7867332531  = 38,254.4079903736
    12 R u₀ x s̈10 at 1 %,  s̈10 = (1.01¹⁰ − 1)/0.01 = 10.4622125411
                                                     = 382.5440799037 x 10.4622125411
                                                     =  4,002.2574703002
    total instalments, months 0 … 119                = 42,256.6654606738

The model's own `annuity_payments + claims_guarantee` over `t = 0 … 119` is
**42,256.6654606738 €**, agreeing to the last digit of double precision. The two errors this closes
off are large and in opposite directions. A model that decremented the guaranteed instalments for
survival — pitfall 2 — would pay only the annuitant's leg, 40 623,3875609246 €, **3,87 % below**. A
model that added the certain floor instead of taking a `max` — pitfall 3 — would pay
82 880,0530215985 €, **96,13 % above**, because it pays `1 + l_a` for the whole guarantee.

### The variant the notes promised: the same cell *nachschüssig*

Model point 9 is model point 1 with `payment_timing = arrears` and nothing else changed. The
first instalment moves from `t = 0` to `t = 1`, the guarantee window from `0 … 119` to
`1 … 120`, and the tariff factor falls from 299.8501045469 to **298.8963990879**, by 0.9537054591 — and that
difference is itself checkable in one line. Arrears does not pay the instalment at `t = 0`, worth
1; against that, its guarantee window is `1 … 120` rather than `0 … 119`, so the instalment at
`t = 120` is certain for it and survival-contingent for advance, worth
`v¹⁰ (1 − l̃(120)) = 0.9052869547 × (1 − 0.9488620258) = 0.0462945409`. The net is
`1 − 0.0462945409 = 0.9537054591`, to the last printed digit. The guaranteed instalment rises in
exactly the inverse proportion:

    319.8039039139 / 318.7867332531  =  299.8501045469 / 298.8963990879  =  1.00319076

| `t` | `pols_if` | `premiums` | `annuity_payments` | `claims_guarantee` | `expenses` | `net_cf` |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.000000 | 100,000.00 | 0.00 | 0.00 | 2,205.00 | 97,795.00 |
| 1 | 1.000000 | 0.00 | 351.60 | 0.18 | 6.50 | −358.28 |
| 2 | 1.000000 | 0.00 | 351.42 | 0.36 | 6.50 | −358.28 |
| 3 | 1.000000 | 0.00 | 351.24 | 0.54 | 6.50 | −358.28 |
| 12 | 1.000000 | 0.00 | 349.94 | 2.17 | 6.63 | −358.73 |
| 120 | 1.000000 | 0.00 | 323.59 | 31.54 | 7.92 | −363.05 |
| 121 | 0.910106 | 0.00 | 323.21 | 0.00 | 7.21 | −330.42 |
| 240 | 0.709466 | 0.00 | 254.57 | 0.00 | 6.85 | −261.43 |
| **Total** | **297.836407** | **100,000.00** | **104,151.03** | **1,670.03** | **4,762.84** | **−10,583.89** |

Three things are worth reading off it. `t = 0` carries no instalment and no instalment-running
expense — 2 205,00 € against the anchor's 2 206,50 € — so the *nachschüssig* cell's first month is
**352,17 €** better, exactly one instalment plus its 1,50 € running cost, and it pays that back
over the following fifty-six years: its undiscounted `net_cf` total is −10 583,89 € against
−10 567,35 €. The guarantee still
covers **120 instalments**, now at `t = 1 … 120` (pitfall 13). And the annuity is **0,32 % higher**,
not 5 %: see the correction recorded at the end of this section.

### The other configuration: an in-force point with a **given** annuity

A *Sofortrente* has one premium form, so the pair this model must serve is *derived* against
*given*. Model point 10 carries an annuity struck in 2012 on a 1,75 % tariff —
`annuity_pp_init = 430.00`, `duration_mth_init = 180`, `pols_if_init = 0.918857`,
`surplus_form = konstant` — and the model uses it rather than striking one. Fifteen years have run
at the valuation date 1 January 2027, so its frame opens at `t = 180` and runs to 671: **492 rows,
and no `t = 0` in them.** The 15-year *Rentengarantiezeit* covered months 0 … 179 and has just run
out, so what remains is the annuitant's survival alone and `claims_guarantee` is zero in every
row.

| `t` | `pols_if` | `premiums` | `annuity_payments` | `claims_guarantee` | `expenses` | `net_cf` |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.918857 | 0.00 | 474.13 | 0.00 | 8.04 | −482.17 |
| 181 | 0.916390 | 0.00 | 472.86 | 0.00 | 8.02 | −480.87 |
| 191 | 0.892091 | 0.00 | 460.32 | 0.00 | 7.80 | −468.12 |
| 192 | 0.889697 | 0.00 | 459.08 | 0.00 | 7.94 | −467.02 |
| 240 | 0.750921 | 0.00 | 387.48 | 0.00 | 7.25 | −394.73 |
| 360 | 0.280907 | 0.00 | 144.95 | 0.00 | 3.31 | −148.26 |
| **Total** | **126.757724** | **0.00** | **65,406.99** | **0.00** | **1,280.04** | **−66,687.03** |

`premiums` is **zero in every row** — the *Einmalbeitrag* was paid in 2012, before the valuation
date of 1 January 2027, and counting it again is pitfall 11 — and the acquisition expense appears
nowhere, which is pitfall 12. `pols_if(180) = 0.918857 = pols_if_init()`, the frame's first row
carrying `pols_if_init()` exactly, as on a new-business point: `lives_if_1(180) = 1`, the survival
path being conditional on the annuitant alive at the valuation date, and `pols_if_init()` is the
probability of that, the point's survival from 1 January 2025 rolled forward by the model over
months 156 … 179 on the basis before the switch to the table factory. It is kept as contract data
with `annuity_pp_init` and not re-rolled: on the switched basis those months give 0,946156, and the
frame from month 180 runs on the switched basis. The instalment is `430.00 + 0.20 x 430.00 = 516.00 €` and stays
there: the *konstante Überschussrente* has `surplus_growth = 0`, so nothing steps at the
anniversary and only the expense inflation index does, at `t = 192` in the table.
`check_equivalence()` returns `True` without asserting anything, the annuity having been struck on a
basis this model does not reproduce.

### And the cell with the *Überschussrente* switched off

Model point 14 is the anchor with `surplus_form = none`. It derives the **identical** guaranteed
instalment — 318.7867332531 € — which is the arithmetic statement that `ä` does not depend on
`surplus_form`, the *Überschussrente* being financed out of surplus actually earned rather than
priced into the guarantee. Everything else differs:

| Over the whole 672-month frame | point 1, *teildynamisch* | point 14, surplus off | difference |
|---|---:|---:|---:|
| `annuity_payments` | 104,170.44 | 93,442.02 | 10,728.42 |
| `claims_guarantee` | 1,633.28 | 1,475.97 | 157.31 |
| `expenses` | 4,763.63 | 4,763.63 | 0.00 |
| `net_cf` | −10,567.35 | **+318.38** | −10,885.73 |

The whole modelled *Überschussrente* is **10 885,73 €** undiscounted, and **none of it is
guaranteed**. It is also what turns the sign of the undiscounted total: on the guaranteed annuity
alone the anchor cell collects 318,38 € more than it pays out over fifty-six years, and with the
surplus it pays out 10 567,35 € more than it collects. Neither figure is an economic result — these
are undiscounted flows and the *Einmalbeitrag* arrives fifty-six years before the last of them —
but the *difference* between them is exactly the quantity the four *Überschussverwendung* forms
distribute, and pricing it is what a sensitivity on this product is for.

### Corrections made to these notes when the model was built

Seven, all in this document, none in `product-spec.md`, `sources.md` or the frozen research
file.
Each is recorded because a reader comparing an earlier draft with this one should not have to
guess which side moved.

1. **`check_net_cf`'s identity now carries the payment-month indicator.** The row in *Published
   `check_*` identities* read `net_cf(t) == premiums(t) − pols_if_init·A(t)·payment_factor(t) −
   claims(t,"REFUND") − expenses(t)`. `payment_factor(t)` is defined at every `t`, not only at
   payment months, so on a quarterly, half-yearly or annual model point the identity as written
   subtracted an instalment in months where none was paid. The annuity term is gated by
   `1{payment month}`, as the cash flows themselves already were.
2. **`check_equivalence`'s tolerance is `roll_fwd_tol` scaled by the *Nettoeinmalbeitrag*.** The
   identity is an equality between euro amounts of the order of 10⁵ and the refund solve converges
   on `R` rather than on the residual, so an unscaled 1e-8 would have been a tolerance on the
   fifteenth significant figure.
3. **The death rates are capped at 1.0.** Before the switch to the table factory the shipped
   series were capped, `SECOND = 1.20 × FIRST` exceeding 1 on the male series at ages 117 to 119.
   Since the switch the table caps its rates at 1 and `mort_rate` caps the best estimate, 1 wherever
   the table rate is 1; the cap binds from age 112 for men and 116 for women on the shipped cohorts.
4. **`lives_if` reaches zero at or before `horizon_mths(life)`, not exactly at it.** With
   `q = 1` the monthly rate is 1 in the first month of that age, so on the anchor the path reaches
   zero at age 112, 107 months inside the horizon (at age 120, eleven months inside it, on the
   files before the switch). The horizon is an upper bound; nothing depends on where inside it.
5. **The unisex anchor was exact to 2,5 × 10⁻⁷ relative** — history: it held for the file proxy
   before the switch to the table factory, whose female factor 0.795455 rounded `0.4375 / 0.55`;
   the table factory's blend is exact by construction and reproduces no research-file law.
6. **The payment-timing convention is worth 0,32 % of the annuity on this product, not 5 %.** The
   figure of about 5 % in *Key sensitivities* was carried over from `_research/sofortrente.md`
   section 8, which computes it as `ä_due − ä_arrears = 1` — the difference between an **annual**
   annuity-due and an annual annuity-immediate. On a **monthly** annuity the difference is one
   *month's* instalment, `1 / (12 a12) ≈ 1 / 299.9 ≈ 0.33 %` before the guarantee period damps it
   further. Model points 1 and 9 measure it directly at **0,32 %**, and the sensitivity list now
   says so. The research file is frozen and is not amended; the discrepancy is recorded here
   instead, and it is a real error in that file's section 8 rather than a difference of basis.

   **And the convention itself is now known to be the minority one.** The 2026-08-30 retrieval
   opened two AVB that state the first payment date for a *Sofortrente*, and both pay in **arrears**:
   NÜRNBERGER, "Die erste Rente wird einen Monat nach dem vereinbarten Versicherungsbeginn gezahlt.
   Die garantierte monatliche Rente wird an jedem Monatsersten gezahlt" [S4]; and CosmosDirekt, for
   which the first instalment on the immediate form falls "ein Jahr, ein halbes Jahr, ein viertel
   Jahr oder einen Monat nach dem vereinbarten Versicherungsbeginn" according to frequency [S6]. The
   GDV template pays "an den vereinbarten Fälligkeitstagen" and does not settle it [S1]. **The model
   keeps `payment_timing = advance` on the anchor and every other shipped point.** Changing the
   default would move the worked example, the printed identities and the golden tests together, which
   is a decision to take deliberately rather than as a side effect of a provenance pass. What changes
   here is the label: *vorschüssig* is no longer an **unestablished** convention filling a gap, it is
   a **[std]** convention that the retrieved market evidence contradicts, and model point 9 already
   carries the alternative at a measured 0,32 %. A later build that adopts `arrears` as the default
   should expect the anchor's guaranteed annuity to rise from 318,79 € to 319,80 € and every golden
   figure downstream to move with it.
7. **The *Überschussrente* total of the surplus-off comparison is formed at full precision.**
   The difference column of that table was once formed by subtracting the two **printed**
   totals, where every other total in this document is summed at full precision and then
   rounded, and on the earlier figures the two readings differed by a cent. At full precision
   the difference is `−10 567,345175 − 318,381964 = −10 885,727139`, which rounds to
   −10 885,73; on the figures since the switch to the table factory the printed totals,
   `−10 567,35 − 318,38`, give the same cent, but they need not, a half-cent in each printed
   total being enough to move the difference by one. `tests/test_sofortrente_de.py` asserts the
   full-precision figure.

---

## Valuation and reserve pointers

This library projects gross best-estimate-style liability cash flows, undiscounted, on a declared
grid. The valuation layers consume them and are **cited, not reproduced**.

- **The HGB *Deckungsrückstellung*.** A prospective, deliberately prudent reserve on the
  *Rechnungsgrundlagen erster Ordnung* of the premium calculation — this contract's own
  *Rechnungszins*, capped at conclusion by § 2 DeckRV [REG-R14] [REG-R15], and a first-order
  biometric table [REG-R47] — formed to the extent necessary to ensure *dauernde Erfüllbarkeit*
  [REG-R54]. For a *Sofortrente* it is simply the actuarial present value of the remaining guaranteed
  annuity, since there are no future premiums to deduct: the same `ä` this model computes, evaluated
  at the attained age rather than at inception. **This is the balance sheet the German surplus system
  actually operates on** — the MindZV 90/90/50 floor [REG-R18], the RfB ring fence [REG-R10], the
  RfBV ceiling [REG-R19] and the § 139 VAG *Bewertungsreserven* test [REG-R9] are all computed on the
  HGB accounts, not the Solvency II ones.
- **The *Zinszusatzreserve*.** Where the § 5 Abs. 3 DeckRV *Referenzzins* falls below the contract's
  tariff rate, an additional HGB reserve arises [REG-R17]. It bites hardest on long-duration annuity
  business and on legacy cohorts: a model point written in 2012 at 1,75 % carries a very different ZZR
  from one written in 2027 at 1,00 %, which is one reason the shipped table carries both vintages. The
  ZZR is **not computed here**, and its release profile is the largest single driver of what a cohort
  of annuitants will actually be credited [REG-R17].
- **Solvency II best estimate.** Probability-weighted future cash flows discounted at the relevant
  risk-free term structure, plus a risk margin [REG-R1] [REG-R2] [REG-R6], with EIOPA publishing the
  curves [REG-R4]. `BEL = Σ_t v(t) × liability_cf(t)` over the recursions above. **No risk-free rate,
  cost-of-capital rate, contract-boundary rule or standard-formula shock in this library was read from
  a retrieved instrument**, so every such figure is **[std]** [REG-R2].
- **The contract boundary is not an open question on this product**, and that is worth saying because
  it is one on most of the others. A *Sofortrente* has a single premium already paid and no
  unilateral right on either side to alter or terminate the contract [R1] [REG-R28], so the whole
  projected stream sits inside the boundary. The one qualification is the *Aufschubzeit* variant,
  where a pre-*Rentenbeginn* surrender right may exist [R1] [R2] and no carrier's terms were
  established (research gap 17).
- **Longevity risk in the standard formula.** The life underwriting module's longevity shock is a
  permanent reduction in mortality rates, and it bites on this product harder than on any other in
  the library, there being no offsetting death benefit beyond a refund that *shrinks* as the annuity
  is paid. **No shock parameter was read from a retrieved instrument** [REG-R2].
- **IFRS 17.** Fulfilment cash flows plus a contractual service margin, effective for financial years
  beginning on or after 1 January 2023 [REG-R55]; a *Sofortrente* with an *Überschussbeteiligung* is
  a direct-participating contract and would fall under the Variable Fee Approach. The same
  expected-cash-flow engine feeds it; grouping, CSM, risk adjustment and coverage units are out of
  scope, and no delib model produces a CSM.

---

## Key sensitivities and model risks

In rough order of leverage for a German payout-annuity block:

1. **The mortality basis, in both dimensions.** This is a pure longevity bet and the basis is a
   **[std]** proxy, because DAV 2004 R is not public [REG-R47] [REG-R49]. Two numbers with no observed
   range decide most of the answer: the **level margin** (`mort_be_factor = 1.2`) and the **trend
   margin** (`mort_be_trend_factor = 0.8`), and behind both the table's own level and trend. On the
   anchor's tariff a 25 % heavier level lowers `ä` by 5,2 % and the survival from 65 to 90 by 8,6 %;
   a trend 25 % weaker lowers them by 3,8 % and 6,8 %. The trend compounds with the distance from the
   base year 2005, so it weighs more on later cohorts: born 1990, the same two changes lower `ä` by
   4,3 % and 5,0 %. A user substituting a real table must replace the **surface**, not the level.
2. **The *Überschussrente* assumption.** On the anchor cell the *Überschussrente* opens at 10 % of the
   guaranteed annuity and grows 1 % a year, so by the twentieth policy year it is running at
   materially more than a tenth of the payment — and **none of it is guaranteed** [R21]. Two stresses
   matter and neither is in the base run: the constant form being reduced, which the consumer
   literature says happens when the insurer earns less than projected [R21]; and the ZZR release
   working the other way [REG-R17]. A model projecting a flat surplus rate has taken a view.
3. **The tariff *Rechnungszins* and the vintage.** On the [std] basis the 0,25 % → 1,00 % step is
   worth about +10 % on the guaranteed annuity at age 65 (`product-spec.md`, *Rentenhöhe*). Model
   points 1 and 13 differ in almost nothing else, so the pair isolates the effect; **the magnitude is
   constructed, not observed** (research gap 5).
4. **The payment timing convention.** *Vorschüssig* is **[std]** and unestablished (research gap 11).
   Model points 1 and 9 are the same cell under the two conventions and measure the difference at
   **0,32 %** of the guaranteed annuity — `319.8039039139 / 318.7867332531`. That is **not** the
   "about 5 %" of `_research/sofortrente.md` section 8, which computes the gap as
   `ä_due − ä_arrears = 1`: true of an **annual** annuity, and twelve times too large for a monthly
   one, where the gap is one *month's* instalment. The research file is frozen and is not amended;
   the correction is recorded in the worked example above. The convention still matters — it shifts
   every payout cash flow by a month and moves the first month's `net_cf` by the whole instalment —
   but it is not the largest assumption in the model, and treating it as such would misdirect a
   sensitivity programme.
5. **The *Kapitalrückgewähr* solve.** Model point 3's guaranteed annuity is about 12 % below the plain
   life annuity on the [std] basis, and the reduction is sensitive to the interest rate in a way the
   plain annuity is not, because the refund is a *death* benefit discounted from an earlier date than
   the annuity payments it displaces. It is also the only place in the model where a numerical solve
   sits inside the pricing, so a change of its tolerance, 1e-10, is a change of answer, not of runtime.
6. **The second life and the independence assumption.** The *Hinterbliebenenrente* is priced with both
   lives independent **[std]**; real joint lives are positively dependent, so the model **overstates**
   the joint-life annuity value and understates the cost of the rider. No delib source quantifies the
   dependence.
7. **`unisex_mix_male` and the unisex tariff.** The realised portfolio mix drives the *Risikoergebnis* the
   MindZV then shares [REG-R18] [REG-R34], and `ρ_M = 0.45` is a direction with no magnitude behind
   it. It moves the tariff annuity factor directly, so it moves every derived annuity in the table.
8. **Expense levels on small tickets.** At model point 11's 25 000 € the [std] acquisition expense of
   `2,0 % + 200 €` is 700 € against a monthly annuity of about 191 €, and the fixed
   per-instalment cost is a materially larger share of the payment than at 100 000 €. That is the
   arithmetic behind the minimum *Einmalbeitrag*, and it means the per-policy expense assumption —
   not mortality — decides whether a small cell is viable.
9. **What is deliberately absent, and would change the answer.** The *Bewertungsreserven* share [S3]
   [REG-R24]; a commuted *Restgarantiezeit* settlement (research gap 10); a reduction of a declared
   *Überschussrente* [R21]; and any *Rentenanpassung* actually observed, of which the corpus contains
   **no specimen at any carrier for any year** [S15] (research gap 16). Each is named here so that a
   reader knows the projection's silence about it is a decision rather than an oversight.

<!-- BEGIN generated citation links -- regenerate with tools/gen_citation_links.py -->
[R1]: #delib-sofortrente-r1
[R10]: #delib-sofortrente-r10
[R19]: #delib-sofortrente-r19
[R2]: #delib-sofortrente-r2
[R20]: #delib-sofortrente-r20
[R21]: #delib-sofortrente-r21
[R22]: #delib-sofortrente-r22
[R23]: #delib-sofortrente-r23
[R4]: #delib-sofortrente-r4
[R5]: #delib-sofortrente-r5
[REG-R1]: #delib-reg-r1
[REG-R10]: #delib-reg-r10
[REG-R14]: #delib-reg-r14
[REG-R15]: #delib-reg-r15
[REG-R17]: #delib-reg-r17
[REG-R18]: #delib-reg-r18
[REG-R19]: #delib-reg-r19
[REG-R2]: #delib-reg-r2
[REG-R24]: #delib-reg-r24
[REG-R27]: #delib-reg-r27
[REG-R28]: #delib-reg-r28
[REG-R34]: #delib-reg-r34
[REG-R4]: #delib-reg-r4
[REG-R41]: #delib-reg-r41
[REG-R47]: #delib-reg-r47
[REG-R49]: #delib-reg-r49
[REG-R52]: #delib-reg-r52
[REG-R54]: #delib-reg-r54
[REG-R55]: #delib-reg-r55
[REG-R6]: #delib-reg-r6
[REG-R8]: #delib-reg-r8
[REG-R9]: #delib-reg-r9
[std]: #delib-std
[unverified]: #delib-unverified
<!-- END generated citation links -->
