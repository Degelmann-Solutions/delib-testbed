# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The by-policy projection of the :mod:`~.KLV_DE_S` model.

The Space is parameterized by ``point_id``, so ``Projection[1]`` is an ItemSpace
projecting model point 1::

    >>> Projection[1].result_cf()          # the worked example's anchor cell
    >>> Projection.point_id = 8            # or switch the default

``t`` counts **policy months, 0-based and measured from issue**: month ``t`` runs from time
``t`` to time ``t + 1``, so ``t = 0`` is the first policy month and the frame runs
``t = t_start() ... proj_len() - 1`` contiguously, with ``t_start() = 12 * duration_init()``
and ``proj_len() = 12 * policy_term()`` — 300 on the anchor cell — the frame's **exclusive**
end. The *Ablauf* falls at the end of the last month. **There is no ``t = proj_len()`` row.**

.. rubric:: Two clocks, and which cells carries which

**A monthly grid is not a monthly product, and on this one almost nothing is monthly.** The
whole *Überschussbeteiligung* is an annual statement — the *laufende Verzinsung* is declared
for a *Versicherungsjahr*, the *Schlussüberschussanteilsatz* accrues on that year's closing
*Deckungskapital*, the *Ansammlungszins* is an annual rate — and so is everything the tariff
defines: an annual *Rechnungszins*, an annual first-order table, a Fackler roll-forward from
one anniversary to the next, the § 169 Abs. 3 five-year spreading, the *Beitragsfreistellung*
election at the end of a *Versicherungsperiode*. None of that becomes monthly. What the finer
grid resolves is everything that is **not** contractually annual: the *Beitrag* the contract
bills in instalments, the insurer's running expense, and the decrements, which now fall in
the month they happen and are paid the balances standing at the last anniversary.

So the argument of a cells says which clock it is on:

* cells that state an **annual account** take ``k``, the 0-based policy year — the whole
  pricing block, :func:`res_net_pp`, :func:`res_zill_pp`, :func:`res_min_pp`, :func:`res_pp`,
  :func:`res_pp_at`, :func:`res_guar_pp`, :func:`pu_single_prem`, :func:`is_paid_up`,
  :func:`bfz_uplift_pp`, :func:`decl_rate`, :func:`term_rate`, :func:`ans_rate`,
  :func:`surplus_base_pp`, :func:`surplus_credit_pp`, :func:`av_sur_pp`, :func:`term_bonus_pp`,
  :func:`bonus_si_pp`, :func:`prem_rebate_pp`, :func:`prem_pp`, :func:`prem_paid_pp`
  and :func:`stornoabzug_rate`;
* cells that state a **month** take ``t`` — the in force, the claims, the instalments, every
  ``result_cf()`` column, the expense inflation :func:`inflation_factor`, and the ``*_close_pp`` cells that say what a mid-month exit is paid;
* the **decrement rates take ``t`` and return the year's annual rate**, which is the
  library-wide convention and is not the same thing as an annual statement.

``duration(t) = t // 12`` is the bridge: it is the completed policy years at the start of
month ``t``, and it is what a month resolves to when it reaches an annual cells.
``policy_year(t) = duration(t) + 1`` is the contractual 1-based label the input tables are
keyed on, ``age(t) = age_y(duration(t))`` steps on the anniversary, and
``is_anniv(t) = (t % 12 == 11)`` marks the month the annual machinery acts in. The frame is
indexed by ``t``; the policy year is derived and never indexed by.

The two-speed structure that follows is the library's convention: :func:`mort_rate` and
:func:`lapse_rate` are the **annual** rates of the policy year containing month ``t`` — the
vectors the technical notes tabulate — and :func:`mort_rate_mth` and :func:`lapse_rate_mth`
are the monthly rates actually applied, each ``1 - (1 - r)^(1/12)``, so that twelve of them
compound back to exactly the year's rate. That is what leaves the annual layer untouched:
``pols_if(12k)`` here is the annual-step model's own ``pols_if(k)``, so every reserve, every
declared credit and every ledger balance is the same number on the two grids.

.. rubric:: Input data

Inputs are **external files**: plain CSVs living in the model folder's parent directory,
``products/kapitallebensversicherung/``, read at run time rather than stored inside the
model. The model folder therefore holds nothing but formulas — no ``_data/``, no IOSpec, no
embedded values — so a diff of the model shows logic changes only, and an input can be
edited or swapped without rewriting the model. This follows ``annuallife.TradLife_A``;
contrast ``basiclife.BasicTerm_S``, which keeps its inputs *inside* the model through
modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``KLV_DE_S`` folder without its parent's CSVs produces a model that reads and then fails on
first evaluation.

Each table has a filename Reference and a reader Cells, both on :mod:`~.KLV_DE_S.Data`,
reached here through the ``data`` Reference:

========================  =================================  ==========================
Reference                 Cells                              File
========================  =================================  ==========================
model_point_file          data.model_point_table()           model_point_table.csv
mort_file                 data.mort_table()                  mort_table.csv
lapse_file                data.lapse_table()                 lapse_table.csv
surplus_rate_file         data.surplus_rate_table()          surplus_rate_table.csv
charge_file               data.charge_table()                cost_table.csv
prem_freq_file            data.prem_freq_table()             prem_freq_table.csv
deckrv_file               data.deckrv_table()                deckrv_table.csv
param_file                data.param()                       param_tariff_type.csv
========================  =================================  ==========================

.. rubric:: Naming

Cells names follow lifelib's ``basiclife.BasicTerm_S`` and ``savings.CashValue_SE``
wherever those models have an analogue — ``pols_*`` for policy counts, plural nouns for
cash flows, ``*_rate`` for rates, ``*_pp`` for per-policy amounts, ``claims(t, kind)`` with
an uppercase ``kind`` string, ``*_at(t, timing)`` for the within-year reads. The technical
notes use compact actuarial symbols instead. The mapping is:

==================  =====================================  ====================================
Notes symbol        Cells                                  Meaning
==================  =====================================  ====================================
(none)              model_point()                          The selected model point row
n                   proj_len_y()                           Policy years = policy_term
12 n                proj_len()                             Projected months; frame end
(none)              t_start()                              First projected month index
(none)              k_start()                              First projected policy year
m                   prem_term()                            Beitragszahlungsdauer
(none)              duration_mth(t)                        Completed policy months, = t
k                   duration(t)                            Completed policy years, t // 12
(none)              is_anniv(t)                            Last month of a policy year
x(t), x(k)          age(t), age_y(k)                       Attained age, on each clock
y(t) = k + 1        policy_year(t)                         Contractual 1-based policy year
SE                  sum_assured()                          Guaranteed Erlebensfallleistung
SD                  sum_death()                            Guaranteed Todesfallleistung
i1                  rechnungszins()                        First-order interest rate
v1^k                disc_factor(k)                         First-order discount factor
kpx                 pols_tariff(k)                         First-order survival from issue
q1(x)               mort_rate_tariff_at_age(x)             First-order tariff rate at age
                                                           x - the unisex blend, which
                                                           prices and reserves
(table)             mort_rate_at_age(x)                    Sex-specific table rate at age x
(table)             mort_rate_base(t)                      Sex-specific annual table rate
q(t)                mort_rate(t)                           Best-estimate annual mortality
qm(t)               mort_rate_mth(t)                       The same, applied in month t
f                   rating_factor()                        Risikozuschlag on the death leg
alpha, beta, gamma  alpha_rate(), load_admin_prem_inst(),  Zillmersatz; premium loading;
                    load_admin_sum_ann()                   sum-insured loading
phi                 prem_freq_load()                       Ratenzahlungszuschlag
(none)              instalments()                          Payments a year
(pricing)           tariff_death_pv(),                     The equivalence's parts
                    tariff_maturity_pv(),
                    tariff_benefit_pv(), tariff_annuity(),
                    tariff_term_annuity()
B                   prem_gross_level_pp()                  Annual Bruttobeitrag before phi
BS                  beitragssumme()                        Beitragssumme = B x m
A                   zillmer_amount()                       Zillmered acquisition cost
P^n                 prem_net_level_pp()                    Net level premium
P^Z                 prem_zill_pp()                         Zillmer premium
(prospective)       pv_benefit_fut(k),                     The reserve's parts
                    ann_due_prem_fut(k)
V^n, V^Z, V^min     res_net_pp(k), res_zill_pp(k),         The three constructions
                    res_min_pp(k)
V(k)                res_pp(k)                              Deckungskapital at start of year k
(within year)       res_pp_at(k, timing)                   BEF_PREM / AFT_PREM / AFT_INT
G(k)                res_guar_pp(k)                         Section 169 value at end of year k
(closing)           res_guar_close_pp(t)                   The same, standing at end of month t
RK(t)               surr_value_pp(t)                       Rueckkaufswert payable in month t
(unit paid-up)      pu_single_prem(k)                      Single premium for one unit
(none)              bfz_si_pp()                            Beitragsfreie Versicherungssumme
(none)              bfz_uplift_pp(k)                       Section 169 uplift on election
(none)              is_paid_up(k)                          Whether the contract is beitragsfrei
(none)              bfz_fails()                            Whether the election became a surrender
d(k)                decl_rate(k)                           Declared laufende Verzinsung
z(k)                zins_ueberschuss_rate(k)               Interest surplus rate
s(k)                term_rate(k)                           Schlussueberschussanteilsatz
a(k)                ans_rate(k)                            Ansammlungszinssatz
(base)              surplus_base_pp(k)                     Deckungskapital at allocation
C(k)                surplus_credit_pp(k)                   Surplus allocated for year k
S(k)                term_bonus_pp(k)                       Accrued Schlussueberschussanteil
(closing)           term_bonus_close_pp(t)                 The same, standing at end of month t
U(k)                av_sur_pp(k)                           Ueberschussguthaben per policy
(within year)       av_sur_pp_at(k, timing)                BEF_INT / AFT_INT / AFT_CREDIT
(closing)           av_sur_close_pp(t)                     The same, standing at end of month t
(aggregate)         av_sur(k), av_sur_at(k, timing)        The same, times pols_if(12k)
Z(k)                bonus_si_pp(k)                         Bonus sum insured
(closing)           bonus_si_close_pp(t)                   The same, standing at end of month t
(offset)            prem_rebate_pp(k)                      Beitragsverrechnung offset
B phi               prem_pp(k)                             Annual Zahlbeitrag before the offset
(none)              prem_paid_pp(k)                        Annual Zahlbeitrag after it
(none)              prem_cycle(), prem_due(t)              The instalment cycle
(none)              prem_charged_inst_pp(t)                Instalment charged in month t
(none)              prem_inst_pp(t)                        Instalment collected in month t
(none)              premiums(t)                            Premium income in month t
w(t)                lapse_rate(t)                          Annual surrender rate of the year
wm(t)               lapse_rate_mth(t)                      The same, applied in month t
sigma(k)            stornoabzug_rate(k)                    Stornoabzug rate
l(t)                pols_if(t)                             In force at the start of month t
(within month)      pols_if_at(t, timing)                  BEF_DECR / AFT_DEATH / AFT_DECR
(exits)             pols_death(t), pols_lapse(t),          Expected exits in month t
                    pols_maturity(t)
