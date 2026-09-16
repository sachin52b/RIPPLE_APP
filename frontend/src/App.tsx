import { useEffect, useMemo, useState } from 'react'
import { NetworkCanvas } from './components/canvas/NetworkCanvas'
import { EdgeInspectorPanel } from './components/inspector/EdgeInspectorPanel'
import { NodeInspectorPanel } from './components/inspector/NodeInspectorPanel'
import { CascadeAuditModal } from './components/shock/CascadeAuditModal'
import { CriticalityPanel } from './components/interventions/CriticalityPanel'
import { PolicyLabPanel } from './components/interventions/PolicyLabPanel'
import { ComparisonMatrixTable } from './components/reporting/ComparisonMatrixTable'
import { FinalResultPanel } from './components/reporting/FinalResultPanel'
import { checkHealth, commitIntervention, evaluatePolicies, fetchCriticalityRankings, loadDemoNetwork, saveRun, simulateShock } from './services/api'
import type {
  Borrower,
  CriticalityProfileName,
  CriticalityScore,
  CommitInterventionResponse,
  CommittablePolicy,
  InterventionEvaluationPayload,
  InterventionEvaluationResponse,
  NetworkResponse,
  Relationship,
  ShockPayload,
  SimulationStateResponse,
} from './services/types'

function App() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null)
  const [network, setNetwork] = useState<NetworkResponse | null>(null)
  const [selectedBorrower, setSelectedBorrower] = useState<Borrower | null>(null)
  const [selectedRelationship, setSelectedRelationship] = useState<Relationship | null>(null)
  const [baselineState, setBaselineState] = useState<SimulationStateResponse | null>(null)
  const [isAuditOpen, setIsAuditOpen] = useState(false)
  const [criticalityRankings, setCriticalityRankings] = useState<CriticalityScore[]>([])
  const [isCriticalityLoading, setIsCriticalityLoading] = useState(false)
  const [selectedInterventionTarget, setSelectedInterventionTarget] = useState<string | null>(null)
  const [policyEvaluation, setPolicyEvaluation] = useState<InterventionEvaluationResponse | null>(null)
  const [isPolicyEvaluationLoading, setIsPolicyEvaluationLoading] = useState(false)
  const [finalResult, setFinalResult] = useState<CommitInterventionResponse | null>(null)
  const [isCommitting, setIsCommitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoadingDemo, setIsLoadingDemo] = useState(false)
  const [isSimulationRunning, setIsSimulationRunning] = useState(false)

  useEffect(() => {
    void checkHealth()
      .then(() => setIsOnline(true))
      .catch(() => setIsOnline(false))
  }, [])

  const borrowersById = useMemo(
    () => new Map(network?.borrowers.map((borrower) => [borrower.borrower_id, borrower])),
    [network],
  )

  const loadDemoDataset = async () => {
    setIsLoadingDemo(true)
    setError(null)
    try {
      const response = await loadDemoNetwork()
      setNetwork(response)
      setSelectedBorrower(null)
      setSelectedRelationship(null)
      setBaselineState(null)
      setCriticalityRankings([])
      setSelectedInterventionTarget(null)
      setPolicyEvaluation(null)
      setFinalResult(null)
      setIsOnline(true)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load the demo dataset.')
      setIsOnline(false)
    } finally {
      setIsLoadingDemo(false)
    }
  }

  const runBaselineSimulation = async (payload: ShockPayload) => {
    setIsSimulationRunning(true)
    setError(null)
    try {
      const response = await simulateShock(payload)
      setBaselineState(response)
      setCriticalityRankings([])
      setSelectedInterventionTarget(null)
      setPolicyEvaluation(null)
      setFinalResult(null)
      setIsAuditOpen(true)
      setIsOnline(true)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to run the baseline simulation.')
      setIsOnline(false)
    } finally {
      setIsSimulationRunning(false)
    }
  }

  const evaluatePolicyCounterfactuals = async (payload: InterventionEvaluationPayload) => {
    setIsPolicyEvaluationLoading(true)
    setError(null)
    try {
      const response = await evaluatePolicies(payload)
      setPolicyEvaluation(response)
      setIsOnline(true)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to evaluate intervention policies.')
      setIsOnline(false)
    } finally {
      setIsPolicyEvaluationLoading(false)
    }
  }

  const adoptAndRunCounterfactual = async (policy: CommittablePolicy) => {
    if (!baselineState) return
    setIsCommitting(true)
    setError(null)
    try {
      const response = await commitIntervention({
        run_id: baselineState.run_id,
        policy,
        ...(policy === 'policy2' ? { policy2_preset: 'Optimal Shield' } : {}),
      })
      setFinalResult(response)
      setIsOnline(true)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to commit the selected intervention.')
      setIsOnline(false)
    } finally {
      setIsCommitting(false)
    }
  }

  const identifyCriticalBorrowers = async (profileName: CriticalityProfileName) => {
    if (!baselineState) return
    setIsCriticalityLoading(true)
    setError(null)
    try {
      const response = await fetchCriticalityRankings({
        run_id: baselineState.run_id,
        profile_name: profileName,
      })
      setCriticalityRankings(response.rankings)
      setIsOnline(true)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to calculate criticality rankings.')
      setIsOnline(false)
    } finally {
      setIsCriticalityLoading(false)
    }
  }

  const healthLabel = isOnline === true ? 'Online' : isOnline === false ? 'Offline' : 'Checking'
  const healthStyle = isOnline === true ? 'bg-emerald-100 text-emerald-800' : isOnline === false ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-600'
  const healthDotStyle = isOnline === true ? 'bg-emerald-500' : isOnline === false ? 'bg-rose-500' : 'bg-slate-400'

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Financial Contagion &amp; Resilience Lab</h1>
            <p className="mt-1 text-sm text-slate-500">Deterministic borrower network simulation</p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium ${healthStyle}`} aria-live="polite">
              <span className={`h-2 w-2 rounded-full ${healthDotStyle}`} />
              {healthLabel}
            </span>
            <button type="button" onClick={() => void loadDemoDataset()} disabled={isLoadingDemo} className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60">
              {isLoadingDemo ? 'Loading demo…' : 'Load Demo Dataset'}
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-[1600px] px-6 py-6">
        {error ? <div className="mb-5 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div> : null}
        {network ? (
          <>
            <div className="flex gap-0 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="min-w-0 flex-1 p-4">
                <div className="mb-3 flex items-center justify-between text-sm text-slate-600">
                  <span><strong className="text-slate-900">{network.node_count}</strong> borrowers · <strong className="text-slate-900">{network.edge_count}</strong> relationships</span>
                  <span className="font-mono text-xs">{network.dataset_id} v{network.dataset_version}</span>
                </div>
                <NetworkCanvas
                  network={network}
                  stressStates={finalResult?.final_state.borrower_states ?? baselineState?.borrower_states}
                  onNodeSelect={(borrowerId) => {
                    setSelectedBorrower(borrowersById.get(borrowerId) ?? null)
                    setSelectedRelationship(null)
                  }}
                  onEdgeSelect={(relationship) => {
                    setSelectedRelationship(relationship)
                    setSelectedBorrower(null)
                  }}
                />
              </div>
              {selectedBorrower ? (
                <NodeInspectorPanel
                  borrower={selectedBorrower}
                  stressState={baselineState?.borrower_states[selectedBorrower.borrower_id]}
                  networkId={network.network_id}
                  onRunShock={runBaselineSimulation}
                  isSimulationRunning={isSimulationRunning}
                  onClose={() => setSelectedBorrower(null)}
                />
              ) : null}
              {selectedRelationship ? <EdgeInspectorPanel relationship={selectedRelationship} onClose={() => setSelectedRelationship(null)} /> : null}
            </div>
            {baselineState ? (
              <CriticalityPanel
                rankings={criticalityRankings}
                isLoading={isCriticalityLoading}
                onIdentify={identifyCriticalBorrowers}
                onSelectTarget={(borrowerId) => {
                  setSelectedInterventionTarget(borrowerId)
                  setPolicyEvaluation(null)
                  setFinalResult(null)
                  setSelectedBorrower(borrowersById.get(borrowerId) ?? null)
                  setSelectedRelationship(null)
                }}
              />
            ) : null}
            {baselineState && selectedInterventionTarget ? (
              <>
                <p className="mt-3 text-sm font-medium text-indigo-700">Selected intervention target: {selectedInterventionTarget}</p>
                <PolicyLabPanel
                  runId={baselineState.run_id}
                  borrowerId={selectedInterventionTarget}
                  isLoading={isPolicyEvaluationLoading}
                  result={policyEvaluation}
                  onEvaluate={evaluatePolicyCounterfactuals}
                />
                {policyEvaluation ? <ComparisonMatrixTable evaluation={policyEvaluation} onAdopt={adoptAndRunCounterfactual} isAdopting={isCommitting} /> : null}
                {finalResult ? <FinalResultPanel result={finalResult} onPersist={() => saveRun({ run_id: finalResult.run_id })} /> : null}
              </>
            ) : null}
          </>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-600 shadow-sm">
            <p className="font-medium text-slate-900">No network loaded</p>
            <p className="mt-2 text-sm">Load the demo dataset to render and inspect the borrower network.</p>
          </div>
        )}
      </section>
      {baselineState && isAuditOpen ? <CascadeAuditModal baseline={baselineState} onClose={() => setIsAuditOpen(false)} /> : null}
    </main>
  )
}

export default App
