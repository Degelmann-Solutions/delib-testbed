# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The by-policy projection of the :mod:`~.RLV_DE_S` model.

The Space is parameterized by ``point_id``, so ``Projection[1]`` is an ItemSpace
projecting model point 1::

    >>> Projection[1].result_cf()          # the worked example's anchor cell
    >>> Projection.point_id = 8            # or switch the default

``t`` counts **policy months from issue** and is **0-based**, the clock
``basiclife.BasicTerm_S`` and the other nine delib models run on: ``t = 0`` is the first
policy month, month ``t`` runs from time ``t`` to time ``t + 1``, ``pols_if(t)`` is the
count at time ``t``, and ``proj_len() = 12 x policy_term`` is the **number** of projected
months — 300 on the anchor cell — and so the frame's **exclusive end**, the loop being
lifelib's ``for t in range(proj_len())``. A new-business model point opens at ``t = 0``;
an **in-force** model point opens at ``t = t_start() = 12 x duration_init``, so that
everything keyed to duration reads off one clock and needs no second one. There is nothing
after ``proj_len() - 1``: the survivors' cover simply expires, nothing is payable, and
``pols_if(proj_len())`` is exactly zero.

Everything *contractual* about this product is nevertheless on an **annual** cycle — the
level *Bruttobeitrag* struck once by first-order equivalence, the annual
*Überschussdeklaration* behind the *Beitragsverrechnung*, the *Versicherungssumme*
schedule, the *Nachversicherungsgarantie* increments, the § 161 three-year window, the
*Beitragszahlungsdauer*, the lapse table and the first-order *Deckungskapital* — and the
model keeps all of them there. So the policy year is derived and used as a lookup key
throughout: ``duration_mth(t) = t`` is the completed policy months at the start of month
``t``, ``duration(t) = duration_mth(t) // 12`` the completed policy years,
``policy_year(t) = duration(t) + 1`` the contractual 1-based label the three schedule CSVs
are keyed on, and the attained age is ``age(t) = issue_age + duration(t)``, stepping on
the anniversary and not monthly. The frame is indexed by ``t``; the policy year is derived
and never indexed by. Cover ends at attained age ``issue_age + policy_term``;
``cover_end_age()`` is derived from the term rather than carried beside it, so the two
cannot disagree.

The two-speed structure that follows is the library's convention: :func:`mort_rate` and
:func:`lapse_rate` are the **annual** rates of the policy year containing month ``t`` —
the vectors the technical notes tabulate — and :func:`mort_rate_mth` and
:func:`lapse_rate_mth` are the monthly rates actually applied, derived at
``1 - (1 - r)^(1/12)`` so that twelve of them compound back to exactly the year's rate.
:func:`result_cf_annual` sums the monthly frame into policy years, which is the view the
notes' worked example is stated on.

.. rubric:: Input data

Inputs are **external files**: plain CSVs living in the model folder's parent directory,
``products/risikolebensversicherung/``, read at run time rather than stored inside the
model. The model folder therefore holds nothing but formulas — no ``_data/``, no IOSpec,
no embedded values — so a diff of the model shows logic changes only, and an input can be
edited or swapped without rewriting the model. This follows ``annuallife.TradLife_A``;
contrast ``basiclife.BasicTerm_S``, which keeps its inputs *inside* the model through
modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``RLV_DE_S`` folder without its parent's CSVs produces a model that reads and then fails
on first evaluation.

Each table has a filename Reference and a reader Cells, both on
:mod:`~.RLV_DE_S.Data`, reached here through the ``data`` Reference:

========================  =================================  ==========================
Reference                 Cells                              File
========================  =================================  ==========================
model_point_file          data.model_point_table()           model_point_table.csv
mort_file                 data.mort_table()                  mort_table.csv
benefit_schedule_file     data.benefit_schedule()            benefit_schedule.csv
nvg_schedule_file         data.nvg_schedule()                nvg_schedule.csv
lapse_file                data.lapse_table()                 lapse_table.csv
prem_freq_file            data.prem_freq_table()             prem_freq_table.csv
param_file                data.param()                       param_tariff_type.csv
========================  =================================  ==========================

.. rubric:: Naming

Cells names follow lifelib's ``basiclife.BasicTerm_S`` wherever that model has an
analogue — ``pols_*`` for policy counts, plural nouns for cash flows, ``*_rate`` for
rates, ``*_pp`` for per-policy amounts, ``claims(t, kind)`` with an uppercase ``kind``
string, ``*_at(t, timing)`` for within-year reads. The technical notes use compact
actuarial symbols instead. The mapping is:

