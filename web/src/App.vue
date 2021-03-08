<template>
  <div id="app" class="ui padded grid">
    <div class="ui animated button help" tabindex="0" v-on:click="help_visible=true">
      <div class="hidden content">Help</div>
      <div class="visible content">
        <i class="help icon"></i>
      </div>
    </div>
    <div class="row">
      <sui-dimmer active v-if="loading">
        <div class="ui text loader">Loading</div>
      </sui-dimmer>
      <div class="four wide column">
        <div class="ui segments">

          <div class="ui segment form">
            <div class="field">
              <label>Experiment</label>
              <sui-dropdown
                  placeholder="Experiment List"
                  selection
                  :options="experiments"
                  v-model="experiment_id"
              />
            </div>
          </div>
          <div class="ui segment form">
            <div class="field">
              <label>Explanation Method</label>
              <sui-dropdown
                  placeholder="Explanation Method"
                  selection
                  :options="explanation_methods"
                  v-model="explanation"
              />
            </div>
          </div>
          <div class="ui segment">
            <sui-accordion>
              <sui-accordion-title>
                <h4 class="ui header">
                  <sui-icon name="dropdown"/>
                  Sample Graphs
                </h4>
              </sui-accordion-title>
              <sui-accordion-content style="max-height: 200px;overflow: auto">
                <div class="ui fluid vertical mini menu">
                  <a class="item" :class="{active: current_sample && current_sample.name===sample.name}" v-for="sample in samples" v-bind:key="sample.name" v-on:click="setSample(sample)">
                    {{ sample.name }}
                  </a>
                </div>
              </sui-accordion-content>
            </sui-accordion>
          </div>

          <div class="ui segment form">
            <h4 class="ui header">Actions</h4>
            <div class="three fields">
              <div class="field">
                <div class="ui primary button tiny" v-on:click="predict">Refresh Explanation</div>
              </div>
              <div class="field">
                <div class="ui info button tiny" v-on:click="resetExplanation">Remove Explanation</div>
              </div>
              <div class="field">
                <div class="ui secondary button tiny" v-on:click="runLayout">Run Layout</div>
              </div>
            </div>
          </div>
          <div class="ui segment form" v-if="currentNode && options.length > 1">
            <div class="field">
              <label>Node Category</label>
              <sui-dropdown
                  placeholder="Category"
                  selection
                  :options="options"
                  v-model="currentNode.feat"
              />
            </div>
          </div>
          <div class="ui segment" v-if="is_graph_classification && graph_prediction">
            <h4 class="ui header">Model Prediction: {{ graph_prediction.text }}</h4>
            <h4 class="ui header" v-if="current_sample">Sample Label: {{ current_sample.label }}</h4>
          </div>
          <div class="ui segment" v-else>
            <h4 class="ui header">Node Labels are the model prediction</h4>
          </div>
        </div>

      </div>
      <div class="pusher twelve wide column blurring">
        <div id="cy">
        </div>
      </div>
      <div class="ui right wide sidebar vertical menu" :class="{visible:help_visible}">
        <a class="item" v-on:click="help_visible=false">
          Close <i class="close icon"></i>
        </a>
        <div class="item">
          <h4 class="ui header">How to modify the graph?</h4>
          <div class="ui list">
            <div class="item">Add nodes by right-clicking or tapping with two fingers on the canvas.</div>
            <div class="item">Draw edges by clicking on the red circle appearing on top of nodes.</div>
            <div class="item">Remove nodes/edges by right clicking or holding your click on the element.</div>
          </div>
        </div>
        <div class="item">
          <h4 class="ui header">How to see model explanation?</h4>
          <div class="ui list">
            <div class="item">Right/Long click on a node and choose the explain option</div>
            <div class="item">The number on each edge represent the importance of that edge for the current prediction
              determined by the explanation method. For undirected graphs, this is the sum of the values for both
              directions of the edge.
              Darker edges are more important.
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import 'semantic-ui-css/semantic.min.css'
import cytoscape from 'cytoscape'
import edgehandles from 'cytoscape-edgehandles'
import cxtmenu from 'cytoscape-cxtmenu'
import defaultStyle from '@/cytoscape_style'
import fcose from 'cytoscape-fcose'

import Vue from 'vue'
import SuiVue from 'semantic-ui-vue'

Vue.use(SuiVue)

let BACKEND_BASE_URI = 'http://localhost:5000'
if (process.env.NODE_ENV === 'production')
  BACKEND_BASE_URI = '' // use the same domain/port

