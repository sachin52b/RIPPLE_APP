import type { InterventionEvaluationResponse, PolicyComparisonResult } from '../../services/types'

interface ComparisonMatrixTableProps {
  evaluation: InterventionEvaluationResponse
  onAdopt: (policy: 'policy1' | 'policy2' | 'policy3') => void
  isAdopting?: boolean
}

const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })

const policyOrder = [
  'Policy 1 — Repayment Relief',
  'Policy 2 — Transmission Severance',
  'Policy 3 — Emergency Liquidity Support',
]

function resultFor(results: PolicyComparisonResult[], name: string): PolicyComparisonResult {
  const result = results.find((item) => item.policy_name === name)
  if (!result) throw new Error(`Missing comparison result for ${name}`)
  return result
}

export function ComparisonMatrixTable({ evaluation, onAdopt, isAdopting = false }: ComparisonMatrixTableProps) {
  const results = policyOrder.map((name) => resultFor(evaluation.comparison, name))
  const metricRows: Array<[string, (result: PolicyComparisonResult) => string]> = [
    ['Avoided Distress (ΔD)', (result) => result.outcome_vector.delta_distressed.toFixed(2)],
    ['Systemic Stress Relief (ΔS)', (result) => result.outcome_vector.systemic_stress_relief.toFixed(4)],
    ['Cascade Reach Reduction (ΔR)', (result) => result.outcome_vector.reach_reduction.toFixed(2)],
    ['Direct Financial Cost', (result) => currency.format(result.outcome_vector.direct_financial_cost)],
    ['ΔCriticality', (result) => result.delta_criticality.toFixed(4)],
    ['Systemic Ranking', (result) => `#${result.systemic_rank}`],
    ['Financial Efficiency', (result) => typeof result.efficiency_phi === 'number' ? result.efficiency_phi.toFixed(6) : result.efficiency_phi],
  ]

  return (
    <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Comparison evidence</p>
      <h2 className="mt-1 text-lg font-semibold text-slate-900">Policy comparison matrix</h2>
      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse text-left text-sm">
          <thead className="border-y border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-3 py-3">Metric</th>{results.map((result) => <th key={result.policy_name} className="px-3 py-3">{result.policy_name.replace('Policy ', 'P')}{result.selected_preset ? ` — ${result.selected_preset}` : ''}</th>)}</tr></thead>
          <tbody>{metricRows.map(([label, formatter]) => <tr key={label} className="border-b border-slate-100"><th className="px-3 py-3 font-medium text-slate-700">{label}</th>{results.map((result) => <td key={result.policy_name} className="px-3 py-3 text-slate-900">{formatter(result)}</td>)}</tr>)}</tbody>
        </table>
      </div>
      <p className="mt-4 text-sm text-slate-600">Policy 2 is explicitly shown as a zero-direct-cost, non-cash intervention; no financial efficiency ratio is calculated for it.</p>
      <div className="mt-5 flex flex-wrap gap-3">
        {(['policy1', 'policy2', 'policy3'] as const).map((policy, index) => (
          <button key={policy} type="button" disabled={isAdopting} onClick={() => onAdopt(policy)} className="rounded-md border border-indigo-200 px-3 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-60">
            {isAdopting ? 'Running counterfactual…' : `Adopt & Run ${['Policy 1', 'Policy 2 Optimal Shield', 'Policy 3'][index]}`}
          </button>
        ))}
      </div>
    </section>
  )
}