=========================  ==============================  ==========================
Notes symbol               Cells                           Meaning
=========================  ==============================  ==========================
(none)                     model_point()                   The selected model point row
n = policy_term            proj_len_y()                    Number of policy years
12 n                       proj_len()                      Number of projected months
t0 = 12 duration_init      t_start()                       First projected month index
(none)                     duration_mth(t)                 Completed policy months, = t
(none)                     duration(t)                     Completed policy years, t // 12
y = duration(t) + 1        policy_year(t)                  Contractual 1-based policy year
x(t)                       age(t)                          Attained age, first life
x2(t)                      age2(t)                         Attained age, second life
S0                         sum_assured()                   Initial Versicherungssumme
k                          prem_term()                     Beitragszahlungsdauer
f(t)                       benefit_factor(t)               Versicherungssumme schedule
u(t)                       sum_uplift(t)                   Cumulative NVG multiplier
B(t)                       benefit_pp(t)                   Versicherungssumme in year t
(none)                     benefit_paid_pp(t)              What a death claim pays
sigma(t)                   suicide_factor(t)               Para 161 benefit switch
q(x) tilde                 mort_rate_at_age(s, r, x)       Shipped table rate
Q(t) tilde                 mort_rate_base(t)               Own-sex rate, first death
(unisex blend)             mort_rate_blend(t)              50/50 blend, first death
q2(t)                      mort_rate(t)                    Second-order annual rate
q2m(t)                     mort_rate_mth(t)                The same, applied in month t
q1(t)                      mort_rate_tariff(t)             First-order tariff rate
(1 + m) rf                 mort_load_tariff(t)             Loading of the tariff rate
(unisex blend)             mort_rate_tariff_base(t)        Base of the tariff rate
rf                         rating_factor()                 Risikozuschlag multiplier
w(t)                       lapse_rate(t)                   Annual lapse rate of the year
wm(t)                      lapse_rate_mth(t)               The same, applied in month t
(table)                    lapse_rate_base(t)              Table lapse rate
w_cum(t)                   lapse_cum(t)                    Cumulative lapse proportion
M_shock(t)                 shock_lapse_factor(t)           Premium-shock multiplier
(gate)                     lapse_factor(t)                 0 in the final year, else M
(none)                     sel_lapse_factor(t)             Loading on persisters
v^y                        disc_factor(y)                  Rechnungszins discount
p1(y)                      pols_tariff(y)                  Tariff survivorship, no lapse
ae                         tariff_annuity()                Premium annuity-due
A                          tariff_benefit_pv()             APV of death benefits
Gamma                      tariff_term_annuity()           Sum-exposure annuity
B(y)                       tariff_schedule(y)              Sum insured of year y
G                          prem_gross_level_pp()           Bruttobeitrag, before phi
Gn                         prem_net_level_pp()             Actuarial Nettopraemie
v_d                        beitragsverrechnung_rate()      Beitragsverrechnungssatz
phi                        prem_freq_load()                Ratenzahlungszuschlag
G phi                      prem_pp(t)                      Bruttobeitrag, annual
v_d G phi                  prem_rebate_pp(t)               Beitragsverrechnung, annual
P(t)                       prem_paid_pp(t)                 Zahlbeitrag, annual
(none)                     instalments()                   Instalments a year, 1/2/4/12
(none)                     prem_cycle()                    Months between instalments
(none)                     prem_due(t)                     Is an instalment due in month t
(none)                     prem_charged_inst_pp(t)         Gross instalment collected
(none)                     prem_rebate_inst_pp(t)          Rebate netted off it
P_inst(t)                  prem_inst_pp(t)                 Zahlbeitrag instalment
(reserve)                  res_pp_at(y, timing)            First-order Deckungskapital
(gezillmert)               res_zill_pp_at(y, timing)       The same, less the Zillmer
l(t)                       pols_if(t)                      In force, start of period t
l(t)(1-q2m), l(t+1)        pols_if_at(t, timing)           BEF_DECR / AFT_DEATH / AFT_DECR
pols_death(t)              pols_death(t)                   Expected deaths in month t
pols_lapse(t)              pols_lapse(t)                   Expected lapses in month t
pols_maturity(t)           pols_maturity(t)                Expiring survivors, last month
premiums(t)                premiums(t)                     Zahlbeitrag income, billed
(none)                     benefit_death_pp(t)             benefit_paid_pp(t)
claims_death               claims(t, kind)                 Benefit outgo by kind
z k G                      acq_cost_pp()                   Acquisition cost at issue
c0 k G                     comm_init_pp()                  Initial Abschlussprovision
(1 + pi)^duration(t)       inflation_factor(t)             Expense inflation factor
maint(t)                   maint_pp(t)                     Admin plus collection cost
(acq_pp - comm_pp)         expenses_acq(t)                 Acquisition net of commission
maint(t) l(t)              expenses_maint(t)               Maintenance on the in-force
ec pols_death(t)           expenses_claim(t)               Claim expense per death
expenses(t)                expenses(t)                     Total expense, ex commission
comm_pp                    comm_init(t)                    comm_init_pp() at issue
(none)                     comm_renew(t)                   Bestandspflegeprovision
commissions(t)             commissions(t)                  Commission outgo
net_cf(t)                  net_cf(t)                       Net cash flow, income positive
liability_cf(t)            liability_cf(t)                 The same stream, outgo positive
(the notes' table)         result_cf_annual()              result_cf() summed by policy year
=========================  ==============================  ==========================

Four names needed care.

**The three "netto"s.** Three unrelated things are called *netto* in this product and
confusing them is the classic implementation error. :func:`prem_net_level_pp` is the
**actuarial** *Nettoprämie* ``Gn = A / ae``: the risk premium on the first-order basis
before expense loadings, a pricing quantity that never becomes a cash flow and is used
only by the reserve. :func:`prem_paid_pp` is the **consumer** *Zahlbeitrag*, what is
actually billed. The *Nettotarif* — a commission-free tariff sold through fee-based
advice — is a third, unrelated sense and is not modelled. The bare word *Nettobeitrag* is
never a name here, and ``prem_net_pp`` is on the library's retired-names register.

The order between the first two is worth stating, because the intuition gets it backwards:
on the shipped calibration ``prem_paid_pp(0)/phi = 733.01 < prem_net_level_pp() =
1 084.80 < prem_pp(0)/phi = 1 275.41``. The billed premium sits **below** the
actuarial net premium, because ``Gn`` is struck on the loaded first-order rate and 90 % of
that loading is handed straight back as *Beitragsverrechnung*. A test asserting
``Gn < P`` is asserting the absence of the product's central mechanic.

**``q1`` prices and ``q2`` projects.** :func:`mort_rate_tariff` is the first-order tariff
rate — the unisex 50/50 blend, loaded by ``mort_load_first``, the factor ``1 + m`` of the
*Sicherheitszuschlag* ``m``, and by the *Risikozuschlag* — and it enters the premium and the reserve and **nothing else**.
:func:`mort_rate` is the second-order rate on the policy's own sex and smoker status and
it drives every decrement and every claim. The ratio between them is *not* ``1 + m``: it
is ``2.25 x (unisex blend / own-sex rate)``, which on the shipped proxy is **1.6875 for a
male and 3.375 for a female**. That asymmetry is the unisex cross-subsidy and it is a
product fact, not a modelling artefact. Applying the *Sicherheitszuschlag* to the
projection is the pitfall; ``claims_death`` must be invariant to ``mort_load_first``
while ``prem_charged_inst_pp`` is not.

**``B(t)`` is the contractual sum; what a claim pays is not always ``B(t)``.**
:func:`benefit_pp` is ``S0 f(t) u(t)``, and :func:`benefit_paid_pp` applies the § 161
switch **tranche by tranche**: the base cover and each *Nachversicherungsgarantie*
increment carry their own three-year window, so in a year when one tranche is inside its
window and another is not, :func:`suicide_factor` — defined as the ratio of the two — is a
weighted average strictly between ``1 - suicide_share`` and ``1``. The switch touches
death claims and nothing else; it never reaches a lapse or an expiry, both of which pay
nothing in any event.

**``expenses`` here excludes ``commissions``.** The notes' identity is ``net_cf =
premiums - claims - expenses - commissions`` and :func:`result_cf` publishes the four
parts, so subtracting both is right rather than double-counting. That is the opposite
convention from ``frlib.TD_FR_S``, where the notes fold commission into the expense total,
and it is stated here because the two libraries' columns look alike and do not mean the
same thing. :func:`check_net_cf` is the identity in code.

.. rubric:: Two premium streams, and why one is not enough

This is the German delta, and both are cells of the model rather than one buried in a parameter.
The **Bruttobeitrag** ``G`` is struck once, at issue, by first-order equivalence on tariff
survivorship — mortality only, no lapse — so it is acyclic with respect to everything
behavioural::

    G = ( A + gamma Gamma ) / ( (1 - beta) ae - z k )

With ``prem_form = single`` the paying term ``k`` is 1 and ``ae`` is 1, so the same
expression returns the *Einmalbeitrag*: the second premium form is this engine at a
boundary, not a second engine.

The **Zahlbeitrag** follows from the surplus mechanic rather than from an assumption. The
tariff's own mortality margin has actuarial value ``(m/(1+m)) A`` at issue, and the
declared *Beitragsverrechnungssatz* returns ``surplus_share`` of it over the paying term::

    v_d = min( v_max, decl_scale surplus_share (m/(1+m)) A / (G ae) )
        = decl_scale surplus_share (m/(1+m)) [ 1 - beta - (gamma Gamma + z k G)/(G ae) ]

— the surplus share, times the margin fraction of the risk element, times the risk share
of the gross premium. On the anchor cell the bracket is 0.8506, so ``v_d = 0.42527476``
and ``Zahlbeitrag / Bruttobeitrag = 0.574725``, reproducing the research file's frozen
[std] ratio **from the mechanic rather than by assumption**. Raising the
*Sicherheitszuschlag* raises ``G`` and ``v_d`` together, which is why the *Bruttobeitrag*
moves far more than the *Zahlbeitrag* — the most useful single result in this product, and
the reason the billed premium is derived.

``surplus_form = keine`` is the § 153-excluded non-participating tariff: ``v_d`` is zero
and the billed premium *is* the guaranteed one, which is model point 12.

.. rubric:: Modules that are off in the base run

Two behavioural constructions are implemented and switched off, so the base run reproduces
the worked example while the machinery stays visible and testable:

- **Premium-shock lapse**, ``shock_lapse_lambda = 0``.
  ``M_shock(t) = 1 + lambda_s max(0, prem_paid_pp(t)/prem_paid_pp(t-1) - 1)``. The
  product's distinctive behavioural risk is that the insurer can raise the bill without
  changing a guaranteed term, simply by cutting the declaration — no § 163 procedure, no
  *Treuhänder*, no policyholder remedy. The module is inert in the base run because the
  billed premium is level there; it bites exactly when ``decl_scale`` is stressed, which
  is when it should. A stress that raises the *Zahlbeitrag* toward the *Bruttobeitrag* and
  leaves lapse unchanged is understating itself.
- **Selective lapse**, ``sel_lapse_lambda = 0``, with ``sel_lapse_ref = 0.25``.
  ``q2_eff = q2 (1 + lambda max(0, w_cum - w_ref))``. Healthy lives can re-underwrite into
  a cheaper contract and impaired lives cannot, so persisters' mortality drifts up. delib
  does not model it in the base run — one basis for stayers and leavers — which is a
  stated simplification rather than an oversight.

Both are driven off the premium and the lapse table alone, never off ``pols_if``, so the
projection stays acyclic: a pricing quantity struck by equivalence cannot depend on a
behavioural assumption that depends on the path that depends on the premium.

.. rubric:: No cash value, anywhere — and yet a reserve

§ 169 Abs. 1 VVG confines the surrender-value duty to a life insurance whose insured event
is certain to occur; a term assurance's is not, so there is no *Rückkaufswert*. § 165's
*Beitragsfreistellung* right and § 166's paid-up conversion on non-payment both collapse
into the same nil through the minimum-benefit test, the paid-up sum a term contract's
reserve buys failing it in most durations. So a lapse is a pure decrement: it moves
``pols_if`` and pays nothing, ``claims(t, "LAPSE")`` and ``claims(t, "MATURITY")`` are
zero columns published rather than dropped, and :func:`check_no_cash_value` asserts it on
every model point. The 30-day § 152 *Widerrufsfrist* sits inside the year-one lapse rate
**[std]**.

What is **not** true is that nothing accumulates. A level premium charged against a rising
death rate necessarily overcharges early and undercharges late, and the difference is a
*Deckungskapital* that builds, peaks near the middle of the term and runs off to exactly
zero at expiry — on the anchor cell it peaks at 7 553,29 €, 2,5 % of the sum insured, at
``t = 15``. :func:`res_pp_at` publishes it and :func:`check_res_roll_fwd` asserts the
Thiele recursion, ``res_pp_at(0) = 0`` by the equivalence and ``res_pp_at(n) = 0`` by
exhaustion. **It is a pricing diagnostic and not a balance-sheet provision**: it is net,
it is not *gezillmert*, it is not floored, it enters no cash flow, and nothing in this
library discounts a published cash flow. :func:`res_zill_pp_at` subtracts the unamortised
Zillmer balance and is ``-z k G`` at ``t = 0`` — negative from the first day and back to
zero at expiry, which is what *Zillmerung* on a contract with almost no reserve looks like.

.. rubric:: The last policy year has no lapse, and why

Lapses fall at the **end** of the month, after the death decrement, and the end of the
last month ``t = proj_len() - 1`` is the moment cover expires. A lapse and an expiry are
then the same event paying the same nothing, so :func:`lapse_rate` returns 0 through the
**whole of the final policy year** — ``duration(t) >= proj_len_y() - 1``, months 288 to
299 on the anchor cell — and the surviving cohort leaves through :func:`pols_maturity`
instead. The zero covers the year rather than merely its last month because that is what
the annual-step model this replaced said of it, and it is what keeps the expiring cohort
at the figure the notes publish. The table's own row for policy year ``n`` still reads
3 %: the zero is a property of the last policy year, not of the assumption, and putting
it in the formula is what keeps the two readable apart.

No cash flow moves either way — the split only decides how the closure identity divides
between the three exits — but the identity itself is load-bearing, and
:func:`check_pols_roll_fwd` asserts that they account for the whole cohort:
``0.03261764`` deaths, ``0.53597922`` lapses and ``0.43140314`` expiries on the anchor
cell, summing to ``pols_if_init() = 1`` exactly. The expiring cohort is the annual-step
model's own figure to the last digit, because it is a survivorship the two grids share;
the **split between deaths and lapses** moved by 0.00044, which is the one thing
interleaving the two decrements monthly genuinely changes — on an annual grid a year's
lapses are taken from a block that has already borne the whole year's mortality, and on a
monthly one each decrement erodes the exposure the other works on.

.. rubric:: Sign convention

:func:`net_cf` is **income positive** — billed premiums in, claims, expenses and
commission out — which is the notes' own orientation and the library-wide sign.
:func:`liability_cf` publishes the same stream outgo-positive,
``liability_cf(t) = -net_cf(t)`` exactly, so a best-estimate liability is
``sum v(t) liability_cf(t)`` over whatever discount curve the valuation layer supplies.
Both are columns of :func:`result_cf`, so the identity is verifiable in the frame rather
than only in prose.

The shape to expect on the anchor, read on :func:`result_cf_annual`, is a year-one strain
of -351,88 €, the acquisition cost and the initial commission together exceeding the first
year's billed premium; thin positive years while the level premium runs ahead of the
natural risk premium; and a crossover in **policy year 14** after which the rising death
rate takes the year negative. Within policy year 1 the monthly frame shows the shape the
annual grid could not: +733,01 € of premium against 826,64 € of acquisition cost and
commission in month 0, a net -108,90 €, then eleven months of about -22 € each as claims
and maintenance accrue against no further premium. The **total** is -644,78 € on model
point 1 and strongly positive on model point 2, and the difference is the unisex
cross-subsidy: the tariff prices a 50/50 blend, the declaration returns 90 % of the margin
measured against that blend, and a male life then claims a third more than the tariff's
own best estimate while paying the same premium as a female one. That is the product
working as the law requires it to, not a defect.

.. rubric:: What the monthly grid changes, and what it does not

The grid is monthly; the **product is not**. Every contractual mechanic stays exactly
where the contract puts it, and each of the following is a decision taken deliberately
rather than inherited from the frame:

- the whole first-order equivalence — the *Bruttobeitrag* ``G``, the *Nettoprämie* ``Gn``,
  the *Beitragsverrechnungssatz* ``v_d`` and the *Deckungskapital* — stays an **annual**
  construction on policy-year arguments (:func:`disc_factor`, :func:`pols_tariff`,
  :func:`res_pp_at`), so every one of them is **bit-identical** to the annual-step model's;
- the *Versicherungssumme* schedule and the *Nachversicherungsgarantie* steps on the
  **anniversary** (:func:`benefit_factor`, :func:`sum_uplift`), so a declining sum insured
  does not decline monthly;
- the § 161 three-year window runs in whole years from issue, tranche by tranche
  (:func:`benefit_paid_pp`), and every boundary it has therefore falls on an anniversary;
- the *Beitragszahlungsdauer* ends on an anniversary (:func:`prem_pp`) and the
  *Bestandspflegeprovision* starts on one (:func:`commissions`);
- expenses inflate **by policy year**, stepping on the anniversary
  (:func:`inflation_factor`), which is ``Sofort_DE_S``'s form rather than ``FRV_DE_S``'s
  continuous one;
- the zero lapse rate of the final projected year covers that whole **year**
  (:func:`lapse_rate`), because the annual model stated it of a year;
- the premium-shock module compares **consecutive renewals** twelve months apart
  (:func:`shock_lapse_factor`) and the selective-lapse loading reads a cumulative lapse
  built from the monthly rates (:func:`lapse_cum`), so both stay experience statements
  about a year rather than about a month.

What the finer grid does resolve is everything that is **not** a contract term. The
*Zahlweise* is now real: a modal *Zahlbeitrag* is collected in instalments on its own
cycle (:func:`prem_inst_pp`) instead of whole at the anniversary, so the four
fractionated model points collect 0,95 %-1,67 % less over the run — model point 4's
`monthly` premium income falls from 4 471,82 € to 4 400,26 € — which is the
premium-cessation rule biting where an annual grid could not express it, and the
*Ratenzahlungszuschlag* at last charging for a service the model renders. Claims fall in
the month of claim rather than at the year end, so the anchor's death claims fall from
9 899,20 € to 9 768,05 €. Maintenance accrues a twelfth a month on the in-force of that
month rather than of the anniversary, so expense falls from 2 396,51 € to 2 367,66 €. And
§ 168 VVG's *Versicherungsperiode*, which follows the *Zahlweise* and which the annual
grid could only book at anniversaries and call an approximation, is simply expressed.

That is also what makes the two grids reconcile. Because the monthly death rate and the
monthly lapse rate each compound back to their policy year's annual rate, the recursion
collapses over any twelve months of one policy year to
``l(t+12) = l(t)(1 - q2(t))(1 - w(t))`` — the annual-step recursion, term for term — so
``pols_if(12k)`` here equals the annual model's ``pols_if(k)`` to 4e-15 across all
fourteen model points, and every annual contractual quantity is unmoved.
:func:`result_cf_annual` sums the frame into policy years so the two can be laid side by
side.
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

def smoker_codes():
    """The codes of the *Nichtraucher* / *Raucher* status, N and R.

    The largest rating split after age, and unlike ``sex`` it is a lawful one: the DAV
    *Richtlinie* states that DAV 2008 T R and DAV 2008 T NR are in principle suitable for
    premium calculation differentiated by smoking status — **but not for policies written
    without a *Gesundheitsprüfung***, which is why simplified-issue German death covers
    are aggregate-rated.  It enters both mortality bases, so a smoker pays more *and* is
    expected to claim more.

    Override reason: the product codes a smoker as ``R`` (*Raucher*), as its
    ``mort_table.csv`` does, products/risikolebensversicherung/technical-notes.md:162
    """
    return ("N", "R")


def prem_form():
    """The premium form: ``regular`` or ``single``.

    ``regular`` is a level *Bruttobeitrag* over ``prem_term`` years and is the German
    market form.  ``single`` is a **[std]** construction — no German standalone
    *Risikolebensversicherung* in the research corpus is written on a single premium — and
    is carried because it is the degenerate case ``k = 1`` of the same equivalence, so it
    exercises the premium engine at a boundary rather than adding a second engine.  The
    cells is a stated consistency gate: ``single`` requires ``prem_term = 1``.

    Override reason: a single premium is the paying term ``k = 1`` of the same equivalence,
    so it requires ``prem_term = 1``, products/risikolebensversicherung/technical-notes.md:166
    """
    v = model_point()["prem_form"]
    if v not in ("regular", "single"):
        raise ValueError("invalid prem_form")
    if v == "single" and prem_term() != 1:
        raise ValueError("single requires prem_term = 1")
    return v


def benefit_schedule_id():
    """The key into *benefit_schedule.csv* naming this policy's *Versicherungssumme* shape."""
    return model_point()["benefit_schedule_id"]


def nvg_schedule_id():
    """The key into *nvg_schedule.csv* naming this policy's *Nachversicherungsgarantie*."""
    return model_point()["nvg_schedule_id"]


def surplus_form():
    """``beitragsverrechnung`` or ``keine``.

    ``beitragsverrechnung`` is the market form and the base design: the declared surplus
    is netted against the *Bruttobeitrag* before billing.  ``keine`` is the § 153-excluded
    non-participating tariff — lawful, since participation may be excluded by express
    agreement, and not the market form; none was located.  It sets
    :func:`beitragsverrechnung_rate` to zero, so the billed premium *is* the guaranteed
    one, which is model point 12 and the cleanest available control on the whole surplus
    mechanic.
    """
    v = model_point()["surplus_form"]
    if v not in ("beitragsverrechnung", "keine"):
        raise ValueError("invalid surplus_form")
    return v


def lives():
    """1 for a single life, 2 for *verbundene Leben* paying on the **first** death.

    One chassis parameterised by the number of lives, not two products.  Both lives are
    underwritten and both give the § 150 VVG *schriftliche Einwilligung*; one payment is
    ever made and the contract then ends.
    """
    n = int(model_point()["lives"])
    if n not in (1, 2):
        raise ValueError("lives must be 1 or 2")
    return n


def issue_age2():
    """The *Eintrittsalter* of the second life; 0 where ``lives = 1``."""
    return int(model_point()["issue_age2"])


def smoker2():
    """The second life's smoker status, R or N; ``-`` where ``lives = 1``."""
    v = model_point()["smoker2"]
    if v not in smoker_codes() + ("-",):
        raise ValueError("invalid smoker2")
    if lives() == 2 and v == "-":
        raise ValueError("lives = 2 requires a smoker2 of N or R")
    return v


def mort_table_id():
    """The key into *mort_table.csv*; one table ships, ``dav2008t_proxy``."""
    return model_point()["mort_table_id"]


def issue_date():
    """The issue date, for reporting only; the model runs on integer durations."""
    return model_point()["issue_date"]


def cover_end_age():
    """The attained age at which cover ends, ``issue_age + policy_term``.

    **Derived, never carried**, so the term and the end age cannot disagree.  The last
    covered policy year is the one at attained age ``cover_end_age() - 1``.
    """
    return issue_age() + policy_term()


def age2(t):
    """x2(t): the attained age of the second life, ``issue_age2 + duration(t)``.

    Meaningless and unused where ``lives = 1``; :func:`mort_rate_base` never reads it
    there.  Steps on the anniversary, like :func:`age`.
    """
    return issue_age2() + duration(t)


# ==========================================================================
# Mortality: the shipped table, and the two orders built from it


def mort_rate_at_age(sex_code, smoker_code, x):
    """q(x) tilde: the shipped second-order table rate for one life at one attained age.

    A lookup into *mort_table.csv* keyed by ``table_id``, sex, smoker status and attained
    age, and nothing else — no loading, no rating, no combination across lives.  Both
    orders and both lives are built from this one cells, which is what keeps the model's
    unsourced mortality level to a single number.  A **[std]** proxy for DAV 2008 T; see
    the ``Data`` docstring for the anchors a replacement must preserve.
    """
    return float(data.mort_table_dict()["mort_rate"][                # noqa: F821
        (mort_table_id(), sex_code, smoker_code, int(x))])


def mort_rate_base(t):
    """Q(t) tilde: the table rate on the policy's **own** sex, before loading or rating.

    For ``lives = 2`` the two lives are combined **at table level, before any loading**,
    on an independence assumption **[std]**::

        Q = q_A + q_B - q_A q_B

    which is the first-death rate of two independent lives.  Combining *after* loading
    inflates the cross term and is a listed pitfall.  The independence assumption
    understates the true first-death rate for a couple sharing a household, a vehicle and
    a lifestyle, and no German figure bounds the understatement.

    Override reason: the table rate is read on sex and smoker status, and for two lives
    combined to the first-death rate before loading,
    products/risikolebensversicherung/model.md:495
    """
    q_a = mort_rate_at_age(sex(), smoker(), age(t))
    if lives() == 1:
        return q_a
    q_b = mort_rate_at_age(sex(), smoker2(), age2(t))
    return q_a + q_b - q_a * q_b


def mort_rate_blend(t):
    """The unisex 50/50 blend of the sex-distinct table rates — the **tariff's** life.

    ``unisex_mix_male()``, the core's, weights the male table and its complement the female
    one, and for ``lives = 2`` the two blends are combined by the same first-death rule as
    :func:`mort_rate_base`, again **before** any loading.  This is what a German tariff is
    priced on, because sex may not enter the premium while the underlying tables remain
    sex-distinct.  The mixing ratio is proprietary at every carrier and the 50/50 here is
    **[std]**.
    """
    w_m = unisex_mix_male()
    q_a = (w_m * mort_rate_at_age("M", smoker(), age(t))
           + (1.0 - w_m) * mort_rate_at_age("F", smoker(), age(t)))
    if lives() == 1:
        return q_a
    q_b = (w_m * mort_rate_at_age("M", smoker2(), age2(t))
           + (1.0 - w_m) * mort_rate_at_age("F", smoker2(), age2(t)))
    return q_a + q_b - q_a * q_b


def sel_lapse_factor(t):
    """The selective-lapse loading on persisters' mortality; 1.0 in the base run.

    ``1 + sel_lapse_lambda max(0, lapse_cum(t) - sel_lapse_ref)``.  Healthy lives can
    re-underwrite into a cheaper contract and impaired lives cannot, so the lapsing
    population is healthier than the remaining one and a term book's mortality drifts up
    relative to a table calibrated on the whole cohort.  **delib does not model selective
    lapse in the base run** — ``sel_lapse_lambda = 0``, one basis for stayers and leavers —
    which is a stated simplification rather than a pitfall.  It is driven off
    :func:`lapse_cum`, which is built from the lapse rates alone and never from
    :func:`pols_if`, so switching it on does not make the projection circular.
    """
    return 1.0 + data.param("sel_lapse_lambda") * max(               # noqa: F821
        0.0, lapse_cum(t) - data.param("sel_lapse_ref"))             # noqa: F821


def mort_rate(t):
    """q2(t): the **second-order** annual death rate actually projected.

    ``mort_be_factor x rating_factor x mort_rate_base(t) x sel_lapse_factor(t)`` — the
    policy's own sex and smoker status, rated, first-death where there are two lives, and
    loaded for selective lapse where that module is on.  This drives every decrement and
    every claim, and the *Sicherheitszuschlag* must not appear in it: ``claims_death`` is
    invariant to ``mort_load_first`` while ``prem_charged_inst_pp`` is not, and an
    implementation that projects on ``q1`` overstates claims by a factor of about two.

    ``mort_be_factor`` is 1.00, so the shipped proxy **is** the best estimate and there is
    exactly one unsourced mortality level in the model rather than two stacked on each
    other.  A user with experience data should move this rather than editing the table.

    It is the **annual** rate of the policy year containing month ``t`` — the vector the
    technical notes tabulate — and is flat across that year's twelve months, the attained
    age stepping on the anniversary.  What the projection applies is
    :func:`mort_rate_mth`.

    Override reason: the second-order rate carries the *Risikozuschlag* and the
    selective-lapse loading, products/risikolebensversicherung/model.md:496
    """
    return (mort_be_factor() * rating_factor()
            * mort_rate_base(t) * sel_lapse_factor(t))


def mort_load_tariff(t):
    """The loading of the first-order tariff rate, ``mort_load_first x rf = (1 + m) x rf``.

    q1(t), :func:`mort_rate_tariff`, is this times the unisex blend, its base.  It prices
    the *Bruttobeitrag* and the first-order *Deckungskapital* and enters nothing else.  The
    *Sicherheitszuschlag* ``m = 1.25``, the row ``mort_load_first = 1 + m = 2.25`` of
    *param_tariff_type.csv*, is **[std]**: the DAV *Richtlinie* regulates the
    **procedure** for setting the *Sicherheitszuschläge*, not the level, which is not
    public, and the argued range is 1.0 to 1.5.  It is the single parameter that sets the
    *Brutto* / *Zahlbeitrag* spread — and, because 90 % of the extra margin is returned as
    *Beitragsverrechnung*, the parameter with the widest uncertainty has the narrowest
    effect on the billed premium.

    ``mort_rate_tariff(t) / mort_rate(t)`` is **not** ``1 + m``.  It is
    ``(1 + m) x (blend / own-sex rate)``, which on the shipped proxy is 1.6875 for a male
    and 3.375 for a female.  That is the unisex cross-subsidy, and expecting 2.25 for both is a
    listed pitfall.

    Override reason: the tariff rate is the unisex blend loaded by ``1 + m`` and the rating
    factor, products/risikolebensversicherung/technical-notes.md:231
    """
    return data.param("mort_load_first") * rating_factor()           # noqa: F821


def mort_rate_tariff_base(t):
    """The base of the first-order tariff rate: the unisex blend, :func:`mort_rate_blend`.

    Override reason: the tariff rate is the unisex blend combined over two lives by the
    first-death rule, not one table read at the attained age,
    products/risikolebensversicherung/technical-notes.md:231
    """
    return mort_rate_blend(t)


# ==========================================================================
# The Versicherungssumme, and the para 161 benefit switch


def benefit_factor(t):
    """f(t): the *Versicherungssumme* schedule factor, from *benefit_schedule.csv*.

    1.0 at every year on ``konstant``; ``(20 - y)/20`` on ``linear_fallend``; and the
    outstanding balance of a thirty-year annuity loan at 3 % on
    ``annuitaet_fallend_3pct``.  The file is keyed on the contractual **1-based**
    ``policy_year``, so the lookup maps through :func:`policy_year` and the factor is
    **flat across a policy year's twelve months**: the *Versicherungssumme* steps on the
    anniversary, which is where the contract steps it, and the monthly grid does not make
    a declining sum insured decline monthly.  The last shape is the *Darlehensabsicherung*
    one and it falls **slowly then fast** — the property a linear schedule gets backwards,
    and the reason a linear sum is a poor match to an annuity loan.  The rate is a
    contractual schedule parameter fixed at issue; it does not follow the borrower's loan
    if that is refinanced, repaid early or rolled onto a new fixed rate.
    """
    return float(data.benefit_schedule_dict()["benefit_factor"][     # noqa: F821
        (benefit_schedule_id(), policy_year(t))])


def sum_uplift_y(y):
    """u(y): the cumulative *Nachversicherungsgarantie* multiplier at **policy year** y.

    From *nvg_schedule.csv*, keyed on the contractual **1-based** ``policy_year``, so the
    lookup is at ``y + 1`` for the 0-based ``y``.  Defined for ``y >= 0`` only: the tranche
    decomposition in :func:`benefit_paid_pp` takes the base cover as its first tranche with
    ``delta u(0) = u(0)`` and never reaches below ``y = 0``.  1.0 throughout on ``keine``,
    the base run.

    The argument is a **policy year and not a month**.  A *Nachversicherungsgarantie*
    increment is granted at a policy anniversary, and its own § 161 window is a whole
    number of years from that anniversary, so the tranche decomposition is an annual
    construction on both counts and stays one on the monthly grid.

    Take-up is exogenous: no event list, cap, exercise window or age limit was established
    from any document, so an increase is supplied as a schedule rather than modelled as a
    decision.  What the model does *with* an increase is not exogenous — see
    :func:`benefit_paid_pp`.
    """
    return float(data.nvg_schedule_dict()["sum_uplift"][             # noqa: F821
        (nvg_schedule_id(), int(y) + 1)])


def sum_uplift(t):
    """u(t): the cumulative *Nachversicherungsgarantie* multiplier in month t.

    ``sum_uplift_y(duration(t))`` — the policy year's multiplier, flat across its twelve
    months.  The month-indexed face of :func:`sum_uplift_y`, so that :func:`benefit_pp`
    and :func:`result_pols` read one clock.
    """
    return sum_uplift_y(duration(t))


def benefit_pp(t):
    """B(t): the *Versicherungssumme* in force in period t, ``S0 f(t) u(t)``.

    The **contractual** sum.  What a death claim actually pays is
    :func:`benefit_paid_pp`, which is smaller inside a § 161 window.  Note what does *not*
    enter here: ``rating_factor`` is a mortality loading, not a benefit uplift, and a
    model that lets it scale the sum insured has confused a price with a promise.
    """
    return sum_assured() * benefit_factor(t) * sum_uplift(t)


def benefit_paid_pp(t):
    """What a death claim in period t actually pays, after the § 161 switch.

    § 161 VVG makes the insurer *leistungsfrei* where the *versicherte Person*
    intentionally takes her own life **within three years of conclusion**, unless the act
    was committed in a state excluding free determination of the will caused by a
    *krankhafte Störung der Geistestätigkeit*; the period may be extended by agreement;
    and where *leistungsfrei* the insurer must nevertheless pay the *Rückkaufswert* — which
    on this product is **nil**.  So on a term contract the rule is an exclusion in all but
    name, and the model carries it as a **benefit switch**, never as a decrement
    adjustment.

    The switch runs **tranche by tranche**, and it runs on **policy years**.  The base
    cover's window runs from issue; a *Nachversicherungsgarantie* increment granted at the
    anniversary opening policy year ``s`` carries **its own** window
    ``s <= duration(t) < s + suicide_years`` [unverified — German AVB practice is
    understood to restart the clock for the increment, and no statutory treatment was
    established].  With ``delta u(s) = u(s) - u(s - 1)`` for ``s > 0`` and
    ``delta u(0) = u(0)``::

        benefit_paid_pp(t) = S0 f(t) sum_s delta u(s) sigma_s(t)
        sigma_s(t) = 1 - suicide_share  if duration(t) < s + suicide_years, else 1

    Both clocks are annual and both boundaries therefore fall on an anniversary, so the
    monthly grid resolves the switch exactly rather than approximately: § 161's three
    years from conclusion are months 0 to 35, and ``duration(t) < 3`` is the same
    statement as ``t < 36``.  The comparison is left in years because that is the unit
    the statute and the *Bedingungen* use.

    On an in-force point with ``duration_init >= 3`` and no increments the switch is inert at
    every projected ``t``, which is model point 8.  ``suicide_share = 0.03`` is **[std]**
    with an argued range of 0.01 to 0.05: no German cause-of-death share was retrieved.
    It carries three times the weight of the French one-year factor simply because the
    German window is three times as long.
    """
    total = 0.0
    for s in range(duration(t) + 1):
        delta = sum_uplift_y(s) - (sum_uplift_y(s - 1) if s > 0 else 0.0)
        if delta == 0.0:
            continue
        sigma = ((1.0 - data.param("suicide_share"))                 # noqa: F821
                 if duration(t) < s + data.param("suicide_years") else 1.0)  # noqa: F821
        total += delta * sigma
    return sum_assured() * benefit_factor(t) * total


def suicide_factor(t):
    """sigma(t): the § 161 switch as a ratio, ``benefit_paid_pp(t) / benefit_pp(t)``.

    Exactly ``1 - suicide_share`` while the only tranche in force is inside its window,
    exactly 1 once every tranche is out of one, and **strictly between the two** in a year
    when one tranche is inside its window and another is not — which is what the tranche
    decomposition buys and what a single policy-level flag would get wrong.  Defined as
    the ratio rather than the other way round, so the weighting across tranches is done
    once, in euros, where it belongs.
    """
    b = benefit_pp(t)
    if b == 0.0:
        return 1.0
    return benefit_paid_pp(t) / b


# ==========================================================================
# Lapse


def shock_lapse_factor(t):
    """M_shock(t): the premium-shock lapse multiplier; 1.0 in the base run.

    ``1 + shock_lapse_lambda max(0, prem_paid_pp(t)/prem_paid_pp(t-12) - 1)``, and 1.0
    through the whole of policy year 1, which has no preceding bill to compare with.  The
    product's distinctive behavioural risk is that the insurer can raise the customer's
    bill without changing a guaranteed term, simply by cutting the *Beitragsverrechnung*:
    no § 163 procedure, no *Treuhänder* and no policyholder remedy, because no guaranteed
    term has moved.  The module is inert in the base run because the billed premium is
    level there — it bites exactly when ``decl_scale`` is stressed, which is when it
    should.  Depends on the premium and never on ``pols_if``, so it does not make the
    projection circular.

    The ratio is between **consecutive renewals** and so reads the annual *Zahlbeitrag*
    twelve months back, not one.  :func:`prem_paid_pp` is the year's whole billed premium
    rather than the instalment, so the comparison is between two annual bills under every
    *Zahlweise*; comparing consecutive **instalments** would make the module fire on the
    *Zahlweise* rather than on the declaration, and on an annual payer it would divide by
    a zero bill in eleven months of twelve.
    """
    if data.param("shock_lapse_lambda") == 0.0 or duration(t) <= 0:  # noqa: F821
        return 1.0
    prev = prem_paid_pp(t - 12)
    if prev <= 0.0:
        return 1.0
    return 1.0 + data.param("shock_lapse_lambda") * max(             # noqa: F821
        0.0, prem_paid_pp(t) / prev - 1.0)


def lapse_factor(t):
    """The factor on the table lapse rate: 0 through the final policy year, else the shock.

    ``duration(t) >= proj_len_y() - 1`` closes the lapse, where cover expires; elsewhere it
    is :func:`shock_lapse_factor`, 1.0 in the base run.

    The end of the final year is the moment cover expires, so a lapse and an expiry are then
    the same event paying the same nothing, and the whole surviving cohort is booked through
    :func:`pols_maturity` instead.  The zero covers the **year** and not merely its last
    month, because that is what the annual-step model this replaced said of it: zeroing only
    the last month would leave eleven months of 3 % lapse inside the final year and move the
    expiring cohort away from the notes' own figure.  No cash flow moves either way — the
    convention only decides how the closure identity divides between lapses and expiries —
    but it is load-bearing for that identity, and putting it here rather than in the table
    keeps the assumption and the convention readable apart.

    Override reason: the lapse is zero through the whole final policy year, where cover
    expires, and loaded by the premium-shock multiplier elsewhere,
    products/risikolebensversicherung/technical-notes.md:762
    """
    if duration(t) >= proj_len_y() - 1:
        return 0.0
    return shock_lapse_factor(t)


def lapse_cum(t):
    """w_cum(t): the cumulative lapse proportion entering period t.

    ``1 - prod (1 - wm(s))`` over the projected **months** before ``t``.  A proportion of
    the original cohort on a **lapse-only** basis, not a running total of
    :func:`pols_lapse` and not read off :func:`pols_if`: it feeds
    :func:`sel_lapse_factor`, which loads *mortality*, so building it from the in-force
    count would close a loop between the two decrements.  Zero at ``t = t_start()``.

    Built on the **monthly** rate, so that at every anniversary it equals the annual-step
    model's own figure exactly — twelve months of ``wm`` compounding back to the year's
    ``w`` — while inside a policy year it now advances month by month instead of jumping
    at the anniversary.
    """
    if t <= t_start():
        return 0.0
    surv = 1.0
    for s in range(t_start(), t):
        surv *= (1.0 - lapse_rate_mth(s))
    return 1.0 - surv


# ==========================================================================
# Pricing: the Bruttobeitrag by first-order equivalence, struck once at issue


def tariff_schedule(y):
    """B(y): the sum insured of policy year y, ``benefit_pp(12 y)``, read at its opening month.

    The death benefits' present value, :func:`tariff_benefit_pv`, is ``sum v^(y+1) p1(y)
    q1(y) B(y)`` over the whole cover period, ``y = 0 .. n - 1``, benefits paid at the end
    of the **policy year** of death.  It is the quantity the whole product turns on: the
    *Bruttobeitrag* is built from it and the *Beitragsverrechnungssatz* returns
    ``surplus_share`` of ``m/(1+m)`` of it.  The end-of-year benefit timing is the
    **tariff's** convention and is not the projection's: the cash flow statement pays a
    death claim at the end of the month of death.  The same schedule weights the
    sum-exposure annuity :func:`tariff_term_annuity`, the base of the gamma loading.

    Override reason: the sum insured follows the benefit schedule and any
    *Nachversicherungsgarantie* uplift, products/risikolebensversicherung/technical-notes.md:227
    """
    return benefit_pp(12 * y)


def prem_gross_level_pp():
    """G: the level *Bruttobeitrag* per policy, **before** the *Ratenzahlungszuschlag*.

    Struck once, at issue, by first-order equivalence with the alpha loading a per-mille
    of the *Beitragssumme* ``k G`` incurred at issue::

        G ae = A + z k G + beta G ae + gamma Gamma

    which is linear in ``G`` and solves in closed form::

        G = ( A + gamma Gamma ) / ( (1 - beta) ae - z k )

    ``z = 0.025`` is the *Höchstzillmersatz* — 25 permille of the *Beitragssumme*, cut
    from 40 permille by the LVRG with effect from 1 January 2015 — and the composite
    **assumes a term tariff runs at the cap**, which may well be wrong: a slim
    direct-channel acquisition cost would sit far below it.  That is the single **[std]**
    charge most likely to be overstated in this model.  ``beta = 0.05`` and
    ``gamma = 0.00030`` are **[std]** placeholders: German term-life charge levels are
    structurally undisclosed — no *Effektivkostenquote*, because a reduction in yield
    presupposes a yield; no *Basisinformationsblatt*, because the product is not a PRIIP;
    and the *Produktinformationsblatt* quotes premiums, not loadings.

    **This is the guaranteed premium** — the maximum the policyholder can ever be required
    to pay, unchanged for the term.  It is not what is billed.
    """
    denom = ((1.0 - data.param("load_admin_prem_inst")) * tariff_annuity()  # noqa: F821
             - data.param("load_acq_bsum_once") * prem_term())       # noqa: F821
    if denom <= 0.0:
        raise ValueError("degenerate premium equivalence: loadings exceed the annuity")
    return (tariff_benefit_pv()
            + data.param("load_admin_sum_ann") * tariff_term_annuity()) / denom  # noqa: F821


def beitragsverrechnung_rate():
    """v_d: the declared *Beitragsverrechnungssatz*, struck once at issue.

    **Derived from the surplus mechanic, not assumed.**  The tariff's own mortality margin
    in year ``t`` is ``(q1 - q1/(1+m)) B = (m/(1+m)) q1 B`` per in-force policy, so its
    actuarial value at issue is exactly ``(m/(1+m)) A``, with ``1 + m`` the row
    ``mort_load_first`` and so ``m/(1+m) = (mort_load_first - 1) / mort_load_first``.  The
    declaration returns ``surplus_share`` of it over the paying term::

        v_d = min( v_max, decl_scale surplus_share (m/(1+m)) A / (G ae) )

    ``surplus_share = 0.90`` is the **MindZV minimum allocation from the
    *Risikoergebnis***, and modelling the statutory minimum is the conservative choice for
    the billed premium and the only level any instrument fixes — no German carrier
    publishes a declaration for this product.  ``decl_scale = 1.00`` is the stress lever:
    setting it to 0 raises the billed premium to the guaranteed one at every ``t``, with
    no change to any claim, no § 163 procedure, no *Treuhänder* and no policyholder
    remedy.  On the anchor that is a 74 % increase in the bill for no change in cover, and
    it is the product's largest policyholder risk.  ``v_max = 0.95`` binds nowhere in the
    shipped model points; it exists so that an extreme ``m`` cannot drive the billed
    premium negative and so that :func:`check_prem_split` has a stated domain.

    Zero where ``surplus_form = keine``, the § 153-excluded non-participating tariff.
    """
    if surplus_form() == "keine":
        return 0.0
    load = data.param("mort_load_first")                             # noqa: F821
    raw = (data.param("decl_scale") * data.param("surplus_share")    # noqa: F821
           * ((load - 1.0) / load)
           * tariff_benefit_pv()
           / (prem_gross_level_pp() * tariff_annuity()))
    return min(data.param("v_max"), raw)                             # noqa: F821


# ==========================================================================
# What is billed


def prem_due(t):
    """Whether a premium instalment falls due at the **beginning** of month t.

    ``duration_mth(t) % prem_cycle() == 0`` inside the *Beitragszahlungsdauer*, ``t >= 0``
    and ``duration(t) < prem_term()``.  An annual payer is due in the first month of
    every paying policy year and nowhere else; a monthly payer is due in every month of
    one.  § 168 VVG makes the *Versicherungsperiode* follow the *Zahlweise*, so this cycle
    is a contractual fact and not a modelling convenience — it is the period the contract
    is written in.

    This cell is the only source of a zero for the end of the premium term: the annual
    amounts :func:`prem_pp` and :func:`prem_rebate_pp` read it at the first month of
    their policy year, the instalments at their month, and none tests ``prem_term()``
    itself.  The *abgekürzte Beitragszahlungsdauer* of model point 6 so pays its last
    premium in month 143 while cover and claims run on to month 239.
    """
    if t < 0 or duration(t) >= prem_term():
        return False
    return duration_mth(t) % prem_cycle() == 0


def prem_pp(t):
    """The **annual** *Bruttobeitrag* per in-force policy for month t's policy year, ``G phi``.

    **The guaranteed stream**: the maximum the policyholder can ever be required to pay in
    a policy year.  Zero in a policy year whose first month :func:`prem_due` makes no
    premium payable, the years after the *Beitragszahlungsdauer*.  It does **not** enter
    :func:`net_cf`; it is the amount the *Beitragsverrechnung* is netted against, because
    a model carrying one premium cannot represent this product.

    An **annual** amount, flat across the policy year: the *Bruttobeitrag* is struck once
    at issue and is level for the term.  What is collected in month ``t`` is
    :func:`prem_charged_inst_pp`, the instalment the elected *Zahlweise* makes due.
    """
    if not prem_due(12 * duration(t)):
        return 0.0
    return prem_gross_level_pp() * prem_freq_load()


def prem_rebate_pp(t):
    """The **annual** *Beitragsverrechnung* per in-force policy, ``v_d G phi``.

    The declared surplus, netted against the *Bruttobeitrag* **before billing** rather
    than credited to an account — which is what § 153 VVG's *verursachungsorientiert*
    allocation looks like on a product with no account to credit.  Zero where
    ``surplus_form = keine`` and zero once the paying term is over.  An annual amount,
    like :func:`prem_pp`; :func:`prem_rebate_inst_pp` is what is netted off each
    instalment.
    """
    if not prem_due(12 * duration(t)):
        return 0.0
    return beitragsverrechnung_rate() * prem_gross_level_pp() * prem_freq_load()


def prem_paid_pp(t):
    """P(t): the **annual** *Zahlbeitrag* per in-force policy — what the customer is billed.

    ``prem_pp(t) - prem_rebate_pp(t)``, formed as the difference so that the split
    identity is true by construction rather than by coincidence.  **Not guaranteed**:
    § 153 VVG confers an entitlement to participate in surplus, not to a level, and a
    reduction of the declaration raises this toward the *Bruttobeitrag* with no procedure
    and no remedy.

    The annual bill, and so the quantity :func:`shock_lapse_factor` compares between
    consecutive renewals.  The stream inside :func:`net_cf` is :func:`prem_inst_pp`,
    collected on the *Zahlweise*'s own cycle.
    """
    return prem_pp(t) - prem_rebate_pp(t)


def prem_charged_inst_pp(t):
    """The *Bruttobeitrag* instalment falling due in month t, or zero.

    ``prem_pp(t) / instalments()`` where :func:`prem_due` makes one due.  The
    instalments of a policy year therefore sum to exactly that year's annual
    *Bruttobeitrag*, the *Ratenzahlungszuschlag* included: ``phi`` is a multiplier on the
    annual amount and dividing the loaded amount into instalments is what the surcharge
    prices.  Loading each instalment again, or dividing and then loading, charges it
    twice.
    """
    return prem_pp(t) / instalments() if prem_due(t) else 0.0


def prem_rebate_inst_pp(t):
    """The *Beitragsverrechnung* netted off the instalment falling due in month t, or zero.

    ``prem_rebate_pp(t) / instalments()`` where one is due.  The declaration is an annual
    one and the rebate an annual amount; what reaches a bill is its share of that bill,
    which is why this divides by the same :func:`instalments` as the gross.
    """
    return prem_rebate_pp(t) / instalments() if prem_due(t) else 0.0


def prem_inst_pp(t):
    """P_inst(t): the *Zahlbeitrag* instalment actually collected per policy in month t.

    ``prem_charged_inst_pp(t) - prem_rebate_inst_pp(t)``, formed as the difference so that
    the split identity holds instalment by instalment as well as year by year.  An annual
    payer therefore collects the whole 733,01 € of the anchor cell in the first month of
    each policy year and nothing in the other eleven; model point 4 is the contrast,
    twelve instalments on a `monthly` *Zahlweise*.

    **This is the one place the finer grid changes an answer rather than its resolution.**
    On a fractionated point the instalments after the first are collected on a block that
    has already lost lives, so the premium-cessation rule finally bites where an annual
    grid could not express it — and the *Ratenzahlungszuschlag* is at last charging for
    something the model does.

    Override reason: the *Zahlbeitrag* instalment is the gross instalment less the rebate,
    products/risikolebensversicherung/technical-notes.md:614
    """
    return prem_charged_inst_pp(t) - prem_rebate_inst_pp(t)


# ==========================================================================
# The first-order Deckungskapital — a pricing diagnostic, not a provision


def res_pp_at(y, timing):
    """The first-order **net** *Deckungskapital* per policy at **policy year** y, prospectively.

    ``"BEF_PREM"``
        before the year's premium: ``sum_{u>=y} v^(u-y+1) (p1(u)/p1(y)) q1(u) B(u)``
        over ``u = y .. n - 1``, less ``Gn sum_{u=y..k-1} v^(u-y) (p1(u)/p1(y))``.

    ``"AFT_PREM"``
        the same plus ``Gn`` where a premium is due in policy year ``y``.

    The argument is a **policy year and not a month**, like the equivalence it belongs to:
    a first-order *Deckungskapital* is struck on the tariff's annual bases, and the annual
    Thiele recursion :func:`check_res_roll_fwd_resid` asserts is the statement the German
    literature makes of it.  A monthly reserve would be a different quantity built on a
    monthly *Rechnungszins* this contract does not have.  :func:`result_pols` publishes it
    against the policy year of each month, so it is flat across that year's twelve rows.

    Zero at ``y = 0`` by the equivalence, zero at ``y = n`` by exhaustion, and strictly
    positive in between — on the anchor cell it peaks at 7 553,29 €, 2,5 % of the sum
    insured, at ``y = 15``.  **That it exists at all is the point.**  An RLV has no
    *Sparanteil* in the endowment's sense, but a level premium charged against a rising
    death rate necessarily overcharges early and undercharges late, and the difference has
    to be held.  Concluding "no *Sparanteil*, therefore no reserve" is wrong, and a model
    built on it fails :func:`check_res_roll_fwd`.

    **It is a pricing diagnostic and not a balance-sheet provision.**  It is net, it is not
    *gezillmert*, it is not floored at zero, it enters no cash flow, and nothing in this
    library discounts a published cash flow.  The statutory *Deckungsrückstellung* of
    HGB § 341f, the *Zinszusatzreserve* and the Solvency II best estimate are cited in the
    technical notes and computed nowhere.
    """
    if timing == "AFT_PREM":
        return res_pp_at(y, "BEF_PREM") + (prem_net_level_pp() if y < prem_term() else 0.0)
    if timing != "BEF_PREM":
        raise ValueError("invalid timing")
    if y >= proj_len_y():
        return 0.0
    p_y = pols_tariff(y)
    claims_pv = sum(
        disc_factor(u - y + 1) * (pols_tariff(u) / p_y)
        * mort_rate_tariff(12 * u) * benefit_pp(12 * u)
        for u in range(y, proj_len_y()))
    prem_pv = prem_net_level_pp() * sum(
        disc_factor(u - y) * (pols_tariff(u) / p_y)
        for u in range(y, prem_term()))
    return claims_pv - prem_pv


def res_zill_pp_at(y, timing):
    """The *gezillmerte* companion of :func:`res_pp_at`: less the unamortised Zillmer balance.

    ``res_pp_at(y, timing) - z k G x [ sum_{u=y..k-1} v^(u-y) (p1(u)/p1(y)) ] / ae``, so it
    is exactly ``-z k G`` at ``y = 0`` — **negative from the first day** — and back to zero
    at expiry.  That is what *Zillmerung* looks like on a contract with almost no reserve:
    the cap is 25 permille of the *Beitragssumme*, which for a twenty-five-year contract is
    twenty-five times the annual premium and therefore large relative to a reserve that
    peaks at a low single-digit percentage of the sum insured.  A **policy-year** quantity,
    like the reserve it adjusts.

    Whether a negative individual reserve must be floored at zero for balance-sheet
    purposes — the *Nullstellung* question — was **not established**, and because this
    model publishes no balance-sheet reserve the question does not reach its cash flows.
    """
    p_y = pols_tariff(y) if y < proj_len_y() else 1.0
    remaining = sum(disc_factor(u - y) * (pols_tariff(u) / p_y)
                    for u in range(max(y, 0), prem_term()))
    zill = (data.param("load_acq_bsum_once") * prem_term() * prem_gross_level_pp()  # noqa: F821
            * remaining / tariff_annuity())
    return res_pp_at(y, timing) - zill


# ==========================================================================
# Decrements


# ==========================================================================
# Cash flows


def benefit_death_pp(t):
    """The *Todesfallleistung* per death in period t, :func:`benefit_paid_pp`.

    Paid at the end of the period of death: the sum insured after the § 161 switch.  The
    only benefit that is ever non-zero.  The lapse and maturity benefits keep the core's
    neutral 0, so ``claims(t, "LAPSE")`` and ``claims(t, "MATURITY")`` are **zero, always**:
    § 169 Abs. 1 VVG confines the surrender-value duty to a life insurance whose insured
    event is certain to occur and a term assurance's is not, § 165's
    *Beitragsfreistellung* and § 166's paid-up conversion both collapse into the same nil
    through the minimum-benefit test, and a term contract pays nothing at expiry.  Both
    zeros are published as columns rather than dropped, and :func:`check_no_cash_value`
    asserts them on every model point.

    Override reason: a death pays the sum insured after the § 161 switch,
    products/risikolebensversicherung/technical-notes.md:228
    """
    return benefit_paid_pp(t)


def acq_cost_pp():
    """The total acquisition cost per policy, ``z k G`` — incurred **once, at issue**.

    25 permille of the *Beitragssumme*, the *Höchstzillmersatz* ceiling, of which
    ``comm_init_pp()`` is the initial *Abschlussprovision* and the remainder is other
    acquisition cost.  **A year-one outgo, not an annualised loading**: the tariff
    amortises it through the equivalence, the cash flow incurs it at issue, and that gap
    is the economic reason an early lapse hurts on a product with no surrender value to
    forfeit.  On an **in-force** model point it is sunk and is not incurred at all.
    """
    return data.param("load_acq_bsum_once") * prem_term() * prem_gross_level_pp()  # noqa: F821


def comm_init_pp():
    """The initial *Abschlussprovision* per policy, ``c0 k G``: 20 permille of the *Beitragssumme*.

    Published apart from the rest of the acquisition cost because :func:`result_cf` prints
    commission as its own column, and because the commission is the part that differs most
    between the German distribution channels — the direct writers' spread is wide precisely
    because no *Abschlussprovision* is paid to an intermediary, leaving more of the
    *Bruttobeitrag* available for *Beitragsverrechnung*.  **[std]**: no German scale is
    public.
    """
    return data.param("comm_acq_bsum_once") * prem_term() * prem_gross_level_pp()  # noqa: F821


def maint_pp(t):
    """Maintenance expense per in-force policy at the beginning of month t.

    ``gamma B(t) (1 + pi)^duration(t) / 12`` — sum-related administration, 0,30 permille
    of the sum insured a year and therefore **one twelfth of it a month**, expressed
    sum-related so it scales across the model point table — plus
    ``a x prem_inst_pp(t)``, collection cost at 3,0 % of the instalment **actually
    collected** in the month.  Both **[std]**; no German level is public.

    The two halves move differently on a monthly grid and both moves are the point.  The
    administration charge accrues a twelfth a month, so a policy that runs a full year
    carries the same annual charge as it did — but it is now borne by the in-force of
    **each month** rather than of the anniversary, which is what makes a decrementing
    block cost less.  The collection cost follows the *Zahlweise*: it is charged when a
    bill is collected, which on an annual payer is once a year and on a `monthly` one is
    twelve times, and that is what a collection cost is.

    The tariff loads 5,0 % of each *Bruttobeitrag* against a modelled collection cost of
    3,0 % of the *Zahlbeitrag*, and the gap is the ***Kostenüberschuss***.  The model does
    **not** return it: splitting the MindZV's *übriges Ergebnis* limb, whose minimum share
    is different, has no basis in the research corpus, so the cost result emerges in
    :func:`net_cf` and stays there.  That is a stated simplification —
    ``prem_rebate_inst_pp`` is invariant to ``expense_collect_prem_inst`` and
    ``comm_renew_prem_inst`` while ``net_cf`` is not — and not an oversight.
    """
    return (data.param("load_admin_sum_ann")                         # noqa: F821
            * benefit_pp(t) * inflation_factor(t) / 12.0
            + data.param("expense_collect_prem_inst") * prem_inst_pp(t))  # noqa: F821


def expenses_acq(t):
    """The acquisition cost net of the initial commission, at issue, or zero.

    A single amount in month ``t = 0`` and only where ``duration_init = 0`` — not an
    annualised loading and not a twelfth of one.  Commission is **not** in the expenses.  It
    is :func:`commissions`, its own column, and :func:`net_cf` subtracts the two separately
    — the opposite convention from ``frlib.TD_FR_S``, whose notes fold commission into the
    expense total.  The two libraries' columns look alike and do not mean the same thing,
    so the identity is written down in :func:`check_net_cf` rather than left to a reader's
    assumption.

    Override reason: the acquisition cost less the initial commission falls at issue on new
    business only, products/risikolebensversicherung/technical-notes.md:606
    """
    return (acq_cost_pp() - comm_init_pp()) if (t == 0 and duration_init() == 0) else 0.0


def expenses_maint(t):
    """Maintenance and collection on the opening in-force, ``maint_pp(t) x pols_if(t)``.

    Override reason: maintenance is a per-policy amount on the opening in-force,
    products/risikolebensversicherung/technical-notes.md:607
    """
    return maint_pp(t) * pols_if(t)


def expenses_claim(t):
    """The claim expense on the month's deaths, 250 € each **[std]**, ``expense_claim_pp_once`` of
    *param_tariff_type.csv*.

    Override reason: the claim expense is an amount per death claim,
    products/risikolebensversicherung/technical-notes.md:400
    """
    return data.param("expense_claim_pp_once") * pols_death(t)       # noqa: F821


def comm_init(t):
    """The initial *Abschlussprovision* at issue, :func:`comm_init_pp`, or zero **[std]**.

    In month ``t = 0`` and only where ``duration_init = 0``, because on an in-force point it
    is sunk.

    Override reason: the initial commission is the per-policy ``comm_pp`` at issue on new
    business, products/risikolebensversicherung/technical-notes.md:608
    """
    return comm_init_pp() if (t == 0 and duration_init() == 0) else 0.0


def comm_renew(t):
    """The *Bestandspflegeprovision*, 1,0 % of each *Zahlbeitrag* instalment **[std]**.

    From ``duration(t) >= 1``, which is policy year 2.  The **rate** is a policy-year rate
    and steps on the anniversary; the **base** is the instalment actually collected, so a
    fractionated payer earns the renewal commission in instalments too.  On an annual-mode
    point that reproduces the annual model's commission exactly, both the rate and the
    collection sitting on the anniversary.

    Override reason: the renewal commission is a rate on each *Zahlbeitrag* instalment from
    policy year 2, products/risikolebensversicherung/technical-notes.md:397
    """
    return (data.param("comm_renew_prem_inst") * prem_inst_pp(t) * pols_if(t)  # noqa: F821
            if duration(t) >= 1 else 0.0)


# ==========================================================================
# The published check_* identities


def check_net_cf_tol(t):
    """The tolerance of :func:`check_net_cf`: ``check_tol`` times the sum insured, at least 1.

    :func:`check_net_cf` is true when the cash flow statement reconciles in every projected
    period.

    No argument, one bool over all ``t``, the library-wide shape;
    :func:`check_net_cf_resid` gives the signed residual of the period that failed.  The
    tolerance scales with the sum insured, which is the largest number in the statement.

    Override reason: the statement is checked to check_tol relative to the sum insured,
    products/risikolebensversicherung/model.md:500
    """
    return data.param("check_tol") * max(sum_assured(), 1.0)           # noqa: F821


def check_pols_roll_fwd_resid(t):
    """The in-force roll-forward residual in month t; zero everywhere.

    ``pols_if(t) - pols_if(t+1) - pols_death(t) - pols_lapse(t) - pols_maturity(t)``.
    What it catches is a **misindexed recursion**: rolling forward with ``wm(t-1)`` or
    ``q2m(t+1)``, or leaving the expiry out of the roll-forward while still booking it as
    an exit.  In the last month ``pols_lapse`` is zero, ``pols_maturity`` carries the
    whole surviving cohort and ``pols_if(proj_len())`` is exactly zero, so the identity
    closes there too — and that it closes at ``proj_len() - 1`` with nothing left over is
    what lets :func:`result_cf` stop there.
    """
    return (pols_if(t) - pols_if(t + 1)
            - pols_death(t) - pols_lapse(t) - pols_maturity(t))


def check_pols_roll_fwd():
    """True when the in-force roll-forward closes in every projected period.

    It also asserts the **closure identity** at the horizon: the three exits summed over
    the whole projection equal ``pols_if_init()``, so every policy the projection opens
    with leaves it through exactly one named door.  On the anchor cell that is
    0,03305608 deaths, 0,53554078 lapses and 0,43140314 expiries.
    """
    tol = roll_fwd_tol() * max(pols_if_init(), 1.0)                  # noqa: F821
    if not all(abs(check_pols_roll_fwd_resid(t)) <= tol
               for t in range(t_start(), proj_len())):
        return False
    exits = sum(pols_death(t) + pols_lapse(t) + pols_maturity(t)
                for t in range(t_start(), proj_len()))
    return abs(exits - pols_if_init()) <= tol


def check_prem_split_resid(t):
    """The premium-split residual in month t: ``Brutto - Zahl - Verrechnung``; zero.

    **The product's signature identity.**  The German term premium is two numbers and a
    difference — a guaranteed *Bruttobeitrag*, a billed *Zahlbeitrag* and the declared
    *Beitragsverrechnung* between them — and every consumer document, every comparison
    test and every rating criterion turns on the gap.  The residual is zero by
    construction, :func:`prem_inst_pp` being formed as the difference; what
    :func:`check_prem_split` adds on top is the **domain**, which is not.

    Struck on the **instalments**, which is what the cash flow statement publishes: an
    identity asserted on the annual amounts alone would not see a *Zahlweise* that
    fractionates the gross and the rebate on different cycles.
    """
    return (prem_charged_inst_pp(t) - prem_inst_pp(t)
            - prem_rebate_inst_pp(t))


def check_prem_split():
    """True when the premium splits, and stays inside its domain, at every ``t``.

    Beyond the residual: in a month where an instalment is due inside the paying term the
    rebate must be non-negative and strictly below the gross instalment — a
    *Beitragsverrechnung* that reached the whole premium would make the contract free,
    which ``v_max`` exists to prevent — and in every other month all three instalments
    must be exactly zero, which is what stops a model running the premium past the
    *Beitragszahlungsdauer* on model point 6 or collecting outside the *Zahlweise*'s own
    cycle.  The annual amounts must close the same way, so both are asserted.

    The identity holds at every *Zahlweise*, because the *Ratenzahlungszuschlag*
    multiplies the annual billed amount once and the division into instalments is applied
    to all three terms alike.
    """
    tol = data.param("check_tol") * max(sum_assured(), 1.0)            # noqa: F821
    for t in range(t_start(), proj_len()):
        if abs(check_prem_split_resid(t)) > tol:
            return False
        if abs(prem_pp(t) - prem_paid_pp(t) - prem_rebate_pp(t)) > tol:
            return False
        if prem_due(t):
            if not (0.0 <= prem_rebate_inst_pp(t) < prem_charged_inst_pp(t)):
                return False
        elif not (prem_charged_inst_pp(t) == prem_rebate_inst_pp(t)
                  == prem_inst_pp(t) == 0.0):
            return False
    return True


def check_res_roll_fwd_resid(y):
    """The Thiele residual of the first-order *Deckungskapital* in **policy year** y; zero.

    ``( res_pp_at(y,"BEF_PREM") + Gn 1{y<k} ) (1 + i)
    - q1(y) B(y) - (1 - q1(y)) res_pp_at(y+1,"BEF_PREM")``, the annual rate and the sum
    insured read at that policy year's opening month ``12 y``.

    An **annual** recursion on an annual reserve, and it stays one on the monthly grid:
    the *Rechnungszins* is an annual rate and the reserve is struck against it.  The
    reserve is built **prospectively** and the recursion rolls it **forward**, so the two
    agree only if the survivorship, the discounting and the premium term are all indexed
    consistently.  It is checked from ``y = 0`` on every model point, including an
    in-force one whose cash flows start later: the reserve is a tariff quantity and the
    tariff was struck at issue.
    """
    lhs = (res_pp_at(y, "AFT_PREM")) * (1.0 + rechnungszins())       # noqa: F821
    q1 = mort_rate_tariff(12 * y)
    rhs = (q1 * benefit_pp(12 * y)
           + (1.0 - q1) * res_pp_at(y + 1, "BEF_PREM"))
    return lhs - rhs


def check_res_roll_fwd():
    """True when the reserve rolls forward, opens at zero and closes at zero.

    ``res_pp_at(0, "BEF_PREM") = 0`` is the premium equivalence restated, and
    ``res_pp_at(n, "BEF_PREM") = 0`` is exhaustion: the *Deckungskapital* of a term
    contract is fully consumed by expiry.  Between them the Thiele recursion must hold in
    every policy year.  This is the check that catches the product's characteristic
    modelling error — concluding from the absence of a *Sparanteil* that there is no
    reserve, and building a projection that cannot close.
    """
    tol = data.param("check_tol") * max(sum_assured(), 1.0)            # noqa: F821
    if abs(res_pp_at(0, "BEF_PREM")) > tol:
        return False
    if abs(res_pp_at(proj_len_y(), "BEF_PREM")) > tol:
        return False
    return all(abs(check_res_roll_fwd_resid(y)) <= tol
               for y in range(proj_len_y()))


def check_no_cash_value_resid(t):
    """The non-death benefit residual: ``claims(t,"LAPSE") + claims(t,"MATURITY")``; zero.

    **Trivially zero by construction**, because both kinds return a literal zero.  It is
    published because the zero is a statutory and contractual fact rather than a modelling
    choice — there is no *Rückkaufswert*, no *beitragsfreie Versicherungssumme* worth
    having and no *Erlebensfallleistung* — and because the failure it guards against is not
    an arithmetic slip but an import: a reader arriving from an endowment or a US model
    with cash surrender values wires a surrender scale into the lapse decrement, and every
    total in the frame still looks plausible.  A named check that must stay at zero makes
    that edit fail loudly.
    """
    return claims(t, "LAPSE") + claims(t, "MATURITY")


def check_no_cash_value():
    """True when a lapse and an expiry both pay nothing in every projected month."""
    return all(abs(check_no_cash_value_resid(t)) <= data.param("check_tol")  # noqa: F821
               for t in range(t_start(), proj_len()))


# ==========================================================================
# Result frames


def result_pols_columns():
    """The columns of :func:`result_pols`, ``(label, cell)`` pairs in their order.

    The frame is the table of policy counts, rates, per-policy amounts and the reserve by t.

    The same 0-based monthly frame as :func:`result_cf`:
    ``t = t_start() ... proj_len() - 1``.  Each **annual** rate is published beside the
    **monthly** rate derived from it, so the two speeds of the conversion can be read off
    one table: ``mort_rate`` and ``lapse_rate`` are the annual rates of the policy year
    containing the month — the vectors the technical notes tabulate — and
    ``mort_rate_mth`` and ``lapse_rate_mth`` the rates actually applied in it.
    ``prem_*_pp`` are likewise the year's annual amounts and ``prem_inst_pp`` the
    instalment collected in the month.  ``res_pp`` and ``res_zill_pp`` are the policy
    year's reserves, flat across its twelve rows, the first-order *Deckungskapital* being
    an annual construction.

    Override reason: the frame publishes the decrement, rate, benefit, premium and reserve
    side beside the cash flows, products/risikolebensversicherung/model.md:62
    """
    return (
        ("age", age),                                                # noqa: F821
        ("policy_year", policy_year),                                # noqa: F821
        ("pols_if", pols_if),                                        # noqa: F821
        ("pols_death", pols_death),                                  # noqa: F821
        ("pols_lapse", pols_lapse),                                  # noqa: F821
        ("pols_maturity", pols_maturity),                            # noqa: F821
        ("mort_rate", mort_rate),                                    # noqa: F821
        ("mort_rate_mth", mort_rate_mth),                            # noqa: F821
        ("mort_rate_tar", mort_rate_tariff),                         # noqa: F821
        ("lapse_rate", lapse_rate),                                  # noqa: F821
        ("lapse_rate_mth", lapse_rate_mth),                          # noqa: F821
        ("benefit_pp", benefit_pp),                                  # noqa: F821
        ("benefit_paid_pp", benefit_paid_pp),                        # noqa: F821
        ("suicide_factor", suicide_factor),                          # noqa: F821
        ("prem_pp", prem_pp),                                        # noqa: F821
        ("prem_rebate_pp", prem_rebate_pp),                          # noqa: F821
        ("prem_paid_pp", prem_paid_pp),                              # noqa: F821
        ("prem_inst_pp", prem_inst_pp),                              # noqa: F821
        ("res_pp", lambda t: res_pp_at(duration(t), "BEF_PREM")),    # noqa: F821
        ("res_zill_pp",
         lambda t: res_zill_pp_at(duration(t), "BEF_PREM")),         # noqa: F821
    )


# ---------------------------------------------------------------------------
# References

data = ("Interface", ("..", "Data"), "auto")

point_id = 1

pd = ("Module", "pandas")
