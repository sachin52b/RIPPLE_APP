# Financial Contagion & Resilience Lab
## Production Prototype Implementation Plan

> **Core principle:** **Don’t predict the next default. Simulate the next cascade.**

This document is the implementation specification for the Financial Contagion & Resilience Lab prototype. It is intended to be handed to an implementation agent (for example, Google Antigravity) and used as the authoritative functional and mathematical blueprint.

The implementation must preserve the distinctions in this document. Do not silently replace formulas with simpler approximations, invent missing financial quantities, or introduce additional hidden scoring systems.

---

# 0. Product Definition

## 0.1 What the system does

The application models a microfinance portfolio as a borrower relationship/exposure graph.

The core pipeline is:

```text
UPLOAD / LOAD DATA
        ↓
VALIDATE DATA
        ↓
BUILD BORROWER NETWORK
        ↓
USER CLICKS BORROWER
        ↓
DEFINE SHOCK
        ↓
STEP 3 — STRESS / DISTRESS
        ↓
STEP 4 — PATHWAY FILTER
        ↓
STEP 5A / 5B / 5C / 5D — PROPAGATION
        ↓
STEP 6 — CASCADE CONTINUATION
        ↓
BASELINE CASCADE COMPLETE
        ↓
INTERVENTION ENGINE
        ↓
STAGE 1 — CRITICALITY OF EVERY BORROWER
        ↓
RANK WHO TO INTERVENE ON
        ↓
STAGE 2 — TEST POLICY 1 / 2 / 3
        ↓
COMPARE
        ↓
USER CHOOSES INTERVENTION
        ↓
FINAL COUNTERFACTUAL RUN
        ↓
BEFORE / AFTER RESULT
        ↓
DECISION SUMMARY
        ↓
PERSIST RUN
```

## 0.2 Explicit scope exclusions

This is not:

- a generic default predictor;
- a repayment tracker;
- a cash-flow planning application;
- a loan recommendation engine;
- an AI chatbot where AI produces the core answer.

The core engine is deterministic graph simulation and mathematical state transitions. AI may be added later only as a helper layer (for example, natural-language scenario parsing or explanation), never as the source of the underlying numerical result.

---

# 1. High-Level Architectural Principles

1. **Raw facts vs derived values must remain separate.**
2. **Every intervention is a counterfactual simulation, not an irreversible mutation of the baseline graph.**
3. **All policy comparisons use the same cascade engine and the same baseline state.**
4. **Common-cause exposure is not treated as borrower-to-borrower contagion.**
5. **Missing institutional information must not be replaced by invented percentages.**
6. **The UI must expose human-auditable outcome components even when the machine uses a scalar score internally.**
7. **Model parameters must be centralized and versioned.**
8. **Every final result must be reproducible from dataset + shock + model parameters + intervention configuration.**

---

# 2. Data Model

## 2.1 Borrower node

Every borrower is represented as a node in:

\[
G=(V,E)
\]

Required core borrower fields:

```text
borrower_id
group_id
location_id
livelihood_type

monthly_income
monthly_essential_expense
monthly_loan_obligation
outstanding_loan
liquidity_buffer

income_stability
```

### Field meanings

| Field | Meaning | Type |
|---|---|---|
| `borrower_id` | Unique borrower identifier | string |
| `group_id` | Formal lending group identifier | string/null |
| `location_id` | Geographic location identifier | string |
| `livelihood_type` | Primary economic activity | string |
| `monthly_income` | Total monthly income | non-negative number |
| `monthly_essential_expense` | Monthly essential living expense | non-negative number |
| `monthly_loan_obligation` | Monthly debt service obligation | non-negative number |
| `outstanding_loan` | Current outstanding principal | non-negative number |
| `liquidity_buffer` | Available liquid cash/savings buffer | non-negative number |
| `income_stability` | Stability descriptor/score from institutional data | numeric/string depending schema |

### Validation

At load time:

- `borrower_id` must be unique.
- Monetary values must be non-negative.
- `Required = monthly_essential_expense + monthly_loan_obligation` must be \(>0\) for the stress engine.
- Missing values must be surfaced as data-quality errors or explicitly handled as unavailable; do not silently substitute arbitrary values.
- Severity is validated separately in the shock form.

---

# 3. Relationship / Edge Model

Exactly four top-level relationship categories exist.

Every edge must retain:

```text
edge_id
super_mechanism
specific_mechanism
source
target
metadata
```

Recommended canonical mechanism names:

```text
joint_liability
formal_group
economic_exposure
geographic_exposure
```

## 3.1 Joint / Shared Financial Liability

### Meaning

A direct contractual financial relationship.

Examples:

- joint liability;
- shared repayment responsibility;
- contractual peer debt exposure.

### Required/important edge data

```text
source_borrower
target_borrower
relationship_type

contractual_monthly_exposure
liability_share
shared_liability_amount
contractual_exposure
```

The canonical monetary quantity used by the propagation engine is a **monthly contractual exposure**.

If the institution only supplies a liability percentage/share, that percentage can be used to derive the transferable amount, but it must come from contractual/institutional data.

Do not invent a 50%, 60%, etc. share merely because the borrowers are connected.

---

## 3.2 Formal Lending Group

### Meaning

A formal MFI center/group relationship.

This represents:

- peer pressure;
- group repayment discipline;
- center friction;
- shared group-level consequences;
- group credit-standing consequences.

### Raw group inputs

```text
group_id
group_size
meeting_attendance_rate
group_sanction_rules
```

### Derived group quantity

\[
GroupDistressRatio
=
\frac{\text{number of distressed group members}}
{\text{total group members}}
\]

### Locked model parameter

\[
\boxed{\gamma_{group}=0.15}
\]

This is a prototype/model parameter, not a user-entered field.

---

## 3.3 Shared Economic Exposure

### Meaning

A common economic source affects multiple borrowers.

Examples:

- same market;
- same employer;
- same crop;
- same business ecosystem.

### Source identity

```text
economic_source_type
economic_source_id
```

### Exposure rule

Do not create arbitrary weights like `economic_strength = 0.6`.

When source-level income is available, exposure is derived from measurable income:

\[
\boxed{
E_B=
\frac{\text{Income from shocked source}}
{\text{Total monthly income}}
}
\]

If it cannot be quantified, do not invent the value.

---

## 3.4 Shared Geographic Exposure

### Meaning

A common geographic environment affects multiple borrowers.

Examples:

