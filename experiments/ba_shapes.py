import json

import networkx as nx
import torch
import torch.nn.functional as F
from torch.nn import Sequential, Linear, ReLU
from torch_geometric.nn import GNNExplainer, GINConv, MessagePassing, GCNConv, GraphConv

from experiments.base import BaseExperiment


class Net(torch.nn.Module):
    def __init__(self, num_node_features, num_classes, num_layers, concat_features, conv_type):
        super(Net, self).__init__()
        dim = 32
        self.convs = torch.nn.ModuleList()
        if conv_type == 'GCNConv':
            conv_class = GCNConv
            kwargs = {'add_self_loops': False}
        elif conv_type == 'GraphConv':
            conv_class = GraphConv
            kwargs = {}
        else:
            raise RuntimeError(f"conv_type {conv_type} not supported")

        self.convs.append(conv_class(num_node_features, dim, **kwargs))
        for i in range(num_layers - 1):
            self.convs.append(conv_class(dim, dim, **kwargs))
        self.concat_features = concat_features
        if concat_features:
            self.fc = Linear(dim * num_layers + num_node_features, num_classes)
        else:
            self.fc = Linear(dim, num_classes)

    def forward(self, x, edge_index, edge_weight=None):
        xs = [x]
        for conv in self.convs:
            x = conv(x, edge_index, edge_weight)
            x = F.relu(x)
            xs.append(x)
        if self.concat_features:
            x = torch.cat(xs, dim=1)
        x = self.fc(x)
        return F.log_softmax(x, dim=1)


class BAShapes(BaseExperiment):
    name = 'BAShapes'

    def __init__(self) -> None:
        super().__init__()
        graph_json = json.load(open('experiments/ba_300_80.json'))
        edges = {int(k): v for k, v in graph_json['edges'].items()}
        self.g = nx.from_dict_of_lists(edges)
        self.labels = graph_json['labels']
        model = Net(1, num_classes=4, num_layers=3,concat_features=True,conv_type='GraphConv')
        model.load_state_dict(torch.load('experiments/BAShapes.pt'))
        model.eval()
        self.model = model

    def predict(self, nodes, edges):
        return self.predict_nodes(nodes, edges)

    def category_to_tensor(self, category):
        return torch.tensor([1]).float()

    def sample_graphs(self):
        samples = []
        depth_limit = 4
        for node_idx in range(600, 630):
            subgraph_nodes = []
            for k, v in nx.shortest_path_length(self.g, target=node_idx).items():
                if v < depth_limit:
                    subgraph_nodes.append(k)
            subgraph = self.g.subgraph(subgraph_nodes)
            nodes = [{'feat': 0, 'id': node} for node in subgraph.nodes()]
            edges = [[u, v] for u, v in subgraph.edges()]
            samples.append({'nodes': nodes, 'edges': edges, 'name': f'3-hop from node {node_idx}'})
        return samples

    def is_directed(self):
        return False
