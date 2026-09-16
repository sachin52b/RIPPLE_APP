# Financial Contagion & Resilience Lab — Frontend Plan

## 1. Purpose and non-negotiable product principles

This document is the authoritative UI/UX and component specification for the React frontend of the Financial Contagion & Resilience Lab. The frontend visualizes and controls the existing deterministic backend; it must not introduce alternate stress formulas, hidden risk scores, invented exposure weights, or client-side simulation logic.

The product goal is to help an MFI officer understand and test a cascade, not to predict individual defaults. Every number displayed in the interface must be traceable to an API response, a stored run, or an explicit user input.

The primary workflow is:

```text
Load validated network → define shock → run baseline cascade → rank critical borrowers
→ evaluate policies → compare outcomes → commit a selected counterfactual → persist run
```

The frontend must preserve these backend invariants:

- A baseline simulation is immutable after it is run.
- Policy previews and final selections are counterfactuals; they never mutate the source graph in the browser.
- Monetary amounts must show units. Monthly amounts and duration-scaled amounts must never be conflated.
- A received transmission is not equivalent to a new distressed propagation source.
- Missing quantified economic exposure must be represented as unavailable/no monetary transfer, never estimated by the UI.
- Policy 2 has ₹0 direct financial cost and must never receive an infinite efficiency ratio.

## 2. Technology and application shell

### Required stack

- React 18+ with Vite and TypeScript in strict mode.
- Tailwind CSS for layout, tokens, responsive variants, and dark/light theming.
- Lucide React for controls, state indicators, and semantic iconography.
- Cytoscape.js with `react-cytoscapejs` for the directed multigraph canvas. React Flow is an acceptable fallback only if it can preserve parallel directed edges and edge metadata inspection.
- Native `fetch` wrapped in a typed API service. Do not add an API client dependency unless required by the host application.

### Visual language

Use a calm, operational workspace rather than a dashboard full of permanently visible cards.

- Canvas background: neutral/slate surface with subtle grid or texture.
- Primary action: indigo/blue.
- Destructive or material-risk state: red, reserved for distress and warnings.
- Non-cash topology action: blue/slate; never imply financial spending.
- Numeric values: tabular figures, Indian rupee formatting (`₹12,000`) for financial fields, and two to four decimals only where analytical precision matters.
- Accessibility: every color state needs a label, icon, tooltip, or pattern. The graph legend is always visible.

## 3. Window architecture and navigation model

Use a nested workspace instead of a linear wizard. The user can inspect prior results while moving forward, but downstream actions remain disabled until their prerequisites exist.

```text
AppShell
├── HeaderBar
├── WorkspaceTabs
│   ├── NetworkWorkspace (View A)
│   ├── SimulationWorkspace (Views B–C)
│   ├── CriticalityWorkspace (View D)
│   ├── PolicyLaboratory (View E)
│   └── DecisionWorkspace (Views F–G)
├── ContextSlideOver (node / edge / selected-borrower context)
├── CascadeModal (step-by-step timeline and heatmap)
├── ConfirmCommitModal
└── Toast / error notification region
```

### Header bar

The persistent header must contain:

- Product title: **Financial Contagion & Resilience Lab**.
- Backend health pill, polling `GET /api/health` on application start and at a modest interval. Show:
  - green `Server` icon + “Engine ready” when healthy;
  - amber `RefreshCw` + “Checking engine” while pending;
  - red `CloudOff` + “Backend unavailable” on failure.
- Parameter-version affordance. A popover exposes locked values returned by health: distress threshold, cash-stress override, weights, gamma group, severance penalty, and the three criticality profiles.
- Dataset controls:
  - **Load Demo Dataset** button (`DatabaseZap`) calling `GET /api/network/demo`.
  - Drag-and-drop upload zone/button (`Upload`) accepting CSV or Excel in the UI. The upload adapter must parse files into the required borrower/relationship record arrays, show a mapping/preview step, and call `POST /api/network/upload` only after confirmation.
  - Current dataset name/version and node/edge count after successful load.
