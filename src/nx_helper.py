#!/usr/bin/env python

"""Exposes classes and functions to supplement those provided by
the NetworkX graph package.
"""
from typing import List, Dict, Tuple

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""

import os

from random import randrange

import networkx as nx

from defaults import logger
from gametime_error import GameTimeError


class Dag(nx.DiGraph):
    """Maintains information about the directed acyclic graph (DAG)
    of the code being analyzed. It is a subclass of
    the :class:`~networkx.DiGraph` class of the NetworkX graph package,
    and stores additional information relevant to the GameTime analysis,
    such as the special 'default' edges in the DAG.
    """

    def __init__(self, *args, **kwargs):
        super(Dag, self).__init__(*args, **kwargs)

        #: Source of the DAG.

        self.source: str = ""

        #: Sink of the DAG.
        self.sink: str = ""

        #: Number of nodes in the DAG.
        self.numNodes: int = 0

        #: Number of edges in the DAG.
        self.numEdges: int = 0

        #: Number of paths in the DAG.
        self.numPaths: int = 0

        #: List of nodes in the DAG.
        self.allNodes: List[str] = []
        self.allNodesWithDescription: List[Tuple[str, Dict[str, str]]] = []

        #: Dictionary that maps nodes to their indices in the list of all_temp_files nodes.
        #: This is maintained for efficiency purposes.
        self.nodesIndices: Dict[str, int] = {}

        #: List of nodes in the DAG that are not the sink.
        #: We assume that there is only one sink.
        #: This is maintained for efficiency purposes.
        self.nodesExceptSink: List[str] = []

        #: Dictionary that maps nodes (except the sink) to their indices in
        #: the list of all_temp_files nodes (except the sink). This is maintained for
        #: efficiency purposes.
        self.nodesExceptSinkIndices: Dict[str, int] = {}

        #: List of nodes in the DAG that are neither the source nor the sink.
        #: We assume that there is only one source and one sink. This is
        #: maintained for efficiency purposes.
        self.nodesExceptSourceSink: List[str] = []

        #: Dictionary that maps nodes (except the source and the sink) to their
        #: indices in the list of all_temp_files nodes (except the source and the sink).
        #: This is maintained for efficiency purposes.
        self.nodesExceptSourceSinkIndices: Dict[str, int] = {}

        #: List of edges in the DAG.
        self.allEdges: List[Tuple[str, str]] = []

        #: Dictionary that maps edges to their indices in the list of all_temp_files edges.
        #: This is maintained for efficiency purposes.
        self.edgesIndices: Dict[Tuple[str, str]: int] = {}

        #: List of non-special edges in the DAG.
        self.edgesReduced: List[Tuple[str, str]] = []

        #: Dictionary that maps non-special edges to their indices in the
        #: list of all_temp_files edges. This is maintained for efficiency purposes.
        self.edgesReducedIndices: Dict[Tuple[str, str], int] = {}

        #: Dictionary that maps nodes to the special ('default') edges.
        self.specialEdges: Dict[str, Tuple[str, str]] = {}

        #: List of the weights assigned to the edges in the DAG, arranged
        #: in the same order as the edges are in the list of all_temp_files edges.
        self.edgeWeights: List[int] = []

    def initialize_dictionaries(self):
        self.numNodes = self.number_of_nodes()
        self.numEdges = self.number_of_edges()
        self.allNodes = nodes = sorted(self.nodes())
        self.allNodesWithDescription = sorted(self.nodes.data(), key=lambda x: x[0])
        self.allEdges = self.edges()

        # We assume there is only one source and one sink.
        self.source = [node for node in nodes if self.in_degree(node) == 0][0]
        self.sink = [node for node in nodes if self.out_degree(node) == 0][0]
        self.nodesExceptSink = [node for node in self.allNodes
                                if node != self.sink]
        self.nodesExceptSourceSink = [node for node in self.allNodes
                                      if node != self.source and
                                      node != self.sink]

        self.numPaths = (0 if has_cycles(self) else
                         num_paths(self, self.source, self.sink))

        # Initialize dictionaries that map nodes and edges to their indices
        # in the node list and edge list, respectively.
        for nodeIndex, node in enumerate(self.allNodes):
            self.nodesIndices[node] = nodeIndex
        for nodeIndex, node in enumerate(self.nodesExceptSink):
            self.nodesExceptSinkIndices[node] = nodeIndex
        for nodeIndex, node in enumerate(self.nodesExceptSourceSink):
            self.nodesExceptSourceSinkIndices[node] = nodeIndex
        for edgeIndex, edge in enumerate(self.allEdges):
            self.edgesIndices[edge] = edgeIndex

    def load_variables(self):
        """Loads the instance variables of this object with appropriate
        values. This method is useful when the DAG is loaded from a DOT file.
        """
        self.initialize_dictionaries()
        self.reset_edge_weights()

        logger.info("Initializing data structures for special edges...")
        self._init_special_edges()
        logger.info("Data structures initialized.")

    def reset_edge_weights(self):
        """Resets the weights assigned to the edges of the DAG."""
        self.edgeWeights = [0] * self.numEdges

    def _init_special_edges(self):
        """To reduce the dimensionality to b = n-m+2, each node, except for
        the source and sink, chooses a 'special' edge. This edge is taken if
        flow enters the node, but no outgoing edge is 'visibly' selected.
        In other words, it is the 'default' edge for the node.

        This method initializes all_temp_files of the data structures necessary
        to keep track of these special edges.
        """
        self.edgesReduced = list(self.allEdges)

        for node in self.nodesExceptSourceSink:
            out_edges = self.out_edges(node)
            out_edges = list(out_edges)
            if len(out_edges) > 0:
                # By default, we pick the first edge as 'special'.
                self.specialEdges[node] = out_edges[0]
                self.edgesReduced.remove(out_edges[0])

        for edge in self.edgesReduced:
            self.edgesReducedIndices[edge] = list(self.allEdges).index(edge)

    @staticmethod
    def get_edges(nodes: List[str]) -> List[Tuple[str, str]]:
        """
        Arguments:
            nodes:
                Nodes of a path in the directed acyclic graph.

        Returns:
            List of edges that lie along the path.
        """
        return list(zip(nodes[:-1], nodes[1:]))


