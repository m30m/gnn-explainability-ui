const defaultStyle = [ // the stylesheet for the graph
  {
    selector: 'node[name]',
    style: {
      'background-color': '#666',
      'label': 'data(name)',
      'text-halign': 'center',
      'text-valign': 'center'
    }
  },
  {
    selector: 'node[name]:selected',
    style: {
      'border-width': 2,
      'border-color': 'black'
    }
  },
  {
    selector: 'edge',
    style: {
      'width': 3,
      'line-color': '#000',
      'target-arrow-color': '#000',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
    }
  },
  {
    selector: 'edge[opacity]',
    style: {
      'line-opacity': 'data(opacity)',
    }
  },
  {
    selector: 'edge[attribution]',
    style: {
      'label': 'data(attribution)',
      'text-rotation': 'autorotate',
      'text-margin-x': '10px',
      'text-margin-y': '10px'
    }
  },
  {
    selector: '.eh-handle',
    style: {
      'background-color': 'red',
      'width': 12,
      'height': 12,
      'shape': 'ellipse',
      'overlay-opacity': 0,
      'border-width': 12, // makes the handle easier to hit
      'border-opacity': 0
    }
  },
  {
    selector: '.eh-hover',
    style: {
      'background-color': 'red'
    }
  },
  {
    selector: '.eh-source',
    style: {
      'border-width': 2,
      'border-color': 'red'
    }
  },
  {
    selector: '.eh-target',
    style: {
      'border-width': 2,
      'border-color': 'red'
    }
  },
  {
    selector: '.eh-preview, .eh-ghost-edge',
    style: {
      'background-color': 'red',
      'line-color': 'red',
      'target-arrow-color': 'red',
      'source-arrow-color': 'red'
    }
  },
  {
    selector: '.eh-ghost-edge.eh-preview-active',
    style: {
      'opacity': 0
    }
  }
]

export default defaultStyle