- A compact pipeline progress indicator: Network → Shock → Cascade → WHO → HOW → Decision. It communicates current readiness; it is not a substitute for tabs.

### Context slide-over and modal rules

- A right-hand slide-over is the persistent inspection surface. It can show either a node, an edge, or selected intervention context; only one context is active at once.
- Modals are reserved for focused, interrupting work: the cascade visualizer, file mapping/validation errors, and final commit confirmation.
- Tabs remain navigable. If a prerequisite is missing, render an empty state with an action that directs the user to the previous appropriate screen.
- On loading a new dataset, clear all run-derived frontend state after a confirmation warning. Do not silently retain a baseline against a different graph.

## 4. Frontend state model

Use a small typed store (React Context plus reducer is sufficient; Zustand is optional) rather than passing execution state through component trees. Server responses remain the source of truth.

```ts
type AppState = {
  health: HealthResponse | null;
  network: NetworkResponse | null;
  baseline: SimulationStateResponse | null;
  criticality: CriticalityScore[];
  criticalityProfile: CriticalityProfileName;
  evaluatedPolicies: InterventionEvaluationResponse | null;
  selectedPolicy: SelectedPolicy | null;
  finalRun: InterventionCommitResponse | null;
  activePanel: NodePanel | EdgePanel | InterventionPanel | null;
  activeTab: WorkspaceTab;
  requestState: Record<RequestKey, "idle" | "loading" | "success" | "error">;
  errors: UiError[];
};
```

Store opaque backend identifiers exactly as returned:

- `network_id` scopes shocks to a loaded graph.
- `run_id` scopes criticality, policy evaluation, committing, and saving to one immutable baseline execution.
- Edge IDs are the only values used when selecting Policy 2 severance sets/presets.

Do not recompute stress, criticality, outcomes, or policy costs in the store. Local state is limited to form values, selection, visibility, filters, and presentation preferences.

## 5. Data contracts and display conventions

### Borrower fields

Render the validated borrower fields supplied by the backend:

| Field | UI label | Formatting |
|---|---|---|
| `borrower_id` | Borrower ID | monospace/label |
| `group_id` | Formal group | `—` when null |
| `location_id` | Location | label |
| `livelihood_type` | Livelihood | humanize snake case |
| `monthly_income` | Monthly income | monthly ₹ |
| `monthly_essential_expense` | Essential expenses | monthly ₹ |
| `monthly_loan_obligation` | Loan obligation | monthly ₹ |
| `outstanding_loan` | Outstanding loan | ₹ |
| `liquidity_buffer` | Liquidity buffer | ₹ |
| `income_stability` | Income stability | text or numeric score |

### Stress fields

Show backend stress values with explanatory tooltips:

- `post_shock_income`
- `required_amount`
- `monthly_deficit`
- `total_deficit` (duration-scaled, explicitly labelled “over modelled horizon”)
- `cash_stress`
- `buffer_stress`
- `effective_stress`
- `is_distressed`

Do not label `cash_stress >= 0.35` “safe” merely because `effective_stress` appears low: the backend’s dual distress gate is authoritative.

### Relationship fields

Show `edge_id`, source, target, `super_mechanism`, `specific_mechanism`, `contractual_monthly_exposure`, `liability_share`, `economic_source_type`, `economic_source_id`, and `metadata`. Explain missing contractual or economic quantities as **not supplied**, never as zero unless the backend has explicitly returned zero.

## 6. Screen A — Interactive Network Canvas and inspection

### Workspace layout

```text
┌──────────────────────────────── Main canvas ───────────────────────────────┐
│ legend / fit / zoom / layout controls                                       │
│                                                                             │
│ Cytoscape directed borrower network                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ┌──────── Context slide-over ──────────────┐
                                  │ Node or edge inspection                  │
                                  │ Shock form when node selected             │
                                  └──────────────────────────────────────────┘
```

### Canvas behavior