- same locality;
- same flood zone;
- local infrastructure disruption;
- other location-specific disruption.

### Core data

```text
location_id
```

No arbitrary geographic edge-strength coefficient is introduced unless actual measurable exposure data exists.

---

# 4. Data Loading and Graph Construction

## 4.1 User data workflow

The user can supply institutional portfolio data through a supported format such as CSV, Excel, or JSON.

The loader must:

1. validate schema;
2. validate identifiers;
3. validate numeric fields;
4. load borrowers;
5. load relationships;
6. derive any relationships that can legitimately be constructed from supplied raw fields;
7. construct \(G=(V,E)\);
8. surface data-quality issues before simulation.

## 4.2 Graph construction

The system builds:

\[
G=(V,E)
\]

where:

- \(V\) = borrower nodes;
- \(E\) = relationships/exposures.

No manual graph drawing is required from the user.

The graph must preserve edge metadata so the UI can explain not only that two nodes are connected, but why.

---

# 5. Network UI

## 5.1 Main network canvas

The network visualization should make relationship categories visually distinguishable.

Recommended prototype styling:

```text
Joint / Shared Liability  → red solid
Formal Lending Group      → blue dashed
Shared Economic Exposure  → green dotted
Shared Geographic Exposure → orange dash-dot
```

Do not hard-code these colors into the mathematical model; these are UI styling conventions only.

Borrowers should be grouped/positioned meaningfully, for example by formal lending group or location where useful.

## 5.2 Node click

Clicking a node opens an inspection panel showing:

```text
Borrower ID
Group
Location
Livelihood

Monthly Income
Essential Expense
Loan Obligation
Outstanding Loan
Liquidity Buffer

Current S_effective
Distress State

Connected Borrowers
Network Structural Role
```

## 5.3 Edge click

Clicking an edge shows:

```text
Super-mechanism
Specific mechanism
Interpretation
Relevant edge metadata
```

Example:

```text
Super-mechanism:
Shared Economic Exposure

Specific mechanism:
Same Market

Interpretation:
A and B depend on the same economic source.
```

---

# 6. Simulation Engine — Shock UI

The simulation begins with a node interaction.

## 6.1 Initial context

For a borrower-specific scenario:

```text
Selected Borrower = B7
```

The clicked borrower is the starting context.

## 6.2 Shock type

The user selects a shock cause/type.

The exact form must adapt to the shock class.

### Borrower-specific

```text
Shock Cause: Income Shock
Severity: 40%
Duration: 3 months
```

### Economic common cause

```text
Shock Cause: Market Shock
Economic Source: M12
Severity: 40%
Duration: 3 months
```

### Geographic common cause

```text
Shock Cause: Geographic Shock
Affected Location: L12
Severity: 40%
Duration: 3 months
```

### User-controlled simulation parameters

```text
shock cause/type
severity
duration
```

Severity is validated as:

\[
0\le Severity\le1
\]

Duration is a non-negative number of months, then normalized by the duration guard below.

Important: **shock definition happens here**, not inside Step 5C or Step 5D.

---

# 7. Step 3 — Stress and Distress Engine

The purpose of Step 3 is to determine whether the affected source is materially distressed.

A shock does not automatically propagate.

## 7.1 Duration guard

\[
\boxed{
EffectiveDuration=\max(1,duration)
}
\]

This guard is used wherever the simulation needs the modeled duration as a denominator/time horizon.

## 7.2 Post-shock income

\[
\boxed{
Income_{new}
=
Income(1-Severity)
}
\]

## 7.3 Required amount

\[
\boxed{
Required
=
MonthlyEssentialExpense+MonthlyLoanObligation
}
\]

Require:

\[
Required>0
\]

## 7.4 Monthly deficit

\[
\boxed{
Deficit
=
\max(0,Required-Income_{new})
}
\]

## 7.5 Cash stress

\[
\boxed{
CashStress
=
\frac{Deficit}{Required}
}
\]

## 7.6 Horizon total deficit

\[
\boxed{
TotalDeficit
=
Deficit\times EffectiveDuration
}
\]

## 7.7 Buffer stress

### Zero-deficit guard

If:

\[
Deficit\times EffectiveDuration\le0
\]

then:

\[
\boxed{
BufferStress=0
}
\]

### Otherwise

\[
Coverage
=
\frac{LiquidityBuffer}
{Deficit\times EffectiveDuration}
\]

\[
\boxed{
BufferStress
=
1-\min(1,Coverage)
}
\]

## 7.8 Effective stress

The locked repaired formulation is:

\[
\boxed{
S_{effective}
=
\max
\left(
CashStress,
0.7CashStress+0.3BufferStress
\right)
}
\]

The \(0.7/0.3\) weighting applies only inside the second component.

## 7.9 Distress trigger

Prototype material-distress threshold:

\[
\boxed{
T_{distress}=0.30
}
\]

High-cash-stress override threshold:

\[
\boxed{
T_{cash}=0.35
}
\]

Final trigger:

\[
\boxed{
IsDistressed
=
(CashStress\ge0.35)
\lor
(S_{effective}\ge0.30)
}
\]

### Outcomes

If false:

```text
Shock Contained
```

No downstream propagation.

If true:

```text
Downstream Impact Possible
```

Activate Step 4.

---

# 8. Step 4 — Relationship Pathway Filtering

Only pathways relevant to the shock are retained.

Canonical logic:

```python
if relationship_type in ["joint_liability", "formal_group"]:
    keep_edge()

elif (
    relationship_type in ["economic_exposure", "geographic_exposure"]
    and shock.cause matches edge.exposure_type
):
    keep_edge()

else:
    discard_edge()
```

### Interpretation

- Joint liability: retained when source is materially distressed.
- Formal group: retained when source is materially distressed.
- Economic exposure: retained only if shock matches represented economic exposure.
- Geographic exposure: retained only if shock matches represented geographic exposure.
- Otherwise: no calculation along that edge.

---

# 9. Step 5A — Joint / Shared Financial Liability Propagation

This is direct monetary contagion.

## 9.1 Source shortfall

Use the source's relevant **uncovered monthly shortfall**.

This is a monthly quantity.

## 9.2 Liability share / contractual exposure

Two valid data paths exist.

### Path A — Contractual monthly exposure is available

Use it directly.

