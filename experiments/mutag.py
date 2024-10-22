import torch
import torch.nn.functional as F
from torch.nn import Linear
from torch_geometric.datasets import TUDataset
from torch_geometric.nn import global_add_pool, GraphConv

from experiments.base import BaseExperiment


class Net(torch.nn.Module):
    def __init__(self, dim, num_classes, num_features):
        super(Net, self).__init__()

        self.dim = dim

        self.conv1 = GraphConv(num_features, dim)
        self.conv2 = GraphConv(dim, dim)
        self.conv3 = GraphConv(dim, dim)
        self.conv4 = GraphConv(dim, dim)
        self.conv5 = GraphConv(dim, dim)

        self.fc1 = Linear(dim, dim)
        self.fc2 = Linear(dim, num_classes)

    def forward(self, x, edge_index, batch, edge_weight=None):
        x = F.relu(self.conv1(x, edge_index, edge_weight))
        x = F.relu(self.conv2(x, edge_index, edge_weight))
        x = F.relu(self.conv3(x, edge_index, edge_weight))
        x = F.relu(self.conv4(x, edge_index, edge_weight))
        x = F.relu(self.conv5(x, edge_index, edge_weight))
        x = global_add_pool(x, batch)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=-1)


ATOM_MAP = ['C', 'O', 'Cl', 'H', 'N', 'F', 'Br', 'S', 'P', 'I', 'Na', 'K', 'Li', 'Ca']


class Mutag(BaseExperiment):
    name = 'Mutag'

    def __init__(self) -> None:
        super().__init__()
        model = Net(32, num_classes=2, num_features=14)
        model.load_state_dict(torch.load('experiments/mutag.pt'))
        model.eval()
        self.model = model

    def category_to_tensor(self, category):
        result = [0] * 14
        result[category] = 1
        return torch.tensor(result).float()

    def sample_graphs(self):
        path = '.'
        dataset = TUDataset(path, name='Mutagenicity')[:50]
        samples = []
        for sample_id, data in enumerate(dataset):
            edges = list(zip(*data.edge_index.tolist()))
            edges = [[u, v] for u, v in edges if u < v]  # one direction of each edge is enough for front-end
            feats = data.x.argmax(dim=1).tolist()
            nodes = [{'feat': f, 'id': idx, 'name': ATOM_MAP[f]} for idx, f in enumerate(feats)]
            samples.append({'nodes': nodes,
                            'edges': edges,
                            'name': f'#{sample_id}: {self.label_text(data.y.item())}',
                            'label': self.label_text(data.y.item())})
        return samples

    def node_categories(self):
        return [{'text': text, 'value': idx} for idx, text in enumerate(ATOM_MAP)]

    def is_graph_classification(self):
        return True

    def label_text(self, label):
        text = 'Mutagenic' if label == 0 else 'Non-mutagenic'
        return text

    def predict(self, nodes, edges):
        pred = self.predict_graph(nodes, edges)
        text = self.label_text(pred)
        return {'prediction': pred, 'text': text}

    def is_directed(self):
        return False

    def custom_style(self):
        colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6',
                  '#6a3d9a', '#ffff99', '#b15928', '#d9d9d9', '#8dd3c7']
        return [{
            'selector': f'node[name][feat={idx}]',
            'style': {
                'background-color': color
            }
        } for idx, color in enumerate(colors)]