cytoscape.use(edgehandles)
cytoscape.use(cxtmenu)
cytoscape.use(fcose)
export default {
  name: 'App',
  data () {
    return {
      currentNode: null,
      explanation: 'sa',
      help_visible: false,
      explainNodeId: null,
      samples: [],
      experiment_configs: null,
      experiments: [],
      experiment_id: null,
      graph_prediction: null,
      loading: true,
      current_sample: null
    }
  },
  computed: {
    options () {
      return this.experiment_configs[this.experiment_id].node_categories
    },
    is_graph_classification () {
      if (this.experiment_configs && this.experiment_id)
        return this.experiment_configs[this.experiment_id].graph_classification
      return false
    },
    explanation_methods () {
      if (this.experiment_configs && this.experiment_id)
        return this.experiment_configs[this.experiment_id].methods
      return []
    }
  },
  watch: {
    currentNode: {
      handler: function (newData, oldData) {
        console.log('data is changed', newData)
        let element = this.cy.nodes().filter(x => (x.data().id === newData.id))[0]
        for (let k in element.data()) {
          if (k === 'id') continue
          element.data(k, newData[k])
        }
        console.log('selected option', this.options.find(x => (x.value === newData['feat'])))
        if(this.options.length > 1)
          element.data('name', this.options.find(x => (x.value === newData['feat'])).text)
        this.predict()
      },
      deep: true
    },
    experiment_id: function () {
      this.getSamples()
      this.cy.style().resetToDefault()
      this.cy.remove('node')
      let experimentConfig = this.experiment_configs[this.experiment_id]
      let directedStyle = []
      if (experimentConfig.directed) {
        directedStyle.push(
            {
              selector: 'edge',
              style: {
                'target-arrow-color': '#000',
                'target-arrow-shape': 'triangle',
              }
            }
        )
      }
      this.cy.style().fromJson([].concat(directedStyle, defaultStyle, experimentConfig.style)).update()
    },
    explanation: function () {
      this.predict()
    }
  },
  methods: {
    runLayout () {
      let layout = this.cy.layout({ name: 'fcose', animate: false })
      layout.run()
    },

    filterGhostElements (elements) {
      return elements.filter(x => !x.hasClass('eh-ghost') && !x.hasClass('eh-handle'))
    },
    setSample (sample) {
      this.cy.remove('node')
      this.current_sample = sample
      sample.nodes.forEach((node, idx) => {
        this.cy.add(
            {
              data: { name: node.name, id: node.id, feat: node.feat },
              group: 'nodes'
            },)
      })
      sample.edges.forEach(([source, target]) => {
        this.cy.add(
            {
              data: { source: source, target: target },
              group: 'edges'
            },
        )
      })
      this.runLayout()
      this.predict()
    },
    getSamples () {
      let vm = this
      fetch(BACKEND_BASE_URI + '/samples?' + new URLSearchParams({
        experiment_id: this.experiment_id
      })).then(response => response.json()).then(function (data) {
        vm.samples = data
        if (vm.samples.length > 0)
          vm.setSample(vm.samples[0])
      })
    },
    getCurrentGraph () {
      console.log('raw nodes', this.cy.nodes())
      let nodes = this.filterGhostElements(this.cy.nodes()).map(x => x.data())
      nodes = nodes.map((data) => {return { id: data.id, feat: data.feat }})
      let edges = this.filterGhostElements(this.cy.edges()).map(x => x.data())
      edges = edges.map((data) => {
        return { source: data.source, target: data.target, id: data.id }
      })
      console.log('prediction nodes', nodes)
      console.log('prediction edges', edges)
      return { nodes, edges }
    },
    predict: async function () {
      if (this.experiment_id == null) return
      const { nodes, edges } = this.getCurrentGraph()
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nodes: nodes, edges: edges, experiment_id: this.experiment_id })
      }
      const response = await fetch(BACKEND_BASE_URI + '/predict', requestOptions)
      let data = await response.json()
      if (this.is_graph_classification) {
        this.graph_prediction = data
        this.explain(null, data.prediction)
        return
      }
      this.cy.nodes().forEach(function (el) {
        el.data('name', data[el.data('id')])
        el.data('pred', data[el.data('id')])
      })
      if (!(this.explainNodeId in data)) { // target node is removed
        this.explainNodeId = null
      }
      if (this.explainNodeId !== null) {
        let target = data[this.explainNodeId]
        this.explain(this.explainNodeId, target)
      } else {
        this.resetExplanation()
      }
    },
    resetExplanation () {
      console.log('resetting explanation')
      this.cy.edges().data('attribution', '')
      this.cy.edges().data('opacity', 1)
    },
    async explain (node_id, target) {
      const { nodes, edges } = this.getCurrentGraph()
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: nodes, edges: edges, node_id: node_id,
          method: this.explanation, target: target,
          experiment_id: this.experiment_id
        })
      }
      const response = await fetch(BACKEND_BASE_URI + '/explain', requestOptions)
      let data = await response.json()
      const max_value = Math.max(...Object.values(data).map(x => Math.abs(x)))
      console.log(data)
      this.cy.edges().forEach(function (el) {
        let id = el.data('id')
        el.data('attribution', data[id])
        let number = Math.abs(data[id]) / max_value
        if (isNaN(number))
          number = 0
        number = number * 0.9 + 0.1
        el.data('opacity', number)
      })
    }
  },
  mounted () {
    let vm = this

    fetch(BACKEND_BASE_URI + '/experiments').then(response => response.json()).then(function (data) {
      vm.experiments = Object.entries(data).map(([key, config]) => ({ value: key, text: config.name }))
      vm.experiment_configs = data
      vm.experiment_id = '0'
      vm.loading = false
    })

    function setupContextMenu (cy) {
      function getCommands (ele) {
        console.log('getCommands', ele)
        let removeCommand = {
          fillColor: 'rgb(219,156,81)', // optional: custom background color for item
          content: 'Remove Node', // html/text content to be displayed in the menu
          contentStyle: {}, // css key:value pairs to set the command's css in js if you want
          select: function (ele) { // a function to execute when the command is selected
            ele.remove()
            vm.predict()
          },
          enabled: true // whether the command is selectable
        }

        function changeFeat (target, text) {
          return function (ele) {
            ele.data('feat', target)
            ele.data('name', text)
            if (vm.currentNode && vm.currentNode.id === ele.data('id'))
              vm.currentNode = { ...ele.data() }
            vm.predict()
          }
        }

        if (ele.group() === 'nodes') {
          if (!('name' in ele.data())) return []
          let commands = [ // an array of commands to list in the menu or a function that returns the array

            removeCommand,
            {
              fillColor: 'rgb(142,246,102)', // optional: custom background color for item
              content: 'Explain', // html/text content to be displayed in the menu
              contentStyle: {}, // css key:value pairs to set the command's css in js if you want
              select: function (ele) { // a function to execute when the command is selected
                const node_id = ele.data('id')
                const target = ele.data('pred')
                vm.explainNodeId = node_id
                vm.explain(node_id, target)
              },
              enabled: true // whether the command is selectable
            }
          ]
          if (vm.experiment_id) {
            const categories = vm.experiment_configs[vm.experiment_id].node_categories
            let length = Object.keys(categories).length
            if (length > 1 && length < 8) {
              categories.forEach(category => {
                commands.push({
                  content: 'To ' + category.text,
                  select: changeFeat(category.value, category.text)
                })
              })
            }
          }
          return commands
        } else // edges
        {
          removeCommand.content = 'Remove Edge'
          return [removeCommand]
        }
      }

      let defaults = {
        menuRadius: function (ele) { return 100 }, // the outer radius (node center to the end of the menu) in pixels. It is added to the rendered size of the node. Can either be a number or function as in the example.
        selector: 'node,edge', // elements matching this Cytoscape.js selector will trigger cxtmenus
        commands: getCommands, // function( ele ){ return [ /*...*/ ] }, // a function that returns commands or a promise of commands
        fillColor: 'rgba(0, 0, 0, 0.75)', // the background colour of the menu
        activeFillColor: 'rgba(255,255,255,0.75)', // the colour used to indicate the selected command
        activePadding: 20, // additional size in pixels for the active command
        indicatorSize: 24, // the size in pixels of the pointer to the active command, will default to the node size if the node size is smaller than the indicator size,
        separatorWidth: 3, // the empty spacing in pixels between successive commands
        spotlightPadding: 4, // extra spacing in pixels between the element and the spotlight
        adaptativeNodeSpotlightRadius: false, // specify whether the spotlight radius should adapt to the node size
        minSpotlightRadius: 24, // the minimum radius in pixels of the spotlight (ignored for the node if adaptativeNodeSpotlightRadius is enabled but still used for the edge & background)
        maxSpotlightRadius: 38, // the maximum radius in pixels of the spotlight (ignored for the node if adaptativeNodeSpotlightRadius is enabled but still used for the edge & background)
        openMenuEvents: 'cxttapstart taphold', // space-separated cytoscape events that will open the menu; only `cxttapstart` and/or `taphold` work here
        itemColor: 'white', // the colour of text in the command's content
        itemTextShadowColor: 'transparent', // the text shadow colour of the command's content
        zIndex: 9999, // the z-index of the ui div
        atMouse: false // draw menu at mouse position
      }

      cy.cxtmenu(defaults)
    }

    let cy = cytoscape({

      container: document.getElementById('cy'), // container to render in

      elements: [],
      selectionType: 'single',

      layout: {
        name: 'fcose',
      }
    })
    cy.style().fromJson(defaultStyle).update()
    cy.edgehandles({ snap: true })

    cy.on('select', 'node', function (event) {
      let element = event.target
      console.log(element)
      vm.currentNode = { ...element.data() }
      console.log(vm.currentNode)
    })
    cy.on('cxttap', function (event) {
      console.log(event)
      cy.add(
          { // node a
            data: { name: '', feat: 0 },
            position: event.position,
            group: 'nodes'
          },
      )
      vm.predict()
    })
    setupContextMenu(cy)
    this.cy = cy
    cy.on('ehcomplete', () => {
      vm.predict()
    })
    this.predict()
  }
}
</script>

<style scoped>
#app {
  height: 100%;
}

#cy {
  background: whitesmoke;
  width: 100%;
  height: 100%;
  user-select: none;
}

.help.button {
  position: fixed;
  right: 0px;
  top: 30px;
  margin: -3px;
}
</style>