(none)              benefit_full_pp(t)                     Full death benefit before 161
(none)              benefit_death_pp(t)                    What a death claim pays
(none)              benefit_maturity_pp(t)                 What the Ablauf pays
RK(t)               benefit_lapse_pp(t)                    surr_value_pp(t), per lapse
(none)              claim_kinds()                          DEATH / MATURITY / LAPSE
claims_*            claims(t, kind)                        DEATH / MATURITY / LAPSE
(none)              expense_infl()                         Its rate, the core item, 2 %
(none)              inflation_factor(t)                    Expense inflation factor
(none)              claim_expenses(t)                      Claim handling expense
(none)              expenses_pp(t)                         Per-policy expense in month t
(none)              expenses_maint(t)                      expenses_pp(t) x pols_if(t)
(none)              expenses_claim(t)                      claim_expenses(t)
E(t)                expenses(t)                            Expense outgo, no commission
(none)              comm_init_rate()                       Initial rate on the Beitragssumme
(none)              comm_renew(t)                          Bestandsprovision
(none)              commissions(t)                         Commission outgo
net_cf(t)           net_cf(t)                              Net cash flow, income positive
liability_cf(t)     liability_cf(t)                        The same stream, outgo positive
(the notes' table)  result_cf_annual()                     result_cf() summed by policy year
==================  =====================================  ====================================

.. rubric:: The declared rate is a total, not an add-on

The single most common way to get this product wrong. The *laufende Verzinsung* **is** the
*Garantieverzinsung* plus the *laufende Zinsüberschussbeteiligung*, so

    zins_ueberschuss_rate(k) = max(0, decl_rate(k) - rechnungszins())

is 1,70 pp on the anchor cell's 2,70 % declaration against a 1,00 % guarantee, and never
2,70 pp on top of 1,00 pp. The interest-surplus rate is **derived and never an input**. The
outer ``max`` is what keeps the ``nil`` scenario honest: the declared rate is then below the
guarantee, which the reserve roll-forward still meets in full, so the surplus is zero rather
than negative.

The base it multiplies is the ***Deckungskapital* at the allocation date** —
``max(res_pp_at(k, "AFT_INT"), 0)`` — not the sum insured and not the premium. That inner
``max`` is equally load-bearing: a *gezillmerte Deckungskapital* is **negative** for the
first several years, and a positive rate on a negative base credits a negative surplus. It
follows that a *gezillmert* contract earns **no** interest surplus in its early years even
though the § 153 VVG entitlement runs from inception — economically right, because there is
no fund to earn on, and worth saying because it looks like a bug.

.. rubric:: Three reserves, and the one the customer gets

:func:`res_zill_pp` is the *gezillmerte Deckungskapital*: it is exactly ``-zillmer_amount()`` at
issue and stays negative for several years. :func:`res_min_pp` is the § 169 Abs. 3 VVG floor,
the same net reserve with the acquisition cost amortised **straight-line over the first five
contract years** rather than over the whole premium term. Because
``ann_due_prem_fut(k) / tariff_annuity()`` falls roughly linearly over ``m`` years while
``max(0, 1 - k/5)`` reaches zero after five, the floor **normally binds** on a long
*gezillmert* contract, with equality only at durations 0 and ``m``. :func:`res_guar_pp` is
their maximum, floored at zero, struck at the **end** of policy year ``k`` because that is
what "zum Schluss der laufenden Versicherungsperiode" requires — so it reads the reserves at
``k + 1``. What a surrender in a *non*-anniversary month is paid is
:func:`res_guar_close_pp`, the value struck at the **last** anniversary.

With ``zillmer_on = 0`` (model point 13) ``zillmer_amount()`` is zero, all three coincide and the
floor is slack — a useful invariance test. With ``prem_term = 1`` (model point 2) the 25 ‰
*Zillmersatz* buys almost nothing and the floor is slack from the first anniversary. Both are
the correct answer rather than a degenerate case.

Note that the acquisition cost is in the **premium** whether or not the contract is
zillmered: ``zillmer_on`` enters :func:`zillmer_amount`, which is a *reserving* quantity, and not
the pricing equation, which always charges ``alpha_rate() * beitragssumme()``. That is why one
insurer can publish a *gezillmerte* and a non-*gezillmerte* edition of the same tariff at the
same price.

.. rubric:: Paid-up is not lapse, and it can fail

§ 165 VVG lets the policyholder demand conversion to a *prämienfreie Versicherung* at the end
of the current *Versicherungsperiode*, **provided the agreed *Mindestversicherungsleistung* is
reached**. The paid-up sum is bought with the § 169 value, so, writing ``e = bfz_year() - 1``
for the 0-based index of the election year, ``bfz_si_pp() = res_guar_pp(e) /
pu_single_prem(e + 1)``, and the contract
stays in ``pols_if`` with that reduced sum in place of ``sum_assured()``. Where the sum falls
short of ``bfz_min_sum``, the statute obliges the insurer to pay the § 169 value instead and
**the election becomes a surrender**: :func:`lapse_rate` returns 1.0 for that year and
:func:`lapse_rate_mth` places the whole of it in the year's **last month**, where the election
falls. The cohort leaves there as ``claims(t, "LAPSE")`` and every later row is zero. Model
point 11 takes the first branch and model point 12 the second.

Placing that 1.0 is the one decrement decision the monthly grid forced. Spreading an annual
rate of 1.0 geometrically would put the whole cohort out in the election year's **first**
month, eleven months before the election it models; the election is an act at the end of a
*Versicherungsperiode*, so it is a month-specific event and :func:`lapse_rate_mth` says so.

Because the § 169 floor generally exceeds the Zillmer reserve, the paid-up sum bought is worth
more than the Zillmer reserve released. :func:`bfz_uplift_pp` is that difference, discounted
to the start of the election year, and it enters :func:`res_pp_at` so that
:func:`check_res_roll_fwd` still closes in the election year rather than being switched off
there.

.. rubric:: What surrender pays, and what it does not

A surrender at the end of month ``t``, in the policy year ``k = duration(t)``, pays::

    surr_value_pp(t) = res_guar_close_pp(t) x (1 - stornoabzug_rate(k))
                       + av_sur_close_pp(t)
                       + term_surr_share x term_bonus_close_pp(t)

where the ``*_close_pp`` cells return the balance **standing at the end of that month**: the
year's own closing figure in an anniversary month, and the one struck at the **last**
anniversary in the other eleven. On a *gezillmert* contract that makes the guaranteed leg
exactly **zero through the whole first policy year** — the consumer fact this product is best
known for, and one the annual grid could not express, having paid a month-0 surrender the
value the coming anniversary would close at.

Four rules ride on that line. The ***Stornoabzug* bites on the guaranteed value only** — the
published deduction is a percentage of the *Deckungskapital* — so the accumulated
*Überschussguthaben* passes through undeducted. ``term_surr_share = 0`` in the base run: the
accrued *Schlussüberschussanteil* is paid at the *Ablauf* and on death and **not** on
surrender, which is the choice that does not invent an entitlement the sources do not
describe; the parameter is exposed rather than hard-coded. And the surrender value is what a
suicide inside three years is paid: § 161 VVG makes the insurer *leistungsfrei* **and**
obliges it to pay the *Rückkaufswert* including *Überschussanteile*, so the German rule is a
benefit **substitution** and not a forfeiture. And the *Stornoabzug* band is a **policy-year**
band: it steps on the anniversary, not monthly.

.. rubric:: The two mortality bases must not be crossed

:func:`mort_rate_tariff_at_age` is the first-order **tariff** rate: it prices and it reserves, and
it is a fixed unisex blend of the two table rows, because German new business has been unisex
since 21 December 2012. :func:`mort_rate_base` is this policy's own **sex-specific** table
rate, and :func:`mort_rate` is ``mort_rate_base(t) * mort_be_factor`` with
``mort_be_factor = 0.75``: it projects. The 33 % wedge is the *Sicherheitszuschlag*, whose systematic release **is** the
*Risikoüberschuss* — which this model does not compute, and which a model that reserves on
the best estimate has thrown away. ``rating_factor`` is a third thing again: it is the
*Risikozuschlag*, and it multiplies the first-order rate **in the death leg of the pricing and
the prospective reserve only** — never the survivorship factors, never the benefit, and never
a best-estimate rate. ``sex`` reaches :func:`mort_rate_base`, and therefore the
**decrement**, and it reaches nothing else: ``prem_gross_level_pp()`` is identical for two model
points differing only in it, which is what model points 1 and 7 exist to make visible. The
unisex blend behind the tariff is **[std]** - no German insurer publishes the portfolio mix
behind its own.

.. rubric:: The three Überschussverwendung systems

``ansammlung`` accumulates the credit at ``ans_rate`` in :func:`av_sur_pp` and raises the maturity
benefit; ``bonus`` buys paid-up sum insured at first-order rates in :func:`bonus_si_pp`,
raising the **death** benefit immediately by the full bonus sum but accumulating only at
``rechnungszins``; ``beitragsverrechnung`` carries last year's credit forward as this year's
premium offset in :func:`prem_rebate_pp` and neither balance grows. Because
``ans_rate > rechnungszins`` the first gives a higher maturity benefit and the second a higher
death benefit — exactly the asymmetry the sources record, and the test that distinguishes
them. A model that sets the two rates equal destroys it.

Under ``beitragsverrechnung`` the **renewal commission is charged on
:func:`prem_pp`, not on :func:`prem_paid_pp`**: the intermediary is paid on the tariff
premium, the surplus offset being a policyholder rebate.

.. rubric:: Modules that are off in the base run

Two dynamic lapse constructions are specified and not built, so the base run reproduces the
worked example; their unread switches are removed. **Premium-shock lapse**, ``beta_shock = 0``:
``1 + beta_shock * max(0, prem_paid_pp(k)/prem_paid_pp(k-1) - 1 - 0.05)`` on the **annual**
*Zahlbeitrag* of consecutive policy years, inert on a level *Bruttobeitrag* but live under
*Beitragsverrechnung*, where a fall in the declared rate raises the *Zahlbeitrag*.
**Rate-gap lapse**, ``lapse_gap_a = 0``:
``lapse_gap_a * max(0, ref_rate - decl_rate(k) - 0.005)``, keyed on the gap between the
declared rate and what is available elsewhere. Both compare **annual** declarations, which is
what they are about; neither becomes a monthly comparison. **No German calibration of any of these numbers
exists**, which is why neither is built. ``bwr_rate = 0``, a row of *param_tariff_type.csv*,
switches off the *Beteiligung an den Bewertungsreserven*, on the reasoning that the
*Sicherungsbedarf* has routinely exhausted the half share.

.. rubric:: Sign convention

:func:`net_cf` is **income positive** — *Beiträge* in, claims, expenses and commission out —
which is the notes' own orientation and the library-wide sign. :func:`liability_cf` publishes
the same stream outgo-positive, ``liability_cf(t) = -net_cf(t)`` exactly. Both are columns of
:func:`result_cf`, so the identity is verifiable in the frame rather than only in prose.
:func:`expenses` **excludes** commission — the deliberate difference from the frlib chassis,
where commission sits inside the expense column — so the six flow columns of
:func:`result_cf` sum to :func:`net_cf` without a double count. That sum is what
:func:`check_net_cf` asserts, and it is this library's first ruling.

The shape to expect on the anchor cell, read on :func:`result_cf_annual`, is a first year that
very nearly washes - the *Beitrag* of 2 004,04 € almost exactly meeting the initial commission
of 2,5 % of the *Beitragssumme* plus the 300 € acquisition expense - then annual margins of
the order of a thousand euros that decay as the cohort lapses, and a single very large
negative year at the *Ablauf* when the *Erlebensfallleistung* and the whole accumulated
*Überschussguthaben* fall due together. The new-business strain of a *gezillmert* German
endowment sits in the **reserve**, which opens at ``-zillmer_amount()``, and not in the cash flow.

.. rubric:: What the monthly grid changes, and what it does not

**Nothing annual moved, and that is checkable rather than asserted.** Because the monthly
decrement rates compound back to their policy year's annual values,
``[(1 - qm)(1 - wm)]^12 = (1 - q)(1 - w)``, the in force at every anniversary is the
annual-step recursion term for term. So ``prem_gross_level_pp()`` is **bit-identical**, and so is
every one of the three reserves at every duration, the § 169 value, the *Beitragssumme*, the
Zillmer cost, the declared credit, the *Ansammlung* balance, the bonus sum, the accrued
terminal share and the paid-up sum the § 169 value buys. The equivalence, the Fackler
roll-forward and the surplus ledgers are all **policy-year identities** and are checked as
such.

What the finer grid changes is the **cash flows**, and each change is a decision:

- a *Beitrag* is collected in instalments on the *Zahlweise*'s own cycle
  (:func:`prem_cycle`, :func:`prem_due`, :func:`prem_inst_pp`), so the four fractionated model
  points collect less than the annual grid charged them — and the ``echt`` / ``unecht``
  distinction of :func:`unterjaehrig_form`, which on an annual grid lived entirely in a
  multiplier, is now a difference in the frame;
- a death, surrender or *Ablauf* falls at the end of the **month** of exit and is paid the
  balances standing **then** (:func:`av_sur_close_pp` and the three cells beside it), so on a
  *gezillmert* contract a surrender in the first policy year is paid the *Überschussguthaben*
  and nothing guaranteed. The annual grid had to pay it the value the coming anniversary would
  close at, which is a forward-looking payment at a date it is not yet due;
- a twelfth of the maintenance expense accrues each month on that month's in-force rather than
  on the anniversary's, so a decrementing block costs less;
- the renewal commission follows the instalment it is charged on.

On the anchor cell that is death claims 2 506,85 → 2 446,09 €, surrender claims
10 104,99 → 9 112,99 €, expenses 1 348,20 → 1 334,17 € and ``net_cf`` −11 068,63 →
−10 001,84 €, with ``premiums`` and the *Ablauf* payment unchanged.
:func:`result_cf_annual` sums the frame into policy years so the two can be laid side by side,
and :func:`result_surplus` stays annual because what it publishes moves once a year.
"""

from modelx.serialize.jsonvalues import *

_formula = lambda point_id: None

_bases = [
    ".CoreProjection"
]

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

# --- the model point -------------------------------------------------------

def death_ratio():
    """The *Todesfallleistung* as a multiple of the *Erlebensfallleistung*.

    1.00 is the *gemischte Versicherung auf den Todes- und Erlebensfall* proper, where the two
    guaranteed sums are equal.  Below 1 the contract is the same chassis with an unequal death
    sum, subject to the *Mindesttodesfallschutz*: for a contract concluded from 1 April 2009
    the death sum must be at least 50 % of the *Beitragssumme*, which is a **model point
    design constraint** checked when the table is built and not a model formula.
    """
    return float(model_point()["death_ratio"])


def unterjaehrig_form():
    """Whether a sub-annual premium is ``echt`` or ``unecht``.

    ``unecht`` means the *Versicherungsperiode* remains the year and the sub-annual payment is
    an **instalment** of an annual premium, which is what the *Ratenzahlungszuschlag*
    compensates.  ``echt`` means the period is genuinely sub-annual, and then **no loading
    applies**.  Model points 4 and 5 are the same monthly contract under the two readings, and
    the distinction is entirely lost on a model that treats frequency as a single multiplier.
    """
    v = model_point()["unterjaehrig_form"]
    if v not in ("echt", "unecht"):
        raise ValueError("invalid unterjaehrig_form")
    return v


def zillmer_on():
    """1 where the *Deckungskapital* is *gezillmert*, 0 where it is not.

    A **per-tariff design choice a German insurer makes and publishes** - one carrier
    maintains a *gezillmerte* and a non-*gezillmerte* edition of the same tariff - and not an
    invariant of German practice.  It enters :func:`zillmer_amount` and therefore the *reserve*;
    it does **not** enter the pricing equation, so the two editions cost the same.

    Override reason: the *Zillmerung* is a per-tariff choice read from the model point,
    products/kapitallebensversicherung/technical-notes.md:144
    """
    return int(model_point()["zillmer_on"])


def cost_id():
    """The key into *cost_table.csv* naming this policy's loadings and expense basis."""
    return model_point()["cost_id"]


def surplus_use():
    """The *Überschussverwendung*: ``ansammlung``, ``bonus`` or ``beitragsverrechnung``.

    *Verzinsliche Ansammlung* accumulates the credit in :func:`av_sur_pp` at ``ans_rate``; the
    *Bonussystem* buys paid-up sum insured in :func:`bonus_si_pp` at first-order rates; the
    *Beitragsverrechnung* carries the credit forward as next year's premium offset.  Because
    ``ans_rate > rechnungszins``, the first pays more at maturity and the second more on an
    early death - the asymmetry the corpus records and pitfall 15 asserts.
    """
    v = model_point()["surplus_use"]
    if v not in ("ansammlung", "bonus", "beitragsverrechnung"):
        raise ValueError("invalid surplus_use")
    return v


def av_sur_pp_init():
    """The *Überschussguthaben* per policy carried at ``t_start()``, in euros.

    Zero for new business; model point 10 opens at duration 14 with 6 000 € already
    accumulated.  It is **not** part of the *Deckungsrückstellung*: § 341f HGB forms that
    provision *excluding verzinslich angesammelte Überschussanteile*, and the separation is
    the reason this balance is a cells of its own rather than part of :func:`res_pp`.
    """
    return float(model_point()["av_sur_pp_init"])


def bonus_si_init():
    """The bonus sum insured already bought at ``t_start()``, in euros.

    Zero on every shipped model point: the *Bonussystem* point starts at issue with nothing
    bought.  The column exists so that an in-force contract on that system can be projected
    without a formula change.
    """
    return float(model_point()["bonus_si_init"])


def term_bonus_pp_init():
    """The accrued *Schlussüberschussanteil* per policy carried at ``t_start()``, in euros.

    Zero on every point that opens at issue.  An in-force point carries what its past policy
    years accrued, so that :func:`term_bonus_pp` goes on from it rather than from zero and
    the death and maturity benefits keep the terminal bonus of the years before the frame.
    """
    return float(model_point()["term_bonus_pp_init"])


def bfz_year():
    """The **contractual, 1-based policy year** at whose end *Beitragsfreistellung* is
    elected; 0 means never.

    It is a policy-year *label* and not a frame index, which is why the column is left
    1-based: 0 has to stay free to mean "never".  The election falls at the end of policy
    year ``bfz_year()``, which is the end of period ``bfz_year() - 1`` and the start of
    period ``bfz_year()``, so :func:`is_paid_up` tests ``t >= bfz_year()`` while
    :func:`lapse_rate`, :func:`bfz_uplift_pp` and :func:`bfz_si_pp` read the election year
    itself as ``bfz_year() - 1``.  A value at or below :func:`duration_init` means the
    contract was already *beitragsfrei* when the frame opened.

    A **deterministic model point column, not a decrement**.  The corpus establishes the § 165
    VVG right in full and gives **no take-up rate at all**, and the one market aggregate that
    would bear on it mixes the paid-up route in with surrenders and cannot be split - so
    modelling the election as a schedule keeps an unsourced number out of the base run.  What
    that costs is stated rather than hidden: a real German book converts a material,
    duration-dependent share to *beitragsfrei*, and this model shows that path only where a
    model point elects it.
    """
    return int(model_point()["bfz_year"])


# --- the projection frame --------------------------------------------------

# --- the bases -------------------------------------------------------------

def mort_rate_tariff_at_age(x):
    """q1(x): the **first-order tariff** death rate at attained age x - the unisex blend.

    ``unisex_blend`` of the male and the female table row, at ``unisex_mix_male`` 0.5 / 0.5
    **[std]**.  This is the *Rechnungsgrundlage erster Ordnung* of the tariff, and **every
    pricing and reserving formula in the model reads it**: :func:`pols_tariff`,
    :func:`tariff_death_pv`, :func:`pv_benefit_fut`, :func:`ann_due_prem_fut` and the Fackler
    roll-forward in :func:`res_pp_at`.

    It is blended rather than read off the policy's own ``sex`` row because **German new
    business has been unisex since 21 December 2012**: § 20 Abs. 2 Satz 1 AGG was repealed,
    and a tariff that charged a woman less than a man for the same endowment would be
    unlawful.  The first-order *table* is nevertheless sex-specific, because that is the raw
    material a unisex tariff blends - which is exactly why this cells and
    :func:`mort_rate_base` are two different quantities and **not two indexings of one**.
    The blend itself is a fixed portfolio mix and is **[std]**: no German insurer publishes
    the mix behind its unisex tariff.

    The table is a **[std]** Makeham-form proxy anchored at
    ``mort_rate_1st(M, 37) = 0.001200`` exactly, standing in for DAV 2008 T, which is the
    property of the Deutsche Aktuarvereinigung, is not public and is not redistributed here;
    see the ``Data`` docstring for what a replacement must preserve.
    """
    rates = data.mort_table_dict()["mort_rate_1st"]                  # noqa: F821
    return unisex_blend(float(rates[("M", int(x))]),
                        float(rates[("F", int(x))]))


def mort_rate_at_age(x):
    """The **sex-specific annual** first-order table rate at attained age x.

    A lookup into *mort_table.csv* on this policy's own ``sex`` row, and through the core's
    ``mort_rate_base(t) = mort_rate_at_age(age(t))`` the parent of the best-estimate
    decrement: ``mort_rate(t) = mort_rate_base(t) * mort_be_factor``.  Flat across a policy
    year's twelve months, the attained age stepping on the anniversary.

    It is **not** the rate the contract is priced or reserved on - that is
    :func:`mort_rate_tariff_at_age`, the unisex blend - and the two are deliberately different
    quantities.  A German tariff may not price on sex; a best-estimate projection of a
    particular life must.  ``sex`` therefore reaches the **decrement** and nothing else, and
    ``prem_gross_level_pp()`` is identical for two model points differing only in it.
    """
    return float(data.mort_table_dict()["mort_rate_1st"][            # noqa: F821
        (sex(), int(x))])


def mort_be_factor():
    """The step from the first-order table to the best estimate, 0.75, from *param_tariff_type.csv*.

    Override reason: the best estimate is 0.75 of the first-order table, a 33 % safety
    loading and a tariff parameter in *param_tariff_type.csv*,
    products/kapitallebensversicherung/model.md:513
    """
    return data.param("mort_be_factor")                              # noqa: F821


def hoechstrechnungszins():
    """The § 2 DeckRV *Höchstrechnungszins* for this contract's ``issue_year``.

    A **cohort fact**: the ceiling in force at conclusion applies for the whole term.  The
    published history splits 1994 and 2000 mid-year and a year-keyed table cannot, so both
    split years carry the **higher** of the two rates - which makes
    :func:`check_rechnungszins_cap` permissive rather than strict in exactly the two years
    where the model cannot know which half of the year a contract was written in **[std]**.

    Override reason: the ceiling is read from the product's year-keyed *deckrv_table.csv*,
    clamped to its range, with the split years 1994 and 2000 at the higher rate,
    products/kapitallebensversicherung/technical-notes.md:253
    """
    rates = data.deckrv_table_dict()["hoechstrechnungszins"]         # noqa: F821
    y = min(max(issue_year(), int(min(rates))), int(max(rates)))
    return float(rates[y])


def zillmer_max():
    """The § 4 DeckRV *Höchstzillmersatz* for this contract's ``issue_year``.

    40 ‰ of the *Beitragssumme* to 2014 and **25 ‰ from 1 January 2015**, the LVRG cut.  A cap
    on the **charge**, and not to be confused with § 169 Abs. 3 VVG's five-year spreading,
    which is a floor on the **value**: :func:`check_zillmer_cap` and :func:`check_surr_floor`
    assert the two separately for that reason.
    """
    rates = data.deckrv_table_dict()["hoechstzillmersatz"]           # noqa: F821
    y = min(max(issue_year(), int(min(rates))), int(max(rates)))
    return float(rates[y])


def prem_freq_load():
    """phi: the *Ratenzahlungszuschlag* multiplier on the annual *Bruttobeitrag*.

    The table value where :func:`unterjaehrig_form` is ``unecht`` - 1.000 annual, 1.020
    half-yearly, 1.030 quarterly, 1.050 monthly **[std]** - and **exactly 1.000 where it is
    ``echt``**, because a genuine sub-annual *Versicherungsperiode* is not an instalment of an
    annual one and carries no loading.  Model points 4 and 5 are the same monthly contract
    under the two readings.

    Override reason: an ``echt`` sub-annual payment is a genuine *Versicherungsperiode* and
    carries no loading, products/kapitallebensversicherung/technical-notes.md:142
    """
    if unterjaehrig_form() == "echt":
        return 1.0
    return float(data.prem_freq_table_dict()["prem_freq_load"][      # noqa: F821
        prem_freq()])


def alpha_rate():
    """alpha: the *Zillmersatz*, a fraction of the *Beitragssumme*.

    25 ‰, sitting **at** the § 4 DeckRV ceiling for a contract written from 2015 - the ceiling
    is cited, the level is **[std]**, and no German carrier's actual acquisition cost is
    public.  It is charged in the premium whether or not the contract is zillmered; only
    :func:`zillmer_amount` carries ``zillmer_on``.
    """
    return float(data.charge_table_dict()["load_acq_bsum_once"][cost_id()])  # noqa: F821


def load_admin_prem_inst():
    """beta: the collection loading, a fraction of the *Bruttobeitrag* over ``prem_term``.

    3,0 % **[std]**.  The *form* - a percentage of the gross premium over the premium-paying
    period - is what the corpus establishes; the level is not.
    """
    return float(data.charge_table_dict()["load_admin_prem_inst"][cost_id()])  # noqa: F821


def load_admin_sum_ann():
    """gamma: the administration loading, a fraction of the *Versicherungssumme* p.a.

    1,5 ‰ over the whole *Versicherungsdauer* **[std]**.  Neither the form nor the level is
    established anywhere in the corpus, which is why the reserve carries no separate
    *Verwaltungskostenrückstellung* for the years after the *Beitragszahlungsdauer*: the
    pricing equation funds the running cost and the classical reserve convention assumes the
    ongoing loadings meet it.
    """
    return float(data.charge_table_dict()["load_admin_sum_ann"][cost_id()])  # noqa: F821


# --- pricing on the first-order basis --------------------------------------

def sum_death():
    """SD: the guaranteed *Todesfallleistung*, ``sum_assured() * death_ratio()``.

    The **tariff** death sum, which is what the pricing and the reserve are struck on.  What a
    death claim actually pays is :func:`benefit_death_pp`, which adds the surplus balances and
    substitutes the *Rückkaufswert* on the § 161 VVG suicide share; and a paid-up contract's
    guaranteed death sum is ``bfz_si_pp() * death_ratio()`` instead.
    """
    return sum_assured() * death_ratio()


def tariff_death_sum():
    """SD: the guaranteed *Todesfallleistung*, :func:`sum_death`, the death leg's sum.

    The core's :func:`tariff_death_pv` multiplies its sum over the policy years by it.

    Override reason: the death leg pays the guaranteed Todesfallleistung SD,
    products/kapitallebensversicherung/technical-notes.md:442
    """
    return sum_death()


def tariff_death_load(y):
    """f: the *Risikozuschlag* :func:`rating_factor`, on the **claim rate in the death leg only**.

    Override reason: the Risikozuschlag loads the death leg only, never the survival leg,
    products/kapitallebensversicherung/technical-notes.md:462
    """
    return rating_factor()


def tariff_maturity_sum():
    """SE: the *Erlebensfallleistung*, :func:`sum_assured`, paid at the end of the term.

    The core's :func:`tariff_maturity_pv` multiplies the discounted survivorship to the end
    of the term by it.

    Override reason: the endowment pays the Erlebensfallleistung SE at maturity,
    products/kapitallebensversicherung/technical-notes.md:443
    """
    return sum_assured()


def prem_gross_level_pp():
    """B: the annual *Bruttobeitrag* per policy before the *Ratenzahlungszuschlag*.

    Struck by the first-order equivalence principle, which is linear in ``B`` because the
    *Beitragssumme* is ``B * m``::

        B (1 - beta) a_m - alpha B m = tariff_benefit_pv + gamma SE a_n

    so ``B = (tariff_benefit_pv + gamma SE a_n) / ((1 - beta) a_m - alpha m)``.
    :func:`check_equivalence` asserts that the identity closes.

    The *Bruttobeitrag* is **not** a model point column: no German endowment premium rate
    table is public for any carrier, so a shipped rate would be an invention.  It is derived,
    reported, and it rises with :func:`rating_factor` while being identical for two points
    differing only in :func:`sex`.
    """
    return ((tariff_benefit_pv() + load_admin_sum_ann() * sum_assured() * tariff_term_annuity())
            / ((1.0 - load_admin_prem_inst()) * tariff_annuity()
               - alpha_rate() * prem_term()))


def prem_zill_pp():
    """P^Z: the Zillmer premium, ``prem_net_level_pp() + zillmer_amount() / tariff_annuity()``.

    The net premium plus the level annual charge that amortises the zillmered acquisition cost
    over the *Beitragszahlungsdauer*.  It is the premium the Zillmer reserve rolls forward on,
    which is why :func:`check_res_roll_fwd` reads it and not :func:`prem_pp`: one is a
    first-order reserving quantity and the other is a cash flow.
    """
    return prem_net_level_pp() + zillmer_amount() / tariff_annuity()


# --- the Deckungskapital ---------------------------------------------------

def pv_benefit_fut(k):
    """The first-order present value of the remaining guaranteed benefits at the start of k.

    Prospective, over the remaining term ``n - k`` for the 0-based **policy year** ``k``, on
    the attained age ``age_y(k)``, with the *Risikozuschlag* on the death leg only.  At
    ``k = n`` the remaining term is zero and the value is ``SE``, the maturity payment then
    due; beyond that it is zero.

    The argument is a policy year and not a month, like every pricing and reserving cells
    here: a first-order reserve is struck on the tariff's annual bases against an annual
    *Rechnungszins*, so it stays on the annual clock whatever the projection grid is.
    """
    rem = policy_term() - k
    if rem < 0:
        return 0.0
    if rem == 0:
        return sum_assured()
    x = age_y(k)
    death = 0.0
    p = 1.0
    for j in range(rem):
        q = mort_rate_tariff_at_age(x + j)
        death += disc_factor(j + 1) * p * rating_factor() * q
        p *= (1.0 - q)
    return sum_death() * death + sum_assured() * disc_factor(rem) * p


def ann_due_prem_fut(k):
    """The first-order annuity-due factor over the **remaining** premium-paying period.

    ``sum over j = 0 .. max(0, m - k) - 1 of v1^j * jp(x(k))`` for the 0-based **policy
    year** ``k``.  Zero once the *Beitragszahlungsdauer* has run out, which is what makes the
    reserve of an *abgekürzte Beitragszahlungsdauer* roll forward on interest and mortality
    alone.
    """
    rem = max(0, prem_term() - k)
    if rem <= 0:
        return 0.0
    x = age_y(k)
    s = 0.0
    p = 1.0
    for j in range(rem):
        s += disc_factor(j) * p
        p *= (1.0 - mort_rate_tariff_at_age(x + j))
    return s


def res_net_pp(k):
    """V^n: the **net** prospective reserve at the start of policy year k, per policy.

    ``pv_benefit_fut(k) - prem_net_level_pp() * ann_due_prem_fut(k)``, and therefore exactly
    zero at ``k = 0`` on a new-business point - which is the equivalence principle stated as a
    reserve.  It carries no acquisition cost at all, so it is neither what the insurer holds
    nor what the customer gets; it is the construction the other two are built from.

    This and the two below are the **premium-paying constructions**, computed on the full
    :func:`sum_assured` for the whole remaining term, whether or not the contract has been
    made paid-up.  What the contract actually holds is :func:`res_pp`.
    """
    return pv_benefit_fut(k) - prem_net_level_pp() * ann_due_prem_fut(k)


def res_zill_pp(k):
    """V^Z: the *gezillmerte Deckungskapital* at the start of policy year k, per policy.

    ``res_net_pp(k) - zillmer_amount() * ann_due_prem_fut(k) / tariff_annuity()``: the net
    reserve less the part of the acquisition cost the future premiums have yet to repay.

    **It is exactly ``-zillmer_amount()`` at ``k = 0``**, which on the anchor cell is
    -1 252,53 €.  That is not a defect: it is the arithmetic of *Zillmerung*, and it is the
    reason § 169 Abs. 3 VVG needs a floor at all.  **How long it stays negative is a parameter
    question.**  At the post-2015 25 ‰ ceiling over a twenty-five-year *Beitragszahlungsdauer*
    the zillmered cost is 0,625 of one annual premium, so the first Zillmer premium more than
    repays it and the reserve is positive from the first anniversary; at the pre-2015 40 ‰
    ceiling, or over a long term with a short premium period, it is negative for longer.  With
    ``zillmer_on = 0`` it coincides with :func:`res_net_pp`.
    """
    return (res_net_pp(k)
            - zillmer_amount() * ann_due_prem_fut(k) / tariff_annuity())


def res_min_pp(k):
    """V^min: the § 169 Abs. 3 VVG floor reserve at the start of policy year k, per policy.

    ``res_net_pp(k) - zillmer_amount() * max(0, 1 - k/5)`` for the 0-based **policy year** ``k``:
    the same net reserve with the *angesetzte Abschluss- und Vertriebskosten* spread **evenly over the
    first five contract years** rather than over the whole premium term.  The straight-line
    reading is **[std]**; the alternative - a five-year *Zillmerung* - gives a slightly lower
    floor at durations 1 to 4 and the same value from duration 5.

    On a long *gezillmert* contract this floor **normally binds**, with equality to
    :func:`res_zill_pp` only at durations 0 and ``m``.  A model publishing only the Zillmer
    reserve as the surrender value understates it at essentially every duration.
    """
    return (res_net_pp(k) - zillmer_amount()
            * max(0.0, 1.0 - k / data.param("surr_spread_years")))   # noqa: F821


def is_paid_up(k):
    """Whether the contract is *beitragsfrei* at the start of policy year k.

    True only where a *Beitragsfreistellung* was elected (``bfz_year > 0``), the election
    year has passed **and the election succeeded** - that is, the
    *beitragsfreie Versicherungssumme* it bought reached the agreed
    *Mindestversicherungsleistung* ``bfz_min_sum``.  Where it did not, § 165 VVG obliges the
    insurer to pay the § 169 value instead and the election **becomes a surrender**; see
    :func:`lapse_rate`.

    ``bfz_year()`` is the **contractual, 1-based** policy year at whose end the election
    falls, so the election year is period ``bfz_year() - 1`` and the contract is paid-up from
    period ``bfz_year()`` onwards: hence ``k >= bfz_year()`` here.

    The clause order matters and is not cosmetic: testing the year **before** calling
    :func:`bfz_si_pp` is what keeps the election year itself off the paid-up basis, so that
    :func:`res_guar_pp` can price the purchase without depending on its own result.
    """
    return (bfz_year() > 0 and k >= bfz_year()
            and bfz_si_pp() >= data.param("bfz_min_sum"))            # noqa: F821


def res_pp(k):
    """V(k): the guaranteed *Deckungskapital* per policy at the **start** of policy year k.

    The *gezillmerte* construction :func:`res_zill_pp` while the contract is premium-paying,
    and ``bfz_si_pp() * pu_single_prem(k)`` once it is *beitragsfrei* - the reserve of the
    reduced paid-up endowment the § 169 value bought.

    Defined at ``k = proj_len_y()``, where it is :func:`sum_assured` (or the paid-up sum):
    the closing reserve of the last policy year is the maturity payment itself.  That value
    weights no cash flow and exists for :func:`check_res_roll_fwd`.

    This is the model's contribution to the § 341f HGB *Deckungsrückstellung* line and is
    **not** floored at zero as the balance sheet would floor it, so the negative early
    *gezillmert* values stay visible.  ``av_sur_pp(k)`` is explicitly not part of it.
    """
    if is_paid_up(k):
        return bfz_si_pp() * pu_single_prem(k)
    return res_zill_pp(k)


def res_pp_at(k, timing):
    """The guaranteed *Deckungskapital* per policy at a point inside policy year k.

    ``"BEF_PREM"``
        ``res_pp(k)``, the opening reserve before the year's *Beitrag*.

    ``"AFT_PREM"``
        after the first-order Zillmer premium has been credited, and after any
        :func:`bfz_uplift_pp`.  The premium credited here is ``prem_zill_pp()`` - a
        **first-order reserving quantity**, not the *Zahlbeitrag* of
        :func:`prem_pp` - and it is credited only while the contract is
        premium-paying.

    ``"AFT_INT"``
        the **closing** guaranteed reserve of policy year k: the Fackler roll-forward of
        ``AFT_PREM`` at :func:`rechnungszins` with the first-order mortality released
        over the survivors,

            (V + P^Z) (1 + i1) = f q1 SD + (1 - q1) V(k+1)

        This is the ***Deckungskapital* at the allocation date** that the declared surplus
        rate multiplies, and it is computed **retrospectively** here while
        :func:`res_pp` computes the same quantity prospectively - which is what gives
        :func:`check_res_roll_fwd` its teeth.
    """
    if timing == "BEF_PREM":
        return res_pp(k)
    if timing == "AFT_PREM":
        prem = (prem_zill_pp()
                if (k < prem_term() and not is_paid_up(k)) else 0.0)
        return res_pp(k) + prem + bfz_uplift_pp(k)
    if timing == "AFT_INT":
        q = mort_rate_tariff_at_age(age_y(k))
        si = bfz_si_pp() if is_paid_up(k) else sum_assured()
        return ((res_pp_at(k, "AFT_PREM") * (1.0 + rechnungszins())
                 - rating_factor() * q * si * death_ratio()) / (1.0 - q))
    raise ValueError("invalid timing")


def pu_single_prem(k):
    """The first-order single premium at the start of year k for **one unit** of paid-up cover.

    ``pv_benefit_fut(k) / sum_assured()``: the present value of one euro of
    *Erlebensfallleistung* with ``death_ratio`` euros of *Todesfallleistung* over the
    remaining term, on the contract's own *Rechnungsgrundlagen der Prämienkalkulation*
    including the *Risikozuschlag*.

    It is the price at which the § 169 value buys the *beitragsfreie Versicherungssumme*
    (:func:`bfz_si_pp`), and the price at which the *Bonussystem* buys bonus sum insured
    (:func:`bonus_si_pp`).  At ``k = proj_len_y()`` it is exactly 1.
    """
    return pv_benefit_fut(k) / sum_assured()


def bfz_si_pp():
    """The *beitragsfreie Versicherungssumme* the § 169 value buys, in euros; 0 if never.

    ``res_guar_pp(e) / pu_single_prem(e + 1)`` with ``e = bfz_year() - 1``, the 0-based index
    of the election year - exactly what § 165 VVG
    prescribes, the paid-up benefit being calculated by recognised actuarial rules on the
    *Rechnungsgrundlagen der Prämienkalkulation* **on the basis of the *Rückkaufswert* under
    § 169 Abs. 3 bis 5**.  Two structural consequences follow: the paid-up sum inherits the
    five-year spreading floor, and because that floor generally exceeds the Zillmer reserve
    the sum bought is worth more than the reserve released - the difference being
    :func:`bfz_uplift_pp`.

    Where the result falls below ``bfz_min_sum`` (2 500 € **[std]**) the election is **not** a
    *Beitragsfreistellung* at all; see :func:`is_paid_up` and :func:`lapse_rate`.
    """
    if bfz_year() <= 0:
        return 0.0
    e = bfz_year() - 1
    return res_guar_pp(e) / pu_single_prem(e + 1)


def bfz_uplift_pp(k):
    """The § 169 uplift credited to the reserve in the *Beitragsfreistellung* year; else 0.

    ``(res_guar_pp(k) - res_zill_pp(k+1)) * (1 - q1(k)) / (1 + i1)`` at ``k = bfz_year() - 1``
    - the 0-based index of the election year -
    where the election succeeds, and zero everywhere else.  It is the § 169 Abs. 3 floor
    uplift - the amount by which the value the paid-up sum is bought with exceeds the Zillmer
    reserve released - discounted back to the start of the election year so that it can enter
    :func:`res_pp_at` as a credit.

    It exists so that :func:`check_res_roll_fwd` **still closes in the election year** rather
    than being switched off there, and the identity it then asserts is a real one: that
    ``bfz_si_pp() * pu_single_prem(bfz_year())`` really is ``res_guar_pp(bfz_year() - 1)``,
    i.e. that the paid-up purchase was made at the right price.
    """
    if bfz_year() <= 0 or k != bfz_year() - 1 or not is_paid_up(k + 1):
        return 0.0
    return ((res_guar_pp(k) - res_zill_pp(k + 1))
            * (1.0 - mort_rate_tariff_at_age(age_y(k))) / (1.0 + rechnungszins()))


def res_guar_pp(k):
    """G(k): the § 169 VVG guaranteed value at the **end** of policy year k, per policy.

    ``max(res_zill_pp(k+1), res_min_pp(k+1), 0)`` while the contract is premium-paying, and
    ``max(res_pp(k+1), 0)`` once it is *beitragsfrei*, where the floor is already inside the
    paid-up sum that was bought.

    It reads the reserves at ``k + 1`` because § 169 Abs. 3 VVG strikes the value **zum
    Schluss der laufenden Versicherungsperiode** and not at the cancellation date, and it
    takes the maximum because the *Mindestrückkaufswert* is a **floor on the value**: the
    customer gets whichever construction is higher.  It is the base of the *Stornoabzug*, the
    base of the paid-up purchase and the base of the *Bewertungsreserven* share.
    """
    if is_paid_up(k):
        return max(res_pp(k + 1), 0.0)
    return max(res_zill_pp(k + 1), res_min_pp(k + 1), 0.0)


# --- the Ueberschussbeteiligung --------------------------------------------

def decl_rate(k):
    """d(k): the declared *laufende Verzinsung* in policy year k, from the scenario table.

    The **total** declared rate - the *Garantieverzinsung* plus the *laufende
    Zinsüberschussbeteiligung* - and not an increment over the guarantee.  2,70 % on the
    ``base`` path, one carrier's 2026 rate for its classic endowment book held level for the
    whole projection **[std]**; 1,20 % on ``low``; 0 on ``nil``.  It is
    insurer-discretionary, revisable annually and **may be zero euros**, which is why it is a
    scenario rather than an assumption.

    The table is keyed by the **contractual, 1-based** ``policy_year``, so the lookup goes
    through :func:`policy_year`, clamped at the table's last row.
    """
    hi = data.surplus_rate_years()[scenario_id()][1]                 # noqa: F821
    y = min(policy_year_y(k), hi)
    return float(data.surplus_rate_table_dict()["decl_rate"][(scenario_id(), y)])  # noqa: F821


def zins_ueberschuss_rate(k):
    """z(k): the interest-surplus rate in policy year k, ``max(0, d(k) - i1)``.

    **Derived and never an input.**  A declared 2,70 % on a 1,00 % guarantee is a 1,70 pp
    credit, not 2,70 pp on top of 1,00 pp - the single most common way to get this product
    wrong.  The ``max`` matters on the ``nil`` scenario, where the declared rate falls below
    the guarantee: the reserve still rolls forward at the full :func:`rechnungszins`, so the
    surplus is zero and never negative.
    """
    return max(0.0, decl_rate(k) - rechnungszins())


def term_rate(k):
    """s(k): the *Schlussüberschussanteilsatz* in policy year k, from the scenario table.

    0,40 % p.a. of the *Deckungskapital* on the ``base`` path **[std]** - **nothing in the
    corpus fixes a terminal-bonus level, for any insurer, in any year**.  It accrues on the
    same base as the interest surplus and is paid at the *Ablauf* and on death, and not on
    surrender unless ``term_surr_share`` is raised.  Keyed by the contractual, 1-based
    ``policy_year``, so the lookup goes through :func:`policy_year`.
    """
    hi = data.surplus_rate_years()[scenario_id()][1]                 # noqa: F821
    y = min(policy_year_y(k), hi)
    return float(data.surplus_rate_table_dict()["term_rate"][(scenario_id(), y)])  # noqa: F821


def ans_rate(k):
    """a(k): the *Ansammlungszinssatz* in policy year k, from the scenario table.

    2,70 % on the ``base`` path, set equal to the declared rate **[std]**.  That equality
    matters for one reason: because ``ans_rate > rechnungszins``, the *verzinsliche
    Ansammlung* out-accumulates the *Bonussystem* at maturity while the *Bonussystem* pays
    more on an early death.  Setting it equal to the guarantee would destroy that asymmetry.
    Keyed by the contractual, 1-based ``policy_year``, so the lookup goes through
    :func:`policy_year`.
    """
    hi = data.surplus_rate_years()[scenario_id()][1]                 # noqa: F821
    y = min(policy_year_y(k), hi)
    return float(data.surplus_rate_table_dict()["ans_rate"][(scenario_id(), y)])  # noqa: F821


def surplus_base_pp(k):
    """The *Deckungskapital* the year-k surplus rates are applied to, per policy.

    ``max(res_pp_at(k, "AFT_INT"), 0)``: the **closing** guaranteed reserve of the year,
    after that year's interest and mortality and before this year's surplus - the reserve
    "calculated at the allocation date", which the sources put at the *Bilanzstichtag*.

    The ``max`` is load-bearing wherever the base is negative, and a *gezillmerte
    Deckungskapital* is negative at issue.  A positive rate on a negative base credits a
    **negative** surplus - so a contract whose *Zillmerung* is not yet recovered earns no
    interest surplus at all, even though the § 153 VVG entitlement runs from inception:
    economically right, because there is no fund to earn on, and worth saying because it looks
    like a bug.

    On the shipped parameters the guard is **inert**: the base here is the *closing* reserve,
    and at a 25 ‰ *Zillmersatz* over a twenty-five-year premium term that is already positive
    in the first policy year, ``k = 0`` (570,75 € on the anchor cell against an opening
    -1 252,53 €).  It is not
    inert at the pre-2015 40 ‰ ceiling, and it is the kind of guard whose absence is invisible
    until the parameter that needs it arrives.
    """
    return max(res_pp_at(k, "AFT_INT"), 0.0)


def surplus_credit_pp(k):
    """C(k): the surplus allocated to the contract for policy year k, per policy.

    ``zins_ueberschuss_rate(k) * surplus_base_pp(k)``.  Zero before the frame opens - a
    defensive floor only: no cells reads it there, because :func:`prem_rebate_pp` returns zero
    in the first projected year instead of reaching for a predecessor outside the frame.

    What it is applied *to* is decided by :func:`surplus_use`, not here: this cells is the
    amount declared, and the three systems differ in what they do with it.
    """
    if k < k_start():
        return 0.0
    return zins_ueberschuss_rate(k) * surplus_base_pp(k)


def term_bonus_pp(k):
    """S(k): the accrued *Schlussüberschussanteil* at the start of policy year k, per policy.

    ``S(k+1) = S(k) + term_rate(k) * surplus_base_pp(k)``, opening at :func:`term_bonus_pp_init`
    at ``k_start()``, zero on new business.  It is paid at the *Ablauf* and on death and
    **not** on surrender in the base run, ``term_surr_share`` being zero - the choice that does not invent an entitlement the sources do not describe.  It
    accrues but never compounds: no source describes interest on an accrued terminal share.
    """
    if k <= k_start():
        return term_bonus_pp_init()
    return term_bonus_pp(k - 1) + term_rate(k - 1) * surplus_base_pp(k - 1)


def av_sur_pp(k):
    """U(k): the *Überschussguthaben* per policy at the start of policy year k, in euros.

    The *verzinsliche Ansammlung* balance: it receives declared surplus and **never premium**.
    There is no unit fund and no policyholder account fed by contributions in this product, so
    the house vocabulary's ``prem_to_av_pp`` has no counterpart here and is not published.

    **Named ``av_sur_*`` and not ``av_*``.**  Across delib ``av_pp`` / ``av_pp_at`` / ``av`` /
    ``av_at`` is the *principal* account balance — the *Deckungskapital* on ``RV_DE_S``,
    ``Index_DE_S`` and ``Basis_DE_S``, the *Fondsguthaben* on ``FRV_DE_S`` — and ``av_sur_*``
    is the *verzinsliche Ansammlung* side account beside it, which is ``RV_DE_S``'s spelling
    on the one model that carries both.  This product's principal balance is a **reserve**
    rather than an account and is published as ``res_pp`` / ``res_zill_pp``, so ``KLV_DE_S``
    publishes the ``av_sur_*`` half of the pair and no ``av_pp``.

    It is explicitly **not** part of the *Deckungsrückstellung*: § 341f HGB forms that
    provision *excluding verzinslich angesammelte Überschussanteile*.
    """
    if k <= k_start():
        return av_sur_pp_init()
    return av_sur_pp_at(k - 1, "AFT_CREDIT")


def av_sur_pp_at(k, timing):
    """The *Überschussguthaben* per policy at a point inside policy year k.

    ``"BEF_INT"``
        the opening balance, ``av_sur_pp(k)``.

    ``"AFT_INT"``
        after the year's *Ansammlungszins*, ``av_sur_pp(k) * (1 + ans_rate(k))``.  The
        balance earns its own interest whatever the current *Überschussverwendung* is.

    ``"AFT_CREDIT"``
        after this year's declared surplus has been added, which happens **only** under
        ``ansammlung``.  This is the closing balance ``av_sur_pp(k + 1)``, and it is what a
        death, maturity or surrender at the end of year k is paid on top of the
        guaranteed benefit.
    """
    if timing == "BEF_INT":
        return av_sur_pp(k)
    if timing == "AFT_INT":
        return av_sur_pp(k) * (1.0 + ans_rate(k))
    if timing == "AFT_CREDIT":
        credit = (surplus_credit_pp(k)
                  if surplus_use() == "ansammlung" else 0.0)
        return av_sur_pp_at(k, "AFT_INT") + credit
    raise ValueError("invalid timing")


def av_sur(k):
    """The *Überschussguthaben* of the whole model point at the start of year k, in euros.

    ``av_sur_pp(k) * pols_if(12 * k)``: the per-policy balance weighted by the in-force count
    **at the anniversary opening policy year k**, which is the quantity a portfolio roll-up
    consumes.  The balance is an annual one and so is the weight; a mid-year in-force count
    would pair a start-of-year balance with a population that has already decremented.
    """
    return av_sur_pp(k) * pols_if(12 * k)


def av_sur_at(k, timing):
    """The aggregate *Überschussguthaben* at a point inside policy year k.

    ``av_sur_pp_at(k, timing) * pols_if(12 * k)``, on the in-force at the anniversary opening
    policy year k.  The timings are :func:`av_sur_pp_at`'s.
    """
    return av_sur_pp_at(k, timing) * pols_if(12 * k)


def bonus_si_pp(k):
    """Z(k): the bonus sum insured bought out of surplus, per policy, at the start of year k.

    ``Z(k+1) = Z(k) + surplus_credit_pp(k) / pu_single_prem(k+1)`` under the *Bonussystem*,
    and frozen at :func:`bonus_si_init` under the other two systems.

    The bonus sum is **paid-up insurance**: it raises the death benefit immediately by its
    full face amount, which is why the *Bonussystem* pays more on an early death - but it
    accumulates only at :func:`rechnungszins`, which is why the *verzinsliche Ansammlung*
    pays more at the *Ablauf*.
    """
    if k <= k_start():
        return bonus_si_init()
    add = (surplus_credit_pp(k - 1) / pu_single_prem(k)
           if surplus_use() == "bonus" else 0.0)
    return bonus_si_pp(k - 1) + add


def prem_rebate_pp(k):
    """The *Beitragsverrechnung* offset applied to the year-k *Zahlbeitrag*, per policy.

    ``min(prem_pp(k), surplus_credit_pp(k - 1))`` under ``beitragsverrechnung`` and
    zero otherwise: **last** year's declared surplus reduces **this** year's premium, floored
    at zero so that a surplus larger than the premium never becomes a payment to the
    policyholder.  In the first projected year there is no last year, so the offset is zero
    outright rather than reaching for a predecessor outside the frame.

    What it reduces is a *Zahlbeitrag*, not a *Bruttobeitrag*: the tariff premium is unchanged
    and the offset is a **discretionary** rebate the insurer may withdraw without invoking
    § 163 VVG at all.  That is why the renewal commission is charged on
    :func:`prem_pp` and not on :func:`prem_paid_pp`.
    """
    if surplus_use() != "beitragsverrechnung":
        return 0.0
    if k <= k_start():
        return 0.0
    return min(prem_pp(k), surplus_credit_pp(k - 1))


# --- premium ---------------------------------------------------------------

def prem_pp(k):
    """The **annual** *Zahlbeitrag* charged per policy in policy year k, before any offset.

    ``prem_gross_level_pp() * prem_freq_load()`` in a policy year whose first month
    :func:`prem_due` makes a premium payable **and** in which the contract is not
    *beitragsfrei*; zero otherwise.  ``m`` premiums fall in years ``k = 0 ... m - 1``, the
    0-based reading of "payable over the *Beitragszahlungsdauer*".  An annual amount:
    ``phi`` loads the year's *Bruttobeitrag* once, and what is collected in a month is
    :func:`prem_charged_inst_pp`.
    """
    if not prem_due(12 * k):
        return 0.0
    if is_paid_up(k):
        return 0.0
    return prem_gross_level_pp() * prem_freq_load()


def prem_paid_pp(k):
    """The **annual** *Zahlbeitrag* actually paid per policy in year k, after the offset.

    ``prem_pp(k) - prem_rebate_pp(k)``.  It differs from :func:`prem_pp` only
    under ``beitragsverrechnung``, and the difference is a policyholder rebate rather than a
    price change - which is why the two are separate cells and why the commission reads the
    first of them.
    """
    return prem_pp(k) - prem_rebate_pp(k)


def prem_due(t):
    """Whether a premium instalment falls due at the **beginning** of month t.

    ``duration_mth(t) % prem_cycle() == 0`` inside the *Beitragszahlungsdauer*,
    ``duration(t) < prem_term()``.  An annual payer is due in the first month of every
    paying policy year and nowhere else; a *monthly* payer is due in every month of one.
    This cell is the only source of a zero for the end of the premium term: the annual
    :func:`prem_pp` reads it at ``12 k``, the first month of its year, and no premium cell
    tests ``prem_term()`` itself.  A *Beitragsfreistellung* is no end of the term and
    stays in :func:`prem_pp`.

    **This is what the ``echt`` / ``unecht`` distinction was always about.** Under ``unecht``
    the *Versicherungsperiode* remains the year and the twelve payments are instalments of an
    annual premium, which is exactly what the *Ratenzahlungszuschlag* compensates; under
    ``echt`` the period is genuinely monthly and no loading applies.  On the annual grid this
    model ran on, both readings collected the same amount at the same instant and the whole
    distinction lived in a multiplier.  Here they differ in the frame: model points 4 and 5
    are the same monthly contract, and only the *Ratenzahlungszuschlag* separates them.
    """
    if duration(t) >= prem_term():
        return False
    return duration_mth(t) % prem_cycle() == 0


def prem_charged_inst_pp(t):
    """The *Zahlbeitrag* instalment **charged** in month t before any offset, or zero.

    ``prem_pp(duration(t)) / instalments()`` where :func:`prem_due` makes one due.
    The instalments of a policy year therefore sum to exactly that year's annual charge, the
    loading included: ``phi`` multiplies the annual amount once and the division into
    instalments is what it pays for.  Loading each instalment again charges it twice.

    This, and not :func:`prem_inst_pp`, is the base of the renewal commission: under
    *Beitragsverrechnung* the intermediary is paid on the tariff premium, the surplus offset
    being a policyholder rebate.
    """
    return (prem_pp(duration(t)) / instalments()
            if prem_due(t) else 0.0)


def prem_inst_pp(t):
    """The *Zahlbeitrag* instalment actually **collected** in month t, or zero.

    ``prem_paid_pp(duration(t)) / instalments()`` where :func:`prem_due` makes one due — the
    year's premium net of the *Beitragsverrechnung* offset, divided into the elected number of
    instalments.  Formed from the annual amount so that the offset is spread over the year's
    instalments exactly as the charge is, and the two cannot fall on different cycles.

    Override reason: the instalment is the year's *Zahlbeitrag*, net of the
    *Beitragsverrechnung*, over the elected instalments where one falls due,
    products/kapitallebensversicherung/technical-notes.md:611
    """
    return (prem_paid_pp(duration(t)) / instalments()
            if prem_due(t) else 0.0)


# --- decrements ------------------------------------------------------------

def lapse_rate(t):
    """w(t): the annual surrender rate applied at the **end** of policy year t.

    From *lapse_table.csv* by the contractual, 1-based ``policy_year`` - so the lookup goes
    through :func:`policy_year` - and **[std]** throughout: 5,0 % in policy years 1-2,
    3,5 % in 3-8, 2,0 % in 9-11, **6,0 % in policy year 12** and 2,5 % from 13.  The *shape* is the
    one thing the evidence supports - the income-tax half-income rule needs twelve years and
    age 60 or 62, so surrenders are suppressed approaching duration 12 and spike at it.  The
    **levels are not sourced**: the only German data are market aggregates that are neither
    endowment-specific nor by duration, and the headline one counts conversions to
    *beitragsfrei* as well as surrenders, so calibrating a surrender decrement to it
    double-counts.

    Two overrides.  **Zero through the whole final policy year**,
    ``duration(t) >= proj_len_y() - 1``: its end is the *Ablauf*, so the survivors leave as a
    maturity - and unlike a term cover this is a real payment decision, a surrender paying the
    § 169 value while a maturity pays the sum insured plus surplus.  The zero covers the year
    and not merely its last month, because that is what the annual-step model this replaced
    said of it.  **1.0 in the year a *Beitragsfreistellung* election fails the
    *Mindestversicherungsleistung* test**, where § 165 VVG turns the election into a
    surrender and the whole cohort leaves; that override is a statutory consequence and not a
    behavioural rate, and it is the only place the shipped table is departed from.

    This is the **annual** rate of the policy year containing month ``t``;
    :func:`lapse_rate_mth` is what the recursion applies, and it is where the election year's
    1.0 is placed on the anniversary rather than spread.

    Override reason: § 165 VVG turns a *Beitragsfreistellung* election that fails the
    minimum-sum test into a surrender, a rate of 1 in that year, and the final year's end is
    the *Ablauf*, products/kapitallebensversicherung/technical-notes.md:538
    """
    if duration(t) >= proj_len_y() - 1:
        return 0.0
    if bfz_fails() and duration(t) == bfz_year() - 1:
        return 1.0
    return lapse_rate_base(t)


def bfz_fails():
    """Whether a *Beitragsfreistellung* was elected and **failed** the minimum-sum test.

    ``bfz_year() > 0 and not is_paid_up(bfz_year())``: the election was made and the
    *beitragsfreie Versicherungssumme* it bought fell short of ``bfz_min_sum``, so § 165 VVG
    obliges the insurer to pay the § 169 value instead and the election **becomes a
    surrender**.  Named because two cells need the same test and a monthly grid makes them
    read it at different arguments — :func:`lapse_rate` at a month, :func:`is_paid_up` at a
    policy year.  Model point 12 is the failing cell.
    """
    return bfz_year() > 0 and not is_paid_up(bfz_year())


def stornoabzug_rate(k):
    """sigma(k): the *Stornoabzug* rate on a surrender at the end of policy year k.

    10 % of the guaranteed value in policy years 1-5, 7,5 % in 6-10, 5 % in 11-15 and 2,5 %
    from 16 **[std]** - contractual, 1-based policy years, so the lookup goes through
    :func:`policy_year` - against an observed range of 5 % to 20 % of the *Deckungskapital* from
    **one carrier**, under collective action and a BGH remittal.

    § 169 Abs. 5 VVG permits a deduction only where it is *vereinbart*, *beziffert* and
    *angemessen*, and a deduction for *noch nicht getilgte Abschluss- und Vertriebskosten* is
    unwirksam - which is what stops an insurer recovering through the deduction what the
    five-year spreading denies it.  It bites on the **guaranteed value only**; see
    :func:`surr_value_pp`.
    """
    rates = data.lapse_table_dict()["stornoabzug_rate"]              # noqa: F821
    return float(rates[min(policy_year_y(k), int(max(rates)))])


def pols_if(t):
    """l(t): the number of policies in force at the **start** of month t.

    ``pols_if_init()`` at ``t_start()``, then ``l(t+1) = l(t) (1 - qm(t)) (1 - wm(t))`` on the
    **best-estimate** monthly rates.  This is the weight on every cash flow of the same
    :func:`result_cf` row.

    Because both monthly rates compound back to their policy year's annual rate, twelve months
    of this recursion collapse to ``l(t+12) = l(t) (1 - q(t)) (1 - w(t))`` — the annual-step
    recursion this replaced, term for term — so the in-force **at every policy anniversary**
    is the annual model's own figure, ``pols_if(12k)`` here equalling its ``pols_if(k)`` to
    floating point.  That is what leaves the whole annual layer of this product — the three
    reserves, the § 169 value, the surplus ledgers, the paid-up purchase — unmoved by the
    conversion.

    A contract made *beitragsfrei* stays here: § 165 VVG keeps it in force with a reduced sum
    insured, and only a *Kündigung* removes it.  ``pols_if(proj_len())`` is defined and is
    the maturing cohort; it is read by :func:`check_pols_roll_fwd` and
    :func:`check_decrement_closure` and weights no cash flow.

    Override reason: the roll-forward subtracts no maturity, so ``pols_if(proj_len())`` is
    the maturing cohort its checks read, and it multiplies the survival factors, another
    float order, products/kapitallebensversicherung/technical-notes.md:617
    """
    if t < t_start() or t > proj_len():
        return 0.0
    if t == t_start():
        return pols_if_init()
    return pols_if_at(t - 1, "AFT_DEATH") * (1.0 - lapse_rate_mth(t - 1))


# --- benefits --------------------------------------------------------------

def av_sur_close_pp(t):
    """The *Überschussguthaben* per policy **standing at the end of month t**, in euros.

    ``av_sur_pp(duration(t) + 1)`` in an anniversary month and ``av_sur_pp(duration(t))`` in
    every other — the balance a claim leaving at the end of that month is actually paid.

    **This is the rule for every time-varying benefit leg on this model, and it is what the
    monthly grid is for.** The *Überschussdeklaration* is an annual act: § 153 VVG's
    entitlement is settled once a year, the rates are declared for a *Versicherungsjahr* and
    the credit lands at the anniversary.  A death or surrender in March is therefore paid the
    balance that was standing at the last anniversary, not the one the coming anniversary will
    produce.  The annual-step model this replaced could only pay a March exit the December
    balance, which is a forward-looking payment at a date it is not yet due; it did so because
    on that grid the exit and the crediting were the same instant.

    The documented alternative — a *pro rata temporis* accrual, crediting a twelfth of the
    year's declared surplus in each month — is a **variant and not the base**: no retrieved
    German wording describes one, and adopting it would put an unsourced accrual rule inside
    the benefit.  It would reconcile at the anniversary just as exactly, the year's credit
    still summing to ``C(k)``, so only the sources decide between them.
    """
    k = duration(t)
    return av_sur_pp(k + 1) if is_anniv(t) else av_sur_pp(k)


def bonus_si_close_pp(t):
    """The bonus sum insured per policy standing at the end of month t, in euros.

    ``bonus_si_pp(duration(t) + 1)`` in an anniversary month and ``bonus_si_pp(duration(t))``
    otherwise, on :func:`av_sur_close_pp`'s rule: the *Bonussystem* buys its paid-up cover out
    of the year's declared surplus, so the purchase falls at the anniversary too.
    """
    k = duration(t)
    return bonus_si_pp(k + 1) if is_anniv(t) else bonus_si_pp(k)


def term_bonus_close_pp(t):
    """The accrued *Schlussüberschussanteil* per policy at the end of month t, in euros.

    ``term_bonus_pp(duration(t) + 1)`` in an anniversary month and
    ``term_bonus_pp(duration(t))`` otherwise.  The *Schlussüberschussanteilsatz* is declared
    for a *Versicherungsjahr* and accrues on that year's closing *Deckungskapital*, so it
    lands at the anniversary like the rest.
    """
    k = duration(t)
    return term_bonus_pp(k + 1) if is_anniv(t) else term_bonus_pp(k)


def res_guar_close_pp(t):
    """G(t): the § 169 VVG guaranteed value **standing at the end of month t**, per policy.

    ``res_guar_pp(duration(t))`` in an anniversary month and ``res_guar_pp(duration(t) - 1)``
    in every other — the value struck at the **last** anniversary, which is what an
    administration system holds and what a mid-year surrender is quoted.

    § 169 Abs. 3 VVG strikes the value "zum Schluss der laufenden Versicherungsperiode", and
    § 12 VVG makes that period follow the *Zahlweise*, so on a monthly-paying contract the
    statute would strike it monthly.  **The model does not, and says so rather than
    interpolating**: a monthly § 169 value needs a monthly *Deckungskapital*, and the tariff
    defines the *Rechnungsgrundlagen der Prämienkalkulation* on an annual *Rechnungszins* and
    an annual first-order table.  What the monthly grid does remove is the opposite and worse
    error, which the annual grid had to make — paying a surrender in the first month of a
    policy year the value that year will close at.

    In the first eleven months of the contract ``res_guar_pp(-1)`` is the § 169 value at issue,
    which on a *gezillmert* contract is exactly zero: a surrender inside the first policy year
    is paid the accumulated *Überschussguthaben* and nothing guaranteed, which is the
    consumer fact this product is best known for.
    """
    k = duration(t)
    return res_guar_pp(k) if is_anniv(t) else res_guar_pp(k - 1)


def benefit_full_pp(t):
    """The full death benefit per claim in month t, before the § 161 VVG substitution.

    The guaranteed *Todesfallleistung* plus **the three surplus balances standing at the end
    of the month**: the *Überschussguthaben*, the bonus sum insured and the accrued
    *Schlussüberschussanteil*, each through the closing rule of :func:`av_sur_close_pp`.  The
    surplus is added to the death benefit whole - the two benefits of a *gemischte
    Versicherung* differ only in their guaranteed leg.

    The guaranteed leg carries no timing question at all: it is a **sum**, not a balance.  A
    *beitragsfrei* contract's is ``bfz_si_pp() * death_ratio()`` instead of ``sum_death()``.
    """
    si = bfz_si_pp() if is_paid_up(duration(t)) else sum_assured()
    return (si * death_ratio() + av_sur_close_pp(t)
            + bonus_si_close_pp(t) + term_bonus_close_pp(t))


def benefit_death_pp(t):
    """What a death claim in month t actually pays, per claim, in euros.

    :func:`benefit_full_pp` from policy year 4 (``duration(t) >= 3``) onwards.  In policy
    years 1 to 3 — the **first thirty-six months** — the § 161 VVG
    *Selbsttötung* rule applies to a share ``suicide_share`` of deaths: the insurer is
    *leistungsfrei* **and must nevertheless pay the *Rückkaufswert* including
    *Überschussanteile* under § 169**.  The German rule is a benefit **substitution**, not a
    forfeiture - materially unlike art. L. 132-7 of the French code, where the cover is of no
    effect in the first year and there is no surrender value to fall back on.

    The window is measured in whole years from conclusion, so its boundary falls on an
    anniversary and ``duration(t) < 3`` is the same statement as ``t < 36``: the monthly grid
    resolves it exactly rather than approximately.

    ``suicide_share = 0.02`` **[std]** stands for "about one death in fifty inside the window
    is an excluded suicide"; no source gives a suicide share of deaths at any age.  Setting it
    to zero is a defensible variant.  Paying **nil** on the excluded share is not.

    Override reason: a death pays the full benefit, with the *Rückkaufswert* on the suicide
    share in the first three years, products/kapitallebensversicherung/technical-notes.md:621
    """
    if duration(t) < data.param("suicide_years"):                    # noqa: F821
        return ((1.0 - data.param("suicide_share")) * benefit_full_pp(t)  # noqa: F821
                + data.param("suicide_share") * surr_value_pp(t))    # noqa: F821
    return benefit_full_pp(t)


def benefit_maturity_pp(t):
    """What the *Ablauf* pays per surviving policy at the end of the last projected month
    ``t = proj_len() - 1``; zero before it.

    The guaranteed *Erlebensfallleistung* plus the three surplus balances, plus the
    *Beteiligung an den Bewertungsreserven* at ``bwr_rate`` on the guaranteed value.  The last
    projected month **is** an anniversary month, so every closing balance here is the year's
    closing one and the *Ablauf* is unchanged by the conversion.

    ``bwr_rate = 0`` in the base run **[std]**: § 153 Abs. 3 VVG allocates half the
    *Bewertungsreserven* determined on termination, but § 139 VAG permits participation only
    to the extent they exceed the *Sicherungsbedarf* arising from contracts with an interest
    guarantee, and that need has routinely exhausted them.  The parameter exists so the
    reasoning is visible and reversible.

    A *beitragsfrei* contract matures on ``bfz_si_pp()`` in place of :func:`sum_assured`.

    Override reason: the *Ablauf* pays the sum assured plus the surplus balances,
    products/kapitallebensversicherung/technical-notes.md:624
    """
    if t != proj_len() - 1:
        return 0.0
    si = bfz_si_pp() if is_paid_up(duration(t)) else sum_assured()
    return (si + av_sur_close_pp(t) + bonus_si_close_pp(t)
            + term_bonus_close_pp(t)
            + data.param("bwr_rate") * res_guar_close_pp(t))         # noqa: F821


def surr_value_pp(t):
    """RK(t): the *Rückkaufswert* payable per policy on a surrender at the end of month t.

    ``res_guar_close_pp(t) * (1 - stornoabzug_rate(duration(t))) + av_sur_close_pp(t)
    + term_surr_share * term_bonus_close_pp(t)`` — every leg struck on the balance standing at
    the end of the month of exit, which is the rule :func:`av_sur_close_pp` states.

    The ***Stornoabzug* bites on the guaranteed value alone**: the published deduction is a
    percentage of the *Deckungskapital*, so the accumulated *Überschussguthaben* passes
    through undeducted.  Its band is a **policy-year** band and steps on the anniversary.
    ``term_surr_share = 0`` in the base run, the accrued
    *Schlussüberschussanteil* being payable at the *Ablauf* and on death and not on surrender;
    the parameter is exposed rather than hard-coded because that choice would move surrender
    values most.

    This is also what a § 161 VVG suicide inside three years is paid, and what a failed
    *Beitragsfreistellung* election is paid under § 165 VVG — the latter falling in the
    election year's last month, where the closing rule makes it the year's own § 169 value.
    """
    return (res_guar_close_pp(t) * (1.0 - stornoabzug_rate(duration(t)))
            + av_sur_close_pp(t)
            + data.param("term_surr_share") * term_bonus_close_pp(t))  # noqa: F821


def claim_kinds():
    """The benefit kinds of :func:`claims` in the order of its total: death, maturity, lapse.

    Override reason: the claim columns are death, maturity and lapse in that order,
    products/kapitallebensversicherung/technical-notes.md:655
    """
    return ("DEATH", "MATURITY", "LAPSE")


def benefit_lapse_pp(t):
    """What a surrender in month t pays, the *Rückkaufswert* :func:`surr_value_pp`.

    Unlike a *Risikolebensversicherung*, where a lapse pays nothing, this is a real and
    often large outflow, and in the last month the distinction between it and a maturity
    decides a payment rather than only a label.

    Override reason: a lapse pays the *Rückkaufswert*,
    products/kapitallebensversicherung/technical-notes.md:631
    """
    return surr_value_pp(t)


# --- expenses and commission -----------------------------------------------

def claim_expenses(t):
    """The claim handling expense on the month's exits **[std]**.

    120 € per death, maturity or surrender claim, uninflated.  Named separately because it is
    the only expense line that scales with **claims** rather than with policies, and it is
    inside :func:`expenses`.
    """
    ce = float(data.charge_table_dict()["expense_claim_pp_once"][cost_id()])  # noqa: F821
    return ce * (pols_death(t) + pols_lapse(t) + pols_maturity(t))


def expenses_pp(t):
    """The per-policy expense in **month** t, in euros, excluding claim handling **[std]**.

    The 300 € acquisition expense at issue - **only** in month ``t_start()`` and **only** for a
    new-business point, an in-force point having incurred it long ago, and a single amount
    rather than a twelfth of one - plus **one twelfth** of the 45 € annual maintenance
    expense, inflated to the policy year the month falls in.  A policy that runs a full year
    therefore carries the same annual maintenance charge it did on the annual grid, but it is
    borne by the in-force of **each month** rather than of the anniversary, which is what makes
    a decrementing block cost less.

    All levels are placeholders: **no charge level of any kind was established for any German
    carrier**, and the levels shipped are sized so that the first-year acquisition outgo
    modestly exceeds what the *Zillmerung* recovers, so that the anchor cell carries the
    new-business strain a real German endowment carries.
    """
    cost = data.charge_table_dict()                                  # noqa: F821
    acq = (float(cost["expense_acq_pp_once"][cost_id()])
           if (t == t_start() and duration_init() == 0) else 0.0)
    return (acq + float(cost["expense_admin_pp_ann"][cost_id()]) / 12.0
            * inflation_factor(t))


def expenses_maint(t):
    """The per-policy expense on the in-force, ``expenses_pp(t) x pols_if(t)`` **[std]**.

    :func:`expenses_pp` folds the acquisition expense of month ``t_start()`` into the
    month's per-policy rate beside the maintenance, so the core's acquisition term keeps its
    neutral 0.  Commission is not in the expenses: :func:`commissions` is a separate line,
    so the six flow columns of :func:`result_cf` sum to :func:`net_cf` rather than
    double-counting the commission.  This is the rule on **every delib model that has a
    commission to publish** — ``Basis_DE_S``, ``Riester_DE_S``, ``RLV_DE_S`` and
    ``FRV_DE_S`` — so ``expenses`` means the same quantity across the library.

    Override reason: the in-force carries the acquisition expense at issue,
    products/kapitallebensversicherung/technical-notes.md:633, and the monthly maintenance,
    products/kapitallebensversicherung/technical-notes.md:634, in one per-policy rate
    """
    return expenses_pp(t) * pols_if(t)


def expenses_claim(t):
    """The claim handling expense, :func:`claim_expenses`.

    Override reason: the claim expense falls per death, lapse and maturity,
    products/kapitallebensversicherung/technical-notes.md:635
    """
    return claim_expenses(t)


def comm_init_rate():
    """The initial commission rate on the *Beitragssumme*, from the cost table **[std]**.

    2,5 % of the *Beitragssumme* at conclusion - anchored to the 25 ‰ § 4 DeckRV ceiling and
    to one carrier's reported 25 ‰, a single amount in month ``t_start()``.  It does not
    apply at ``t_start()`` on an in-force point: it was paid at conclusion, long before the
    frame opens.  Commission is excluded from :func:`expenses`.

    Override reason: the initial commission is the cost table's ``comm_acq_bsum_once`` of the
    *Beitragssumme*, products/kapitallebensversicherung/technical-notes.md:375
    """
    return float(data.charge_table_dict()["comm_acq_bsum_once"][cost_id()])  # noqa: F821


def comm_renew(t):
    """The 1,5 % *Bestandsprovision* on each *Bruttobeitrag* **instalment** **[std]**.

    From the second projected policy year; not at ``t_start()`` on an in-force point.  The
    **rate** is a policy-year rate and steps on the anniversary; the **base** is the
    instalment actually charged, so a fractionated payer earns the renewal commission in
    instalments too.  It is charged on :func:`prem_charged_inst_pp` and **not** on
    :func:`prem_inst_pp`: under *Beitragsverrechnung* the intermediary is paid on the tariff
    premium, the surplus offset being a policyholder rebate rather than a price reduction.

    Override reason: the renewal commission is a rate on the charged instalment after the
    first projected policy year, products/kapitallebensversicherung/technical-notes.md:637
    """
    cost = data.charge_table_dict()                                  # noqa: F821
    return (float(cost["comm_renew_prem_inst"][cost_id()]) * prem_charged_inst_pp(t) * pols_if(t)
            if duration(t) > k_start() else 0.0)


# --- output ----------------------------------------------------------------

def check_net_cf_scale(t):
    """The scale of :func:`check_net_cf`'s tolerance in month t: the sum insured, at least 1.

    :func:`check_net_cf` is true when the cash flow statement reconciles in every projected
    policy year.

    **This library's first ruling**: every model publishes the identity that reconstructs
    ``net_cf(t)`` from its own cash flow statement's published parts, so that the headline
    number of a cash flow model is not the one quantity nothing checks.  No argument, one bool
    over all ``t``; :func:`check_net_cf_resid` gives the signed residual of the year that
    failed.

    Override reason: the statement is checked relative to the sum insured,
    products/kapitallebensversicherung/technical-notes.md:692
    """
    return max(sum_assured(), 1.0)                                   # noqa: F821


def check_pols_roll_fwd_resid(t):
    """The in-force roll-forward residual in policy year t; zero everywhere.

    ``pols_if(t) - pols_if(t+1) - pols_death(t) - pols_lapse(t)``, plus in the final policy
    year the difference between :func:`pols_maturity` and the survivors of that year's
    mortality.  The recursion multiplies ``(1 - q)(1 - w)`` while the exits are formed
    separately, so the two agree by algebra when - and only when - every one of them is read
    at the same ``t``.  What it catches is a **misindexed recursion**, and in the last year a
    maturity count that is not exactly the cohort that survived to it.
    """
    r = (pols_if(t) - pols_if(t + 1) - pols_death(t) - pols_lapse(t))
    if t == proj_len() - 1:
        r += pols_maturity(t) - pols_if_at(t, "AFT_DEATH")
    return r


def check_pols_roll_fwd():
    """True when the in-force roll-forward closes in every projected policy year.

    No argument, one bool over all ``t``; :func:`check_pols_roll_fwd_resid` gives the signed
    residual of the year that failed.
    """
    tol = roll_fwd_tol() * max(pols_if_init(), 1.0)                  # noqa: F821
    return all(abs(check_pols_roll_fwd_resid(t)) <= tol
               for t in range(t_start(), proj_len()))


def pols_exits_cum(t):
    """The deaths, surrenders and maturities from ``t_start()`` through t; 0 before.

    A running total: each month adds ``pols_death(t) + pols_lapse(t) + pols_maturity(t)`` to
    the month before, so a month costs one step rather than re-summing the frame.  It equals
    the direct sum over the exit cells up to floating-point noise (Python's ``sum`` is
    compensated, this total is not), far inside the tolerance of
    :func:`check_decrement_closure`.  A recursion over the exit cells only, never over
    :func:`pols_if`.
    """
    if t < t_start():
        return 0
    return pols_exits_cum(t - 1) + (pols_death(t) + pols_lapse(t) + pols_maturity(t))


def check_decrement_closure_resid(t):
    """The cumulative decrement-closure residual at the end of policy year t; zero.

    Deaths plus surrenders plus maturities up to ``t``, plus the survivors carried into
    ``t + 1`` before the *Ablauf*, less the original cohort.  It is built by **direct
    summation over the exit cells**, the running total :func:`pols_exits_cum`, with no
    reference to the recursion that produced :func:`pols_if`, which is what makes it more
    than the telescope of :func:`check_pols_roll_fwd`: it catches a wrong starting cohort,
    an exit counted in two places, and a maturity that double-counts the final year's
    surrenders.
    """
    exits = pols_exits_cum(t)
    carried = pols_if(t + 1) if t < proj_len() - 1 else 0.0
    return exits + carried - pols_if_init()


def check_decrement_closure():
    """True when deaths, surrenders, maturities and survivors account for the whole cohort.

    No argument, one bool over all ``t``; :func:`check_decrement_closure_resid` gives the
    signed residual of the year that failed.  At ``t = proj_len() - 1`` it is the notes'
    closure identity: the three exit streams sum to :func:`pols_if_init` exactly.
    """
    tol = roll_fwd_tol() * max(pols_if_init(), 1.0)                  # noqa: F821
    return all(abs(check_decrement_closure_resid(t)) <= tol
               for t in range(t_start(), proj_len()))


def check_res_roll_fwd_resid(k):
    """The *Deckungskapital* roll-forward residual in **policy year** k; zero everywhere.

    ``res_pp_at(k, "AFT_INT") - res_pp(k + 1)``: the Fackler recursion

        (V(k) + P^Z + uplift) (1 + i1) = f q1(k) SD + (1 - q1(k)) V(k+1)

    computed **retrospectively** on the left and **prospectively** on the right.  This is the
    strongest single check in the model: it proves that the premium, the first-order
    mortality, the interest rate and the prospective reserve formula are mutually consistent,
    and it fails on a *Risikozuschlag* applied to the survivorship, a Zillmer premium
    amortised over the wrong annuity, a reserve read at the wrong duration, and an
    *abgekürzte Beitragszahlungsdauer* that keeps crediting a premium after it has stopped.

    In the *Beitragsfreistellung* year the identity it asserts is a different one -
    :func:`bfz_uplift_pp` is defined to close it - and there it says that the paid-up sum was
    bought at exactly the § 169 value.

    It is a **policy-year** identity and stays one on the monthly grid: an annual Fackler
    recursion at an annual *Rechnungszins*, which is what the tariff defines.
    """
    return res_pp_at(k, "AFT_INT") - res_pp(k + 1)


def check_res_roll_fwd():
    """True when the guaranteed reserve rolls forward in every projected policy year.

    No argument, one bool over all policy years ``k``; :func:`check_res_roll_fwd_resid` gives
    the signed residual of the year that failed.
    """
    tol = roll_fwd_tol() * max(sum_assured(), 1.0)                   # noqa: F821
    return all(abs(check_res_roll_fwd_resid(k)) <= tol
               for k in range(k_start(), proj_len_y()))


def check_surplus_roll_fwd_resid(k):
    """The active *Überschussverwendung* ledger's residual in **policy year** k; zero.

    Under ``ansammlung``, ``av_sur_pp(k+1) - [av_sur_pp(k) (1 + a(k)) + C(k)]``; under
    ``bonus``, ``bonus_si_pp(k+1) - [bonus_si_pp(k) + C(k) / pu_single_prem(k+1)]``; under
    ``beitragsverrechnung``, ``prem_rebate_pp(k) - min(prem_pp(k), C(k-1))``.

    One check for three ledgers, because exactly one of them is live on any model point - and
    a model that credits the same surplus to two of them fails here rather than quietly
    paying it twice.  All three are **policy-year** ledgers and stay so: the declaration is an
    annual act and the finer grid does not subdivide it.
    """
    if surplus_use() == "ansammlung":
        return (av_sur_pp(k + 1)
                - (av_sur_pp(k) * (1.0 + ans_rate(k)) + surplus_credit_pp(k)))
    if surplus_use() == "bonus":
        return (bonus_si_pp(k + 1)
                - (bonus_si_pp(k)
                   + surplus_credit_pp(k) / pu_single_prem(k + 1)))
    return prem_rebate_pp(k) - min(
        prem_pp(k),
        surplus_credit_pp(k - 1) if k > k_start() else 0.0)


def check_surplus_roll_fwd():
    """True when the live surplus ledger closes in every projected policy year.

    No argument, one bool over all policy years ``k``; :func:`check_surplus_roll_fwd_resid`
    gives the signed residual of the year that failed.
    """
    tol = roll_fwd_tol() * max(sum_assured(), 1.0)                   # noqa: F821
    return all(abs(check_surplus_roll_fwd_resid(k)) <= tol
               for k in range(k_start(), proj_len_y()))


def check_surr_floor_resid(k):
    """The § 169 Abs. 3 VVG surrender-floor residual in **policy year** k; zero everywhere.

    The sum of four one-sided violations, each of which can only be negative:
    ``res_guar_pp(k)`` below :func:`res_zill_pp` at ``k + 1``, below :func:`res_min_pp` at
    ``k + 1``, below zero, and the *Rückkaufswert* payable at that year's anniversary —
    ``surr_value_pp(12k + 11)`` — below zero.  The two reserve comparisons
    are made only while the contract is premium-paying: once it is *beitragsfrei* the
    premium-paying constructions describe a contract that no longer exists, and the floor is
    already inside the paid-up sum that was bought.

    Near-trivial by construction, since :func:`res_guar_pp` is that maximum - and published
    for the same reason frlib publishes its gate checks: the rule is written twice, so the two
    disagree if either is edited.  What it guards against is the specific and tempting error
    of publishing the Zillmer reserve alone as the surrender value, which understates it at
    essentially every duration on a *gezillmert* contract.
    """
    r = min(0.0, res_guar_pp(k)) + min(0.0, surr_value_pp(12 * k + 11))
    if not is_paid_up(k):
        r += min(0.0, res_guar_pp(k) - res_zill_pp(k + 1))
        r += min(0.0, res_guar_pp(k) - res_min_pp(k + 1))
    return r


def check_surr_floor():
    """True when the § 169 Abs. 3 floor holds in every projected policy year.

    No argument, one bool over all policy years ``k``; :func:`check_surr_floor_resid` gives
    the signed residual of the year that failed.  The *Rückkaufswert* is also checked
    non-negative in **every month** by :func:`check_surr_nonneg`, because the monthly grid
    quotes one in eleven months the annual grid never priced.
    """
    tol = roll_fwd_tol() * max(sum_assured(), 1.0)                   # noqa: F821
    return all(abs(check_surr_floor_resid(k)) <= tol
               for k in range(k_start(), proj_len_y()))


def check_surr_nonneg_resid(t):
    """``min(0, surr_value_pp(t))``: the *Rückkaufswert* payable in month t, one-sided.

    Zero everywhere, and it exists because the monthly grid quotes a surrender value in the
    eleven months of each policy year the annual grid never priced.  Those months are paid on
    the **last** anniversary's § 169 value (:func:`res_guar_close_pp`), which is a different
    and smaller number than the one the annual model used — and in the first eleven months of
    a *gezillmert* contract it is exactly zero.  A model that reached for the coming
    anniversary's value instead would pay a forward-looking amount; a model that subtracted a
    *Stornoabzug* from a zero guaranteed value and forgot the *Überschussguthaben* could go
    negative.  This says it does not.
    """
    return min(0.0, surr_value_pp(t))


def check_surr_nonneg():
    """True when the *Rückkaufswert* is non-negative in every projected month."""
    tol = roll_fwd_tol() * max(sum_assured(), 1.0)                   # noqa: F821
    return all(abs(check_surr_nonneg_resid(t)) <= tol
               for t in range(t_start(), proj_len()))


def check_equivalence_resid(t):
    """The first-order pricing equivalence residual; the same value at every month t.

    ``B (1 - beta) a_m - alpha BS - tariff_benefit_pv - gamma SE a_n``.  It does not depend on
    ``t`` - the equivalence is struck once, at issue - and it carries the argument only so
    that every ``check_*`` in this library has the same shape.

    Note that it charges ``alpha_rate() * beitragssumme()`` and **not** :func:`zillmer_amount`:
    the acquisition cost is in the premium whether or not the contract is zillmered, which is
    why a *gezillmerte* and a non-*gezillmerte* edition of one tariff cost the same.
    """
    return (prem_gross_level_pp() * (1.0 - load_admin_prem_inst()) * tariff_annuity()
            - alpha_rate() * beitragssumme()
            - tariff_benefit_pv()
            - load_admin_sum_ann() * sum_assured() * tariff_term_annuity())


def check_equivalence():
    """True when the first-order pricing equivalence closes.

    No argument, one bool; :func:`check_equivalence_resid` gives the signed residual.  It is
    what makes :func:`prem_gross_level_pp` a derived quantity rather than an asserted one, and it is
    the only check that would fail if the *Beitragssumme* were formed on the loaded
    *Zahlbeitrag* instead of on the *Bruttobeitrag*.
    """
    tol = roll_fwd_tol() * max(sum_assured(), 1.0)                   # noqa: F821
    return all(abs(check_equivalence_resid(t)) <= tol
               for t in range(t_start(), proj_len()))


def check_rechnungszins_cap_resid(t):
    """The § 2 DeckRV ceiling residual; zero unless the guarantee exceeds the cohort's cap.

    ``min(0, hoechstrechnungszins() - rechnungszins())``, the same value at every ``t``.
    A **parameter invariant rather than a roll-forward identity**, and it lives in the model rather than in
    a build script because a German model point's cohort *is* an assumption: a 4,00 %
    guarantee on a 2026 issue year is not a stress, it is a data error.
    """
    return min(0.0, hoechstrechnungszins() - rechnungszins())


def check_rechnungszins_cap():
    """True when the contract's *Rechnungszins* is within its cohort's *Höchstrechnungszins*.

    No argument, one bool; :func:`check_rechnungszins_cap_resid` gives the signed shortfall.
    """
    return all(abs(check_rechnungszins_cap_resid(t)) <= roll_fwd_tol()  # noqa: F821
               for t in range(t_start(), proj_len()))


def check_zillmer_cap_resid(t):
    """The § 4 DeckRV ceiling residual; zero unless the *Zillmersatz* exceeds the cohort's cap.

    ``min(0, zillmer_max() - alpha_rate()) + min(0, zillmer_max() * beitragssumme()
    - zillmer_amount())``, the same value at every ``t``: the rate against the ceiling and the
    zillmered amount against the ceiling applied to the *Beitragssumme*.

    It is asserted **separately** from :func:`check_surr_floor` on purpose.  § 4 DeckRV caps
    **how much** may be zillmered at all - a cap on the *charge* - while § 169 Abs. 3 VVG
    fixes **how** the acquisition cost is spread for the surrender floor - a floor on the
    *value*.  Conflating the two is a documented failure mode, and one search summary in the
    research corpus does exactly that.
    """
    return (min(0.0, zillmer_max() - alpha_rate())
            + min(0.0, zillmer_max() * beitragssumme() - zillmer_amount()))


def check_zillmer_cap():
    """True when the *Zillmersatz* is within its cohort's *Höchstzillmersatz*.

    No argument, one bool; :func:`check_zillmer_cap_resid` gives the signed shortfall.
    """
    tol = roll_fwd_tol() * max(sum_assured(), 1.0)                   # noqa: F821
    return all(abs(check_zillmer_cap_resid(t)) <= tol
               for t in range(t_start(), proj_len()))


def result_surplus():
    """Result table of the surplus machinery and the reserves, indexed by ``policy_year``.

    **The annual frame, and deliberately so.** ``decl_rate``, ``zins_ueberschuss_rate``,
    ``surplus_base_pp``, ``surplus_credit_pp``, ``res_pp``, ``av_sur_pp`` and
    ``term_bonus_pp`` are annual **state** and move once a year; publishing them monthly would
    repeat each value twelve times and invite a reader to think a *Deckungskapital* accrues
    through the year.  ``surr_value_pp`` is the *Rückkaufswert* payable at that policy year's
    **anniversary**, ``surr_value_pp(12k + 11)``; what a mid-year surrender is paid is in
    :func:`result_cf` through :func:`res_guar_close_pp`, and is smaller.

    They are state, not cash flow, which is why they are published here rather than in
    :func:`result_cf`: a cash flow statement whose columns do not all sum to its bottom line
    is a statement a reader has to know which columns to skip.

    Read the first rows of this frame beside the first rows of :func:`result_cf_annual` and
    the product is visible in two numbers.  ``res_pp`` opens at ``-zillmer_amount()`` - the whole
    of the *Zillmerung*, unrecovered - while ``surplus_credit_pp`` is struck on the year's
    *closing* reserve and is therefore small but positive from the first year.  The gap
    between the two columns in the early durations is the entire economics of a German
    endowment's first years.
    """
    ks = list(range(k_start(), proj_len_y()))
    return pd.DataFrame(                                             # noqa: F821
        {
            "decl_rate": [decl_rate(k) for k in ks],
            "zins_ueberschuss_rate": [zins_ueberschuss_rate(k) for k in ks],
            "surplus_base_pp": [surplus_base_pp(k) for k in ks],
            "surplus_credit_pp": [surplus_credit_pp(k) for k in ks],
            "res_pp": [res_pp(k) for k in ks],
            "av_sur_pp": [av_sur_pp(k) for k in ks],
            "term_bonus_pp": [term_bonus_pp(k) for k in ks],
            "surr_value_pp": [surr_value_pp(12 * k + 11) for k in ks],
        },
        index=pd.Index([k + 1 for k in ks], name="policy_year"),     # noqa: F821
    )


# ---------------------------------------------------------------------------
# References

data = ("Interface", ("..", "Data"), "auto")

point_id = 1

pd = ("Module", "pandas")