def write_dag_to_dot_file(dag: Dag, location: str, dag_name: str = "",
                          edges_to_labels: Dict[Tuple[str, str], str] = None,
                          highlighted_edges: List[Tuple[str, str]] = None,
                          highlight_color: str = "red"):
    """Writes the directed acyclic graph provided to a file in DOT format.

    Arguments:
        dag:
            Dag to save to dot
        location:
            Location of the file.
        dag_name:
            Name of the directed acyclic graph, as will be written to
            the file. If this argument is not provided, the directed
            acyclic graph will not have a name.
        edges_to_labels:
            Dictionary that maps an edge to the label that will annotate
            the edge when the DOT file is processed by a visualization tool.
            If this argument is not provided, these annotations will not
            be made.
        highlighted_edges:
            List of edges that will be highlighted when the DOT file is
            processed by a visualization tool. If this argument
            is not provided, no edges will be highlighted.
        highlight_color:
            Color of the highlighted edges. This argument can be any value
            that is legal in the DOT format. If the `highlightedEdges` argument
            is not provided, this argument is ignored.
    """
    _, extension = os.path.splitext(location)
    if extension.lower() != ".dot":
        location = "%s.dot" % location

    dag_name = " %s" % dag_name.strip()
    contents = ["digraph%s {" % dag_name]

    for node in dag.allNodesWithDescription:
        line: str = "  %s" % node[0]
        attributes: List[str] = []
        for key in node[1]:
            attributes.append(' %s="%s"' % (key, node[1][key]))
        line += " [%s]" % ", ".join(attributes)
        contents.append("%s;" % line)

    for edge in dag.edges():
        line = "  %s -> %s" % edge
        attributes = []
        if edges_to_labels:
            attributes.append("label = \"%s\"" % edges_to_labels[edge])
        if highlighted_edges and edge in highlighted_edges:
            attributes.append("color = \"%s\"" % highlight_color)
        if len(attributes) > 0:
            line += " [%s]" % ", ".join(attributes)
        contents.append("%s;" % line)
    contents.append("}")

    try:
        dag_dot_file_handler = open(location, "w")
    except EnvironmentError as e:
        err_msg = ("Error writing the DAG to a file located at %s: %s" %
                   (location, e))
        raise GameTimeError(err_msg)
    else:
        with dag_dot_file_handler:
            dag_dot_file_handler.write("\n".join(contents))