- Render every borrower as a node keyed by `borrower_id` and every relationship as a directed edge keyed by `edge_id`.
- Use a stable layout, initially grouping members by `group_id` and/or `location_id`; include layout choices such as “By group”, “By location”, and “Network”.
- Preserve parallel relationships. Edges sharing source and target need visual curvature/offset and individual selection handling.
- Controls: fit to graph, zoom, reset layout, toggle labels, filter by mechanism, show only distressed/reached/activated nodes after a run.
- Use graph state from baseline/final responses to update node classes without rewriting the graph model.

### Mandatory visual legend

Node precedence is important. Apply the most severe applicable state:

| Element | Visual treatment | Meaning |
|---|---|---|
| Normal/safe node | slate fill | no displayed high cash stress or material distress |
| High cash-stress node | amber fill + `AlertTriangle` marker | `cash_stress >= 0.35` |
| Material-distress node | red fill + `OctagonAlert` marker | `is_distressed` / effective-stress gate |
| Activated source | thick indigo halo | processed source in baseline/final run |
| Reached node | outlined/animated ring | received or initially experienced an impact |
| Joint liability edge | red solid arrow | contractual financial relationship |
| Formal group edge | blue dashed arrow | non-monetary group pressure |
| Shared economic edge | green dotted arrow | common economic source |
| Shared geographic edge | orange dash-dot arrow | common geographic cause |

The legend should explicitly state that edge styles identify relationship mechanism, not probability or severity.

### Node inspection slide-over

Open on node click. It contains:

1. Header with borrower ID, distress badge, close icon, and “Run intervention” shortcut when a baseline and ranking are available.
2. Identity section: group, location, livelihood, income stability.
3. Financial facts section: income, expenses, loan obligation, outstanding loan, liquidity buffer.
4. Current simulation section, if a baseline/final state exists: post-shock income, monthly and total deficit, cash/buffer/effective stress, distress boolean, extra monthly obligation, and income loss.
5. Related edges section showing outgoing/incoming records with mechanism icons. Clicking an edge switches to edge inspection.
6. Embedded Shock Simulator form described in Screen B.

### Edge inspection slide-over

Open on edge click. Show source → target, relation type, specific mechanism, and an “interpretation” sentence generated from fields only:

- Joint liability: contractual monthly exposure and liability share if supplied.
- Formal group: group-mediated, non-monetary pressure; never call it a debt transfer.
- Economic exposure: source type/ID and quantified exposure if supplied; otherwise explain that no monetary transfer can be inferred.
- Geographic exposure: represented geographic context.

Render raw `metadata` in an expandable JSON/details block for auditing.

## 7. Screen B — Dynamic Shock Simulator

The shock form is embedded in the selected node’s inspection panel. For common-cause shocks it may also be opened from the header/workspace toolbar, but it must always retain an explicit target/context.

### Form controls

| Shock cause | Required/visible controls | API mapping |
|---|---|---|
| Borrower-Specific Income Shock | selected borrower ID, severity slider, duration | `cause: "income_shock"`, `target_borrower_id` |
| Shared Economic Shock / Market Event | economic source ID select, severity slider, duration | `cause: "market_shock"`, `economic_source_id` |
| Shared Geographic Shock / Location Event | location ID select, severity slider, duration | `cause: "geographic_shock"`, `location_id` |

- Severity is a 0–100% slider, displayed as a percentage and sent as `0.0–1.0`.
- Duration is a non-negative integer in months. Helper text states that the engine applies `max(1, duration)` internally; do not silently change the user’s input in the UI.
- Economic source and location options are derived from loaded graph data. If no valid source exists, disable that cause and explain why.
- Display a small request preview before submission. A `shock_id` is generated client-side (UUID) or supplied by the UI orchestration layer.

### Submission behavior

**Simulate Cascade** calls `POST /api/simulation/shock` with `network_id` and the validated `Shock` object. While pending:

- disable duplicate submission;
- show a loading state such as “Running stress, pathway filtering, and cascade…”;
- retain the prior baseline until the new response succeeds;
- on success, replace baseline state, clear criticality/policy/final-decision state, recolor the graph, and open Screen C;
- on API validation failure, retain input values and render field-level/server error details.

