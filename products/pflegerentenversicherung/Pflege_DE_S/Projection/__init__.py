# modelx: pseudo-python
# This file is part of a modelx model.
# It can be imported as a Python module, but functions defined herein
# are model formulas and may not be executable as standard Python.

"""The by-policy projection of the :mod:`~.Pflege_DE_S` model.

The Space is parameterized by ``point_id``, so ``Projection[1]`` is an ItemSpace
projecting model point 1::

    >>> Projection[1].result_cf()          # the worked example's anchor cell
    >>> Projection.point_id = 5            # or switch the default

``t`` counts **policy months**, 0-based: ``t = 0`` is the month of issue and
``age(t) = issue_age + t // 12``, so the attained age steps at the policy anniversary.
The frame **starts** at ``t_start() = duration_mth_init()`` — ``0`` for new business,
the elapsed duration for an in-force model point — and runs to ``proj_len() - 1``, where
``proj_len() = 12 * (omega_age() - issue_age())`` is the **number of projected months**,
the exclusive end of ``range(t_start(), proj_len())``, and depends on the entry
age and the terminal age alone. There is no maturity, no survival benefit and no tail state:
the contract runs for life, and the closure is carried by the decrements.

.. rubric:: Input data

Inputs are **external files**: plain CSVs living in the model folder's parent directory,
``products/pflegerentenversicherung/``, read at run time rather than stored inside the
model. The model folder therefore holds nothing but formulas — no ``_data/``, no IOSpec,
no embedded values — so a diff of the model shows logic changes only, and an input can be
edited or swapped without rewriting the model. This follows ``annuallife.TradLife_A``;
contrast ``basiclife.BasicTerm_S``, which keeps its inputs *inside* the model through
modelx's IOSpec machinery.

The consequence worth knowing: **the model is not portable on its own.** Copying the
``Pflege_DE_S`` folder without its parent's CSVs produces a model that reads and then
fails on first evaluation.

Each table has a filename Reference and a reader Cells, both on
:mod:`~.Pflege_DE_S.Data`, reached here through the ``data`` Reference:

=========================  ===================================  =========================
Reference                  Cells                                File
=========================  ===================================  =========================
model_point_file           data.model_point_table()             model_point_table.csv
benefit_scale_file         data.benefit_scale_table()           benefit_scale_table.csv
mort_file                  data.mort_table()                    mort_table.csv
incidence_file             data.incidence_table()               incidence_table.csv
care_file                  data.care_table()                    care_table.csv
lapse_file                 data.lapse_table()                   lapse_table.csv
surrender_file             data.surrender_table()               surrender_table.csv
prem_freq_file             data.prem_freq_table()               prem_freq_table.csv
param_file                 data.param()                         param_tariff_type.csv
=========================  ===================================  =========================

.. rubric:: Naming

Cells names follow lifelib's ``basiclife.BasicTerm_S`` wherever that model has an
analogue — ``pols_*`` for policy counts, plural nouns for cash flows, ``*_rate`` for
annual rates and ``*_rate_mth`` for monthly ones, ``*_pp`` for per-policy amounts,
``claims(t, kind)`` with an uppercase ``kind`` string, ``pols_if_at(t, timing)`` for the
end-of-period read. The technical notes use compact actuarial symbols instead. The
mapping is:

==========================  ==============================  ==========================
Notes symbol                Cells                           Meaning
==========================  ==============================  ==========================
(none)                      model_point()                   The selected model point row
n = 12(omega - entry)       proj_len()                      Number of projected months
d0                          t_start()                       Month the frame opens at
t                           duration_mth(t)                 Months since issue
y(t) = t // 12 + 1          policy_year(t)                  Versicherungsjahr
x(t)                        age(t)                          Attained age in month t
R                           rente_mth()                     Vereinbarte Pflegerente, PG5
pi_g                        benefit_pct(g)                  Leistungsstaffel percentage
(none)                      waiver_flag(g)                  Is an annuity payable at g?
P                           premium_mth_pp()                Level monthly gross Beitrag
(none)                      prem_net_level_pp()             Net level premium, A / U
m                           prem_cycle()                    1, 3, 6, 12; prem_form single
(table)                     mort_rate_at_age(x)             Active table rate at age x
(table)                     mort_rate_base(t)               Its value at age(t)
q_A(x)                      mort_rate(t)                    Active annual death rate
(none)                      mort_rate_mth(t)                The same rate, monthly
mu_A(t)                     mort_force(t)                   Active force of mortality
q_g(x)                      mort_rate_care(t, g)            Annual death rate at grade g
mu_g(t)                     mort_force_care(t, g)           mort_mult(g) x mu_A(t)
i(x)                        inc_rate(t)                     Annual incidence into care
iota(t)                     inc_force(t)                    Force of incidence, 0 in the
                                                            Wartezeit
s_g                         inc_share(g)                    Grade first entered, entry mix
(table)                     det_rate(g)                     Annual deterioration rate
delta_g(x)                  det_force(x, g)                 Force of deterioration
(table, damped)             rec_rate(x, g)                  Annual recovery rate
rho_g(x)                    rec_force(x, g)                 Force of recovery
(table)                     lapse_rate(t)                   Annual lapse, active state
(gate)                      lapse_factor(t)                 0 after the premium term
w(t)                        lapse_rate_mth(t)               Monthly lapse probability
(allocation)                p_act_age(x, waiting)           Active-state month transitions
                                                            (stay, death, care), keyed by
                                                            age and the Wartezeit gate
(allocation)                p_pg_age(x, g)                  Grade-g month transitions
                                                            (stay, death, worse, better),
                                                            keyed by age
l_A(t)                      pols_act(t)                     Active at the start of month t
W_{g,z}(t)                  pols_karenz(t, g, z)            In the Karenz ledger
l_g(t)                      pols_pg(t, g)                   In a paying Pflegegrad
E_g(t)                      esc_pg(t, g)                    Escalation-weighted l_g
(none)                      pols_ledger(t)                  The four ledgers as one
                                                            state, with the previous
                                                            month's entries and
                                                            graduations
(none)                      pols_care(t)                    Everyone in care
l(t)                        pols_if(t)                      In force at the start of t
l(t+1)                      pols_if_at(t, timing)           BEF_DECR / AFT_DECR
(none)                      pols_in_term(t)                 In force inside the term
(none)                      pols_waived(t)                  Beitragsbefreiung population
(none)                      pols_prem(t)                    Units actually paying
(none)                      pols_entry(t, g)                Entrants into grade g
(none)                      pols_grad(t, g)                 Karenz graduations into g
(none)                      pols_reactiv(t)                 Reaktivierung to the active
                                                            state
pols_death(t)               pols_death(t)                   Deaths from every state
pols_lapse(t)               pols_lapse(t)                   Surrenders, active state only
(none)                      pols_dead_cum(t)                Cumulative deaths
(none)                      pols_lapse_cum(t)               Cumulative surrenders
(none)                      premium_due(t)                  Is an instalment due?
(none)                      premium_pp(t)                   The instalment charged
(none)                      cum_prem_max_pp(t)              Premium payable to date
(none)                      prem_units_at(t)                The same, in units of P
(none)                      prem_inst_pp(t)                 premium_pp(t), per unit
premiums(t)                 premiums(t)                     Beitrag income
(none)                      rkw_pp(t)                       Rueckkaufswert per policy
(none)                      brg_pp(t)                       Beitragsrueckgewaehr per policy
claims_annuity, _lapse,     claims(t, kind)                 Benefit outgo by kind
_death
alpha x Beitragssumme       zillmer_amount()                Acquisition charge at t = 0
(none)                      beitragssumme()                 The Zillmerung base
t / 12                      inflation_years(t)              Years of expense inflation
(1 + f)^(t/12)              inflation_factor(t)             Expense inflation factor
expenses(t)                 expenses(t)                     Acquisition + administration
c x annuity payments        claim_expenses(t)               Per-annuity-payment cost
net_cf(t)                   net_cf(t)                       Net cash flow, income positive
-net_cf(t)                  liability_cf(t)                 The same stream, outgo positive
i                           rechnungszins()                 Technical rate, pricing only
v**t                        disc_factor_mth(t)              (1 + i)^(-t/12)
(first order)               mort_rate_tariff(t)             Blended, margined active q
(first order)               tar_mort_rate_care(x, g)        Blended, margined in-care q
(first order)               tar_inc_rate(x)                 Blended, margined incidence
(first order)               tar_det_rate(g)                 Margined deterioration
(first order)               tar_rec_rate(x, g)              Margined recovery
(first order)               tar_p_act(t), tar_p_pg(x, g)    Tariff month transitions
(first order)               tar_pols_act(t)                 Tariff active ledger
(first order)               tar_pols_karenz(t, g, z)        Tariff Karenz ledger
(first order)               tar_pols_grad(t, g)             Tariff Karenz graduations
(first order)               tar_pols_pg(t, g)               Tariff paying ledger
(first order)               tar_esc_pg(t, g)                Tariff escalation ledger
(first order)               tar_ledger(t)                   Tariff ledgers as one state
(first order)               tar_pols_if(t)                  Tariff in force
(first order)               tar_pols_prem(t)                Tariff premium-paying units
(first order)               tar_pols_death(t)               Tariff deaths
A                           tariff_benefit_pv()             EPV of the Pflegerente
U                           tariff_annuity()                EPV of premium, in units of P
G                           epv_admin()                     EPV of per-policy admin
C                           epv_claim_expense()             EPV of claims cost
==========================  ==============================  ==========================

Four names needed care.

``pols_if(t)`` is the count at the **start** of month ``t`` and is the weight on that same
``result_cf()`` row's cash flows, which is the library-wide convention; the end-of-period
count is :func:`pols_if_at` with ``"AFT_DECR"`` and never :func:`pols_if` at ``t + 1`` written
into a cash-flow row. Breaking that is silent: the exposure column becomes the correct
series shifted one period while every cash flow beside it stays right.

``pols_pg(t, g)`` and ``esc_pg(t, g)`` are the **same population** counted two ways. The
first is a head count; the second weights each life by its own escalation factor since its
annuity began. With ``leistungsdynamik = 0`` they are identical at every ``t`` and ``g``,
which :func:`check_esc_ledger` asserts. The annuity is weighted on ``esc_pg`` and never on
``pols_pg``, because using the head count would silently drop the escalation on the model
points that carry one.

``pols_waived(t)`` is the *Beitragsbefreiung* population, and it is **not** everyone in
care. A life in the *Karenz* ledger pays, because no annuity is yet payable and the waiver
runs with the annuity; a life at *Pflegegrad* 1 pays on the ``delib_std`` grid, where
``benefit_pct(1) = 0``, and is waived on the ``bahr`` grid, where it is 10 %. That is why
the split is driven by :func:`waiver_flag` rather than by membership of the care ledger,
and why ``pols_prem(t)`` is **not monotone**: a *Herabstufung* out of the insured grades
revives the premium.

``mort_rate(t)`` is the **active-life** rate. In-care mortality is not tabulated at all:
:func:`mort_force_care` is ``mort_mult(g)`` times the active *force*, so
:func:`mort_rate_care` is ``1 - exp(-mort_mult(g) mu_A)``. The multiple is on the force and
not on the rate, which matters at the oldest ages where the rate saturates.

.. rubric:: The monthly step: constant forces, proportional allocation

Every shipped rate is **annual** and every transition inside a month is computed from
**forces held constant over the month**, the competing transitions sharing one survival
probability in proportion to their forces. Writing ``q`` for an annual rate, the force is
``mu = -ln(1 - q)``; with forces ``mu_1 ... mu_k`` out of a state,

    p_stay = exp(-(mu_1 + ... + mu_k) / 12)      p_j = (mu_j / sum mu) (1 - p_stay)

so ``p_stay + sum p_j = 1`` exactly, by construction, which is what the components of
:func:`p_act_age` and :func:`p_pg_age` hold and what makes :func:`check_states` an
identity rather than an approximation. Adding monthly rates instead, or applying ``q/12``,
gives different answers wherever the forces are large — which on this product is exactly
where the money is.

The limiting-age convention needs one number. ``mort_rate`` is forced to 1.0 at
``omega_age() - 1``, whose force is infinite; it is capped at ``-ln(1e-12) = 27.63`` so
the proportional allocation stays finite, and the incidence, deterioration and recovery
forces are set to zero there so that every exit at the limiting age is death. What
survives to ``omega_age`` is then ``1e-12`` of the age-109 cohort, which on the anchor
cell is of the order of ``1e-17`` of the original policy.

.. rubric:: The pricing engine, and why it is a separate ledger

The library publishes **undiscounted** cash flows. The *Beitrag*, however, is a *priced*
quantity, so the model carries a second, self-contained actuarial-value engine — the
``tar_*`` cells and :func:`mort_rate_tariff` — whose only output is
:func:`premium_mth_pp`. **That engine discounts; the projection does not.**

Where ``premium_mth`` is positive on the model point, that is the premium and the engine
is not consulted. Where it is ``0.0``, ``P`` is struck by equivalence on the
**first-order** (*erster Ordnung*) bases: every rate multiplied by its prudence margin,
the sexes blended at ``unisex_mix_male`` because sex may not enter a German premium, and
**no lapse at all**. The first-order basis carrying no lapse is both German practice and
what keeps the model acyclic — a pricing quantity must not depend on a behavioural
assumption that depends on the path that depends on the premium.

Everything on the benefit side that scales with ``P`` — the *Beitragsrückgewähr* and the
*Zillmerung* allowance — is linear in ``P``, so the equivalence

    P U = A + P D1 + P a1 + beta P U + G + C

solves in closed form, ``P = (A + G + C) / (U (1 - beta) - D1 - a1)``, and
:func:`premium_mth_pp` multiplies that by the *Risikozuschlag*, which loads the **gross**
premium and never the benefit. :func:`check_prem_equiv` then re-assembles both legs month
by month from the tariff ledgers rather than from the closed form, so substituting a
best-estimate rate into one leg, or dropping the *Zillmerung* term, makes it fail.

.. rubric:: Modules that are off in the base run

Five constructions are implemented and switched off through the model point, so the base
run reproduces the worked example while the machinery stays visible and testable:
the *Wartezeit* (``wartezeit_months = 0``), the *Karenzzeit* (``karenz_months = 0``, in
which case the ledger is empty and a life graduates in the month it enters), the
*Leistungsdynamik* (``leistungsdynamik = 0``, in which case ``esc_pg == pols_pg``), the
*Beitragsrückgewähr* (``beitragsrueckgewaehr = False``, in which case ``claims_death`` is
structurally zero) and the *Stornoabzug* (``stornoabzug_rate = 0``). Model points 7, 8, 9 and
10 switch them on one at a time.

Four further constructions are described in the technical notes and **not** implemented,
each for a stated reason: no *Überschussbeteiligung* in any application form, the surplus
chassis belonging to ``products/kapitallebensversicherung/``; no *Beitragsdynamik*, whose
acceptance rate is a behavioural assumption with nothing behind it; no
*Beitragsfreistellung*, so every voluntary exit is a surrender; and no § 163 VVG re-rating,
which is a management action conditional on emerging experience rather than a projected
assumption.

.. rubric:: Sign convention

:func:`net_cf` is **income positive** — *Beitrag* in, annuity, surrender value, death
benefit and expenses out — which is the notes' own orientation and the library-wide sign.
:func:`liability_cf` publishes the same stream outgo-positive,
``liability_cf(t) = -net_cf(t)`` exactly, so a best-estimate liability is
``sum v(t) liability_cf(t)`` over whatever discount curve the valuation layer supplies.
Both are columns of :func:`result_cf`, so the identity is verifiable in the frame rather
than only in prose.

The shape to expect on the anchor cell is a large new-business strain at ``t = 0`` — the
25 ‰ *Zillmerung* allowance is charged in full there — then thirty-odd years of positive
monthly margins as the level *Beitrag* runs far above the risk premium, then a long
negative tail from the seventies onward as the incidence curve overtakes it. That crossing
is the *Deckungskapital*'s peak, and it is the whole economic content of an ageing reserve
carried on a life-assurance chassis.
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

def status_init():
    """The state at the projection start: ``aktiv`` or ``pg1`` … ``pg5``.

    An ``aktiv`` point seeds :func:`pols_act`; a point in claim seeds :func:`pols_pg` at
    its grade with the *Karenzzeit* already served, because a life in payment at the
    valuation date has served whatever deferral its contract carried.  Model point 12 is
    the in-claim case.
    """
    v = str(model_point()["status"])
    if v not in ("aktiv", "pg1", "pg2", "pg3", "pg4", "pg5"):
        raise ValueError("invalid status")
    return v


def rente_mth():
    """R: the *vereinbarte Pflegerente* at *Pflegegrad* 5, in euro per month.

    The scaling constant of the whole benefit schedule: every grade pays
    ``benefit_pct(g) x rente_mth()``.  The market sells 1 000 € to 1 500 € a month, sized
    against the residual a *Pflegeheim* resident funds from savings after the statutory
    contribution and an average pension; the shipped 1 000 € is the round number at the
    lower end of that band and is a **[std]** choice, not an observation.
    """
    return float(model_point()["rente_mth"])


def staffel_id():
    """The key into *benefit_scale_table.csv* naming this policy's *Leistungsstaffel*.

    ``delib_std`` is 0 / 30 / 50 / 75 / 100 %; ``bahr`` is the statutory
    10 / 20 / 30 / 40 / 100 % minimum grid of § 127 SGB XI.  The difference is not only a
    level: on ``bahr`` *Pflegegrad* 1 is insured, so a grade-1 life is **waived** there and
    **pays** on ``delib_std``.
    """
    return str(model_point()["staffel_id"])


def prem_end_age():
    """The attained age at which the *Beitrag* ceases; ``110`` means lifelong.

    Three forms are sold: lifelong payment until death or claim, payment to a fixed age —
    typically 65 or 85 — and a single *Einmalbeitrag*.  A shortened
    *Beitragszahlungsdauer* raises the level premium and the reserve and best matches the
    buyer's earning life; model point 4 carries it.  Once the term has ended the contract
    is paid up: no premium, no lapse, and the cover runs on.
    """
    return int(model_point()["prem_end_age"])


def premium_mth():
    """The contractual monthly *Beitrag* from the model point; ``0.0`` is a sentinel.

    ``0.0`` does not mean a free contract.  It means **derive the premium by
    equivalence**, and :func:`premium_mth_pp` then runs the first-order pricing engine.
    A positive value is taken as the contractual premium and the engine is not consulted —
    which is how an in-force model point carries the premium it was actually sold at.
    """
    return float(model_point()["premium_mth"])


def wartezeit_months():
    """The *Wartezeit* from inception, in months; ``0`` in the base run.

    Care beginning inside it is not covered, so :func:`inc_force` is zero while
    ``t < wartezeit_months()``.  The underwritten mainstream product usually has none — the
    *Gesundheitsprüfung* does the screening the *Wartezeit* does in the subsidised
    *Pflege-Bahr* product, where the statutory maximum is five years.  The pairing is near
    deterministic: no underwriting implies a long *Wartezeit*, underwriting implies none.
    Model point 7 carries 36 months.
    """
    return int(model_point()["wartezeit_months"])


def leistungsdynamik():
    """d: the annual escalation of the annuity **in payment**; ``0.0`` in the base run.

    Not to be confused with a *Beitragsdynamik*, which raises premium and cover before
    claim and is not modelled at all.  The economic case for this one is that the
    *Eigenanteil* a resident pays rises continuously while the statutory benefit is uprated
    episodically, so a level annuity loses ground throughout a spell.  Its cost is much
    smaller than it looks — the annuity is paid to a population with heavily elevated
    mortality, so the escalation compounds over three to five years, not fifteen.  Model
    point 8 carries 2 % a year.
    """
    return float(model_point()["leistungsdynamik"])


def beitragsrueckgewaehr():
    """Whether the *Beitragsrückgewähr* death benefit is on; ``False`` in the base run.

    Switched on, the contract returns the premiums payable to date on death at any time,
    which converts a pure biometric risk cover into a savings-bearing one: the reserve
    needed to fund it is close to the accumulated premium itself, and the option roughly
    doubles the premium for the same annuity.  The base run leaves it off because the
    savings roll-forward is demonstrated far better by
    ``products/kapitallebensversicherung/``; model point 9 turns it on to show how large
    the effect is.

    The implemented form is the **gross** one — no offset for annuity already paid.  The
    market's more common form nets the annuity off, but that netting is floored at zero
    **per life**, and these ledgers are aggregates, so netting at the aggregate level would
    let a life that received a large annuity subsidise one that received none.  The
    consequence — the option overstates the death benefit relative to the market-standard
    form — is stated rather than hidden.
    """
    return bool(model_point()["beitragsrueckgewaehr"])


def stornoabzug_rate():
    """The deduction from the *Rückkaufswert*, as a fraction; ``0.0`` in the base run.

    Admissible only if agreed, appropriate and **quantified in the contract**, and a
    deduction for unamortised acquisition costs is expressly ineffective.  No
    *Stornoabzug* for any German *Pflegerenten* tariff was established, so the base run
    ships zero — a non-zero deduction requires a contractual quantification this corpus
    cannot supply — and model point 10 carries 5 % as a **[std]** illustration.

    **Named ``stornoabzug_rate`` and not ``stornoabzug``.**  It is a fraction, and the
    library gives every rate the ``*_rate`` suffix; ``RV_DE_S``, ``FRV_DE_S`` and
    ``Riester_DE_S`` all spell this rate the same way.  Bare ``stornoabzug`` is
    ``FRV_DE_S``'s *euro amount* retained from surrenders and one of its ``result_cf()``
    columns — a different quantity, which is why the two do not share a name.
    """
    return float(model_point()["stornoabzug_rate"])


def t_start():
    """The month the frame opens at, ``duration_mth_init()``; 0 for new business.

    Override reason: the model point carries the elapsed duration in months, so the frame
    opens at ``duration_mth_init()``, products/pflegerentenversicherung/technical-notes.md:43
    """
    return duration_mth_init()


def horizon_age():
    """The attained age at which the projection ends: ``omega_age()``.

    So ``proj_len() = 12 (omega_age - issue_age)``, the **exclusive end** of the frame
    counted from ``t = 0``.  On the anchor cell — entry age 45, ``omega_age`` 110 — it is
    780, so the frame runs ``t = 0 … 779``, attained ages 45 to 109.  It does **not**
    depend on :func:`duration_mth_init`: a point opening partway through shortens the
    frame at the front (``t_start``), never at the back.

    Override reason: the horizon is fixed by the entry age and the terminal age in months, with no
    policy term, products/pflegerentenversicherung/technical-notes.md:54
    """
    return omega_age()


def benefit_pct(g):
    """pi_g: the *Leistungsstaffel* percentage at *Pflegegrad* ``g``.

    Read from *benefit_scale_table.csv* on this policy's ``staffel_id``.  The annuity paid
    at grade ``g`` is ``benefit_pct(g) x rente_mth()``, irrespective of the care setting:
    the same amount is payable at home and in a *Pflegeheim*, which is what makes the
    product a *Summenversicherung* and removes any need to prove where care is given.

    The middle steps carry the cost.  Time spent at each grade is very unequal — a person
    entering at grade 2 and deteriorating spends most of the spell at grades 2 and 3 and
    only the final months at grade 5 — so the time-weighted average percentage over a spell
    is far below 100 %, and two tariffs with the same top step and different middle steps
    differ by more than the headline suggests.
    """
    return float(data.benefit_scale_table_dict()["benefit_pct"][     # noqa: F821
        (staffel_id(), g)])


def waiver_flag(g):
    """True when an annuity is payable at *Pflegegrad* ``g``, and so the *Beitrag* waived.

    Waiver and benefit run on **one** trigger: the premium is waived from the first month
    in which any annuity is payable and revives on exit from the paying grades.  That is
    the market-standard design, and it is what lets :func:`check_waiver` reconcile the
    premium stream and the benefit stream against a single ledger.

    The grade-1 case is the whole point of publishing this as its own cells.  On
    ``delib_std`` ``benefit_pct(1)`` is zero, so a grade-1 life is in care, is counted in
    :func:`pols_if`, generates no annuity and **keeps paying**; on ``bahr`` the same life
    is waived.  Wiring the waiver to membership of the care ledger instead gets both wrong.
    """
    return benefit_pct(g) > 0.0


def mort_rate_at_age(x):
    """q_A(x): the table's annual **active-life** death rate at attained age x, by sex.

    A lookup into *mort_table.csv* at ``(sex(), x)``; the core's ``mort_rate_base(t)`` reads
    it at ``age(t)``.
    """
    return float(data.mort_table_dict()["mort_rate"][(sex(), x)])    # noqa: F821


def mort_rate_mth(t):
    """The monthly active-life death rate, ``1 - (1 - mort_rate(t))**(1/12)``.

    Published because it is the quantity a reader checks the monthly step against, and
    because the error it guards is dividing an annual rate by twelve: ``mort_rate(t)/12``
    is strictly **below** this rate wherever the annual rate is positive, so dividing by
    twelve understates the monthly decrement.  Twelve of these rates *compounded* return
    the annual rate exactly, while twelve of them *added* overshoot it — the direction is
    the opposite of the intuition, which is why the pair is published.  The projection
    itself does not use it — it works in forces, through :func:`mort_force` — but the two
    agree by construction, ``1 - exp(-mort_force(t)/12)`` being this same number.

    Override reason: a published diagnostic of the force-based monthly step, the plain
    geometric twelfth at every age, the limiting one included, as the house convention asserts,
    products/pflegerentenversicherung/technical-notes.md:762
    """
    return 1.0 - (1.0 - mort_rate(t)) ** (1.0 / 12.0)


def mort_force(t):
    """mu_A(t): the force of active-life mortality, ``-ln(1 - mort_rate(t))``.

    Held constant over the month.  At the limiting age ``mort_rate`` is 1.0 and the force
    is infinite; it is capped at ``-ln(1e-12) = 27.63`` so the proportional allocation of
    the month's exits stays finite.  What survives the year of age 109 is then ``1e-12`` of
    the cohort that entered it — of the order of ``1e-17`` of the original policy on the
    anchor cell — so the closure identity is exact to far beyond the tolerance.
    """
    return -math.log(1.0 - min(mort_rate(t), 1.0 - data.param("rate_cap_eps")))  # noqa: F821


def mort_rate_care(t, g):
    """q_g(x): the annual death rate of a life in *Pflegegrad* ``g``.

    ``1 - exp(-mort_force_care(t, g))``.  Published so the single most load-bearing
    biometric statement in this product is visible as a number: the mortality of a
    *Pflegebedürftiger* is a large multiple of an active life's at the same age, rising
    sharply with the grade.

    Two consequences.  **The annuity in payment is short** — three to five years, not the
    fifteen to twenty of a healthy-life pension at the same age — so pricing it on an
    annuity table built to be prudent about people living *longer* would be prudent in
    exactly the wrong direction and would materially overprice the benefit.  And **grade
    and mortality are correlated**, so the highest-paying state is the shortest-lived: a
    model applying an average benefit percentage to a survival curve computed at an average
    mortality gets the wrong answer in a way no total will reveal.
    """
    return 1.0 - math.exp(-mort_force_care(t, g))                    # noqa: F821


def mort_force_care(t, g):
    """mu_g(t): ``mort_mult(g)`` times the **force** of active mortality at the same age.

    On the force and not on the rate, which is what makes the multiple mean the same thing
    at every age: 1.5 at grade 1 rising to 9.0 at grade 5, carrying the research file's
    order of magnitude — two to three times an active life at grade 2, five to ten times at
    grade 5.  On *rates* the ratio compresses towards 1 as ``mort_rate`` saturates at the
    oldest ages, which is an artefact of the rate scale and not a change in the basis.
    """
    mult = float(data.care_table_dict()["mort_mult"][g])             # noqa: F821
    return mult * mort_force(t)


def inc_rate(t):
    """i(x): the annual rate at which an active life enters **any** *Pflegegrad*.

    Read from *incidence_table.csv* by sex and attained age, a **[std]** exponential proxy
    capped at ``inc_cap``.  It is the rate of *leaving the active state for care*; the
    grade actually entered is drawn from :func:`inc_share`, because entry is not uniformly
    at the lowest grade — a stroke or a fracture enters directly at grade 3 or 4.

    The *Wartezeit* is **not** applied here.  It gates the force, in :func:`inc_force`, so
    that this cells stays the tariff-comparable table rate at every age.
    """
    return float(data.incidence_table_dict()["inc_rate"][            # noqa: F821
        (sex(), age(t))])


def inc_force(t):
    """iota(t): the force of incidence into care, **zero inside the *Wartezeit***.

    ``-ln(1 - inc_rate(t))`` once ``t >= wartezeit_months()``, and exactly zero before
    that: care beginning inside the *Wartezeit* is not covered at all.  It is also zero at
    the limiting age, so every exit there is death and the allocation stays well defined.
    """
    if duration_mth(t) < wartezeit_months():
        return 0.0
    return inc_force_age(age(t))


def inc_force_age(x):
    """The force of incidence at attained age ``x`` outside the *Wartezeit*.

    ``-ln(1 - inc_rate)`` at the age, zero at the limiting age.  Keyed by age: the
    incidence rate depends on the month only through ``age(t)``; it is read at
    :func:`age_month`.  :func:`inc_force` applies the *Wartezeit* gate on top.
    """
    if x >= omega_age() - 1:
        return 0.0
    return -math.log(1.0 - min(inc_rate(age_month(x)),               # noqa: F821
                               1.0 - data.param("rate_cap_eps")))    # noqa: F821


def inc_share(g):
    """s_g: the share of entrants into care whose first *Pflegegrad* is ``g``.

    Read from *care_table.csv*; sums to 1.00 over the five grades.  It is deliberately
    **not** the stock distribution of *Pflegebedürftige*, which runs about
    9 / 44 / 27 / 14 / 6 %: entrants skew lower than the stock, because deterioration moves
    people up the grades over a spell.  Using the stock as the entry mix is a listed
    pitfall, and the model's own stock share at grades 4 and 5 over a whole projection
    exceeds the entry share, which is the arithmetic statement of the same thing.
    """
    return float(data.care_table_dict()["entry_share"][g])           # noqa: F821


def det_rate(g):
    """The annual rate of deterioration from *Pflegegrad* ``g`` to ``g + 1``.

    Read from *care_table.csv*; zero at grade 5, which has nowhere to go.  Deterioration
    dominating recovery is one of the four properties a replacement table must preserve,
    and it is what makes the benefit grow over a spell.
    """
    return float(data.care_table_dict()["det_rate"][g])              # noqa: F821


def det_force(x, g):
    """delta_g(x): the force of deterioration out of grade ``g`` at attained age ``x``.

    Zero at grade 5, and zero also at the limiting age, so every exit there is death.
    Keyed by age, not by month: it depends on ``x`` and ``g`` alone, so it is evaluated
    once per age and grade; the monthly transitions read it at ``age(t)``.
    """
    if x >= omega_age() - 1:
        return 0.0
    q = det_rate(g)
    if q <= 0.0:
        return 0.0
    return -math.log(1.0 - min(q, 1.0 - data.param("rate_cap_eps")))  # noqa: F821


def recov_age_ref():
    """The attained age above which recovery is damped, from *param_tariff_type.csv*.

    A shape parameter of the recovery basis; :func:`rec_rate` reads it.
    """
    return float(data.param("recov_age_ref"))                        # noqa: F821


def recov_age_decay():
    """The recovery damping per year of age above ``recov_age_ref``, from *param_tariff_type.csv*.

    A shape parameter of the recovery basis; :func:`rec_rate` reads it.
    """
    return float(data.param("recov_age_decay"))                      # noqa: F821


def rec_rate(x, g):
    """The annual recovery rate from grade ``g`` at age ``x``, damped above ``recov_age_ref``.

    ``rec_rate(g) x exp(-recov_age_decay x max(0, x - recov_age_ref))`` with
    ``recov_age_ref = 75`` and ``recov_age_decay = 0.10`` **[std]**.  The damping is what makes
    deterioration dominate recovery above 75 — property (b) of a replacement table — and it
    encodes the one thing about *Reaktivierung* that is not in doubt: it is real after
    acute events at younger ages and small at the ages where most claims arise.

    Recovery from grade 1 leads to the **active** state, and a life that recovers starts
    paying its *Beitrag* again.

    Keyed by age, not by month: it depends on ``x`` and ``g`` alone, so it is evaluated
    once per age and grade; :func:`rec_force` and :func:`tar_rec_rate` read it at the
    attained age.
    """
    base = float(data.care_table_dict()["rec_rate"][g])              # noqa: F821
    return base * math.exp(-recov_age_decay() * max(0.0, x - recov_age_ref()))  # noqa: F821


def rec_force(x, g):
    """rho_g(x): the force of recovery out of grade ``g`` at attained age ``x``.

    Zero at the limiting age.  Keyed by age, like :func:`rec_rate`; the monthly
    transitions read it at ``age(t)``.
    """
    if x >= omega_age() - 1:
        return 0.0
    q = rec_rate(x, g)
    if q <= 0.0:
        return 0.0
    return -math.log(1.0 - min(q, 1.0 - data.param("rate_cap_eps")))  # noqa: F821


def lapse_factor(t):
    """The factor on the table lapse rate: 0 once the premium term has ended, else 1.

    Override reason: lapse is zero once the premium term has ended, a paid-up contract
    having no premium-driven exit, products/pflegerentenversicherung/technical-notes.md:363
    """
    if age(t) >= prem_end_age():
        return 0.0
    return 1.0


def p_act_age(x, waiting):
    """The active-state month transitions at attained age ``x``, as ``(stay, death, care)``.

    ``waiting`` is whether the month lies inside the *Wartezeit*, where the incidence force
    is zero.  The force of mortality :func:`mort_force` is read at :func:`age_month` and
    the incidence force is :func:`inc_force_age`; ``stay = exp(-(mu_A + iota)/12)`` and
    each exit its force's share of ``1 - stay``.  Allocating the one survival probability in
    proportion to the forces is what makes the three components sum to 1 exactly; adding
    monthly rates instead, or dividing an annual rate by twelve, does not.  ``care`` is zero
    inside the *Wartezeit*; the grade entered is then split by :func:`inc_share`.  Keyed by
    age and the gate, so it is evaluated about once per year of age; the ledger and the
    decrement counts read it at ``age(t)``.
    """
    mu = mort_force(age_month(x))
    iota = 0.0 if waiting else inc_force_age(x)
    stay = math.exp(-(mu + iota) / 12.0)                             # noqa: F821
    total = mu + iota
    return (stay, mu / total * (1.0 - stay), iota / total * (1.0 - stay))


def age_month(x):
    """The first month ``t`` on the projection clock at which the attained age is ``x``.

    ``12 (x - issue_age()) - clock_offset_mth()``, so that ``age(age_month(x)) == x``
    exactly.  The month at which the age-keyed transitions read the month-keyed forces.
    """
    return 12 * (x - issue_age()) - clock_offset_mth()


def p_pg_age(x, g):
    """The grade-``g`` month transitions at attained age ``x``, ``(stay, death, worse, better)``.

    Keyed by age, not by month: the care-grade force of mortality :func:`mort_force_care`
    depends on the month only through ``age(t)`` (the core's ``mort_rate(t)`` reads the
    table at the attained age), and :func:`det_force` and :func:`rec_force` are keyed by
    age already, so the transitions are the same in every month of a year of age.  The
    force is read at :func:`age_month`, the first month of that age.  If the core's
    ``mort_rate`` ever depends on the month beyond the age, this keying is wrong and has to
    go back to ``t`` (Moritz, 2026-10-29, lifting story 2.7's choice to keep ``t``).

    Three forces compete out of a paying state, not one — death, deterioration and
    recovery — which is the arithmetic form of the product's central structural fact: **the
    paying state has three exits and only death is absorbing**.  A model that lets it be
    exited only by death overstates the liability; one that treats every downgrade as a
    termination understates it.  ``death`` is grade-increasing because the mortality
    multiple is.  ``worse`` is the *Höherstufung* to ``g + 1``, zero at grade 5; the insured
    does not elect it: it is applied for and re-assessed by the *Medizinischer Dienst* or
    MEDICPROOF, so grade change is a biometric transition here rather than a
    claims-management outcome.  ``better`` is the *Herabstufung* to ``g - 1``: out of grade 1
    it leads to the **active** state — *Reaktivierung* — where the life starts paying its
    *Beitrag* again and becomes exposed to lapse once more; out of the higher grades it moves
    the life down one step of the *Leistungsstaffel*, which reduces the annuity without
    ending it, and out of the lowest **insured** grade it stops the annuity and revives the
    premium.  All three cases fall out of the same recursion; none of them is a claim
    decision.
    """
    mu = mort_force_care(age_month(x), g)
    delta = det_force(x, g)
    rho = rec_force(x, g)
    total = mu + delta + rho
    stay = math.exp(-total / 12.0)                                   # noqa: F821
    rest = 1.0 - stay
    return (stay, mu / total * rest, delta / total * rest, rho / total * rest)


def pols_ledger(t):
    """The second-order ledgers at the start of month ``t``, as one state.

    ``(act, pg, esc, karenz, entry, grad)``: :func:`pols_act`, :func:`pols_pg` and
    :func:`esc_pg` for ``g = 1 .. 5`` and :func:`pols_karenz` for ``g = 1 .. 5`` and
    ``z = 1 .. karenz_months()``, rolled forward from the state at ``t - 1`` by the
    recursions those cells state, with the same operations in the same order.  ``entry``
    and ``grad`` are month ``t - 1``'s entrants into *Pflegegrad* ``g`` and graduations out
    of the *Karenz* ledger into it, ``g = 1 .. 5``, which the roll forward forms from the
    previous state together with the month's reactivations (:func:`pols_reactiv`); zeros
    at ``t_start()``.  One evaluation per month instead of one per month, grade and clock;
    the published cells, :func:`pols_entry` and :func:`pols_grad` among them, read their
    component.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    k = karenz_months()
    if t <= t_start():
        status = status_init()
        act = pols_if_init() if status == "aktiv" else 0.0
        pg = tuple(pols_if_init() if status == "pg%d" % g else 0.0 for g in range(1, n + 1))
        none = (0.0,) * n
        return (act, pg, pg, tuple((0.0,) * k for g in range(1, n + 1)), none, none)
    act0, pg0, esc0, kar0, _, _ = pols_ledger(t - 1)
    x = age(t - 1)
    p = tuple(p_pg_age(x, g) for g in range(1, n + 1))
    pa = p_act_age(age(t - 1), duration_mth(t - 1) < wartezeit_months())
    care = act0 * pa[2]
    entry = tuple(care * inc_share(g) for g in range(1, n + 1))
    if k <= 0:
        grad = entry
        kar = kar0
    else:
        grad = []
        kar = []
        for g in range(1, n + 1):
            total = 0.0
            for h in range(max(1, g - 1), min(n, g + 1) + 1):
                w = kar0[h - 1][k - 1]
                if w == 0.0:
                    continue
                if h == g:
                    total += w * p[h - 1][0]
                elif g == h + 1:
                    total += w * p[h - 1][2]
                else:
                    total += w * p[h - 1][3]
            grad.append(total)
            row = [entry[g - 1]]
            for z in range(2, k + 1):
                total = 0.0
                for h in range(max(1, g - 1), min(n, g + 1) + 1):
                    w = kar0[h - 1][z - 2]
                    if w == 0.0:
                        continue
                    if h == g:
                        total += w * p[h - 1][0]
                    elif g == h + 1:
                        total += w * p[h - 1][2]
                    else:
                        total += w * p[h - 1][3]
                row.append(total)
            kar.append(tuple(row))
        kar = tuple(kar)
    reactiv = pg0[0]
    for z in range(1, k + 1):
        reactiv += kar0[0][z - 1]
    reactiv = reactiv * p[0][3]
    act = (act0 * pa[0] + reactiv) * (1.0 - lapse_rate_mth(t - 1))
    factor = (1.0 + leistungsdynamik()) ** (1.0 / 12.0)
    pg = []
    esc = []
    for g in range(1, n + 1):
        total = pg0[g - 1] * p[g - 1][0] + grad[g - 1]
        carried = esc0[g - 1] * p[g - 1][0]
        if g > 1:
            total += pg0[g - 2] * p[g - 2][2]
            carried += esc0[g - 2] * p[g - 2][2]
        if g < n:
            total += pg0[g] * p[g][3]
            carried += esc0[g] * p[g][3]
        pg.append(total)
        esc.append(factor * carried + grad[g - 1])
    return (act, tuple(pg), tuple(esc), kar, entry, tuple(grad))


def pols_act(t):
    """l_A(t): lives in the **active** state at the start of month ``t``.

    Seeded at ``t_start()`` from :func:`status_init` and rolled forward as

        l_A(t+1) = [ l_A(t) p_stay(t) + pols_reactiv(t) ] (1 - w(t))

    with ``p_stay(t)`` the ``stay`` component of :func:`p_act_age` at ``age(t)`` — survivors
    of both insured decrements, plus the month's *Reaktivierungen*, then exposed to lapse.
    **Lapse acts after the insured decrements and after the reactivation
    inflow**; the alternatives give different answers and this ordering is the one the
    notes' processing order states.
    """
    return pols_ledger(t)[0]


def pols_entry(t, g):
    """Lives entering *Pflegegrad* ``g`` from the active state during month ``t``.

    ``pols_act(t) x p_care(t) x inc_share(g)``, with ``p_care(t)`` the ``care`` component of
    :func:`p_act_age` at ``age(t)``.  Entry is split across the grades because it is not
    uniformly at the lowest one, and the split is one of the four properties a replacement
    basis must preserve.  The ledger forms it when it rolls month ``t`` forward, so this
    reads it from :func:`pols_ledger` at ``t + 1`` rather than computing it a second time.
    """
    return pols_ledger(t + 1)[4][g - 1]


def pols_karenz(t, g, z):
    """W_{g,z}(t): lives in *Pflegegrad* ``g`` whose *Karenzzeit* clock stands at ``z``.

    The ledger exists only when ``karenz_months() > 0``; otherwise it is empty and a life
    graduates in the month it enters.  Entrants join at ``z = 1`` and advance one month at
    a time, subject to the **same** transitions as a served life — they die, deteriorate
    and recover exactly as if the annuity were running, they simply are not paid.

    The clock is **discarded on reactivation**: the *Karenzzeit* runs from onset, so a
    recovered life who later relapses starts a new onset and a new clock.  That is why
    recovery out of ``g = 1`` leaves this ledger for the active state instead of moving to
    a lower ``g``, and why :func:`pols_reactiv` reads across both ledgers.

    A life in this ledger is in care, is counted in :func:`pols_if` and in
    :func:`pols_care`, receives no annuity, and **pays its Beitrag**, because the waiver
    runs with the annuity and not with the diagnosis.
    """
    k = karenz_months()
    if k <= 0 or z < 1 or z > k:
        return 0.0
    if t <= t_start():
        return 0.0
    return pols_ledger(t)[3][g - 1][z - 1]


def pols_grad(t, g):
    """Lives graduating out of the *Karenz* ledger into *Pflegegrad* ``g`` in month ``t``.

    Where ``karenz_months() == 0`` this is exactly :func:`pols_entry` — the degenerate case
    the base run runs in — and where it is positive it is the ``z = K`` cohort carried one
    more month through the same transitions.

    The difference between the two is the whole cost of a *Karenzzeit*: summed over the
    projection, graduations fall strictly short of entries, and the shortfall is the deaths
    and recoveries recorded **inside** the deferral.  Because mortality is highest
    immediately after onset, that shortfall is larger than the length of the deferral
    suggests — a deferred period on a population with elevated mortality removes
    disproportionately more claims than the same period would on a healthy population.

    The ledger forms the graduations when it rolls month ``t`` forward, from the ``z = K``
    cohort of :func:`pols_karenz` and the grade transitions of :func:`p_pg_age` at
    ``age(t)``, so this reads them from :func:`pols_ledger` at ``t + 1``.
    """
    return pols_ledger(t + 1)[5][g - 1]


def pols_reactiv(t):
    """Lives recovering out of *Pflegegrad* 1 to the **active** state during month ``t``.

    Read across both care ledgers — the paying one and the *Karenz* one — because a life
    still inside its deferred period can recover just as a paid one can.  A reactivated
    life rejoins :func:`pols_act`, resumes paying its *Beitrag* and becomes exposed to lapse
    again in the same month, which is why the term appears inside :func:`pols_act`'s lapse
    bracket rather than beside it.
    """
    state = pols_ledger(t)
    total = state[1][0]
    for z in range(1, karenz_months() + 1):
        total += state[3][0][z - 1]
    return total * p_pg_age(age(t), 1)[3]


def pols_pg(t, g):
    """l_g(t): lives in *Pflegegrad* ``g`` at the start of month ``t``, *Karenz* served.

    The ledger the annuity is paid on.  Seeded at ``t_start()`` from
    :func:`status_init` — an in-claim model point opens with its whole cohort here, at its
    grade, with the deferral already served — and rolled forward as

        l_g(t+1) = l_g(t) p_stay + l_{g-1}(t) p_worse + l_{g+1}(t) p_better + grad_g(t)

    with the ``g = 1`` recovery term flowing to the active state instead and the ``g = 5``
    deterioration term absent.  Every one of those moves is **internal** to the in-force
    population, which is why :func:`check_pols_roll_fwd` sees only deaths and lapses.
    """
    return pols_ledger(t)[1][g - 1]


def esc_pg(t, g):
    """E_g(t): the **escalation-weighted** counterpart of :func:`pols_pg`.

    The same population, weighted by each life's own escalation factor since its annuity
    began: the identical recursion with one extra factor of ``(1 + d)**(1/12)`` on the
    surviving weights, entrants joining at weight 1.

    Carrying the escalation as a **value ledger** rather than as a duration-since-onset
    cohort dimension is what keeps the model O(n) instead of O(n squared); the price is
    that it reports only the aggregate escalation, which is all the cash flow needs.  With
    ``leistungsdynamik = 0`` the extra factor is 1 and this is the :func:`pols_pg`
    recursion exactly, so the two ledgers agree at every ``t`` and ``g`` —
    :func:`check_esc_ledger` asserts it.

    The annuity is weighted on **this** ledger and never on :func:`pols_pg`.  Using the
    head count would silently drop the escalation on every model point that carries one,
    and no total in the frame would look wrong.
    """
    return pols_ledger(t)[2][g - 1]


def pols_care(t):
    """Everyone in care at the start of month ``t``: the *Karenz* and paying ledgers.

    ``sum_g pols_pg(t, g) + sum_{g,z} pols_karenz(t, g, z)``.  It is **not** the population
    receiving an annuity and **not** the population whose premium is waived: a life inside
    its *Karenzzeit* is here and is paid nothing, and a life at *Pflegegrad* 1 on the
    ``delib_std`` grid is here, is paid nothing and keeps paying.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    state = pols_ledger(t)
    total = 0.0
    for g in range(1, n + 1):
        total += state[1][g - 1]
    for g in range(1, n + 1):
        for z in range(1, karenz_months() + 1):
            total += state[3][g - 1][z - 1]
    return total


def pols_if(t):
    """l(t): policies in force at the **start** of month ``t``, active or in care.

    The weight on that same ``result_cf()`` row's cash flows, which is the library-wide
    convention; end-of-period state goes through :func:`pols_if_at` and never through this
    cells read at ``t + 1``.  ``result_cf()``'s first value equals :func:`pols_if_init`
    exactly, because no decrement has been applied when a period opens.

    Every *Pflegegrad* transition is internal to this count.  Lives leave it only by death
    or by surrender, which is what :func:`check_pols_roll_fwd` asserts.

    Override reason: the count is the sum of the active and the care ledgers, every
    *Pflegegrad* transition internal to it,
    products/pflegerentenversicherung/technical-notes.md:203
    """
    return pols_ledger(t)[0] + pols_care(t)


def pols_in_term(t):
    """In-force units inside the premium-paying term: ``pols_if(t)`` while x(t) < prem_end_age.

    Zero once the term has ended, at which point the contract is paid up: no premium, no
    waiver population and no lapse, with the cover running on to the terminal age.
    """
    if age(t) >= prem_end_age():
        return 0.0
    return pols_if(t)


def pols_waived(t):
    """The *Beitragsbefreiung* population: in-term units in a **paying** *Pflegegrad*.

    ``sum_{g : waiver_flag(g)} pols_pg(t, g)``, restricted to the premium term.  Three
    consequences follow directly from the *Leistungsstaffel*, and each is a way to get the
    waiver wrong: a life in a *Karenz* ledger is **not** here, because no annuity is yet
    payable; a *Pflegegrad* 1 life is **not** here on ``delib_std`` and **is** here on
    ``bahr``; and a life downgraded out of the insured grades **leaves** here and starts
    paying again.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    if age(t) >= prem_end_age():
        return 0.0
    total = 0.0
    for g in range(1, n + 1):
        if waiver_flag(g):
            total += pols_ledger(t)[1][g - 1]
    return total


def pols_prem(t):
    """The units that actually pay a *Beitrag*: ``pols_in_term(t) - pols_waived(t)``.

    **Not monotone.** It falls as lives die, lapse and enter paying grades, and it *rises*
    again whenever a *Herabstufung* takes a life out of the insured grades and revives its
    premium obligation.  A model whose premium-paying count only ever falls has wired the
    waiver as an absorbing state, which is the single most common way to get this product's
    premium stream wrong.

    Override reason: the paying units are the lives inside the premium term less those whose
    *Beitrag* is waived in care, products/pflegerentenversicherung/technical-notes.md:540
    """
    return pols_in_term(t) - pols_waived(t)


def pols_death(t):
    """Deaths during month ``t``, from **every** state.

    The active state at the ``death`` component of :func:`p_act_age`, and each *Pflegegrad*
    — in the paying ledger and in the *Karenz* ledger alike — at that of :func:`p_pg_age`,
    which is grade-increasing because the mortality multiple is.  Aggregating the care
    ledgers into one average death rate is the arithmetic form of forgetting that the
    highest-paying state is also the shortest-lived.

    Override reason: the deaths come from every state, the active state and each *Pflegegrad*
    at its own rate, products/pflegerentenversicherung/technical-notes.md:207
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    state = pols_ledger(t)
    total = state[0] * p_act_age(age(t), duration_mth(t) < wartezeit_months())[1]
    for g in range(1, n + 1):
        in_grade = state[1][g - 1]
        for z in range(1, karenz_months() + 1):
            in_grade += state[3][g - 1][z - 1]
        total += in_grade * p_pg_age(age(t), g)[1]
    return total


def pols_lapse(t):
    """Surrenders during month ``t``, from the **active state only**.

    ``[ pols_act(t) p_stay(t) + pols_reactiv(t) ] w(t)``, with ``p_stay(t)`` the ``stay``
    component of :func:`p_act_age` at ``age(t)`` — the survivors of the insured
    decrements together with the month's reactivations, exposed to lapse after both.
    Nothing in care lapses: a claimant with a waived premium has no premium to default on
    and a live annuity to forfeit.  A *Pflegegrad* 1 life on ``delib_std`` does still pay
    and could in principle surrender; the population is small and the model does not model
    it, which is a stated simplification rather than an oversight.

    Override reason: the lapses come from the active state only, its survivors of the
    insured decrements together with the month's reactivations,
    products/pflegerentenversicherung/technical-notes.md:491
    """
    survivors = (pols_ledger(t)[0] * p_act_age(age(t), duration_mth(t) < wartezeit_months())[0]
                 + pols_reactiv(t))
    return survivors * lapse_rate_mth(t)


def pols_dead_cum(t):
    """Cumulative deaths before the start of month ``t``.

    One of the two absorbing counts that, with the three live ledgers, partition the
    initial cohort at every ``t``; see :func:`check_states`.
    """
    if t <= t_start():
        return 0.0
    return pols_dead_cum(t - 1) + pols_death(t - 1)


def pols_lapse_cum(t):
    """Cumulative surrenders before the start of month ``t``."""
    if t <= t_start():
        return 0.0
    return pols_lapse_cum(t - 1) + pols_lapse(t - 1)


def premium_due(t):
    """Whether an instalment falls due at the start of month ``t``.

    ``t % prem_cycle() == 0`` inside the premium term, and for the *Einmalbeitrag*
    only at ``t = 0``.  The instalment months key off **issue**, not off the frame's first
    row, so an in-force quarterly point opening at ``t = 240`` still pays in the months the
    contract always paid in.

    A waiver that begins between two due dates therefore takes effect **at the next due
    date**, which is the German convention for a *Beitragsbefreiung* on a fractionated
    contract; the alternative — refunding the unearned instalment — is a different and
    equally arguable rule the model does not implement.
    """
    if age(t) >= prem_end_age():
        return False
    if prem_form() == "single":
        return t == 0
    return t % prem_cycle() == 0


def premium_pp(t):
    """The instalment charged per paying policy at the start of month ``t``.

    ``premium_mth_pp() x prem_cycle()`` on a due month and zero otherwise, so a
    quarterly contract pays three months' worth three times a year rather than a twelfth of
    the annual amount every month.  For the *Einmalbeitrag*, ``prem_form() == "single"``,
    it is the whole *Einmalbeitrag*, once, at ``t = 0``, and ``prem_freq`` is not read: the
    premium cells test the form before the frequency.

    The model charges **no separate** *Ratenzahlungszuschlag*: the instalment loading is
    folded into ``load_admin_prem_inst``, which is a percentage of the premium collected and so
    is invariant to the mode.  The consequence is worth stating because a user will read
    it the wrong way round — in this model annual mode prices very slightly *below*
    monthly, through the timing of the discounting alone, which is the opposite sign to a
    real German tariff.
    """
    if not premium_due(t):
        return 0.0
    if prem_form() == "single":
        return premium_mth_pp()
    return premium_mth_pp() * prem_cycle()


def cum_prem_max_pp(t):
    """The *Beitrag* payable to date per policy on an **uninterrupted** path.

    A deterministic quantity, not a ledger: it is what a policy that never claimed, never
    lapsed and never died would have paid by the end of month ``t``, and it is the base of
    both the *Rückkaufswert* and the *Beitragsrückgewähr*.  It includes the instalment
    collected at the start of month ``t``, because both benefits fall at the **end** of the
    month.

    Computing it in closed form rather than by accumulating :func:`premiums` is what lets an
    in-force model point carry the right base at the frame's first row: the premiums paid
    before the valuation date were paid, whether or not the model projected them.
    """
    if prem_form() == "single":
        return premium_mth_pp() if t >= 0 else 0.0
    m = prem_cycle()
    last = min(t, 12 * (prem_end_age() - issue_age()) - 1)
    if last < 0:
        return 0.0
    return premium_mth_pp() * m * (last // m + 1)


def prem_inst_pp(t):
    """The *Beitrag* per paying unit in month ``t``, :func:`premium_pp`.

    Collected **in advance**, at the start of the month; the core's :func:`premiums`
    weights it by :func:`pols_prem`, the lives then inside the term and not waived.
    Income-positive, like every other term of :func:`net_cf`.

    Override reason: the premium is ``premium_pp(t)``, the monthly *Beitrag* in a month it
    is due, products/pflegerentenversicherung/technical-notes.md:551
    """
    return premium_pp(t)


def rkw_pp(t):
    """The *Rückkaufswert* per surrendering policy at the end of month ``t``.

    ``rkw_prem_ratio(min(y(t), Y)) x cum_prem_max_pp(t) x (1 - stornoabzug_rate())``, with
    ``Y = data.surrender_table_last_year()`` the table's last policy year, 40 — the
    guaranteed surrender value as a fraction of premiums paid to date, which is the
    scale-free form a German contract states, less any contractual *Stornoabzug*.

    It is **near zero for the first several years** and stays well below premiums paid for
    a long time, because the *Zillmerung* allowance is large and the risk premium in the
    early years is small.  That is the honest thing to tell a buyer, and it is the strongest
    argument for the *Beitragsrückgewähr* option.  Whether a **pure-risk** *Pflegerente*
    falls inside § 169 VVG at all is an open question this library states rather than
    assumes away; the table encodes the answer for a contract that does.
    """
    ratio = float(data.surrender_table_dict()["rkw_prem_ratio"][     # noqa: F821
        min(policy_year(t), data.surrender_table_last_year())])     # noqa: F821
    return ratio * cum_prem_max_pp(t) * (1.0 - stornoabzug_rate())


def brg_pp(t):
    """The *Beitragsrückgewähr* per dying policy at the end of month ``t``.

    ``cum_prem_max_pp(t)`` where the option is on and ``0.0`` where it is not, so
    ``claims(t, "DEATH")`` is structurally zero in the base run.  The **gross** form —
    no offset for annuity already paid — for the reason given at
    :func:`beitragsrueckgewaehr`.
    """
    if not beitragsrueckgewaehr():
        return 0.0
    return cum_prem_max_pp(t)


def claims(t, kind=None):
    """Benefit outgo in month ``t`` by ``kind``; the total when ``kind`` is omitted.

    ``"ANNUITY"`` is the *Pflegerente*, ``R sum_g pi_g E_g(t)``, paid **in advance** on the
    escalation ledger.  Two things about that weighting are load-bearing.  It is
    :func:`esc_pg` and not :func:`pols_pg`, so an escalation is never silently dropped.  And
    it is a **grade-by-grade** sum, never an average percentage on an average survival
    curve: grade and mortality are correlated, so the highest-paying state is the
    shortest-lived and the two are not interchangeable.  The *Karenz* ledger contributes
    nothing — a life inside its deferred period is in care, is counted in force, pays its
    premium and receives no annuity.

    ``"LAPSE"`` is the *Rückkaufswert* and ``"DEATH"`` the *Beitragsrückgewähr*, both at the
    **end** of the month on the lives that left during it.

    Override reason: the total adds the three kinds left to right, ``A + L + D``, where the
    core's ``sum`` over the kinds rounds otherwise (compensated summation),
    products/pflegerentenversicherung/technical-notes.md:570
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    if kind is None:
        return (claims(t, "ANNUITY") + claims(t, "LAPSE")
                + claims(t, "DEATH"))
    elif kind == "ANNUITY":
        total = 0.0
        for g in range(1, n + 1):
            pct = benefit_pct(g)
            if pct > 0.0:
                total += pct * pols_ledger(t)[2][g - 1]
        return rente_mth() * total
    elif kind == "LAPSE":
        return rkw_pp(t) * pols_lapse(t)
    elif kind == "DEATH":
        return brg_pp(t) * pols_death(t)
    else:
        raise ValueError("invalid kind")


def beitragssumme_prem():
    """The annual premium of the *Beitragssumme*: ``premium_mth_pp() x 12``.

    And, for the *Einmalbeitrag*, the *Einmalbeitrag* itself, counted once.  The
    *Beitragssumme* is the base the *Zillmerung* allowance is struck on.

    Override reason: the premium is monthly, ``premium_mth_pp()``, or a single premium,
    products/pflegerentenversicherung/technical-notes.md:403
    """
    if prem_form() == "single":
        return premium_mth_pp()
    return premium_mth_pp() * 12.0


def beitragssumme_years():
    """The premium years of the *Beitragssumme*, ``min(prem_end_age(), 85) - issue_age()``.

    A lifelong-premium contract has no finite *Beitragssumme* without a convention, and
    ``beitragssumme_cap_age = 85`` **[std]** is that convention.  It is a parameter, not a
    citation: what is cited is the 25 ‰ ceiling of DeckRV § 4 that the rate is set
    exactly at, cut from 40 ‰ by the LVRG from 1 January 2015.  1 for the *Einmalbeitrag*.

    Override reason: the premium runs to ``prem_end_age``, capped at
    ``beitragssumme_cap_age``, products/pflegerentenversicherung/technical-notes.md:403
    """
    if prem_form() == "single":
        return 1
    cap = int(data.param("beitragssumme_cap_age"))                   # noqa: F821
    return max(0, min(prem_end_age(), cap) - issue_age())


def alpha_rate():
    """The acquisition rate on the *Beitragssumme*, ``load_acq_bsum_once``.

    :func:`zillmer_amount`, the acquisition and distribution charge per policy, incurred
    once at ``t = 0``, is ``load_acq_bsum_once x beitragssumme()``, with the rate set
    **exactly at** the § 4 DeckRV *Höchstzillmersatz* so the ceiling binds visibly.  The
    base is the *Beitragssumme*, **not** the annual premium — charging the rate on an
    annual premium understates it by a factor of the paying term and is a listed pitfall.

    Because it falls at ``t = 0`` only, an in-force model point never incurs it: its frame
    opens at ``duration_mth_init() > 0`` and the cost was incurred before the valuation
    date.  That is correct, and it is worth knowing before comparing an in-force point's
    first row with a new-business point's.
    """
    return float(data.param("load_acq_bsum_once"))                   # noqa: F821


def inflation_years(t):
    """The years of expense inflation at month ``t``, ``t / 12``: continuous, not stepped.

    The core's :func:`inflation_factor` is then ``(1 + expense_infl)**(t/12)``, applied to the
    per-policy administration cost and to the per-annuity-payment claims cost, both of which
    are euro amounts quoted at ``t = 0`` prices.  Over the anchor cell's sixty-five years it
    is a factor of about 3.6 at the 2.0 % rate, which is enough for the per-policy line to decide the viability
    of a small contract on its own.

    Override reason: the expense inflation compounds continuously over ``t / 12`` years,
    products/pflegerentenversicherung/technical-notes.md:591
    """
    return t / 12.0


def expenses(t):
    """Acquisition and administration expense in month ``t``, at the start of the month.

    Three components: the acquisition charge at ``t = 0`` only; a per-policy administration
    cost on every policy in force, inflated; and a percentage of the *Beitrag* just
    collected, which is where the instalment loading the model does not charge separately
    lives.  Claims-handling cost is **not** here — it is a per-event cost and is published
    as its own column, :func:`claim_expenses`.

    Override reason: the acquisition expense is the *Zillmerung* allowance at ``t = 0``,
    products/pflegerentenversicherung/technical-notes.md:593, added after the two
    administration terms, an order the core's sum of its terms would reassociate
    """
    admin_pp = float(data.param("load_admin_pp_mth"))                # noqa: F821
    admin_pct = float(data.param("load_admin_prem_inst"))            # noqa: F821
    total = admin_pp * inflation_factor(t) * pols_if(t)
    total += admin_pct * premiums(t)
    if t == 0:
        total += zillmer_amount()
    return total


def claim_expenses(t):
    """The claims-handling cost of month ``t``, per **annuity payment made**.

    ``load_claim_pp_inst x inflation_factor(t) x sum_{g : waiver_flag(g)} pols_pg(t, g)``,
    so it is weighted on the paying grades only: a *Pflegegrad* 1 life on ``delib_std``
    generates none, and neither does a life inside its *Karenzzeit*.

    The level is set low, and that is a product fact rather than an optimistic assumption:
    the *Pflegegrad* is determined by the *Medizinischer Dienst* or by MEDICPROOF and not
    by the insurer, so the *Nachprüfung* is a documentation exercise rather than the
    adversarial re-assessment that drives a *Berufsunfähigkeitsrente*'s claims cost.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    per_payment = float(data.param("load_claim_pp_inst"))            # noqa: F821
    total = 0.0
    for g in range(1, n + 1):
        if waiver_flag(g):
            total += pols_ledger(t)[1][g - 1]
    return per_payment * inflation_factor(t) * total


def net_cf(t):
    """The net liability cash flow of month ``t``, **income positive**.

    *Beitrag* less the *Pflegerente*, the *Rückkaufswert*, any *Beitragsrückgewähr*, the
    acquisition and administration expense and the claims-handling cost.  The notes' own
    sign, and the library-wide one.

    The shape to expect on the anchor cell is a large strain at ``t = 0``, where the 25 ‰
    *Zillmerung* allowance is charged in full; then thirty-odd years of positive monthly
    margins, the level *Beitrag* running far above the risk premium; then a long negative
    tail from the seventies onward as the incidence curve overtakes it.  That crossing is
    where the *Deckungskapital* peaks, and it is the whole economic content of an ageing
    reserve carried on a life-assurance chassis.

    Override reason: the claim total is subtracted at once and the claims-handling cost
    after the expenses, products/pflegerentenversicherung/technical-notes.md:597
    """
    return premiums(t) - claims(t) - expenses(t) - claim_expenses(t)


def mort_actv_load_first():
    """The first-order prudence margin on active mortality, from *param_tariff_type.csv*.

    Read by :func:`mort_rate_tariff`.
    """
    return float(data.param("mort_actv_load_first"))                 # noqa: F821


def mort_care_load_first():
    """The first-order prudence margin on in-care mortality, from *param_tariff_type.csv*.

    Read by :func:`tar_mort_rate_care`.
    """
    return float(data.param("mort_care_load_first"))                 # noqa: F821


def inc_load_first():
    """The first-order prudence margin on incidence, from *param_tariff_type.csv*.

    Read by :func:`tar_inc_rate`.
    """
    return float(data.param("inc_load_first"))                       # noqa: F821


def inc_cap():
    """The cap on the first-order incidence rate, a shape parameter of *param_tariff_type.csv*.

    Read by :func:`tar_inc_rate`.
    """
    return float(data.param("inc_cap"))                              # noqa: F821


def det_load_first():
    """The first-order prudence margin on deterioration, from *param_tariff_type.csv*.

    Read by :func:`tar_det_rate`.
    """
    return float(data.param("det_load_first"))                       # noqa: F821


def recov_load_first():
    """The first-order prudence margin on recovery, from *param_tariff_type.csv*.

    Read by :func:`tar_rec_rate`.
    """
    return float(data.param("recov_load_first"))                     # noqa: F821


def mort_rate_tariff(t):
    """The first-order active-life death rate: blended across the sexes, margined.

    ``mort_actv_load_first x [ mix q_M(x) + (1 - mix) q_F(x) ]``, forced to 1.0 at the limiting
    age.  Two separate things are happening and both are deliberate.

    The **blend** is the unisex constraint: sex may not enter the premium of a contract
    concluded from 21 December 2012, so the price is struck on a mixed basis while the
    projection runs on the model point's own sex.  ``unisex_mix_male = 0.50`` is a
    **[std]** assumption, and pricing a 50 / 50 mix while writing 60 / 40 is a named model
    risk — the mismatch is the whole cross-subsidy, and the mix is endogenous to the price.

    The **margin** is prudence, and its direction forks by risk.  For an active life,
    prudence means *lower* mortality — a life that survives is a life that can claim — so
    the margin is 0.90 and not 1.10.  Only the direction is cited; no German
    *Sicherheitszuschlag* level for a *Pflegetafel* was established, and the responsible
    actuary sets it in practice.

    Override reason: the first-order rate is the table rate times its prudence margin, the
    sexes blended, products/pflegerentenversicherung/model.md:204
    """
    if age(t) >= omega_age() - 1:
        return 1.0
    margin = mort_actv_load_first()
    q_m = float(data.mort_table_dict()["mort_rate"][("M", age(t))])  # noqa: F821
    q_f = float(data.mort_table_dict()["mort_rate"][("F", age(t))])  # noqa: F821
    return min(1.0 - data.param("rate_cap_eps"), margin * unisex_blend(q_m, q_f))  # noqa: F821


def tar_mort_rate_care(x, g):
    """The first-order in-care death rate at *Pflegegrad* ``g`` and attained age ``x``.

    ``mort_care_load_first x [ 1 - exp(-mort_mult(g) mu_blend) ]``, where ``mu_blend`` is the
    force of the **unmargined** blended active rate.  Taking the multiple on the unmargined
    force is what keeps the two mortality margins from compounding: the active margin
    lengthens the pre-claim period and the in-care margin lengthens the annuity, and they
    are separate prudence statements about separate risks.  ``mort_care_load_first = 0.85``
    lowers in-care mortality, which lengthens the annuity — prudent in the direction that
    costs money here, and the opposite of what an annuity table would do.

    Keyed by age, not by month: every input depends on ``x`` and ``g`` alone, so it is
    evaluated once per age and grade; :func:`tar_p_pg` reads it at the attained age.
    """
    if x >= omega_age() - 1:
        return 1.0
    margin = mort_care_load_first()
    mult = float(data.care_table_dict()["mort_mult"][g])             # noqa: F821
    q_m = float(data.mort_table_dict()["mort_rate"][("M", x)])       # noqa: F821
    q_f = float(data.mort_table_dict()["mort_rate"][("F", x)])       # noqa: F821
    q = min(1.0 - data.param("rate_cap_eps"), unisex_blend(q_m, q_f))  # noqa: F821
    mu = -math.log(1.0 - q)                                          # noqa: F821
    return min(1.0 - data.param("rate_cap_eps"),                     # noqa: F821
               margin * (1.0 - math.exp(-mult * mu)))                # noqa: F821


def tar_inc_rate(x):
    """The first-order incidence rate: blended across the sexes, margined, capped.

    ``min(inc_load_first x [ mix i_M(x) + (1 - mix) i_F(x) ], inc_cap)``.
    ``inc_load_first = 1.25`` is prudence in the obvious direction — more claims — and it is the margin the whole
    product's basis risk sits behind: DAV 2008 P was built on the superseded *Pflegestufen*
    and the 2017 reform widened the insured population, and no margin is a substitute for
    that.  The cap binds only at the very oldest ages, where the exponential proxy would
    otherwise exceed the survival it is applied to.

    Keyed by attained age ``x``, not by month: the *Wartezeit* gate, which does depend on
    the month, is applied by :func:`tar_p_act`, which reads this at ``age(t)``.
    """
    margin = inc_load_first()
    cap = inc_cap()
    i_m = float(data.incidence_table_dict()["inc_rate"][("M", x)])   # noqa: F821
    i_f = float(data.incidence_table_dict()["inc_rate"][("F", x)])   # noqa: F821
    return min(margin * unisex_blend(i_m, i_f), cap)


def tar_det_rate(g):
    """The first-order deterioration rate: ``det_load_first x det_rate(g)``, capped below 1.

    ``det_load_first = 1.15`` moves lives faster into the higher-paying grades, which is
    prudence on a schedule whose top steps pay most.  Keyed by the grade alone, since
    neither factor depends on the age or the month.
    """
    return min(1.0 - data.param("rate_cap_eps"), det_load_first() * det_rate(g))  # noqa: F821


def tar_rec_rate(x, g):
    """The first-order recovery rate at attained age ``x``: ``recov_load_first x rec_rate(x, g)``.

    ``recov_load_first = 0.80`` produces **fewer** recoveries and so longer spells in payment,
    which is the prudent direction for a benefit that stops on recovery.  Keyed by age and
    grade, like :func:`rec_rate`.
    """
    return recov_load_first() * rec_rate(x, g)


def tar_p_act(t):
    """The first-order active-state month transitions, as ``(stay, death, care)``.

    The same constant-force, proportional-allocation step as :func:`p_act_age`, on the
    first-order rates and with the *Wartezeit* gate applied to the incidence force.
    Returned as one tuple rather than three cells because the tariff
    ledgers are an internal engine: they have no reader outside :func:`premium_mth_pp` and
    :func:`check_prem_equiv`, and splitting them would triple the pricing engine's surface
    for no gain.
    """
    mu_a = -math.log(1.0 - min(mort_rate_tariff(t), 1.0 - data.param("rate_cap_eps")))  # noqa: F821
    if duration_mth(t) < wartezeit_months() or age(t) >= omega_age() - 1:
        mu_i = 0.0
    else:
        mu_i = -math.log(1.0 - min(tar_inc_rate(age(t)),             # noqa: F821
                                   1.0 - data.param("rate_cap_eps")))  # noqa: F821
    total = mu_a + mu_i
    stay = math.exp(-total / 12.0)                                   # noqa: F821
    return (stay, mu_a / total * (1.0 - stay), mu_i / total * (1.0 - stay))


def tar_p_pg(x, g):
    """The first-order grade-``g`` month transitions, as ``(stay, death, worse, better)``.

    The same allocation as :func:`p_pg_age`, on the first-order rates.
    The four components sum to exactly 1 by construction, which is what makes the tariff
    ledgers a closed system and :func:`check_prem_equiv` a real identity.

    Keyed by age, not by month: every rate it reads depends on ``x`` and ``g`` alone, so
    the transitions are evaluated once per age and grade; the tariff ledgers, which run
    by month, read them at ``age(t)``.
    """
    mu_g = -math.log(1.0 - min(tar_mort_rate_care(x, g),             # noqa: F821
                               1.0 - data.param("rate_cap_eps")))    # noqa: F821
    if x >= omega_age() - 1:
        mu_d = 0.0
        mu_r = 0.0
    else:
        q_d = tar_det_rate(g)
        q_r = tar_rec_rate(x, g)
        mu_d = -math.log(1.0 - q_d) if q_d > 0.0 else 0.0            # noqa: F821
        mu_r = -math.log(1.0 - q_r) if q_r > 0.0 else 0.0            # noqa: F821
    total = mu_g + mu_d + mu_r
    stay = math.exp(-total / 12.0)                                   # noqa: F821
    rest = 1.0 - stay
    return (stay, mu_g / total * rest, mu_d / total * rest, mu_r / total * rest)


def tar_ledger(t):
    """The first-order ledgers at the start of month ``t``, as one state.

    ``(act, pg, esc, karenz)``: :func:`tar_pols_act`, :func:`tar_pols_pg` and
    :func:`tar_esc_pg` for ``g = 1 .. 5`` and :func:`tar_pols_karenz` for ``g = 1 .. 5``
    and ``z = 1 .. karenz_months()``, rolled forward from the state at ``t - 1`` by the
    recursions those cells state, with the same operations in the same order: the month's
    entrants and graduations (:func:`tar_pols_grad`) are formed inline from the previous
    state.  One evaluation per month instead of one per month, grade and clock; the
    published cells read their component.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    k = karenz_months()
    if t <= 0:
        zero = (0.0,) * n
        return (1.0, zero, zero, tuple((0.0,) * k for g in range(1, n + 1)))
    act0, pg0, esc0, kar0 = tar_ledger(t - 1)
    x = age(t - 1)
    p = tuple(tar_p_pg(x, g) for g in range(1, n + 1))
    pa = tar_p_act(t - 1)
    if k <= 0:
        grad = tuple(act0 * pa[2] * inc_share(g) for g in range(1, n + 1))
        kar = kar0
    else:
        grad = []
        kar = []
        for g in range(1, n + 1):
            total = 0.0
            for h in range(max(1, g - 1), min(n, g + 1) + 1):
                w = kar0[h - 1][k - 1]
                if w == 0.0:
                    continue
                if h == g:
                    total += w * p[h - 1][0]
                elif g == h + 1:
                    total += w * p[h - 1][2]
                else:
                    total += w * p[h - 1][3]
            grad.append(total)
            row = [act0 * pa[2] * inc_share(g)]
            for z in range(2, k + 1):
                total = 0.0
                for h in range(max(1, g - 1), min(n, g + 1) + 1):
                    w = kar0[h - 1][z - 2]
                    if w == 0.0:
                        continue
                    if h == g:
                        total += w * p[h - 1][0]
                    elif g == h + 1:
                        total += w * p[h - 1][2]
                    else:
                        total += w * p[h - 1][3]
                row.append(total)
            kar.append(tuple(row))
        kar = tuple(kar)
    reactiv = pg0[0]
    for z in range(1, k + 1):
        reactiv += kar0[0][z - 1]
    act = act0 * pa[0] + reactiv * p[0][3]
    factor = (1.0 + leistungsdynamik()) ** (1.0 / 12.0)
    pg = []
    esc = []
    for g in range(1, n + 1):
        total = pg0[g - 1] * p[g - 1][0] + grad[g - 1]
        carried = esc0[g - 1] * p[g - 1][0]
        if g > 1:
            total += pg0[g - 2] * p[g - 2][2]
            carried += esc0[g - 2] * p[g - 2][2]
        if g < n:
            total += pg0[g] * p[g][3]
            carried += esc0[g] * p[g][3]
        pg.append(total)
        esc.append(factor * carried + grad[g - 1])
    return (act, tuple(pg), tuple(esc), kar)


def tar_pols_act(t):
    """The first-order active ledger, from one policy at issue.

    Seeded at ``t = 0`` with 1.0 whatever the model point's ``status`` is, because the
    premium is struck **at issue on an active life** — an in-force point that supplies its
    own premium never reaches this engine at all — and rolled forward with **no lapse**.
    The absence of lapse is both German first-order practice and what keeps the model
    acyclic: a pricing quantity must not depend on a behavioural assumption that depends on
    the path that depends on the premium.
    """
    return tar_ledger(t)[0]


def tar_pols_karenz(t, g, z):
    """The first-order *Karenz* ledger, empty unless ``karenz_months() > 0``.

    Present so that the tariff basis prices the benefit the contract actually pays: a
    *Karenzzeit* removes a material share of claims, more than its length suggests, and
    omitting it from the pricing basis would load the premium with a benefit the contract
    does not provide.
    """
    k = karenz_months()
    if k <= 0 or z < 1 or z > k or t <= 0:
        return 0.0
    return tar_ledger(t)[3][g - 1][z - 1]


def tar_pols_grad(t, g):
    """First-order graduations into *Pflegegrad* ``g``; the entrants themselves when K = 0."""
    n = data.pflegegrad_count()                                      # noqa: F821
    state = tar_ledger(t)
    k = karenz_months()
    if k <= 0:
        return state[0] * tar_p_act(t)[2] * inc_share(g)
    total = 0.0
    for h in range(max(1, g - 1), min(n, g + 1) + 1):
        w = state[3][h - 1][k - 1]
        if w == 0.0:
            continue
        p = tar_p_pg(age(t), h)
        if h == g:
            total += w * p[0]
        elif g == h + 1:
            total += w * p[2]
        else:
            total += w * p[3]
    return total


def tar_pols_pg(t, g):
    """The first-order paying ledger at *Pflegegrad* ``g``."""
    return tar_ledger(t)[1][g - 1]


def tar_esc_pg(t, g):
    """The first-order **escalation** ledger, the one the tariff annuity is valued on.

    Identical in construction to :func:`esc_pg`, so a contract sold with a
    *Leistungsdynamik* is priced with one.  With the dynamic off it equals
    :func:`tar_pols_pg` at every ``t`` and ``g``.
    """
    return tar_ledger(t)[2][g - 1]


def tar_pols_if(t):
    """The first-order in-force count: active, deferred and paying together."""
    n = data.pflegegrad_count()                                      # noqa: F821
    state = tar_ledger(t)
    total = state[0]
    for g in range(1, n + 1):
        total += state[1][g - 1]
        for z in range(1, karenz_months() + 1):
            total += state[3][g - 1][z - 1]
    return total


def tar_pols_prem(t):
    """The first-order premium-paying units: in-term, less the waived paying grades.

    The waiver enters the **price**, not only the projection.  On a level-premium contract
    issued at 45 and claiming at 82 it removes the remaining premium stream for the whole
    of the paying period — of the order of four years of premium, the same order as one
    year of benefit — and that cost sits inside the level premium.  It is one of the
    reasons a *Pflegerente* is dearer than a *Pflegetagegeld* of nominally equal benefit.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    if age(t) >= prem_end_age():
        return 0.0
    total = tar_pols_if(t)
    for g in range(1, n + 1):
        if waiver_flag(g):
            total -= tar_ledger(t)[1][g - 1]
    return total


def tar_pols_death(t):
    """First-order deaths in month ``t``, from every state.

    Read only by the *Beitragsrückgewähr* leg of the equivalence: a death benefit written
    into a *Pflegerente* is a death cover and has to be priced as one.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    state = tar_ledger(t)
    total = state[0] * tar_p_act(t)[1]
    for g in range(1, n + 1):
        in_grade = state[1][g - 1]
        for z in range(1, karenz_months() + 1):
            in_grade += state[3][g - 1][z - 1]
        total += in_grade * tar_p_pg(age(t), g)[1]
    return total


def tariff_benefit_pv():
    """A: the expected present value of the *Pflegerente* on the first-order basis.

    ``sum_t v**t R sum_g pi_g tar_esc_pg(t, g)``, discounted at the *Rechnungszins*.  On
    the anchor cell it is the whole of the benefit side: with no *Beitragsrückgewähr* and no
    survival benefit, this annuity is the only thing the contract ever pays.

    Override reason: the benefit is a *Pflegerente* by care grade on the multi-state tariff
    ledger, monthly, not a death or survival benefit,
    products/pflegerentenversicherung/technical-notes.md:617
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    total = 0.0
    for t in range(proj_len()):
        row = 0.0
        for g in range(1, n + 1):
            pct = benefit_pct(g)
            if pct > 0.0:
                row += pct * tar_ledger(t)[2][g - 1]
        if row:
            total += disc_factor_mth(t) * rente_mth() * row
    return total


def tariff_annuity():
    """U: the expected present value of the premium stream **in units of P**.

    ``sum_{t : premium_due(t)} v**t m tar_pols_prem(t)``.  Dividing the benefit and expense
    values by this is what strikes the level premium, so it is the annuity factor of the
    equivalence and the quantity a reader recomputes to check the premium by hand.

    Override reason: the premium is monthly, so the annuity sums the premium months on the
    multi-state tariff ledger ``tar_pols_prem`` in units of the monthly premium, not an
    annual annuity-due, products/pflegerentenversicherung/technical-notes.md:618
    """
    mult = 1 if prem_form() == "single" else prem_cycle()
    total = 0.0
    for t in range(proj_len()):
        if premium_due(t):
            total += disc_factor_mth(t) * mult * tar_pols_prem(t)
    return total


def epv_admin():
    """G: the expected present value of the per-policy administration cost, first order."""
    admin_pp = float(data.param("load_admin_pp_mth"))                # noqa: F821
    total = 0.0
    for t in range(proj_len()):
        total += disc_factor_mth(t) * admin_pp * inflation_factor(t) * tar_pols_if(t)
    return total


def epv_claim_expense():
    """C: the expected present value of the per-annuity-payment claims cost, first order."""
    n = data.pflegegrad_count()                                      # noqa: F821
    per_payment = float(data.param("load_claim_pp_inst"))            # noqa: F821
    total = 0.0
    for t in range(proj_len()):
        row = 0.0
        for g in range(1, n + 1):
            if waiver_flag(g):
                row += tar_ledger(t)[1][g - 1]
        if row:
            total += disc_factor_mth(t) * per_payment * inflation_factor(t) * row
    return total


def premium_mth_pp():
    """P: the level monthly gross *Beitrag* per policy.

    Where ``premium_mth`` is positive on the model point, that is the premium and this
    cells returns it unchanged.  Where it is ``0.0``, the premium is struck by equivalence
    on the **first-order** bases at the *Rechnungszins*:

        P U = A + P D1 + P a1 + beta P U + G + C

    where ``A`` is :func:`tariff_benefit_pv`, ``U`` :func:`tariff_annuity`, ``G``
    :func:`epv_admin`, ``C`` :func:`epv_claim_expense`, ``beta`` the premium-related
    administration percentage, ``a1`` the *Zillmerung* allowance in units of ``P`` and
    ``D1`` the *Beitragsrückgewähr* value in units of ``P``.  Everything that scales with
    ``P`` is linear in it, so the equation solves in closed form,

        P = (A + G + C) / [ U (1 - beta) - D1 - a1 ]

    and for the *Einmalbeitrag* ``U = 1``, so the same expression gives the
    *Einmalbeitrag* directly.

    The *Risikozuschlag* multiplies the **gross** premium and never the benefit, so
    :func:`claims` is invariant to it.  It is applied here, after the equivalence, which
    means the *Beitragssumme* an extra-risk contract's *Zillmerung* is charged on is the
    rated premium's — the amount the policyholder actually contracts to pay.

    There is **no published German rate card for this product to reproduce**, so this is a
    computed quantity rather than a reproduced one, and the technical notes sanity-check its
    level against an argued band rather than against a citation.
    """
    if premium_mth() > 0.0:
        return premium_mth()
    acq_load = float(data.param("load_acq_bsum_once"))               # noqa: F821
    admin_pct = float(data.param("load_admin_prem_inst"))            # noqa: F821
    if prem_form() == "single":
        a1 = acq_load
    else:
        cap = int(data.param("beitragssumme_cap_age"))               # noqa: F821
        years = max(0, min(prem_end_age(), cap) - issue_age())
        a1 = acq_load * 12.0 * years
    d1 = 0.0
    if beitragsrueckgewaehr():
        for t in range(proj_len()):
            d1 += disc_factor_mth(t) * prem_units_at(t) * tar_pols_death(t)
    numerator = tariff_benefit_pv() + epv_admin() + epv_claim_expense()
    denominator = tariff_annuity() * (1.0 - admin_pct) - d1 - a1
    return rating_factor() * numerator / denominator


def prem_units_at(t):
    """The number of premium **units of P** payable to date on an uninterrupted path.

    ``cum_prem_max_pp(t) / P`` written without ``P``, so the *Beitragsrückgewähr* leg of the
    equivalence can be assembled before the premium it would otherwise depend on is known.
    Breaking that circularity is the only reason this cells exists.
    """
    if prem_form() == "single":
        return 1.0 if t >= 0 else 0.0
    m = prem_cycle()
    last = min(t, 12 * (prem_end_age() - issue_age()) - 1)
    if last < 0:
        return 0.0
    return float(m * (last // m + 1))


def check_net_cf_resid(t):
    """The cash flow statement's residual in month ``t`` — the library's first ruling.

    ``net_cf(t)`` less its reconstruction from the statement's own **published parts**:
    ``premiums - claims_annuity - claims_lapse - claims_death - expenses - claim_expenses``,
    every one of them a column of :func:`result_cf`.  Zero everywhere.

    It is zero by construction while :func:`net_cf` subtracts ``claims(t)``, and that is the
    point: the residual re-derives the headline number from the three ``claims`` **kinds**
    separately rather than from their subtotal, so a benefit that stops being included in
    ``claims(t)``, or a column added to the frame without being subtracted, fails here
    instead of silently changing the answer.  Every model in this library publishes this
    cells and its no-argument companion, so that no model's headline number is the one
    quantity nothing checks.

    Override reason: rebuilt from the cells of the three claim kinds and the claims-handling
    cost, products/pflegerentenversicherung/model.md:292
    """
    return net_cf(t) - (premiums(t)
                        - claims(t, "ANNUITY")
                        - claims(t, "LAPSE")
                        - claims(t, "DEATH")
                        - expenses(t)
                        - claim_expenses(t))


def check_net_cf_scale(t):
    """The scale of :func:`check_net_cf`'s tolerance: the book's monthly annuity, at least 1.

    :func:`check_net_cf` is true when the cash flow statement reconciles in every projected
    month.

    No argument, one bool over all ``t``, the library-wide shape;
    :func:`check_net_cf_resid` gives the signed residual of the month that failed.

    Override reason: the statement is checked relative to the policy count times the monthly
    Pflegerente, products/pflegerentenversicherung/technical-notes.md:675
    """
    return max(pols_if_init() * max(rente_mth(), 1.0), 1.0)            # noqa: F821


def check_pols_roll_fwd_resid(t):
    """The in-force roll-forward residual in month ``t``; zero everywhere.

    ``pols_if(t+1) - [ pols_if(t) - pols_death(t) - pols_lapse(t) ]``.  It says that lives
    leave the in-force population **only** by death or surrender, and that every
    *Pflegegrad* transition — entry into care, deterioration, *Herabstufung*,
    *Reaktivierung*, graduation out of the *Karenz* ledger — is internal to it.

    That is a strong statement about a nine-state ledger and it is not trivially true: the
    three ledgers are rolled forward independently, and a life double-counted between them,
    or lost between the *Karenz* ledger and the paying one, or lapsed out of a paying grade,
    leaves a residual here.  What it does **not** catch is a life leaving the system
    altogether, which is why :func:`check_states` is published beside it.
    """
    return pols_if(t + 1) - (pols_if(t) - pols_death(t) - pols_lapse(t))


def check_pols_roll_fwd():
    """True when the in-force roll-forward closes in every projected month."""
    tol = roll_fwd_tol()
    scale = max(pols_if_init(), 1.0)
    return all(abs(check_pols_roll_fwd_resid(t)) <= tol * scale
               for t in range(t_start(), proj_len()))


def check_states_resid(t):
    """The state-partition residual at the start of month ``t``; zero everywhere.

    ``pols_act + sum_{g,z} pols_karenz + sum_g pols_pg + pols_dead_cum + pols_lapse_cum``
    less ``pols_if_init()``.  The three live ledgers and the two absorbing counts partition
    the initial cohort at **every** ``t``, and the identity is assembled by direct summation
    over the ledgers, with no reference to the recursion that produced any of them.

    That independence is what makes it more than the telescope of
    :func:`check_pols_roll_fwd`.  It catches a wrong seeding of an in-force model point, a
    life counted in two grades at once, an entrant into care who never leaves the active
    ledger, and a *Karenz* cohort that graduates twice.  Because ``mort_rate`` is forced to
    1 at the limiting age, it also closes at the far end: the decrements account for the
    whole policy rather than leaving a truncation residue.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    state = pols_ledger(t)
    total = state[0] + pols_dead_cum(t) + pols_lapse_cum(t)
    for g in range(1, n + 1):
        total += state[1][g - 1]
        for z in range(1, karenz_months() + 1):
            total += state[3][g - 1][z - 1]
    return total - pols_if_init()


def check_states():
    """True when the ledgers and the absorbed counts partition the cohort at every month."""
    tol = roll_fwd_tol()
    scale = max(pols_if_init(), 1.0)
    return all(abs(check_states_resid(t)) <= tol * scale
               for t in range(t_start(), proj_len()))


def check_waiver_resid(t):
    """The *Beitragsbefreiung* split residual in month ``t``; zero everywhere.

    ``pols_prem(t) + pols_waived(t) - pols_in_term(t)``.  The waiver **splits** the in-term
    population: it neither loses a policy nor creates one, and a life that stops paying is a
    life that started being paid.

    It is arithmetically trivial while :func:`pols_prem` is a difference, and it is
    published anyway because the failure it guards is not a slip in the subtraction but a
    disagreement about who belongs on each side — a *Karenz* life counted as waived, a
    grade-1 life waived on the ``delib_std`` grid, a waiver that never revives on a
    *Herabstufung*.  Each of those changes ``pols_waived`` and ``pols_prem`` in ways that
    still sum correctly, so the check is read together with the tests that assert the
    membership itself.
    """
    return pols_prem(t) + pols_waived(t) - pols_in_term(t)


def check_waiver():
    """True when the waiver splits the in-term population in every projected month."""
    tol = roll_fwd_tol()
    scale = max(pols_if_init(), 1.0)
    return all(abs(check_waiver_resid(t)) <= tol * scale
               for t in range(t_start(), proj_len()))


def check_esc_ledger_resid(t):
    """The escalation-ledger residual in month ``t``; zero everywhere.

    With ``leistungsdynamik = 0`` it is ``sum_g [ esc_pg(t, g) - pols_pg(t, g) ]``, which
    must be **exactly** zero: the two recursions are then identical and any difference is a
    coding divergence between them.  With a positive dynamic it is the sum of the *negative*
    parts of the same differences, which must be zero because an escalated ledger can never
    fall below the head count it escalates.

    The invariant matters because the annuity is weighted on ``esc_pg``.  If the escalation
    ledger drifted below the population — an entrant added at the wrong weight, a survivor
    escalated before rather than after the transition — the benefit would be understated and
    no total in the frame would look wrong.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    state = pols_ledger(t)
    if leistungsdynamik() == 0.0:
        return sum(state[2][g - 1] - state[1][g - 1] for g in range(1, n + 1))
    return sum(min(0.0, state[2][g - 1] - state[1][g - 1]) for g in range(1, n + 1))


def check_esc_ledger():
    """True when the escalation ledger dominates the head count in every projected month."""
    tol = roll_fwd_tol()
    scale = max(pols_if_init(), 1.0)
    return all(abs(check_esc_ledger_resid(t)) <= tol * scale
               for t in range(t_start(), proj_len()))


def check_prem_equiv_resid(t):
    """The discounted first-order imbalance of month ``t``; its **sum** over ``t`` is zero.

    ``v**t [ premium - benefit - expense ]`` on the tariff ledgers: the premium leg is
    ``P m tar_pols_prem(t)`` on due months, the benefit leg the *Pflegerente* valued on
    ``tar_esc_pg`` plus the *Beitragsrückgewähr* where the option is on, and the expense leg
    the *Zillmerung* allowance at ``t = 0``, the per-policy administration, the
    premium-related administration and the claims cost.

    It is **not** a tautology.  The premium level comes from the closed form in
    :func:`premium_mth_pp`, but both legs here are re-assembled month by month from the
    ledgers, so substituting a best-estimate rate into one leg, dropping the *Zillmerung*
    term, forgetting the waiver in ``tar_pols_prem`` or valuing the annuity on
    ``tar_pols_pg`` instead of ``tar_esc_pg`` all make the sum miss zero.

    Individual months are large and of both signs — the early ones strongly positive, the
    late ones strongly negative — so only the **sum** is an identity.  Where the model point
    supplies its own *Beitrag* no equivalence was struck, and the residual is zero by
    construction: an equivalence that was never struck cannot be checked.
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    if premium_mth() > 0.0:
        return 0.0
    p0 = premium_mth_pp() / rating_factor()
    single = prem_form() == "single"
    mult = 1 if single else prem_cycle()
    admin_pct = float(data.param("load_admin_prem_inst"))            # noqa: F821
    admin_pp = float(data.param("load_admin_pp_mth"))                # noqa: F821
    per_payment = float(data.param("load_claim_pp_inst"))            # noqa: F821
    acq_load = float(data.param("load_acq_bsum_once"))               # noqa: F821

    prem_leg = p0 * mult * tar_pols_prem(t) if premium_due(t) else 0.0

    state = tar_ledger(t)
    ben_leg = 0.0
    paying = 0.0
    for g in range(1, n + 1):
        pct = benefit_pct(g)
        if pct > 0.0:
            ben_leg += pct * state[2][g - 1]
            paying += state[1][g - 1]
    ben_leg = rente_mth() * ben_leg
    if beitragsrueckgewaehr():
        ben_leg += p0 * prem_units_at(t) * tar_pols_death(t)

    exp_leg = (admin_pp * inflation_factor(t) * tar_pols_if(t)
               + per_payment * inflation_factor(t) * paying
               + admin_pct * prem_leg)
    if t == 0:
        if single:
            exp_leg += p0 * acq_load
        else:
            cap = int(data.param("beitragssumme_cap_age"))           # noqa: F821
            years = max(0, min(prem_end_age(), cap) - issue_age())
            exp_leg += p0 * acq_load * 12.0 * years

    return disc_factor_mth(t) * (prem_leg - ben_leg - exp_leg)


def check_prem_equiv():
    """True when the gross premium closes the first-order equivalence.

    The sum of :func:`check_prem_equiv_resid` over the whole tariff horizon, against a
    tolerance scaled by ``P U`` — the size of the premium leg — because the residual is a
    difference of two large discounted values and an absolute tolerance on it would be a
    statement about the contract's size rather than about the equivalence.
    """
    tol = roll_fwd_tol()
    if premium_mth() > 0.0:
        return True
    scale = max(premium_mth_pp() / rating_factor() * tariff_annuity(), 1.0)
    total = sum(check_prem_equiv_resid(t) for t in range(proj_len()))
    return abs(total) <= tol * scale


def result_cf_columns():
    """The columns of :func:`result_cf`, ``(label, cell)`` pairs in their order.

    The frame is the table of cash flows, indexed by policy month ``t``.

    Contiguous from :func:`t_start` to ``proj_len() - 1``.  ``pols_if`` is the
    **start**-of-month count, which is the weight applied to every cash flow on the same
    row, and its first value equals ``pols_if_init()`` exactly.  ``pols_act``,
    ``pols_care`` and ``pols_prem`` split it three ways for a reader following the
    projection: active, in care — deferred and paying together — and actually paying a
    *Beitrag*.

    ``claims_death`` is structurally zero unless ``beitragsrueckgewaehr`` is on, and
    ``claims_lapse`` is zero once the premium term has ended, both published rather than
    dropped so the product facts are stated instead of inferred.  ``net_cf`` is
    ``premiums`` less the three ``claims`` columns, ``expenses`` and ``claim_expenses``;
    ``liability_cf`` is its negative.

    Override reason: the statement carries the state counts and the paying count, its three
    claim kinds and the claims-handling cost, and no commission,
    products/pflegerentenversicherung/technical-notes.md:649-660
    """
    return (
        ("pols_if", pols_if),                                        # noqa: F821
        ("pols_act", pols_act),                                      # noqa: F821
        ("pols_care", pols_care),                                    # noqa: F821
        ("pols_prem", pols_prem),                                    # noqa: F821
        ("premiums", premiums),                                      # noqa: F821
        ("claims_annuity", lambda t: claims(t, "ANNUITY")),          # noqa: F821
        ("claims_lapse", lambda t: claims(t, "LAPSE")),              # noqa: F821
        ("claims_death", lambda t: claims(t, "DEATH")),              # noqa: F821
        ("expenses", expenses),                                      # noqa: F821
        ("claim_expenses", claim_expenses),                          # noqa: F821
        ("net_cf", net_cf),                                          # noqa: F821
        ("liability_cf", liability_cf),                              # noqa: F821
    )


def result_states_columns():
    """The columns of :func:`result_states`, ``(label, cell)`` pairs in their order.

    The frame is the table of the state ledgers, flows and rates by policy month ``t``.

    The frame a reader needs to follow the multi-state machinery behind
    :func:`result_cf`: the five paying grades, the *Karenz* ledger and the three flows
    between them, the two decrements out of the system, and the four annual rates the whole
    projection is built from.  It is not part of the house contract and carries no
    ``check_*``; ``mort_rate_care_pg5`` is published in preference to all five grades'
    because the grade-5 rate is the one that carries the product's central biometric fact.

    Override reason: the frame publishes the Pflegegrad and Karenz ledgers, the flows
    between them, the two decrements and the four annual rates,
    products/pflegerentenversicherung/technical-notes.md:662
    """
    n = data.pflegegrad_count()                                      # noqa: F821
    return tuple(
        ("pols_pg%d" % g, lambda t, g=g: pols_pg(t, g))              # noqa: F821
        for g in range(1, n + 1)) + (
        ("pols_karenz",
         lambda t: sum(pols_karenz(t, g, z)                          # noqa: F821
                       for g in range(1, n + 1)
                       for z in range(1, karenz_months() + 1))),     # noqa: F821
        ("pols_entry",
         lambda t: sum(pols_entry(t, g) for g in range(1, n + 1))),  # noqa: F821
        ("pols_grad",
         lambda t: sum(pols_grad(t, g) for g in range(1, n + 1))),   # noqa: F821
        ("pols_reactiv", pols_reactiv),                              # noqa: F821
        ("pols_death", pols_death),                                  # noqa: F821
        ("pols_lapse", pols_lapse),                                  # noqa: F821
        ("mort_rate", mort_rate),                                    # noqa: F821
        ("mort_rate_care_pg%d" % n, lambda t: mort_rate_care(t, n)), # noqa: F821
        ("inc_rate", inc_rate),                                      # noqa: F821
        ("lapse_rate", lapse_rate),                                  # noqa: F821
        ("premium_pp", premium_pp),                                  # noqa: F821
    )


# ---------------------------------------------------------------------------
# References

data = ("Interface", ("..", "Data"), "auto")

point_id = 1

math = ("Module", "math")

pd = ("Module", "pandas")
