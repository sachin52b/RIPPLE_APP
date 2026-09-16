import { useState } from 'react'
import type {
  CriticalityProfileName,
  InterventionEvaluationPayload,
  InterventionEvaluationResponse,
} from '../../services/types'

interface PolicyLabPanelProps {
  runId: string
  borrowerId: string
  profileName?: CriticalityProfileName
  isLoading: boolean
  result: InterventionEvaluationResponse | null
  onEvaluate: (payload: InterventionEvaluationPayload) => Promise<void>
}

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export function PolicyLabPanel({
  runId,
  borrowerId,
  profileName = 'BALANCED',
  isLoading,
  result,
  onEvaluate,
}: PolicyLabPanelProps) {
  const [monthlyRelief, setMonthlyRelief] = useState(500)
  const [reliefDuration, setReliefDuration] = useState(3)
  const [budgetCap, setBudgetCap] = useState(2000)

  const evaluate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await onEvaluate({
      run_id: runId,
      borrower_id: borrowerId,
      monthly_relief_amount: monthlyRelief,
      relief_duration: reliefDuration,
      M_cap: budgetCap,
      profile_name: profileName,
    })
  }

  return (
    <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Stage 2 — HOW</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">Intervention policy laboratory</h2>
        <p className="mt-1 text-sm text-slate-600">Testing counterfactuals for selected borrower <strong>{borrowerId}</strong> under the {profileName.toLowerCase()} policy profile.</p>
      </div>
      <form onSubmit={(event) => void evaluate(event)}>
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <PolicyCard title="Policy 1 — Repayment Relief" subtitle="Temporarily reduces only the selected borrower’s monthly repayment obligation.">
            <NumberField label="Monthly relief amount (r)" value={monthlyRelief} onChange={setMonthlyRelief} step={100} prefix="₹" />
            <NumberField label="Relief duration (d months)" value={reliefDuration} onChange={setReliefDuration} step={1} integer />
            {result ? <ResultLine label="Direct cost" value={currency.format(result.policy1.total_cost)} /> : null}
          </PolicyCard>

          <PolicyCard title="Policy 2 — Transmission Severance" subtitle="Changes controllable topology only; direct financial cost is ₹0.">
            <Preset name="Surgical" description="Targeted protection of a single key link with minimum network disruption." active={Boolean(result?.policy2.presets.Surgical)} edges={result?.policy2.presets.Surgical.severed_edges} />
            <Preset name="Optimal Shield" description="System-recommended edge severance set maximizing stress relief." active={Boolean(result?.policy2.presets['Optimal Shield'])} edges={result?.policy2.presets['Optimal Shield'].severed_edges} />
            <Preset name="Full Containment" description="Disables all severable outgoing joint-liability and formal-group links." active={Boolean(result?.policy2.presets['Full Containment'])} edges={result?.policy2.presets['Full Containment'].severed_edges} />
          </PolicyCard>

          <PolicyCard title="Policy 3 — Emergency Liquidity Support" subtitle="Increases only the selected borrower’s liquidity buffer.">
            <NumberField label="Maximum budget cap (M_cap)" value={budgetCap} onChange={setBudgetCap} step={100} prefix="₹" />
            {result ? <>
              <ResultLine label="Required liquidity (L*)" value={currency.format(result.policy3.required_liquidity_L_star)} />
              <ResultLine label="Actual injection (C_actual)" value={currency.format(result.policy3.actual_injection_C_actual)} />
              <ResultLine label="Remaining shortfall" value={currency.format(result.policy3.remaining_shortfall)} />
            </> : null}
          </PolicyCard>
        </div>
        <button type="submit" disabled={isLoading} className="mt-5 rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isLoading ? 'Evaluating policy counterfactuals…' : 'Evaluate Policies'}
        </button>
      </form>
    </section>
  )
}

function PolicyCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return <article className="rounded-lg border border-slate-200 p-4"><h3 className="font-semibold text-slate-900">{title}</h3><p className="mt-1 text-sm leading-5 text-slate-600">{subtitle}</p><div className="mt-4 space-y-3">{children}</div></article>
}

function NumberField({ label, value, onChange, step, prefix, integer = false }: { label: string; value: number; onChange: (value: number) => void; step: number; prefix?: string; integer?: boolean }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<div className="relative mt-1">{prefix ? <span className="absolute left-3 top-2 text-slate-500">{prefix}</span> : null}<input type="number" min="0" step={step} value={value} onChange={(event) => onChange(Math.max(0, integer ? Math.trunc(Number(event.target.value)) : Number(event.target.value)))} className={`block w-full rounded-md border border-slate-300 py-2 pr-3 text-sm shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 ${prefix ? 'pl-7' : 'pl-3'}`} /></div></label>
}

function Preset({ name, description, active, edges }: { name: string; description: string; active: boolean; edges?: string[] }) {
  return <div className={`rounded-md border p-3 ${active ? 'border-indigo-200 bg-indigo-50' : 'border-slate-200 bg-slate-50'}`}><p className="text-sm font-semibold text-slate-900">{name}</p><p className="mt-1 text-xs leading-5 text-slate-600">{description}</p>{active ? <p className="mt-2 text-xs font-medium text-indigo-700">Severed edges: {edges?.length ? edges.join(', ') : 'None'}</p> : null}</div>
}

function ResultLine({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between gap-3 text-sm"><span className="text-slate-500">{label}</span><strong className="text-slate-900">{value}</strong></div>
}
