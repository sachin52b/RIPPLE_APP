import type { Relationship } from '../../services/types'

interface EdgeInspectorPanelProps {
  relationship: Relationship
  onClose: () => void
}

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

function interpretation(relationship: Relationship): string {
  switch (relationship.super_mechanism) {
    case 'joint_liability':
      return 'A direct contractual financial relationship. Any transfer must be based on supplied contractual exposure or liability share.'
    case 'formal_group':
      return 'A formal lending-group connection that carries non-monetary group pressure; it does not automatically create debt.'
    case 'economic_exposure':
      return relationship.economic_source_id
        ? `A common economic source relationship for ${relationship.economic_source_id}. Monetary impact requires quantified source-level exposure.`
        : 'A shared economic exposure. No monetary impact can be inferred without a quantified source-level connection.'
    case 'geographic_exposure':
      return 'A shared geographic-context relationship; no arbitrary geographic edge-strength is applied.'
  }
}

export function EdgeInspectorPanel({ relationship, onClose }: EdgeInspectorPanelProps) {
  const fields = [
    ['Edge ID', relationship.edge_id],
    ['Direction', `${relationship.source} → ${relationship.target}`],
    ['Super-mechanism', relationship.super_mechanism.replaceAll('_', ' ')],
    ['Specific mechanism', relationship.specific_mechanism.replaceAll('_', ' ')],
    ['Contractual exposure', relationship.contractual_monthly_exposure === null ? 'Not supplied' : `${currency.format(relationship.contractual_monthly_exposure)} / month`],
    ['Liability share', relationship.liability_share === null ? 'Not supplied' : relationship.liability_share],
    ['Economic source', relationship.economic_source_id ?? 'Not supplied'],
  ]

  return (
    <aside className="w-full max-w-md border-l border-slate-200 bg-white shadow-xl">
      <header className="flex items-start justify-between border-b border-slate-200 p-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Relationship inspection</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">{relationship.edge_id}</h2>
        </div>
        <button type="button" onClick={onClose} className="rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100" aria-label="Close inspector">
          ×
        </button>
      </header>
      <div className="space-y-6 overflow-y-auto p-5">
        <dl className="space-y-3">
          {fields.map(([label, value]) => (
            <div key={label} className="flex items-start justify-between gap-4 text-sm">
              <dt className="text-slate-500">{label}</dt>
              <dd className="text-right font-medium capitalize text-slate-900">{String(value)}</dd>
            </div>
          ))}
        </dl>
        <section className="rounded-lg bg-slate-50 p-4">
          <h3 className="text-sm font-semibold text-slate-900">Interpretation</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">{interpretation(relationship)}</p>
        </section>
        <details className="rounded-lg border border-slate-200 p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-700">Metadata</summary>
          <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-slate-600">{JSON.stringify(relationship.metadata, null, 2)}</pre>
        </details>
      </div>
    </aside>
  )
}