## 8. Screen C — Cascade simulation and heatmap visualizer

Open as a sizeable modal or full-height bottom panel after baseline cascade completion. It must be usable alongside the canvas.

### Summary banner

Display backend-derived information only:

- initial shock context (borrower, market source, or location);
- total activated sources;
- total reached borrowers;
- total distressed borrowers;
- total effective stress (baseline summary); and
- number of propagation events.

When comparing to a prior final state, show a separate labelled delta; do not call the baseline total “systemic stress delta.”

### Propagation event timeline

Render ordered `propagation_events` as a vertical stepper:

```text
Source → Target
Mechanism / specific mechanism
Impact type + amount or Δstress
Target state before → target state after
```

Use mechanism-specific icons and units:

- `extra_monthly_obligation`: monthly ₹.
- `group_pressure`: Δstress.
- `monthly_income_loss`: monthly ₹.

Selecting a timeline entry temporarily highlights source, target, and edge on the canvas and opens a detailed event drawer with pre/post state snapshots.

### Heatmap and playback

- Provide event index slider/playback controls; there is no claim of real-time simulation.
- At each event, color nodes by state from the applicable pre/post payload.
- Clearly differentiate reached-but-not-distressed nodes from escalated sources.
- Include “View final borrower states” table with filtering/sorting but no client-side recalculation.

After the baseline display is complete, make **Continue to Criticality** available. The interface may auto-focus View D, but do not automatically choose a borrower or intervention.

## 9. Screen D — Stage 1 WHO: criticality ranking

This workspace becomes enabled after a baseline run.

### Policy objective selector

Present profiles as radio cards with exact locked values and plain-language intent:

| Profile | Locked settings | Copy |
|---|---:|---|
| Strict Distress Minimization | `mu=0.05`, `cap=0.50` | “Prioritizes containing the raw count of materially distressed borrowers.” |
| Balanced Portfolio Health | `mu=0.20`, `cap=1.25` | “Balances stopping severe distress with reducing widespread portfolio stress.” |
| Aggressive Early Intervention | `mu=0.40`, `cap=2.50` | “Aggressively targets widespread stress stabilization early.” |

The cards describe policy objectives, not empirically calibrated predictions. The active profile must be passed unchanged to the API.

### Ranking request and result

The **Identify Critical Borrowers** action calls `POST /api/intervention/criticality` with `run_id` and `profile_name`.

- Show an active spinner/progress state: “Benchmarking containment for every borrower…”.
- Disable re-entry while pending.
- Render the sorted response as a data table: rank, borrower ID, criticality, avoided-distress delta, systemic stress delta, and bounded stress component.
- Highlight rank 1 in a recommendation card labelled **#1 Critical Target**, while retaining the instruction that the officer chooses the target.
- Each table row has **Inspect** and **Run Intervention** actions. The latter opens Screen E with that borrower preselected.

## 10. Screen E — Stage 2 policy laboratory

The selected borrower context remains pinned at the top: borrower ID, baseline effective stress/distress status, rank if available, and policy profile. The laboratory evaluates all three policies from the same immutable baseline.

### Shared evaluation contract

The **Evaluate Interventions** action calls `POST /api/intervention/evaluate` with:

```ts
{
  run_id,
  borrower_id,
  monthly_relief_amount,
  relief_duration,
  M_cap,
  profile_name
}
```

Use debounced local input validation, but evaluate only when the user explicitly submits. During computation, show all three cards in a coherent loading state so users do not mistake partial results for a comparison.

### Policy 1 — Repayment Relief card

- Inputs: monthly relief amount `r` and relief duration `d` months.
- Validate both are non-negative.
- Explain: “Only the selected borrower’s monthly loan obligation changes in this counterfactual.”
- Display response values: monthly relief, duration, total cost (`r × d`), and resulting borrower/cascade impact.
- Never label a repayment relief value as an up-front liquidity injection.

### Policy 2 — Transmission Severance card

Display the three backend-supplied presets as selectable cards, including severed edge IDs, edge count, internal score, and direct cost ₹0:

