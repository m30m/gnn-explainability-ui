import json

import networkx as nx
import torch

from experiments.base import BaseExperiment


class BAShapes(BaseExperiment):
    name = 'BAShapes'

    def __init__(self) -> None:
        super().__init__()
        graph_json = json.load(open('ba_300_80.json'))
        edges = {int(k): v for k, v in graph_json['edges'].items()}
        self.g = nx.from_dict_of_lists(edges)
        self.labels = graph_json['labels']
        self.model = torch.load('BAShapes.pt')

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
