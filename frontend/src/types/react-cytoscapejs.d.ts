declare module 'react-cytoscapejs' {
  import type { Core, ElementDefinition, StylesheetJson } from 'cytoscape'
  import type { CSSProperties, ComponentType } from 'react'

  interface CytoscapeComponentProps {
    elements: ElementDefinition[]
    stylesheet?: StylesheetJson
    cy?: (cy: Core) => void
    style?: CSSProperties
  }

  const CytoscapeComponent: ComponentType<CytoscapeComponentProps>
  export default CytoscapeComponent
}