def construct_dag(location: str) -> Dag:
    """Constructs a :class:`~gametime.nxHelper.Dag` object to represent
    the directed acyclic graph described in DOT format in the file provided.

    Arguments:
        location:
            Path to the file describing a directed acyclic graph
            in DOT format.

    Returns:
        :class:`~gametime.nxHelper.Dag` object that represents
        the directed acyclic graph.
    """
    try:
        with open(location, "r") as f:
            graph_from_dot: nx.Graph = nx.nx_agraph.read_dot(f)

    except EnvironmentError as e:
        err_msg: str = ("Error opening the DOT file, located at %s, that contains "
                        "the directed acyclic graph to analyze: %s") % (location, e)
        raise GameTimeError(err_msg)

    dag: Dag = Dag(graph_from_dot)
    dag.load_variables()
    return dag


def num_paths(dag: Dag, source: str, sink: str) -> int:
    """
    Arguments:
        dag:
            DAG represented by a :class:`~gametime.nxHelper.Dag` object.
        source:
            Source node.
        sink:
            Sink node.

    Returns:
        Number of paths in the DAG provided.
    Note:
        Passed in DAG must be actually acyclic.
    """
    # TODO: make programs that have cycles work
    if has_cycles(dag):
        err_msg = ("The dag has cycles, so number of path is infinite. "
                   "Get rid of cycles before analyzing")
        raise GameTimeError(err_msg)
    # Dictionary that maps each node to the number of paths in the
    # DAG provided from the input source node to that node.
    nodes_to_num_paths: Dict[str, int] = {source: 1}

    # Topologically sort the nodes in the graph.
    nodes_to_visit: List[str] = list(nx.topological_sort(dag))
    if nodes_to_visit.pop(0) != source:
        err_msg = ("The source node should be the first node in "
                   "a topological sort of the control-flow graph.")
        raise GameTimeError(err_msg)

    while len(nodes_to_visit) > 0:
        curr_node = nodes_to_visit.pop(0)
        num_paths_to_node = 0
        for inEdge in dag.in_edges(curr_node):
            in_neighbor = inEdge[0]
            num_paths_to_node += nodes_to_num_paths[in_neighbor]
        nodes_to_num_paths[curr_node] = num_paths_to_node

    return nodes_to_num_paths[sink]


def get_random_path(dag: Dag, source: str, sink: str) -> List[str]:
    """
    Arguments:
        dag:
            DAG represented by a :class:`~gametime.nxHelper.Dag` object.
        source:
            Source node.
        sink:
            Sink node.

    Returns:
        Random path in the DAG provided from the input source node to
        the input sink node, represented as a list of nodes arranged in
        order of traversal from source to sink.
    """
    result_path = [source]

    curr_node: str = source
    while curr_node != sink:
        curr_node_neighbors: List[str] = list(dag.neighbors(curr_node))
        num_neighbors: int = len(curr_node_neighbors)
        if num_neighbors == 1:
            neighbor: str = curr_node_neighbors[0]
            result_path.append(neighbor)
            curr_node = neighbor
        elif num_neighbors > 1:
            rand_pos: int = randrange(num_neighbors)
            rand_neighbor: str = curr_node_neighbors[rand_pos]
            result_path.append(rand_neighbor)
            curr_node = rand_neighbor
        else:
            # Restart.
            result_path, curr_node = [], source
    return result_path


def has_cycles(dag: Dag) -> bool:
    """
    Arguments:
        dag:
            DAG represented by a :class:`~gametime.nxHelper.Dag` object.

    Returns:
        `True` if, and only if, the DAG provided has cycles.
    """
    return len(list(nx.simple_cycles(dag))) > 0
