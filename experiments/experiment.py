# This is a template for custom experiments. Copy this file and fix the TODOs.
# After implementing the functions, just re-run the web server, the models are registered automatically.

from experiments.base import BaseExperiment


class CustomExperiment(BaseExperiment):
    # TODO: Name of your experiment that appears in the Ui
    name = 'CHANGE_ME'

    def __init__(self) -> None:
        super().__init__()
        raise NotImplementedError
        # TODO: Load your trained model here. Don't forget to call `model.eval()` in order to disable training.
        # self.model = model

    def category_to_tensor(self, category):
        """
        Converts a single category value to a node feature tensor
        :param category: category value, this is one of the values returned by the `node_categories` function
        :return: a node feature tensor corresponding to the category value
        """
        # TODO: Implement this function. This can be a simple one hot encoding of the category value
        #  or a fixed value if nodes do not have any features
        raise NotImplementedError

    def sample_graphs(self):
        """

        :return: A list of sample graphs. Each graph is a dictionary with the following keys:
        `nodes`: list of nodes where each node is a dictionary with three keys:
                 1. `feat`: node category value
                 2. `id`: id of the node used for referencing the edges endpoints
                 3. `name`: name of the node [only used in graph classification]
        `edges`: list of edges where each edge is a list with size 2 representing
        the endpoints of the edge (using node ids).
        If the graph is undirected, only return one direction for each edge.
        `name`: Name of the sample graph, used in the UI
        `label`: Label of the sample [only used in graph classification]
        """
        # TODO: It's not necessary to provide samples, but it's usually easier to start with an existing graph
        #  and not to draw nodes and edges from scratch
        return []

    def node_categories(self):
        """

        :return: An array of dictionaries with `text` and `value` keys.
        Each item represents one possible category for each node.
        """
        # TODO: this array should represent all the possible node features.
        #  This approach is limited to categorical features and will not work for continous features.
        return [{'text': 'No category', 'value': 0}]

    def is_graph_classification(self):
        # TODO: return True or False depending on your model
        raise NotImplementedError

    def is_directed(self):
        # TODO: return True or False depending on your model
        raise NotImplementedError

    def predict(self, nodes, edges):
        # TODO: you can use predict_node and predict_graph functions implemented in the base class
        # For node classification you can directly return the result of `predict_node` function.
        # For graph classification you must return a dictionary with `prediction` and `text` keys.
        raise NotImplementedError