| Preset | Constraint | User-facing explanation |
|---|---|---|
| Surgical | `|C| = 1` | “Targeted protection of a single key link with minimum network disruption.” |
| Optimal Shield | `C*` | “System-recommended edge severance set maximizing stress relief.” |
| Full Containment | `C = K` | “Disables all severable outgoing joint-liability and formal-group links.” |

- Show the eligible edge list and its mechanism. Economic and geographic links must never appear selectable.
- Explain that the penalty/score reflects topology/contractual friction, not cash cost.
- Direct financial cost is fixed at ₹0. The interface displays “Financial efficiency: N/A — non-cash intervention.”

### Policy 3 — Emergency Liquidity Support card

- Input: maximum budget cap `M_cap`, non-negative ₹.
- After evaluation, show exact backend values:
  - required buffer coverage `L*`;
  - budget cap `M_cap`;
  - actual injection `C_actual = min(L*, M_cap)`;
  - remaining shortfall;
  - direct cost `C_actual`.
- Include a dual-gate note: full buffer coverage does not necessarily remove distress if the cash-stress override remains triggered.
- Explain that this policy changes only liquidity buffer; it does not alter income, loan obligation, outstanding principal, or network edges.

## 11. Screens F and G — comparison, commitment, and decision

### Comparison matrix

Render the `comparison` response from the evaluation endpoint as the canonical matrix. Do not create a new client-side score.

| Metric | Policy 1 | Policy 2 (Optimal Shield) | Policy 3 |
|---|---:|---:|---:|
| Avoided distress | ΔD | ΔD | ΔD |
| Systemic stress relief | ΔS | ΔS | ΔS |
| Cascade reach reduction | ΔR | ΔR | ΔR |
| Direct financial cost | ₹ | ₹0 | ₹ |
| Systemic delta criticality | value | value | value |
| Financial efficiency | Φ1 | N/A — non-cash intervention | Φ3 |

Sort/show the systemic ranking returned by the API. Provide a recommendation card for rank 1, but phrase it as an evidence-led result rather than an automatic decision. Display all outcome components beside the scalar rank.

### Commit selected intervention

The officer selects one of Policy 1, a named Policy 2 preset, or Policy 3. Before sending, show a confirmation modal summarizing:

- target borrower;
- policy and specific parameters/edge set;
- direct cost / non-cash status;
- a reminder that the final counterfactual will be re-run from the immutable baseline.

Call `POST /api/intervention/commit` with `run_id`, `policy`, and optional `policy2_preset`. On success:

- replace final display state with the returned final state;
- render before/after metrics from the returned `decision_summary`;
- update canvas classes to final stress state while retaining a toggle to view baseline;
- retain the selected intervention object for persistence.

### Before/after and human-readable result

Show side-by-side, source-derived metrics:

```text
Distressed borrowers: baseline → final
Cascade reach:         baseline → final
Systemic stress:       baseline → final
ΔD, ΔS, ΔR, direct financial cost, delta criticality, efficiency
```

Render the backend `summary_text` as an auditable summary. The frontend may format it but must not append unsupported causal claims.

### Persistence controls

- **Save complete run** calls `POST /api/persistence/save` with `run_id` and an optional safe filename.
- Offer a download link/record metadata returned by the backend.
- A run-history drawer calls `GET /api/persistence/runs` to list stored records.
- Selecting a history item replays it with `GET /api/persistence/runs?run_id=…&network_id=…`. Explain if the backend requires the associated retained network context.

## 12. API contract map

