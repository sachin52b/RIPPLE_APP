import { useState } from 'react'
import type { CommitInterventionResponse, SaveRunResponse } from '../../services/types'

interface FinalResultPanelProps {
  result: CommitInterventionResponse
  onPersist: () => Promise<SaveRunResponse>
}

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export function FinalResultPanel({ result, onPersist }: FinalResultPanelProps) {
  const [isPersisting, setIsPersisting] = useState(false)
  const [savedPath, setSavedPath] = useState<string | null>(null)
  const summary = result.decision_summary
  const vector = result.outcome_vector
  const parameters = Object.entries(result.selected_intervention)
    .filter(([key]) => !['policy', 'borrower_id', 'profile_name'].includes(key))
    .map(([key, value]) => `${key.replaceAll('_', ' ')}: ${Array.isArray(value) ? value.join(', ') : String(value)}`)

  const persist = async () => {
    setIsPersisting(true)
    try {
      const saved = await onPersist()
      setSavedPath(saved.filepath)
    } finally {
      setIsPersisting(false)
    }
  }

  return (
    <section className="mt-6 rounded-xl border border-emerald-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">View G — Final result</p>
      <h2 className="mt-1 text-lg font-semibold text-slate-900">Final counterfactual outcome</h2>
      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse text-left text-sm">
          <thead className="border-y border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-3 py-3">Metric</th><th className="px-3 py-3">Baseline</th><th className="px-3 py-3">Final</th></tr></thead>
          <tbody>
            <MetricRow label="Distressed Borrowers" before={summary.before.distressed_borrowers} after={summary.after.distressed_borrowers} />
            <MetricRow label="Cascade Reach" before={summary.before.cascade_reach} after={summary.after.cascade_reach} />
            <MetricRow label="Systemic Stress" before={summary.before.systemic_stress.toFixed(4)} after={summary.after.systemic_stress.toFixed(4)} />
          </tbody>
        </table>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard label="ΔD" value={vector.delta_distressed.toFixed(2)} />
        <MetricCard label="ΔS" value={vector.systemic_stress_relief.toFixed(4)} />
        <MetricCard label="ΔR" value={vector.reach_reduction.toFixed(2)} />
        <MetricCard label="Cost" value={currency.format(vector.direct_financial_cost)} />
        <MetricCard label="ΔCriticality" value={summary.delta_criticality.toFixed(4)} />
      </div>
      <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-5">
        <h3 className="text-sm font-semibold text-slate-900">Decision summary</h3>
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
          <SummaryField label="Selected policy" value={summary.selected_policy} />
          <SummaryField label="Target borrower" value={summary.target_borrower_id} />
          <SummaryField label="Specific parameters" value={parameters.length ? parameters.join(' · ') : 'No additional parameters'} />
          <SummaryField label="Total cost" value={currency.format(vector.direct_financial_cost)} />
          <SummaryField label="Avoided distress" value={vector.delta_distressed.toFixed(2)} />
        </dl>
        <p className="mt-4 text-sm leading-6 text-slate-600">{summary.summary_text}</p>
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button type="button" onClick={() => void persist()} disabled={isPersisting} className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isPersisting ? 'Persisting run…' : 'Persist & Export Run'}
        </button>
        {savedPath ? <span className="text-sm text-emerald-700">Saved reproducible run: {savedPath}</span> : null}
      </div>
    </section>
  )
}

function MetricRow({ label, before, after }: { label: string; before: string | number; after: string | number }) {
  return <tr className="border-b border-slate-100"><th className="px-3 py-3 font-medium text-slate-700">{label}</th><td className="px-3 py-3 text-slate-900">{before}</td><td className="px-3 py-3 font-semibold text-emerald-800">{after}</td></tr>
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg border border-slate-200 p-3"><p className="text-xs font-medium text-slate-500">{label}</p><p className="mt-1 font-semibold text-slate-900">{value}</p></div>
}

function SummaryField({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-slate-500">{label}</dt><dd className="mt-1 font-medium text-slate-900">{value}</dd></div>
}
