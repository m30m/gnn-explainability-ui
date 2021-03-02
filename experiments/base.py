import torch
from torch_geometric.data import Data
from explainers.node_methods import *


class BaseExperiment:
    name = 'base'

    def category_to_tensor(self, category):
        raise NotImplemented

    def ohe_to_str(self):
        pass

    def str_to_ohe(self):
        pass

    def models(self):
        pass

    def sample_graphs(self):
        pass

    def node_categories(self):
        return [{'text': 'No Category', 'value': 0}]

    def predict_nodes(self, nodes, edges):
        data = self.make_data(nodes, edges)
        return self.model(data.x, data.edge_index).argmax(dim=1).tolist()

    def make_data(self, nodes, edges):
        x = torch.stack([self.category_to_tensor(node['feat']) for node in nodes])
        edge_index = torch.tensor(list(zip(*edges)), dtype=torch.int64)
        data = Data(x=x, edge_index=edge_index)
        return data

    def explain_node(self, nodes, edges, node_id, target, method):
        data = self.make_data(nodes, edges)
        explain_function = eval('explain_' + method)
        attributions = explain_function(self.model, node_id, data.x, data.edge_index, target)
        return attributions

    def custom_style(self):
        return []

    def is_directed(self):
        return False
