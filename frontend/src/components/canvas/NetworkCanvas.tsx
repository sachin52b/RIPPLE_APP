import CytoscapeComponent from 'react-cytoscapejs'
import type { Core, ElementDefinition, StylesheetJson } from 'cytoscape'
import type {
  BorrowerStressState,
  NetworkResponse,
  Relationship,
} from '../../services/types'

interface NetworkCanvasProps {
  network: NetworkResponse
  stressStates?: Record<string, BorrowerStressState>
  onNodeSelect: (borrowerId: string) => void
  onEdgeSelect: (relationship: Relationship) => void
}

const stylesheet: StylesheetJson = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      color: '#e2e8f0',
      'font-size': 11,
      'font-weight': 600,
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': '#475569',
      width: 48,
      height: 48,
      'border-width': 2,
      'border-color': '#64748b',
    },
  },
  {
    selector: 'node.high-cash-stress',
    style: {
      'background-color': '#f59e0b',
      'border-color': '#fbbf24',
      color: '#1e293b',
    },
  },
  {
    selector: 'node.material-distress',
    style: {
      'background-color': '#dc2626',
      'border-color': '#f87171',
      color: '#fff',
    },
  },
  {
    selector: 'edge',
    style: {
      width: 3,
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'target-arrow-color': 'data(color)',
      'line-color': 'data(color)',
      opacity: 0.9,
    },
  },
  {
    selector: 'edge.joint-liability',
    style: { 'line-style': 'solid', 'line-color': '#dc2626', 'target-arrow-color': '#dc2626' },
  },
  {
    selector: 'edge.formal-group',
    style: { 'line-style': 'dashed', 'line-color': '#2563eb', 'target-arrow-color': '#2563eb' },
  },
  {
    selector: 'edge.economic-exposure',
    style: { 'line-style': 'dotted', 'line-color': '#16a34a', 'target-arrow-color': '#16a34a' },
  },
  {
    selector: 'edge.geographic-exposure',
    style: {
      'line-style': 'dashed',
      'line-dash-pattern': [10, 4, 2, 4],
      'line-color': '#ea580c',
      'target-arrow-color': '#ea580c',
    },
  },
  {
    selector: ':selected',
    style: { 'overlay-color': '#6366f1', 'overlay-opacity': 0.2, 'overlay-padding': 8 },
  },
]

const mechanismClass: Record<Relationship['super_mechanism'], string> = {
  joint_liability: 'joint-liability',
  formal_group: 'formal-group',
  economic_exposure: 'economic-exposure',
  geographic_exposure: 'geographic-exposure',
}

function nodeClass(stress?: BorrowerStressState): string {
  if (stress?.is_distressed || (stress?.effective_stress ?? 0) >= 0.3) {
    return 'material-distress'
  }
  if ((stress?.cash_stress ?? 0) >= 0.35) {
    return 'high-cash-stress'
  }
  return ''
}

export function NetworkCanvas({
  network,
  stressStates,
  onNodeSelect,
  onEdgeSelect,
}: NetworkCanvasProps) {
  const elements: ElementDefinition[] = [
    ...network.borrowers.map((borrower) => ({
      data: { id: borrower.borrower_id, label: borrower.borrower_id },
      classes: nodeClass(stressStates?.[borrower.borrower_id]),
    })),
    ...network.relationships.map((relationship) => ({
      data: {
        id: relationship.edge_id,
        source: relationship.source,
        target: relationship.target,
        relationship,
      },
      classes: mechanismClass[relationship.super_mechanism],
    })),
  ]

  const onCy = (cy: Core) => {
    cy.on('tap', 'node', (event) => onNodeSelect(event.target.id()))
    cy.on('tap', 'edge', (event) => {
      const relationship = event.target.data('relationship') as Relationship
      onEdgeSelect(relationship)
    })
    cy.layout({ name: 'cose', animate: false, padding: 48 }).run()
  }

  return (
    <section className="relative h-[calc(100vh-185px)] min-h-[520px] overflow-hidden rounded-xl border border-slate-200 bg-slate-900 shadow-sm">
      <CytoscapeComponent
        elements={elements}
        stylesheet={stylesheet}
        cy={onCy}
        style={{ width: '100%', height: '100%' }}
      />
      <aside className="absolute bottom-4 left-4 rounded-lg border border-slate-700 bg-slate-950/95 p-3 text-xs text-slate-100 shadow-lg">
        <p className="mb-2 font-semibold text-white">Network legend</p>
        <div className="grid grid-cols-2 gap-x-5 gap-y-2">
          <LegendItem color="bg-slate-500" label="Normal / safe" />
          <LegendItem color="bg-amber-500" label="Cash stress ≥ 0.35" />
          <LegendItem color="bg-red-600" label="Material distress" />
          <LegendLine color="bg-red-600" label="Joint liability" />
          <LegendLine color="border-t-2 border-dashed border-blue-500" label="Formal group" />
          <LegendLine color="border-t-2 border-dotted border-green-500" label="Economic exposure" />
          <LegendLine color="border-t-2 border-dashed border-orange-500" label="Geographic exposure" />
        </div>
      </aside>
    </section>
  )
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-2">
      <span className={`h-3 w-3 rounded-full ${color}`} />
      {label}
    </span>
  )
}

function LegendLine({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-2">
      <span className={`w-5 border-t-2 ${color}`} />
      {label}
    </span>
  )
}
