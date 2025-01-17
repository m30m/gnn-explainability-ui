from typing import Union, Tuple, Any

import networkx as nx
import numpy as np
import torch
import torch.nn.functional as F
from captum._utils.common import (
    _format_additional_forward_args,
    _format_input,
    _format_output,
)
from captum._utils.gradient import (
    apply_gradient_requirements,
    compute_layer_gradients_and_eval,
    undo_gradient_requirements,
)
from captum._utils.typing import TargetType
from captum.attr import Saliency, IntegratedGradients, LayerGradCam
from torch import Tensor
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import to_networkx

from explainers.gnn_explainer import TargetedGNNExplainerGraph

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class GraphLayerGradCam(LayerGradCam):

    def attribute(self, inputs: Union[Tensor, Tuple[Tensor, ...]], target: TargetType = None,
                  additional_forward_args: Any = None, attribute_to_layer_input: bool = False,
                  relu_attributions: bool = False) -> Union[Tensor, Tuple[Tensor, ...]]:
        inputs = _format_input(inputs)
        additional_forward_args = _format_additional_forward_args(
            additional_forward_args
        )
        gradient_mask = apply_gradient_requirements(inputs)
        # Returns gradient of output with respect to
        # hidden layer and hidden layer evaluated at each input.
        layer_gradients, layer_evals = compute_layer_gradients_and_eval(
            self.forward_func,
            self.layer,
            inputs,
            target,
            additional_forward_args,
            device_ids=self.device_ids,
            attribute_to_layer_input=attribute_to_layer_input,
        )
        undo_gradient_requirements(inputs, gradient_mask)

        summed_grads = tuple(
            torch.mean(
                layer_grad,
                dim=0,
                keepdim=True,
            )
            for layer_grad in layer_gradients
        )

        scaled_acts = tuple(
            torch.sum(summed_grad * layer_eval, dim=1, keepdim=True)
            for summed_grad, layer_eval in zip(summed_grads, layer_evals)
        )
        if relu_attributions:
            scaled_acts = tuple(F.relu(scaled_act) for scaled_act in scaled_acts)
        return _format_output(len(scaled_acts) > 1, scaled_acts)


def model_forward(edge_mask, model, x, edge_index):
    batch = torch.zeros(x.shape[0], dtype=int)
    out = model(x, edge_index, batch, edge_mask)
    return out


def model_forward_node(x, model, edge_index):
    batch = torch.zeros(x.shape[0], dtype=int)
    out = model(x, edge_index, batch)
    return out


def node_attr_to_edge(edge_index, node_mask):
    edge_mask = np.zeros(edge_index.shape[1])
    edge_mask += node_mask[edge_index[0].cpu().numpy()]
    edge_mask += node_mask[edge_index[1].cpu().numpy()]
    return edge_mask


def get_all_convolution_layers(model):
    layers = []
    for module in model.modules():
        if isinstance(module, MessagePassing):
            layers.append(module)
    return layers


def explain_random(model, x, edge_index, target, include_edges=None):
    return np.random.uniform(size=edge_index.shape[1])


# def explain_gradXact(model, node_idx, x, edge_index, target, include_edges=None):
#     # Captum default implementation of LayerGradCam does not average over nodes for different channels because of
#     # different assumptions on tensor shapes
#     input_mask = x.clone().requires_grad_(True).to(device)
#     layers = get_all_convolution_layers(model)
#     node_attrs = []
#     for layer in layers:
#         layer_gc = LayerGradCam(model_forward_node, layer)
#         node_attr = layer_gc.attribute(input_mask, target=target, additional_forward_args=(model, edge_index, node_idx))
#         node_attr = node_attr.cpu().detach().numpy().ravel()
#         node_attrs.append(node_attr)
#     node_attr = np.array(node_attrs).mean(axis=0)
#     edge_mask = node_attr_to_edge(edge_index, node_attr)
#     return edge_mask


def explain_pagerank(model, x, edge_index, target, include_edges=None):
    data = Data(x=x, edge_index=edge_index)
    g = to_networkx(data)
    pagerank = nx.pagerank(g)

    node_attr = np.zeros(x.shape[0])
    for node, value in pagerank.items():
        node_attr[node] = value
    edge_mask = node_attr_to_edge(edge_index, node_attr)
    return edge_mask


def explain_sa_node(model, x, edge_index, target, include_edges=None):
    saliency = Saliency(model_forward_node)
    input_mask = x.clone().requires_grad_(True).to(device)
    saliency_mask = saliency.attribute(input_mask, target=target, additional_forward_args=(model, edge_index),
                                       abs=False)

    node_attr = saliency_mask.cpu().numpy().sum(axis=1)
    edge_mask = node_attr_to_edge(edge_index, node_attr)
    return edge_mask


def explain_sa(model, x, edge_index, target, include_edges=None):
    saliency = Saliency(model_forward)
    input_mask = torch.ones(edge_index.shape[1]).requires_grad_(True).to(device)
    saliency_mask = saliency.attribute(input_mask, target=target,
                                       additional_forward_args=(model, x, edge_index), abs=False)

    edge_mask = saliency_mask.cpu().numpy()
    return edge_mask


def explain_ig_node(model, x, edge_index, target, include_edges=None):
    ig = IntegratedGradients(model_forward_node)
    input_mask = x.clone().requires_grad_(True).to(device)
    ig_mask = ig.attribute(input_mask, target=target, additional_forward_args=(model, edge_index),
                           internal_batch_size=input_mask.shape[0])

    node_attr = ig_mask.cpu().detach().numpy().sum(axis=1)
    edge_mask = node_attr_to_edge(edge_index, node_attr)
    return edge_mask


def explain_ig(model, x, edge_index, target, include_edges=None):
    ig = IntegratedGradients(model_forward)
    input_mask = torch.ones(edge_index.shape[1]).requires_grad_(True).to(device)
    ig_mask = ig.attribute(input_mask, target=target, additional_forward_args=(model, x, edge_index),
                           internal_batch_size=edge_index.shape[1])

    edge_mask = ig_mask.cpu().detach().numpy()
    return edge_mask


def explain_occlusion(model, x, edge_index, target, include_edges=None):
    batch = torch.zeros(x.shape[0], dtype=int)
    pred_prob = model(x, edge_index, batch)[0][target].item()
    num_edges = len(edge_index[0])
    edge_occlusion_mask = np.ones(num_edges, dtype=bool)
    edge_mask = np.zeros(num_edges)
    for i in range(num_edges):
        if include_edges is not None and not include_edges[i].item():
            continue
        edge_occlusion_mask[i] = False

        prob = model(x, edge_index[:, edge_occlusion_mask], batch)[0][target].item()
        edge_mask[i] = pred_prob - prob
        edge_occlusion_mask[i] = True
    return edge_mask


def explain_gnnexplainer(model, x, edge_index, target, include_edges=None, epochs=200, **kwargs):
    epochs = min(epochs, 600)
    explainer = TargetedGNNExplainerGraph(model, epochs=epochs, log=False)
    explainer.coeffs.update(kwargs)
    batch = torch.zeros(x.shape[0], dtype=int)
    node_feat_mask, edge_mask = explainer.explain_with_target(x, edge_index, target_class=target, batch=batch)
    return edge_mask.cpu().numpy()


methods = {
    'sa': explain_sa,
    'ig': explain_ig,
    'sa_node': explain_sa_node,
    'ig_node': explain_ig_node,
    'random': explain_random,
    'pagerank': explain_pagerank,
    'gnnexplainer': explain_gnnexplainer,
}
