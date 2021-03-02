from flask import Flask, request, jsonify
from flask_cors import CORS

from experiments.base import BaseExperiment

experiments_registry = dict()
for idx, cls in enumerate(BaseExperiment.__subclasses__()):
    experiments_registry[str(idx)] = cls()

app = Flask(__name__)
CORS(app)


def make_id_mappings(elements):
    id_to_index = {}
    index_to_id = {}
    for idx, element in enumerate(elements):
        id_ = element['id']
        id_to_index[id_] = idx
        index_to_id[idx] = id_
    assert (len(id_to_index) == len(elements))
    return id_to_index, index_to_id


def make_edges(edges, node_id_to_index):
    sources = []
    targets = []
    for edge in edges:
        sources.append(node_id_to_index[edge['source']])
        targets.append(node_id_to_index[edge['target']])
    return list(zip(sources, targets))


@app.route('/predict', methods=['POST'])
def predict():
    experiment_id = request.json['experiment_id']
    experiment: BaseExperiment = experiments_registry[experiment_id]
    nodes, edges = request.json['nodes'], request.json['edges']
    edge_id_to_index, edge_index_to_id = make_id_mappings(edges)
    node_id_to_index, node_index_to_id = make_id_mappings(nodes)
    # blue =1
    # red =2
    converted_edges = make_edges(edges, node_id_to_index)
    preds = experiment.predict_nodes(nodes, converted_edges)
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
    edge_id_to_index, edge_index_to_id = make_id_mappings(edges)
    node_id_to_index, node_index_to_id = make_id_mappings(nodes)
    converted_edges = make_edges(edges, node_id_to_index)
    attributions = experiment.explain_node(nodes, converted_edges, node_id_to_index[node_id], target, method)
    edge_id_to_attribution = {}
    for idx, attribution in enumerate(attributions.tolist()):
        edge_id_to_attribution[edge_index_to_id[idx]] = float('%.2e' % attribution)
    return edge_id_to_attribution


@app.route('/samples')
def samples():
    experiment_id = request.args.get('experiment_id')
    experiment: BaseExperiment = experiments_registry[experiment_id]
    graphs = experiment.sample_graphs()
    return jsonify(graphs)


@app.route('/experiments')
def experiments():
    result = {}
    for id, experiment in experiments_registry.items():
        result[id] = {'name': experiment.name,
                      'node_categories': experiment.node_categories(),
                      'style': experiment.custom_style()}
    return result


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
