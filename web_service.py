from collections import defaultdict

from flask import Flask, request, jsonify
from flask_cors import CORS

from experiments.base import BaseExperiment
# noinspection PyUnresolvedReferences
from experiments import *

experiments_registry = dict()
for idx, cls in enumerate(BaseExperiment.__subclasses__()):
    try:
        experiments_registry[str(idx)] = cls()
    except NotImplementedError:
        print(f'Ignoring experiment class {str(idx)} since the constructor is not implemented')

app = Flask(__name__)
CORS(app)


def make_node_mappings(elements):
    id_to_index = {}
    index_to_id = {}
    for idx, element in enumerate(elements):
        id_ = element['id']
        id_to_index[id_] = idx
        index_to_id[idx] = id_
    assert (len(id_to_index) == len(elements))
    return id_to_index, index_to_id


def make_edges(edges, node_id_to_index, is_directed):
    sources = []
    targets = []
    index_to_id = {}
    idx = 0
    for edge in edges:
        sources.append(node_id_to_index[edge['source']])
        targets.append(node_id_to_index[edge['target']])
        index_to_id[idx] = edge['id']
        idx += 1
        if not is_directed:
            targets.append(node_id_to_index[edge['source']])
            sources.append(node_id_to_index[edge['target']])
            index_to_id[idx] = edge['id']
            idx += 1
    return list(zip(sources, targets)), index_to_id


@app.route('/predict', methods=['POST'])
def predict():
    experiment_id = request.json['experiment_id']
    experiment: BaseExperiment = experiments_registry[experiment_id]
    nodes, edges = request.json['nodes'], request.json['edges']
    node_id_to_index, node_index_to_id = make_node_mappings(nodes)
    converted_edges, edge_index_to_id = make_edges(edges, node_id_to_index, experiment.is_directed())
    preds = experiment.predict(nodes, converted_edges)
    if experiment.is_graph_classification():
        return preds
    id_to_pred = {}
    for idx, result in enumerate(preds):
        id_to_pred[node_index_to_id[idx]] = result
    return id_to_pred


@app.route('/explain', methods=['POST'])
def explain():
    experiment_id = request.json['experiment_id']
    experiment: BaseExperiment = experiments_registry[experiment_id]
    nodes, edges = request.json['nodes'], request.json['edges']
    method = request.json['method']
    target = request.json['target']
    node_id = request.json['node_id']
    node_id_to_index, node_index_to_id = make_node_mappings(nodes)
    converted_edges, edge_index_to_id = make_edges(edges, node_id_to_index, experiment.is_directed())
    if experiment.is_graph_classification():
        attributions = experiment.explain_graph(nodes, converted_edges, target, method)
    else:
        attributions = experiment.explain_node(nodes, converted_edges, node_id_to_index[node_id], target, method)
    edge_id_to_attribution = defaultdict(float)

    # for undirected graphs we return the attribution of each edge as the sum of both directions
    for idx, attribution in enumerate(attributions.tolist()):
        edge_id_to_attribution[edge_index_to_id[idx]] += attribution
    edge_id_to_attribution = {k: float('%.2e' % value) for k, value in edge_id_to_attribution.items()}
    return edge_id_to_attribution


@app.route('/samples')
def samples():
    experiment_id = request.args.get('experiment_id')
    experiment: BaseExperiment = experiments_registry[experiment_id]
    graphs = experiment.sample_graphs()
    return jsonify(graphs)


METHODS_PRETTY_NAMES = {
    'sa': 'Edge Gradients',
    'ig': 'Edge IG',
    'sa_node': 'Node Gradients',
    'ig_node': 'Node IG',
    'gnnexplainer': 'GNN Explainer',
    'random': 'Random',
    'pagerank': 'Pagerank',
    'distance': 'Distance',
    'gradXact': 'gradXact',
    'pgmexplainer': 'PGMExplainer',
}


@app.route('/experiments')
def experiments():
    result = {}
    for id, experiment in experiments_registry.items():
        methods = experiment.get_explain_methods()
        methods = [{'text': METHODS_PRETTY_NAMES[method], 'value': method} for method in methods]
        result[id] = {'name': experiment.name,
                      'node_categories': experiment.node_categories(),
                      'style': experiment.custom_style(),
                      'directed': experiment.is_directed(),
                      'graph_classification': experiment.is_graph_classification(),
                      'methods': methods}
    return result


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
