import { useState } from 'react'
import type {
  CriticalityProfileName,
  CriticalityScore,
} from '../../services/types'

interface CriticalityPanelProps {
  rankings: CriticalityScore[]
  isLoading: boolean
  onIdentify: (profileName: CriticalityProfileName) => Promise<void>
  onSelectTarget: (borrowerId: string) => void
}

const profiles: Record<CriticalityProfileName, { label: string; description: string }> = {
  BALANCED: {
    label: 'Balanced Portfolio Health',
    description: 'Balances stopping severe distress with reducing widespread portfolio stress.',
  },
  STRICT: {
    label: 'Strict Distress Minimization',
    description: 'Prioritizes containing the raw count of materially distressed borrowers.',
  },
  AGGRESSIVE: {
    label: 'Aggressive Early Intervention',
    description: 'Aggressively targets widespread stress stabilization early.',
  },
}

export function CriticalityPanel({ rankings, isLoading, onIdentify, onSelectTarget }: CriticalityPanelProps) {
  const [profileName, setProfileName] = useState<CriticalityProfileName>('BALANCED')

  return (
    <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Stage 1 — WHO</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Criticality ranking</h2>
        </div>
        <button type="button" onClick={() => void onIdentify(profileName)} disabled={isLoading} className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isLoading ? 'Benchmarking borrowers…' : 'Identify Critical Borrowers'}
        </button>
      </div>
      <div className="mt-5 max-w-xl">
        <label className="block text-sm font-medium text-slate-700">
          MFI policy objective
          <select value={profileName} onChange={(event) => setProfileName(event.target.value as CriticalityProfileName)} disabled={isLoading} className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">
            {Object.entries(profiles).map(([value, profile]) => <option key={value} value={value}>{profile.label}</option>)}
          </select>
        </label>
        <p className="mt-2 text-sm text-slate-600">{profiles[profileName].description}</p>
      </div>
      {rankings.length ? (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse text-left text-sm">
            <thead className="border-y border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr><th className="px-3 py-3">Rank</th><th className="px-3 py-3">Borrower</th><th className="px-3 py-3">Criticality</th><th className="px-3 py-3">ΔD</th><th className="px-3 py-3">ΔS</th><th className="px-3 py-3" /></tr>
            </thead>
            <tbody>
              {rankings.map((score) => <CriticalityRow key={score.borrower_id} score={score} onSelectTarget={onSelectTarget} />)}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="mt-6 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">Choose an objective and run containment benchmarks to identify structural intervention targets.</p>
      )}
    </section>
  )
}

function CriticalityRow({ score, onSelectTarget }: { score: CriticalityScore; onSelectTarget: (borrowerId: string) => void }) {
  const isTop = score.rank === 1
  return (
    <tr className={`border-b border-slate-100 ${isTop ? 'bg-amber-50' : 'text-slate-700'}`}>
      <td className="px-3 py-3 font-semibold">#{score.rank}</td>
      <td className="px-3 py-3 font-medium text-slate-900">{score.borrower_id}{isTop ? <span className="ml-2 rounded-full bg-amber-200 px-2 py-0.5 text-xs font-semibold text-amber-900">#1 Critical Target</span> : null}</td>
      <td className="px-3 py-3">{score.criticality.toFixed(4)}</td>
      <td className="px-3 py-3">{score.delta_distressed.toFixed(2)}</td>
      <td className="px-3 py-3">{score.systemic_stress_delta.toFixed(4)}</td>
      <td className="px-3 py-3 text-right"><button type="button" onClick={() => onSelectTarget(score.borrower_id)} className="rounded-md border border-indigo-200 px-3 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-50">Select Target for Intervention</button></td>
    </tr>
  )
}