| UI surface/action | Endpoint | Request | Response consumed |
|---|---|---|---|
| Header health monitor | `GET /api/health` | — | status + locked parameter config |
| Load demo dataset | `GET /api/network/demo` | — | network ID, borrower/relationship records, counts |
| Upload custom dataset | `POST /api/network/upload` | borrowers, relationships, dataset ID/version | validated network payload |
| Simulate Cascade | `POST /api/simulation/shock` | network ID + `Shock` | baseline state, reached/activated nodes, events |
| Identify Critical Borrowers | `POST /api/intervention/criticality` | run ID + profile | ranked criticality scores |
| Evaluate interventions | `POST /api/intervention/evaluate` | run ID, target, Policy 1/3 inputs, profile | Policy 1/2/3 results + comparison |
| Commit final selection | `POST /api/intervention/commit` | run ID, policy, Policy 2 preset | final state, outcome vector, decision summary |
| Save run | `POST /api/persistence/save` | run ID + optional filename | stored record/path |
| Run history/replay | `GET /api/persistence/runs` | optional run ID/network ID query | records or reproduced baseline/final states |

### Typed API service requirements

`services/api.ts` owns all fetch calls and converts non-2xx responses into one typed `ApiError` shape. It must:

- use a `VITE_API_BASE_URL` environment variable, defaulting to `http://127.0.0.1:8000` for local development;
- send and accept JSON;
- retain backend error detail text for validation messages;
- never retry simulation/commit POSTs automatically;
- expose typed functions named after the workflow, such as `loadDemoNetwork`, `runShock`, `rankCriticality`, `evaluateInterventions`, `commitIntervention`, and `saveRun`.

## 13. Recommended component structure

```text
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── AppShell.tsx
│   │   ├── routes.ts
│   │   └── AppProvider.tsx
│   ├── components/
│   │   ├── layout/
│   │   │   ├── HeaderBar.tsx
│   │   │   ├── PipelineProgress.tsx
│   │   │   ├── WorkspaceTabs.tsx
│   │   │   └── ContextSlideOver.tsx
│   │   ├── canvas/
│   │   │   ├── NetworkCanvas.tsx
│   │   │   ├── cytoscapeElements.ts
│   │   │   ├── graphStyles.ts
│   │   │   ├── NetworkLegend.tsx
│   │   │   ├── CanvasControls.tsx
│   │   │   └── CascadeHeatmap.tsx
│   │   ├── inspector/
│   │   │   ├── BorrowerInspector.tsx
│   │   │   ├── EdgeInspector.tsx
│   │   │   ├── BorrowerFinancialFacts.tsx
│   │   │   └── StressStateCard.tsx
│   │   ├── shock/
│   │   │   ├── ShockSimulatorForm.tsx
│   │   │   ├── ShockCauseSelector.tsx
│   │   │   └── CascadeTimelineModal.tsx
│   │   ├── criticality/
│   │   │   ├── PolicyObjectiveSelector.tsx
│   │   │   ├── CriticalityRankingTable.tsx
│   │   │   └── CriticalTargetCard.tsx
│   │   ├── interventions/
│   │   │   ├── PolicyLaboratory.tsx
│   │   │   ├── RepaymentReliefCard.tsx
│   │   │   ├── TransmissionSeveranceCard.tsx
│   │   │   ├── LiquiditySupportCard.tsx
│   │   │   └── Policy2PresetCard.tsx
│   │   ├── reporting/
│   │   │   ├── ComparisonMatrix.tsx
│   │   │   ├── SystemicRankingCard.tsx
│   │   │   ├── BeforeAfterPanel.tsx
│   │   │   ├── DecisionSummary.tsx
│   │   │   └── RunHistoryDrawer.tsx
│   │   └── ui/
│   │       └── reusable accessible primitives
│   ├── services/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── formatters.ts
│   ├── store/
│   │   ├── appReducer.ts
│   │   └── selectors.ts
│   ├── styles/
│   │   └── globals.css
│   └── main.tsx
├── .env.example
└── vite.config.ts
```

Keep graph element conversion separate from the canvas component so visual states can be tested independently from Cytoscape initialization.

## 14. Interaction, loading, and failure specifications

- Every API action has an inline loading state and disabled duplicate action control.
- Use toast notifications for successful load/save actions and non-field-specific errors. Use inline errors for validation and missing prerequisites.
- Preserve a successful baseline when an attempted later request fails.
- If the backend becomes unavailable, retain rendered results but disable actions requiring the engine and offer a retry health check.
- Use optimistic UI only for local panel/tab selection, never for simulation result values or persistence confirmation.
- Confirm before replacing a loaded dataset or committing an intervention. Do not confirm ordinary read-only inspection or ranking requests.
- Provide keyboard support: Escape closes panels/modals, Enter submits focused forms where safe, graph selection is reachable by an alternate list/table view.

