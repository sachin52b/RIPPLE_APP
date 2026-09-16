import type { PropagationEvent, SimulationStateResponse } from '../../services/types'

interface CascadeAuditModalProps {
  baseline: SimulationStateResponse
  onClose: () => void
}

function totalSystemicStress(baseline: SimulationStateResponse): number {
  return Object.values(baseline.borrower_states).reduce(
    (total, stress) => total + stress.effective_stress,
    0,
  )
}

function totalDistressed(baseline: SimulationStateResponse): number {
  return Object.values(baseline.borrower_states).filter(
    (stress) => stress.is_distressed,
  ).length
}

function eventImpact(event: PropagationEvent): string {
  const amount = event.impact_amount_or_delta
  if (event.impact_type === 'group_pressure') {
    return `ΔStress ${amount.toFixed(4)}`
  }
  if (event.impact_type === 'extra_monthly_obligation') {
    return `₹${amount.toLocaleString('en-IN')} / month`
  }
  return `₹${amount.toLocaleString('en-IN')} / month income loss`
}

export function CascadeAuditModal({ baseline, onClose }: CascadeAuditModalProps) {
  const shock = baseline.shock_config
  const initialSource =
    shock.target_borrower_id ?? shock.economic_source_id ?? shock.location_id ?? '—'
  const stress = totalSystemicStress(baseline)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" role="dialog" aria-modal="true" aria-labelledby="cascade-audit-title">
      <section className="flex max-h-[85vh] w-full max-w-6xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl">
        <header className="flex items-start justify-between border-b border-slate-200 p-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Baseline cascade complete</p>
            <h2 id="cascade-audit-title" className="mt-1 text-xl font-semibold text-slate-900">Cascade audit trail</h2>
          </div>
          <button type="button" onClick={onClose} className="rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100" aria-label="Close cascade audit">×</button>
        </header>
        <div className="grid grid-cols-2 gap-3 border-b border-slate-200 bg-slate-50 p-5 md:grid-cols-4">
          <Metric label="Initial source" value={initialSource} />
          <Metric label="Total distressed" value={String(totalDistressed(baseline))} />
          <Metric label="Cascade reach" value={String(baseline.reached_nodes.length)} />
          <Metric label="Total systemic stress delta" value={stress.toFixed(4)} />
        </div>
        <div className="overflow-auto p-6">
          <h3 className="mb-3 text-sm font-semibold text-slate-900">Propagation events</h3>
          {baseline.propagation_events.length ? (
            <table className="w-full min-w-[720px] border-collapse text-left text-sm">
              <thead className="border-y border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3">Path</th>
                  <th className="px-3 py-3">Super-mechanism</th>
                  <th className="px-3 py-3">Specific mechanism</th>
                  <th className="px-3 py-3">Numerical impact</th>
                </tr>
              </thead>
              <tbody>
                {baseline.propagation_events.map((event) => (
                  <tr key={event.event_id} className="border-b border-slate-100 text-slate-700">
                    <td className="px-3 py-3 font-medium text-slate-900">{event.source_borrower} → {event.target_borrower}</td>
                    <td className="px-3 py-3">{event.super_mechanism.replaceAll('_', ' ')}</td>
                    <td className="px-3 py-3">{event.specific_mechanism.replaceAll('_', ' ')}</td>
                    <td className="px-3 py-3">{eventImpact(event)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">No propagation events occurred; the shock was contained at its initially affected borrower(s).</p>
          )}
        </div>
      </section>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  )
}
