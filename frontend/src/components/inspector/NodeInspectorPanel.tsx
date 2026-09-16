import type { Borrower, BorrowerStressState } from '../../services/types'
import { ShockPanel } from '../shock/ShockPanel'
import type { ShockPayload } from '../../services/types'

interface NodeInspectorPanelProps {
  borrower: Borrower
  stressState?: BorrowerStressState
  networkId: string
  onRunShock: (payload: ShockPayload) => Promise<void>
  isSimulationRunning?: boolean
  onClose: () => void
}

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export function NodeInspectorPanel({ borrower, stressState, networkId, onRunShock, isSimulationRunning, onClose }: NodeInspectorPanelProps) {
  const fields = [
    ['Borrower ID', borrower.borrower_id],
    ['Group', borrower.group_id ?? 'Not assigned'],
    ['Location', borrower.location_id],
    ['Livelihood', borrower.livelihood_type.replaceAll('_', ' ')],
    ['Monthly income', currency.format(borrower.monthly_income)],
    ['Essential expense', currency.format(borrower.monthly_essential_expense)],
    ['Loan obligation', currency.format(borrower.monthly_loan_obligation)],
    ['Outstanding loan', currency.format(borrower.outstanding_loan)],
    ['Liquidity buffer', currency.format(borrower.liquidity_buffer)],
  ]

  return (
    <aside className="w-full max-w-md border-l border-slate-200 bg-white shadow-xl">
      <header className="flex items-start justify-between border-b border-slate-200 p-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Borrower inspection</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">{borrower.borrower_id}</h2>
        </div>
        <button type="button" onClick={onClose} className="rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100" aria-label="Close inspector">
          ×
        </button>
      </header>
      <div className="space-y-6 overflow-y-auto p-5">
        <dl className="space-y-3">
          {fields.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between gap-4 text-sm">
              <dt className="text-slate-500">{label}</dt>
              <dd className="text-right font-medium text-slate-900">{String(value)}</dd>
            </div>
          ))}
        </dl>
        <section className="rounded-lg bg-slate-50 p-4">
          <h3 className="text-sm font-semibold text-slate-900">Current stress state</h3>
          {stressState ? (
            <dl className="mt-3 space-y-2 text-sm">
              <StressField label="Cash stress" value={stressState.cash_stress} />
              <StressField label="Buffer stress" value={stressState.buffer_stress} />
              <StressField label="Effective stress" value={stressState.effective_stress} />
              <div className="flex items-center justify-between">
                <dt className="text-slate-500">Distress state</dt>
                <dd className={stressState.is_distressed ? 'font-semibold text-red-700' : 'font-semibold text-emerald-700'}>
                  {stressState.is_distressed ? 'Distressed' : 'Not distressed'}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="mt-2 text-sm text-slate-500">Run a shock simulation to view stress measures.</p>
          )}
        </section>
        <ShockPanel
          networkId={networkId}
          selectedBorrowerId={borrower.borrower_id}
          onSubmit={onRunShock}
          isSubmitting={isSimulationRunning}
        />
      </div>
    </aside>
  )
}

function StressField({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium text-slate-900">{value.toFixed(3)}</dd>
    </div>
  )
}