\[
TransferredBurden_{A\to B}
=
\min
\left(
A\text{'s uncovered monthly shortfall},
B\text{'s contractual monthly exposure}
\right)
\]

### Path B — Liability share is available

If the contract provides:

\[
LiabilityShare_{A,B}
\]

then:

\[
ShareBasedTransfer
=
A\text{'s uncovered monthly shortfall}
\times LiabilityShare_{A,B}
\]

and then bound by B's contractual monthly exposure when available:

\[
\boxed{
TransferredBurden_{A\to B}
=
\min
\left(
ShareBasedTransfer,
B\text{'s contractual monthly exposure}
\right)
}
\]

If no actual share or exposure exists, do not invent one.

## 9.3 Extra monthly burden on B

Maintain the simulation-state accumulator:

\[
\boxed{
r_{extra,B}^{new}
=
r_{extra,B}^{old}
+
TransferredBurden_{A\to B}
}
\]

For a fresh simulation, initialize:

\[
r_{extra,B}^{old}=0
\]

unless the institutional dataset explicitly supplies an existing applicable additional contractual monthly burden.

Update:

\[
\boxed{
LoanObligation_{B,new}
=
LoanObligation_B+r_{extra,B}^{new}
}
\]

Then rerun the exact Step 3 engine for B.

### Unit rule

`TransferredBurden` is monthly.

Do not divide it by duration.

If an institution supplies a cumulative multi-month contractual amount, normalize it to an appropriate monthly exposure using the modeled horizon before feeding it into the monthly formula.

---

# 10. Step 5B — Formal Lending Group Propagation

This is non-monetary group-mediated contagion.

Ordinary group membership does not automatically create debt.

The mechanism represents:

- peer pressure;
- repayment discipline;
- center friction;
- group-level credit consequences.

## 10.1 Group parameter

\[
\boxed{
\gamma_{group}=0.15
}
\]

## 10.2 Group pressure

For \(N_{group}>1\):

\[
\boxed{
\Delta GroupPressure_{A\to B}
=
\frac{
S_{effective,A}\times0.15
}{
N_{group}-1
}
}
\]

## 10.3 Singleton/no-peer guard

If:

\[
N_{group}\le1
\]

then:

\[
\boxed{
\Delta GroupPressure=0
}
\]

There is no peer to receive pressure.

## 10.4 Existing financial stress of B

Use the exact output of Step 3:

\[
\boxed{
Stress_B^{financial}=S_{effective,B}
}
\]

There is no separate standalone financial-stress variable.

## 10.5 Group-pressure update

\[
\boxed{
Stress_B^{new}
=
S_{effective,B}
+
(1-S_{effective,B})
\Delta GroupPressure_{A\to B}
}
\]

This is a non-monetary stress update.

Do not alter B's loan ledger merely because a normal formal-group edge transmitted group pressure.

## 10.6 Multiple distressed members

Aggregate group pressure using:

\[
\boxed{
\Delta TotalGroupPressure_B
=
1-
\prod_k
(1-\Delta GroupPressure_{k\to B})
}
\]

This provides diminishing aggregation rather than uncontrolled linear addition.

## 10.7 Actual monetary group rules

If the institutional MFI data explicitly specifies a monetary emergency-pool or mandatory shared-payment mechanism, that specific mechanism can create a monetary burden. Do not fabricate such a rule merely from group membership.

---

# 11. Step 5C — Shared Economic Exposure

This is common-cause exposure, not borrower-to-borrower contagion.

The causal chain is:

\[
\boxed{
Economic\ Shock
\rightarrow
Economic\ Source
\rightarrow
Borrower
}
\]

## 11.1 Exposure identification

The system uses:

```text
economic_source_type
economic_source_id
```

and borrower source-level income data where available.

## 11.2 Exposure fraction

\[
\boxed{
E_B
=
\frac{
Income\ from\ shocked\ source
}{
Total\ monthly\ income
}
}
\]

## 11.3 Income loss

\[
\boxed{
IncomeLoss_B
=
Income_B\times E_B\times Severity
}
\]

## 11.4 New income

\[
\boxed{
Income_{B,new}
=
Income_B-IncomeLoss_B
}
\]

Then rerun the exact Step 3 engine.

## 11.5 Missing exposure

If the data only says:

```text
livelihood_type = agriculture
```

without an actual measurable connection between B's income and the shocked source, do not invent \(E_B\).

\[
\boxed{
\text{Unquantifiable exposure}
\Rightarrow
\text{No monetary economic propagation}
}
\]

---

# 12. Step 5D — Shared Geographic Exposure

This is also common-cause exposure.

The causal chain is:

\[
\boxed{
Geographic\ Shock
\rightarrow
Affected\ Area
\rightarrow
Borrower
}
\]

## 12.1 Location identification

Borrower has:

```text
location_id
```

The shock identifies an affected location/area.

## 12.2 Impact

If the existing simulation shock specifies a 40% income disruption for borrowers in the affected area:

\[
\boxed{
IncomeLoss_B
=
Income_B\times0.40
}
\]

Then:

\[
Income_{B,new}
=
Income_B-IncomeLoss_B
\]

and rerun Step 3.

Do not create arbitrary geographic relationship-strength values unless actual measurable geographic exposure data exists.

---

# 13. Step 6 — Cascade Continuation

After propagation, affected borrowers are evaluated again.

For each affected B:

1. recompute CashStress;
2. recompute BufferStress;
3. recompute \(S_{effective}\);
4. recompute `IsDistressed`.

## 13.1 Transmission but no escalation

If:

\[
IsDistressed_B=False
\]

then:

```text
Impact absorbed
Cascade stops at B
```

## 13.2 Escalation

If:

\[
IsDistressed_B=True
\]

then:

```text
B becomes a new propagation source
```

The key distinction is:

\[
\boxed{
Transmission\neq Escalation
}
\]

---

# 14. Cascade Engine Implementation

Use a deterministic source queue.

## 14.1 State objects

A simulation should maintain at least:

```text
borrower_state[borrower_id]
active_sources
processed_sources
propagation_events
reached_nodes
```

Each borrower state should preserve:

```text
current_income
current_essential_expense
current_loan_obligation
current_liquidity_buffer

cash_stress
buffer_stress
effective_stress
is_distressed

extra_monthly_obligation
```

## 14.2 Queue

Initialize:

```python
source_queue = [initial_distressed_source]
```

Also maintain a set:

```python
activated_sources = set()
```

## 14.3 Processing rule

Conceptually:

```python
while source_queue:

    A = pop_next_source()

    if A in activated_sources:
        continue

    activated_sources.add(A)

    retained_edges = filter_edges(A, shock)

    for edge in retained_edges:
        apply_mechanism_specific_effect(edge)

    for each affected borrower B:

        finalize_accumulated_effects(B)

        recompute_step3(B)

        if B.is_distressed and B not in activated_sources:
            source_queue.append(B)
```

The exact queue discipline can be BFS-like, but the implementation must be deterministic.

## 14.4 Loop prevention

A borrower is activated as a source at most once per simulation.

This prevents infinite cycles such as:

```text
A → B → C → A → B → ...
```

## 14.5 Multiple incoming effects

If B receives multiple effects from different sources, apply/accumulate those effects according to their mechanism-specific rules before deciding whether B becomes the next source.

Do not repeatedly recompute/activate B after every individual incoming edge in a way that produces order-dependent results.

---

# 15. Baseline Simulation Output

When the cascade finishes, store the complete baseline state.

At minimum:

```text
baseline_run_id
final borrower states
final stress values
distress states
propagation events
active/activated sources
reached nodes
cascade reach
final graph state
shock configuration
model parameters
```

The baseline becomes the immutable comparison reference for the Intervention Engine.

---

# 16. Intervention Engine

The intervention engine is a **counterfactual simulation laboratory**.

It is not a manual “click distressed borrower and help them” tool.

The conceptual flow is:

\[
\boxed{
Baseline
\rightarrow
WHO
\rightarrow
HOW
\rightarrow
Re\text{-}simulate
\rightarrow
Compare
\rightarrow
Finalize
}
\]

---

# 17. Stage 1 — Criticality: Find WHO

The engine evaluates borrowers structurally, not just by their own stress.

Important distinction:

\[
\boxed{
Most\ Distressed
\neq
Most\ Critical
}
\]

A moderately stressed borrower can be much more important if containing that borrower prevents a large downstream cascade.

---

# 18. Criticality Counterfactual

For every candidate borrower \(i\):

1. take the immutable baseline;
2. run a benchmark containment counterfactual in which \(i\) is prevented from propagating;
3. complete the affected cascade;
4. compare the final state with baseline;
5. calculate criticality.

This benchmark is **not** one of Policies 1–3. It is a ranking experiment.

---

# 19. Criticality Formula

Locked bounded formula:

\[
\boxed{
Criticality_i
=
\Delta Distressed_i
+
\min
\left(
\mu_{policy}
\sum_j\Delta Stress_{j,i},
C_{policy}
\right)
}
\]

where:

\[
\boxed{
\Delta Distressed_i
=
D_{baseline}
-
D_{counterfactual,i}
}
\]

and:

\[
\boxed{
\Delta Stress_{j,i}
=
Stress_{j,baseline}
-
Stress_{j,counterfactual,i}
}
\]

The prototype distress threshold remains:

\[
\boxed{
T_{distress}=0.30
}
\]

## 19.1 Important rule about negative stress deltas

Do not use a logarithm.

The previously considered logarithmic formula is rejected.

Keep the bounded linear formulation exactly as defined above.

A negative systemic stress change is allowed and should reduce the score.

---

# 20. Criticality Policy Profiles

The UI exposes a human-readable policy profile rather than raw \(\mu\) and \(C\).

## 20.1 Strict Distress Minimization

\[
\boxed{
\mu_{policy}=0.05
}
\]

\[
\boxed{
C_{policy}=0.50
}
\]

Intent:

> Prioritize reducing the number of materially distressed borrowers.

## 20.2 Balanced Portfolio Health

\[
\boxed{
\mu_{policy}=0.20
}
\]

\[
\boxed{
C_{policy}=1.25
}
\]

Intent:

> Give meaningful weight to widespread stress reduction while retaining strong priority on preventing material distress.

## 20.3 Aggressive Early Intervention

\[
\boxed{
\mu_{policy}=0.40
}
\]

\[
\boxed{
C_{policy}=2.50
}
\]

Intent:

> Give substantially greater weight to widespread stress stabilization.

These parameters are policy settings, not borrower data.

---

# 21. Criticality Ranking

For every borrower:

```python
criticality[i] = calculate_criticality(i)
```

Then sort descending:

```text
rank #1
rank #2
rank #3
...
rank #N
```

If intervention capacity allows only one target:

\[
\boxed{
SelectedBorrower=Rank\ #1
}
\]

Multiple borrowers may have high criticality, but the exact selection logic depends on the intervention capacity available.

---

# 22. Stage 2 — Intervention Policies

Exactly three core policies are locked:

\[
\boxed{
Policy\ 1=\text{Repayment Relief}
}
\]

\[
\boxed{
Policy\ 2=\text{Transmission Severance}
}
\]

\[
\boxed{
Policy\ 3=\text{Emergency Liquidity Support}
}
\]

They modify different parts of the system.

| Policy | Primary modification |
|---|---|
| Policy 1 | Monthly repayment burden |
| Policy 2 | Contagion topology |
| Policy 3 | Liquidity buffer |

---

# 23. Policy 1 — Repayment Relief

## 23.1 Purpose

Temporarily reduce the selected borrower's repayment burden.

## 23.2 User inputs

```text
monthly_relief_amount = r
duration = d months
```

## 23.3 State modification

Let:

\[
R_i
=
\text{original monthly loan obligation}
\]

Then during the intervention period:

\[
\boxed{
R_{i,new}
=
\max(0,R_i-r)
}
\]

This is a temporary counterfactual state.

## 23.4 Recalculate stress

Update:

\[
Required_i
=
Essential_i+LoanObligation_{i,new}
\]

then run the exact Step 3 engine.

Do not create a second stress formula.

## 23.5 Intervention duration

The lower obligation applies only for the selected intervention period.

After the relief duration ends, restore the original obligation in a time-aware simulation.

## 23.6 Cost

\[
\boxed{
Cost_1=r\times d
}
\]

## 23.7 Full re-simulation

```text
Policy 1
→ Step 3
→ Step 4
→ Step 5A/5B/5C/5D
→ Step 6
```

The whole network is re-simulated.

---

# 24. Policy 2 — Transmission Severance

## 24.1 Purpose

Alter the network topology to prevent controllable institutional contagion.

It does not inject cash and does not directly modify the borrower's underlying financial variables.

## 24.2 Severability

### Severable

```text
Joint / Shared Financial Liability
Formal Lending Group
```

### Non-severable

```text
Shared Economic Exposure
Shared Geographic Exposure
```

Do not allow the UI to sever common market/location realities.

## 24.3 Counterfactual edge mask

For target borrower \(i\) and candidate edge set \(C\):

\[
\boxed{
w^{CF}_e
=
\begin{cases}
0,&e\in C\\
w_e,&e\notin C
\end{cases}
}
\]

This is simulation-only.

The source graph remains immutable.

## 24.4 Mechanism-specific effect

### Joint liability

For severed edge:

\[
\boxed{
E^{joint}_{i\to j}=0
}
\]

therefore:

\[
\boxed{
TransferredBurden_{i\to j}=0
}
\]

### Formal group

For severed edge:

\[
\boxed{
\gamma_{group,i\to j}=0
}
\]

therefore:

\[
\boxed{
\Delta Stress_{j,group}=0
}
\]

All non-severed mechanisms remain active.

---

# 25. Policy 2 Candidate Extraction

For selected borrower \(i\):

\[
\boxed{
K=
\left\{
e_{i\to j}
\mid
Type(e)\in
\{JointLiability,FormalGroup\}
\right\}
}
\]

and:

\[
k=|K|
\]

Economic and geographic edges are never included.

---

# 26. Policy 2 Search Algorithm

## 26.1 If \(k\le8\)

Evaluate all:

\[
\boxed{
2^k
}
\]

candidate subsets.

Examples:

\[
k=4\Rightarrow16
\]

\[
k=6\Rightarrow64
\]

This gives an exact local optimization.

## 26.2 If \(k>8\)

Use greedy forward selection.

Conceptually:

```python
C = empty_set

while True:
    evaluate adding each remaining edge
    choose the edge with the best current improvement
    if marginal improvement is below stopping threshold:
        break
    add chosen edge to C
```

The 5% stopping threshold is an implementation parameter, not an empirical microfinance constant.

Do not promise a universal runtime such as “always under 50 ms”.

---

# 27. Policy 2 Candidate Re-Simulation

For every candidate edge subset \(C\):

```text
1. Copy/instantiate counterfactual state from baseline.
2. Apply zero-mask to all e in C.
3. Re-run downstream cascade.
4. Recalculate borrower states.
5. Recalculate distress states.
6. Record final counterfactual state.
7. Calculate ΔD, ΔS, ΔR, cost, ΔCriticality, Score(C).
```

The re-simulation must use the same propagation mathematics as the baseline engine.

A localized downstream traversal may be used for performance, but it must not change the mathematical result.

---

# 28. Policy 2 Outcome Metrics

For candidate set \(C\):

\[
\boxed{
\Delta D(C)
=
D_{baseline}
-
D_{CF}(C)
}
\]

\[
\boxed{
\Delta S(C)
=
\sum_j
(
Stress_{j,baseline}
-
Stress_{j,CF}(C)
)
}
\]

\[
\boxed{
\Delta R(C)
=
R_{baseline}
-
R_{CF}(C)
}
\]

Direct financial cost:

\[
\boxed{
Cost_2=0
}
\]

This means zero direct cash outlay in the prototype accounting model.

It does not mean zero contractual/operational consequence.

---

# 29. Policy 2 Internal Candidate Score

First calculate:

\[
\boxed{
\Delta Criticality(C)
=
\Delta D(C)
+
\min
(
\mu_{policy}\Delta S(C),
C_{policy}
)
}
\]

Then apply severance-friction penalty:

\[
\boxed{
Score(C)
=
\Delta Criticality(C)
-
0.05|C|
}
\]

Locked:

\[
\boxed{
\lambda_{severance}=0.05
}
\]

This penalty is not monetary.

---

# 30. Policy 2 Presets

The backend should produce three understandable presets.

## 30.1 Surgical

Constraint:

\[
\boxed{
|C|=1
}
\]

Choose the best single edge.

Purpose:

> Targeted protection with minimum topology disruption.

## 30.2 Optimal Shield

\[
\boxed{
C^*
=
\arg\max_C Score(C)
}
\]

System-recommended balance.

## 30.3 Full Containment

\[
\boxed{
C=K
}
\]

All eligible outgoing severable edges are disabled.

---

# 31. Policy 2 UI Result

Example:

```text
Selected Borrower: B7

Transmission Severance

Surgical
  Sever: B7 → B12

Optimal Shield ★
  Sever: B7 → B12
  Sever: B7 → B4

Full Containment
  Sever: B7 → B12
  Sever: B7 → B4
  Sever: B7 → B15
```

For every preset show:

```text
Avoided Distress
Systemic Stress Relief
Cascade Reach Reduction
Financial Cost
Internal Criticality
```

---

# 32. Policy 3 — Emergency Liquidity Support

## 32.1 Purpose

Inject fresh capital into the selected borrower's liquidity buffer.

It modifies only:

\[
LiquidityBuffer
\]

It does not directly alter:

```text
Income
Loan Obligation
Outstanding Loan
Network Edges
```

## 32.2 Policy-specific user budget

Only Policy 3 asks the user for a maximum monetary intervention cap:

\[
\boxed{
M_{cap}
=
\text{maximum ELS amount available}
}
\]

This is a UI rule.

---

# 33. Policy 3 Required Liquidity

First calculate the exact post-shock monthly deficit using Step 3:

\[
\boxed{
Deficit_i
=
\max(0,Required_i-Income_{i,new})
}
\]

Then:

\[
\boxed{
TargetDeficit_i
=
Deficit_i\times EffectiveDuration
}
\]

Required injection for complete cumulative buffer coverage:

\[
\boxed{
L_i^*
=
\max
\left(
0,
TargetDeficit_i-LiquidityBuffer_i
\right)
}
\]

This is an analytical calculation.

No discrete “Surgical/Optimal/Full” presets are needed for Policy 3.

---

# 34. Policy 3 Budget Cap

Actual injection:

\[
\boxed{
C_{actual}
=
\min(L_i^*,M_{cap})
}
\]

Remaining requirement:

\[
\boxed{
Shortfall_i
=
\max(0,L_i^*-M_{cap})
}
\]

---

# 35. Policy 3 State Modification

Only liquidity changes:

\[
\boxed{
LiquidityBuffer_i^{new}
=
LiquidityBuffer_i+C_{actual}
}
\]

Then rerun the exact Step 3 engine.

## Important dual-gate consequence

Full buffer coverage means:

\[
BufferStress=0
\]

but it does not necessarily mean:

\[
IsDistressed=False
\]

because:

\[
CashStress\ge0.35
\]

can independently trigger distress.

Therefore:

\[
\boxed{
L^*
\text{ guarantees complete modeled buffer coverage, not necessarily zero distress.}
}
\]

---

# 36. Policy 3 Full Re-Simulation

```text
Inject liquidity
→ Step 3
→ Step 4
→ Step 5A/5B/5C/5D
→ Step 6
```

ELS itself does not sever edges.

If the borrower's post-ELS stress remains distress-level, propagation can continue.

---

# 37. Standard Outcome Measurement Engine

Every intervention must produce the same audit vector:

\[
\boxed{
Outcome=
[\Delta D,\Delta S,\Delta R,Cost]
}
\]

## 37.1 Avoided distress

\[
\boxed{
\Delta D
=
D_{baseline}-D_{counterfactual}
}
\]

## 37.2 Systemic stress relief

\[
\boxed{
\Delta S
=
\sum_j
(
Stress_{j,baseline}
-
Stress_{j,counterfactual}
)
}
\]

This captures improvements that do not cross the distress threshold.

## 37.3 Cascade reach reduction

\[
\boxed{
\Delta R
=
R_{baseline}
-
R_{counterfactual}
}
\]

where:

\[
R=
\text{number of borrowers reached by propagation}
\]

A reached borrower does not have to become distressed.

## 37.4 Cost

### Policy 1

\[
\boxed{
Cost_1=r\times d
}
\]

### Policy 2

\[
\boxed{
Cost_2=0
}
\]

direct financial cost.

### Policy 3

\[
\boxed{
Cost_3=C_{actual}
}
\]

---

# 38. Internal Machine Metric

For every intervention scenario:

\[
\boxed{
\Delta Criticality
=
\Delta D
+
\min
(
\mu_{policy}\Delta S,
C_{policy}
)
}
\]

This is the machine-layer outcome metric.

The UI should still expose the uncollapsed vector:

\[
\boxed{
[\Delta D,\Delta S,\Delta R,Cost]
}
\]

Do not replace this with an opaque new “portfolio health score”.

---

# 39. Efficiency Metrics

## Policy 1

\[
\boxed{
\Phi_1
=
\frac{\Delta Criticality_1}
{\max(1,Cost_1)}
}
\]

## Policy 3

\[
\boxed{
\Phi_3
=
\frac{\Delta Criticality_3}
{\max(1,C_{actual})}
}
\]

## Policy 2

Policy 2 has zero direct financial cost, so do not calculate:

\[
\frac{\Delta Criticality_2}{0}
\]

and claim infinite efficiency.

Display:

```text
Financial cost: ₹0
Financial efficiency: N/A — non-cash intervention
```

Use systemic impact and topology/contractual disruption metrics for its interpretation.

---

# 40. Intervention Comparison

The comparison must begin from:

```text
same selected borrower
same immutable baseline state
same model parameters
```

Then independently execute:

```text
Policy 1
Policy 2
Policy 3
```

Each must use the same cascade simulator.

---

# 41. Comparison Workflow

## Stage 1 — Systemic ranking

Rank the three policies by:

\[
\boxed{
\Delta Criticality_p
}
\]

This tells the MFI which intervention performs better under the selected policy objective.

Example:

```text
1. Policy 3
2. Policy 1
3. Policy 2
```

This is the **systemic ranking**.

## Stage 2 — Financial efficiency

Display separately:

\[
\Phi_1
\]

and:

\[
\Phi_3
\]

This gives the officer a direct measure of systemic improvement per monetary unit for the two cash-consuming policies.

Policy 2 is shown as a zero-direct-cash intervention rather than receiving a fake infinite ROI.

---

# 42. Policy 3 Budget Interaction

When Policy 3 is evaluated, require the user to enter:

\[
M_{cap}
\]

The UI can show:

```text
Required for full buffer coverage: ₹3,400
Maximum ELS budget:              ₹2,000
Actual possible injection:       ₹2,000
```

No equivalent Policy-3 maximum-budget field is required for Policy 1 or Policy 2.

---

# 43. Final Decision Philosophy

The engine should inform the MFI officer rather than hide the decision inside a single automatic recommendation.

Show:

```text
SYSTEMIC RANKING
1. Policy ...
2. Policy ...
3. Policy ...

FINANCIAL EFFICIENCY
Policy 1: ...
Policy 3: ...

Policy 2
Direct financial cost: ₹0
```

The officer considers:

- systemic performance;
- capital availability;
- operational/contractual consequences.

The system's scalar ranking does not erase the underlying evidence.

---

# 44. Step 8 — Commit Selected Intervention

After comparison, the user selects the intervention to actually adopt in the model.

Persist:

```text
selected_borrower
selected_policy
selected_parameters
selected_edge_set       # Policy 2
M_cap                   # Policy 3
policy_profile
baseline_run_id
```

The baseline remains immutable.

No new mathematical transformation is introduced here.

---

# 45. Step 9 — Final Counterfactual Run

Run the chosen intervention one final time from the stored baseline.

```text
baseline state
→ apply chosen intervention
→ full cascade re-simulation
→ authoritative final state
```

The final run must use the same mathematical engine used for comparison.

Do not substitute a simplified calculation on the final screen.

---

# 46. Step 10 — Before / After

Compare baseline and final intervention state.

At minimum show:

```text
Distressed borrowers
Baseline → Final

Cascade reach
Baseline → Final

Total/systemic stress
Baseline → Final
```

and:

```text
Avoided distress ΔD
Stress reduction ΔS
Reach reduction ΔR
Financial cost
ΔCriticality
```

---

# 47. Step 11 — Decision Summary

Generate a human-readable summary directly from stored simulation results.

Example:

```text
Selected Intervention:
Repayment Relief

Target:
Borrower B7

Intervention:
₹1,500/month for 3 months

Distressed borrowers:
8 → 3

Cascade reach:
11 → 6

Systemic stress reduction:
1.41

Cost:
₹4,500
```

No hidden AI-generated quantitative claim is allowed.

---

# 48. Step 12 — Persistence and Reproducibility

Every simulation run must be persistable and reproducible.

## 48.1 Core run record

Store:

```text
run_id
timestamp

dataset_id
dataset_version

baseline_network_state

shock_configuration

model_parameters

distress_threshold

policy_profile

criticality_results

baseline_cascade

candidate_interventions

selected_intervention

intervention_parameters

counterfactual_state

outcome_vector

final_result
```

## 48.2 Policy 2 persistence

Also store:

```text
severable_edges
candidate_edge_sets
selected_edge_set
candidate_scores
selected_policy2_preset
```

## 48.3 Policy 3 persistence

Also store:

```text
L_required
M_cap
C_actual
remaining_shortfall
```

## 48.4 Reproducibility invariant

Every final result must be reconstructable from:

\[
\boxed{
Dataset
+
Shock
+
Model\ Parameters
+
Intervention
}
\]

---

# 49. State Isolation Rules

This is critical for implementation.

## Baseline

Immutable.

## Criticality counterfactual

Temporary derived state; never modify baseline.

## Policy 1

Temporary repayment-relief state.

## Policy 2

Temporary edge-mask state.

## Policy 3

Temporary liquidity-buffer state.

## Final chosen intervention

A new stored final counterfactual state.

Never mutate the baseline object in-place.

---

# 50. Recommended Backend Module Structure

```text
backend/
  data/
    schema_validation
    borrower_loader
    relationship_loader
    graph_builder
    data_quality

  simulation/
    shock_engine
    stress_engine
    step3
    step4_filter
    propagation/
      joint_liability
      formal_group
      economic_exposure
      geographic_exposure
    cascade_engine
    simulation_state

  intervention/
    criticality_engine
    policy1_repayment_relief
    policy2_transmission_severance
    policy3_emergency_liquidity
    comparison_engine

  reporting/
    outcome_engine
    ranking
    before_after
    decision_summary

  persistence/
    run_store
    scenario_store
```

The exact framework can be chosen by the implementation agent, but responsibilities should remain separated.

---

# 51. Core Function Contracts

Recommended conceptual interfaces:

```text
validate_dataset()

load_borrowers()

load_relationships()

build_graph()

define_shock()

calculate_post_shock_income()

calculate_required()

calculate_deficit()

calculate_cash_stress()

calculate_buffer_stress()

calculate_effective_stress()

calculate_distress_state()

filter_relevant_edges()

propagate_joint_liability()

propagate_formal_group()

propagate_economic_exposure()

propagate_geographic_exposure()

simulate_cascade()

simulate_borrower_containment()

calculate_criticality()

rank_borrowers()

simulate_repayment_relief()

simulate_transmission_severance()

simulate_emergency_liquidity()

calculate_outcome_vector()

calculate_delta_criticality()

calculate_efficiency()

compare_policies()

commit_intervention()

persist_run()
```

Each function should have one clear responsibility.

---

# 52. Recommended Canonical Simulation State

A simulation state should preserve, at minimum:

```text
SimulationState
├── run_id
├── graph_reference
├── shock_config
├── model_params
├── borrowers
│   └── BorrowerState
│       ├── borrower_id
│       ├── income
│       ├── essential_expense
│       ├── loan_obligation
│       ├── outstanding_loan
│       ├── liquidity_buffer
│       ├── extra_monthly_obligation
│       ├── cash_stress
│       ├── buffer_stress
│       ├── effective_stress
│       └── is_distressed
├── activated_sources
├── reached_nodes
├── propagation_events
└── final_metrics
```

---

# 53. Propagation Event Record

For debugging, auditing, and UI explanation, every propagation event should be recordable.

Recommended structure:

```text
event_id
source_borrower
target_borrower
super_mechanism
specific_mechanism

pre_state_target
impact_type
impact_amount_or_delta
post_state_target

simulation_run_id
```

Examples:

```text
A → B
Joint / Shared Financial Liability
Joint Liability
₹1,000 monthly transferred burden
```

or:

```text
A → B
Formal Lending Group
Group Pressure
ΔStress = 0.036
```

This makes the cascade auditable.

---

# 54. Distress State and Stress State Separation

Never conflate:

```text
stress value
```

with:

```text
distress boolean
```

A borrower may have:

\[
Stress=0.28
\]

and not be distressed.

Another may have:

\[
CashStress=0.37
\]

and therefore be distressed through the high-cash-stress gate.

The implementation must retain both.

---

# 55. Important Unit Rules

These rules prevent subtle implementation bugs.

### Monthly quantities

The following are monthly:

```text
monthly_income
monthly_essential_expense
monthly_loan_obligation
TransferredBurden
contractual_monthly_exposure
repayment_relief
```

### Cumulative horizon quantities

```text
TargetDeficit
TotalDeficit
```

are duration-scaled quantities.

Never mix monthly and cumulative quantities.

---

# 56. Numerical Safety Rules

The implementation must include guards for:

## Duration

\[
EffectiveDuration=\max(1,duration)
\]

## Zero deficit

\[
Deficit\times EffectiveDuration\le0
\Rightarrow BufferStress=0
\]

## Required amount

Reject or explicitly flag:

\[
Required\le0
\]

## Singleton group

\[
N_{group}\le1
\Rightarrow GroupPressure=0
\]

## Liquidity budget

\[
C_{actual}=\min(L^*,M_{cap})
\]

## Criticality

Never use logarithmic transformation.

---

# 57. Parameter Registry

Model parameters should live in a single versioned configuration object.

Example:

```json
{
  "distress_threshold": 0.30,
  "cash_stress_override": 0.35,
  "cash_stress_weight": 0.70,
  "buffer_stress_weight": 0.30,
  "gamma_group": 0.15,
  "severance_penalty": 0.05,
  "criticality_profiles": {
    "STRICT": {
      "mu": 0.05,
      "cap": 0.50
    },
    "BALANCED": {
      "mu": 0.20,
      "cap": 1.25
    },
    "AGGRESSIVE": {
      "mu": 0.40,
      "cap": 2.50
    }
  }
}
```

Store the parameter version with every run.

---

# 58. Locked Parameters

| Parameter | Locked value / rule |
|---|---:|
| \(T_{distress}\) | **0.30** |
| Cash-stress override | **0.35** |
| CashStress weight | **0.70** |
| BufferStress weight | **0.30** |
| \(\gamma_{group}\) | **0.15** |
| Severance penalty | **0.05** |
| EffectiveDuration | **max(1, duration)** |
| Strict \((\mu,C)\) | **(0.05, 0.50)** |
| Balanced \((\mu,C)\) | **(0.20, 1.25)** |
| Aggressive \((\mu,C)\) | **(0.40, 2.50)** |
| Policy 2 direct financial cost | **₹0** |
| Policy 3 budget | **user-entered \(M_{cap}\)** |

---

# 59. Explicitly Rejected / Do Not Reintroduce

Do not reintroduce:

1. Arbitrary universal liability percentages.
2. Arbitrary economic exposure weights.
3. Arbitrary geographic edge-strength weights.
4. Automatic propagation of every shock.
5. “Every transmission = default.”
6. Logarithmic criticality scoring.
7. Hidden health indices replacing the audit vector.
8. Policy 3 presets instead of analytical \(L^*\).
9. Policy 2 financial ROI calculated by division by zero.
10. Permanent mutation of the baseline graph/state.
11. AI deciding numerical outcomes.
12. Unsupported universal runtime guarantees such as “always <50 ms”.

---

# 60. End-to-End Implementation Sequence

```text
1. Load dataset
2. Validate borrower and relationship data
3. Construct graph
4. Render graph
5. User clicks borrower
6. Open shock UI
7. User selects shock cause
8. Show dynamic cause-specific fields
9. User sets severity
10. User sets duration
11. Run Step 3
12. If not distressed → end baseline simulation
13. If distressed → Step 4
14. Propagate through 5A / 5B / 5C / 5D
15. Recalculate receiving borrowers
16. Activate newly distressed sources
17. Continue cascade until queue is empty
18. Store baseline
19. Enter Intervention Engine
20. Choose MFI policy profile
21. For every borrower:
      a. benchmark containment counterfactual
      b. calculate criticality
22. Rank borrowers
23. Select target based on intervention capacity
24. Run Policy 1 counterfactual
25. Run Policy 2 candidate search/counterfactuals
26. Ask Policy 3 for M_cap
27. Run Policy 3 counterfactual
28. Calculate [ΔD, ΔS, ΔR, Cost]
29. Calculate ΔCriticality for every policy
30. Rank policies by ΔCriticality
31. Show Φ1 and Φ3
32. Show Policy 2 as zero-direct-cost/non-cash option
33. User chooses intervention
34. Commit selected configuration
35. Run final counterfactual
36. Compare baseline vs final
37. Produce decision summary
38. Persist complete run
```

---

# 61. Final Product Screens / Logical Views

A prototype can be organized into these principal views:

## View A — Network

```text
Borrower graph
Upload data
Load demo
Node/edge inspection
```

## View B — Shock panel

```text
Selected borrower
Shock cause
Dynamic context field
Severity
Duration
Run simulation
```

## View C — Cascade result

```text
Initial source
Propagation waves/events
Distressed borrowers
Cascade reach
Final network state
```

## View D — Intervention / WHO

```text
Policy profile
Criticality-ranked borrowers
Top intervention candidates
Criticality components
```

## View E — Intervention / HOW

```text
Selected borrower

Policy 1
Policy 2
Policy 3

Policy-specific controls
Simulation results
```

## View F — Comparison

```text
Systemic ranking
ΔD
ΔS
ΔR
Cost
ΔCriticality
Φ1
Φ3
Policy 2 zero direct financial cost
```

## View G — Final result

```text
Before
After
Selected intervention
Impact summary
Persist / review run
```

---

# 62. Acceptance Tests

The implementation should pass at least these functional tests.

## Stress engine

- Severity 0 produces no income reduction.
- Deficit 0 produces `BufferStress = 0`.
- Duration 0 uses `EffectiveDuration = 1`.
- Large liquidity buffer cannot hide `CashStress >= 0.35`.
- \(S_{effective}\) follows the exact max formula.

## Group engine

- Singleton group produces zero group pressure.
- Five-member group uses denominator \(4\).
- Multiple distressed members use bounded aggregation.
- `Stress_B^financial` maps to `S_effective,B`.

## Joint liability

- Contractual exposure controls transferred burden.
- Missing exposure/share does not create an invented number.
- Transferred burden is monthly.
- Multiple incoming burdens accumulate in `r_extra`.

## Economic exposure

- Shock to Market M12 only affects borrowers actually exposed to M12.
- Missing source-income exposure does not create a fake percentage.

## Geographic exposure

- Only borrowers in the affected geographic context receive the modeled geographic shock.
- No arbitrary geographic multiplier appears.

## Cascade

- A borrower can be reached without becoming distressed.
- A distressed borrower can become a new source.
- Cycles do not cause infinite loops.

## Criticality

- Every borrower is counterfactually evaluated.
- Criticality uses the bounded linear formula.
- No logarithm is used.
- Ranking is descending by criticality.

## Policy 1

- Only repayment obligation changes.
- Cost equals monthly relief × duration.
- Full cascade is re-run.

## Policy 2

- Only joint-liability/formal-group edges can be severed.
- Baseline graph remains unchanged.
- All candidate sets are evaluated correctly for \(k\le8\).
- Presets are generated.

## Policy 3

- Only liquidity buffer changes.
- M_cap is explicitly requested.
- \(C_{actual}=\min(L^*,M_{cap})\).
- Full buffer coverage does not incorrectly force `IsDistressed = False`.

## Comparison

- All policies use the same baseline.
- Same outcome dimensions are shown.
- Policy ranking uses \(\Delta Criticality\).
- \(\Phi_1\) and \(\Phi_3\) are shown.
- Policy 2 is not assigned infinite financial efficiency.

## Persistence

- A saved run can reproduce the same result.

---

# 63. Current Model Boundary

The following remain model/prototype parameters rather than claims of universal real-world truth:

- \(\gamma_{group}=0.15\);
- \(T_{distress}=0.30\);
- \(CashStress\) override \(=0.35\);
- criticality profile weights and caps;
- severance penalty \(=0.05\).

Institution-specific contractual definitions, historical repayment data, actual group sanction rules, and empirical calibration should be supported later without changing the architecture.

The prototype should make these parameters centralized, visible to developers, and versioned.

---

# 64. Final Architectural Invariant

The most important implementation invariant is:

\[
\boxed{
\text{Every intervention changes a defined state variable or edge set, and the same cascade engine determines the resulting network response.}
}
\]

The system therefore remains a true simulation engine:

\[
\boxed{
\text{Shock}
\rightarrow
\text{Stress}
\rightarrow
\text{Pathway}
\rightarrow
\text{Mechanism}
\rightarrow
\text{Cascade}
\rightarrow
\text{Criticality}
\rightarrow
\text{Intervention}
\rightarrow
\text{Counterfactual Cascade}
\rightarrow
\text{Measured Outcome}
}
\]

This is the authoritative prototype implementation plan.