## 15. Responsive behavior

- Desktop (`>= 1280px`): canvas plus persistent inspector slide-over; policy cards in three columns; full matrix.
- Tablet: inspector becomes overlay; policy cards use two then one columns; graph controls collapse into a menu.
- Mobile: use one workspace at a time, full-screen inspector/modal, horizontal-scroll comparison table with sticky metric labels, and a list alternative for graph inspection. Do not attempt to make dense graph manipulation the only interaction mode on a small screen.

## 16. Phase-by-phase implementation schedule

### Phase 1 — foundation and API integration

1. Scaffold Vite/React/TypeScript/Tailwind application and environment configuration.
2. Implement typed API client and backend health monitor.
3. Add central state reducer/context and prerequisite gating.
4. Build header, workspace shell, notification layer, and basic empty/loading/error states.

**Acceptance:** health and demo network can be loaded; backend identifiers are retained in state; no simulation math exists in the frontend.

### Phase 2 — network and inspection

1. Transform `NetworkResponse` into Cytoscape elements.
2. Implement visual legend, layouts, filters, node/edge selection, and slide-over inspection.
3. Add accessible network table/list fallback.
4. Implement dataset upload preview/mapping and backend validation display.

**Acceptance:** every borrower and parallel relationship can be inspected; graph styles match the required legend.

### Phase 3 — shock and cascade

1. Build dynamic shock form and request validation.
2. Integrate baseline response with graph state classes.
3. Implement cascade summary, event timeline, event selection, and heatmap playback.

**Acceptance:** income, market, and geography fields adapt correctly; propagation events show backend pre/post states and units.

### Phase 4 — criticality and policy laboratory

1. Implement profile cards and criticality ranking table.
2. Implement Policy 1, 2, and 3 input/cards.
3. Render backend Policy 2 presets and prohibit selection of non-severable edge types.
4. Integrate common policy evaluation request and results.

**Acceptance:** all policies are evaluated against one run ID/baseline and Policy 2 shows N/A rather than an efficiency ratio.

### Phase 5 — comparison, final decision, and persistence

1. Implement comparison matrix/systemic rank cards.
2. Implement commit confirmation and final counterfactual display.
3. Implement before/after summary, JSON persistence, run-history listing, and replay handling.

**Acceptance:** displayed final values derive from the committed backend response; saved/replayed run state is identifiable and auditable.

### Phase 6 — quality assurance

1. Unit-test formatters, API error mapping, graph element conversion, and state transitions.
2. Component-test dynamic shock forms, profile selection, Policy 2 non-cash labelling, and prerequisite empty states.
3. End-to-end test demo load → shock → criticality → evaluation → commit → save against the FastAPI service.
4. Conduct keyboard, color-contrast, small-screen, and large-network usability checks.

## 17. Frontend acceptance checklist

- [ ] The graph never fabricates a visual numerical relationship strength.
- [ ] Normal, high-cash-stress, and distressed node states are distinguishable and labelled.
- [ ] All four edge mechanisms use the required visual treatments and remain inspectable.
- [ ] Shock form sends only valid backend `Shock` inputs.
- [ ] Cascade display separates impact/reach from escalation/distress.
- [ ] Criticality uses only the backend ranking and displays the active profile’s exact locked values.
- [ ] Policy cards state precisely which variable/edge set each policy changes.
- [ ] Policy 2 cannot include economic or geographic edges and is labelled as ₹0 direct cost/non-cash.
- [ ] Comparison shows the uncollapsed audit vector before or alongside any scalar rank.
- [ ] Final decision screen re-runs the selected counterfactual through the backend before showing final metrics.
- [ ] Saved runs are handled as reproducible backend records, not browser-only snapshots.
