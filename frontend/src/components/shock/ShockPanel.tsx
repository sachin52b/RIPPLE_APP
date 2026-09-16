import { useState } from 'react'
import type { ShockCause, ShockPayload } from '../../services/types'

interface ShockPanelProps {
  networkId: string
  selectedBorrowerId: string
  onSubmit: (payload: ShockPayload) => Promise<void>
  isSubmitting?: boolean
}

const causeLabels: Record<ShockCause, string> = {
  income_shock: 'Borrower Income Shock',
  market_shock: 'Economic Source Shock',
  geographic_shock: 'Geographic Area Shock',
}

export function ShockPanel({
  networkId,
  selectedBorrowerId,
  onSubmit,
  isSubmitting = false,
}: ShockPanelProps) {
  const [cause, setCause] = useState<ShockCause>('income_shock')
  const [economicSourceId, setEconomicSourceId] = useState('M12')
  const [locationId, setLocationId] = useState('L12')
  const [severity, setSeverity] = useState(0.4)
  const [duration, setDuration] = useState(3)

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await onSubmit({
      network_id: networkId,
      shock_id: `shock-${crypto.randomUUID()}`,
      cause,
      target_borrower_id: cause === 'income_shock' ? selectedBorrowerId : null,
      economic_source_id: cause === 'market_shock' ? economicSourceId : null,
      location_id: cause === 'geographic_shock' ? locationId : null,
      severity,
      duration,
    })
  }

  return (
    <section className="border-t border-slate-200 pt-5">
      <h3 className="text-sm font-semibold text-slate-900">Shock simulator</h3>
      <form className="mt-3 space-y-4" onSubmit={(event) => void submit(event)}>
        <label className="block text-sm font-medium text-slate-700">
          Shock cause
          <select
            value={cause}
            onChange={(event) => setCause(event.target.value as ShockCause)}
            className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
          >
            {Object.entries(causeLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>

        {cause === 'income_shock' ? (
          <label className="block text-sm font-medium text-slate-700">
            Target borrower ID
            <input value={selectedBorrowerId} readOnly className="mt-1 block w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm text-slate-600" />
          </label>
        ) : null}
        {cause === 'market_shock' ? (
          <label className="block text-sm font-medium text-slate-700">
            Economic source ID
            <input value={economicSourceId} onChange={(event) => setEconomicSourceId(event.target.value)} required className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
          </label>
        ) : null}
        {cause === 'geographic_shock' ? (
          <label className="block text-sm font-medium text-slate-700">
            Location ID
            <input value={locationId} onChange={(event) => setLocationId(event.target.value)} required className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
          </label>
        ) : null}

        <label className="block text-sm font-medium text-slate-700">
          Severity: {Math.round(severity * 100)}%
          <input type="range" min="0" max="1" step="0.01" value={severity} onChange={(event) => setSeverity(Number(event.target.value))} className="mt-2 block w-full accent-indigo-600" />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Duration (months)
          <input type="number" min="0" step="1" value={duration} onChange={(event) => setDuration(Math.max(0, Math.trunc(Number(event.target.value))))} required className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
        </label>
        <button type="submit" disabled={isSubmitting} className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isSubmitting ? 'Running baseline simulation…' : 'Run Baseline Simulation'}
        </button>
      </form>
    </section>
  )
}
