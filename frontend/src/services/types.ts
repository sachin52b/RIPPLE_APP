export interface Borrower {
  borrower_id: string
  group_id: string | null
  location_id: string
  livelihood_type: string
  monthly_income: number
  monthly_essential_expense: number
  monthly_loan_obligation: number
  outstanding_loan: number
  liquidity_buffer: number
  income_stability: number | string
}

export type SuperMechanism =
  | 'joint_liability'
  | 'formal_group'
  | 'economic_exposure'
  | 'geographic_exposure'

export interface Relationship {
  edge_id: string
  super_mechanism: SuperMechanism
  specific_mechanism: string
  source: string
  target: string
  metadata: Record<string, unknown>
  contractual_monthly_exposure: number | null
  liability_share: number | null
  economic_source_type: string | null
  economic_source_id: string | null
}

export interface BorrowerStressState {
  post_shock_income: number
  required_amount: number
  monthly_deficit: number
  total_deficit: number
  cash_stress: number
  buffer_stress: number
  effective_stress: number
  is_distressed: boolean
}

export interface NetworkResponse {
  network_id: string
  dataset_id: string
  dataset_version: string
  node_count: number
  edge_count: number
  borrowers: Borrower[]
  relationships: Relationship[]
}

export type ShockCause = 'income_shock' | 'market_shock' | 'geographic_shock'

export interface ShockPayload {
  network_id: string
  shock_id: string
  cause: ShockCause
  target_borrower_id?: string | null
  economic_source_id?: string | null
  location_id?: string | null
  severity: number
  duration: number
}

export interface PropagationEvent {
  event_id: string
  source_borrower: string
  target_borrower: string
  super_mechanism: string
  specific_mechanism: string
  pre_state_target: Record<string, unknown>
  impact_type: string
  impact_amount_or_delta: number
  post_state_target: Record<string, unknown>
}

export interface SimulationStateResponse {
  run_id: string
  shock_config: Omit<ShockPayload, 'network_id'>
  borrower_states: Record<string, BorrowerStressState>
  extra_monthly_obligations: Record<string, number>
  group_pressure_deltas: Record<string, number[]>
  income_losses: Record<string, number>
  activated_sources: string[]
  reached_nodes: string[]
  propagation_events: PropagationEvent[]
  summary: Record<string, unknown>
}

export type CriticalityProfileName = 'STRICT' | 'BALANCED' | 'AGGRESSIVE'

export interface CriticalityScore {
  borrower_id: string
  rank: number
  criticality: number
  delta_distressed: number
  systemic_stress_delta: number
  bounded_stress_component: number
}

export interface CriticalityRequestPayload {
  run_id: string
  profile_name: CriticalityProfileName
}

export interface CriticalityResponse {
  run_id: string
  profile_name: CriticalityProfileName
  rankings: CriticalityScore[]
}

export interface OutcomeVector {
  delta_distressed: number
  systemic_stress_relief: number
  reach_reduction: number
  direct_financial_cost: number
}

export interface Policy2Preset {
  name: 'Surgical' | 'Optimal Shield' | 'Full Containment'
  severed_edges: string[]
  cost: number
  internal_score: number
  simulation_state: SimulationStateResponse
}

export interface InterventionEvaluationPayload {
  run_id: string
  borrower_id: string
  monthly_relief_amount: number
  relief_duration: number
  M_cap: number
  profile_name: CriticalityProfileName
}

export interface InterventionEvaluationResponse {
  run_id: string
  target_borrower_id: string
  policy1: {
    borrower_id: string
    monthly_relief_amount: number
    relief_duration: number
    total_cost: number
    simulation_state: SimulationStateResponse
  }
  policy2: {
    borrower_id: string
    eligible_edges: string[]
    presets: Record<'Surgical' | 'Optimal Shield' | 'Full Containment', Policy2Preset>
  }
  policy3: {
    borrower_id: string
    required_liquidity_L_star: number
    M_cap: number
    actual_injection_C_actual: number
    remaining_shortfall: number
    total_cost: number
    simulation_state: SimulationStateResponse
  }
  comparison: PolicyComparisonResult[]
}

export interface PolicyComparisonResult {
  policy_name: string
  selected_preset: string | null
  outcome_vector: OutcomeVector
  delta_criticality: number
  efficiency_phi: number | 'N/A — non-cash intervention'
  systemic_rank: number
  summary_text: string
}

export type CommittablePolicy = 'policy1' | 'policy2' | 'policy3'

export interface CommitInterventionPayload {
  run_id: string
  policy: CommittablePolicy
  policy2_preset?: 'Surgical' | 'Optimal Shield' | 'Full Containment'
}

export interface DecisionSummary {
  selected_policy: string
  selected_preset: string | null
  target_borrower_id: string
  before: {
    distressed_borrowers: number
    systemic_stress: number
    cascade_reach: number
  }
  after: {
    distressed_borrowers: number
    systemic_stress: number
    cascade_reach: number
  }
  outcome_vector: OutcomeVector
  delta_criticality: number
  efficiency_phi: number | 'N/A — non-cash intervention'
  systemic_rank: number
  summary_text: string
}

export interface CommitInterventionResponse {
  run_id: string
  selected_intervention: Record<string, unknown>
  final_state: SimulationStateResponse
  outcome_vector: OutcomeVector
  decision_summary: DecisionSummary
}

export interface SaveRunPayload {
  run_id: string
  filename?: string
}

export interface SaveRunResponse {
  run_id: string
  filepath: string
  record: Record<string, unknown>
}

export interface HealthResponse {
  status: 'ok'
  parameters: Record<string, unknown>
}

export interface DatasetUploadPayload {
  borrowers: Borrower[]
  relationships: Relationship[]
  dataset_id?: string
  dataset_version?: string
}
