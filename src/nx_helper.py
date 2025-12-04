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

def find_root_node(G):
    """
    Parameters:
        G :
            The graph to find root node in

    Returns:
        Node
            Root node of G or None if one doesn't exist.
    """
    for node in G.nodes():
        if len(list(G.predecessors(node))) == 0:
            return node
    return None

def remove_back_edges_to_make_dag(G, root):     
    """
    Remove all back edges from G to make it a DAG. Assuming G is connected and rooted at ROOT.
    
    Parameters:
        G :
            The graph to remove root edges
        root :
            The root node of G to start DFS with

    Returns:
        DAG version of G with all back edges removed.
    """
    visited = {node: False for node in G.nodes()}
    back_edges = []
    start_node = root
    # Iteratively perform DFS on unvisited nodes
    stack = [(start_node, iter(G.neighbors(start_node)))]
    visited[start_node] = True
    
    while stack:
        parent, children = stack[-1]
        try:
            child = next(children)
            if not visited[child]:
                visited[child] = True
                stack.append((child, iter(G.neighbors(child))))
            elif child in [node for node, _ in stack]:
                # If child is in stack, it's an ancestor, and (parent, child) is a back edge
                back_edges.append((parent, child))
        except StopIteration:
            stack.pop()

    # Remove identified back edges
    print(f"num_edges pre = {G.number_of_edges()}")
    G.remove_edges_from(back_edges)
    # Update num_edges after edge removal
    G.num_edges = G.number_of_edges()
    print(f"num_edges post = {G.num_edges}")
    return G


class Dag(nx.DiGraph):
    """
    Maintains information about the directed acyclic graph (DAG)
    of the code being analyzed. It is a subclass of
    the `~networkx.DiGraph` class of the NetworkX graph package,
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
        self.num_nodes: int = 0

        #: Number of edges in the DAG.
        self.num_edges: int = 0

        #: Number of paths in the DAG.
        self.num_paths: int = 0

        #: List of nodes in the DAG.
        self.all_nodes: List[str] = []
        self.all_nodes_with_description: List[Tuple[str, Dict[str, str]]] = []

        #: Dictionary that maps nodes to their indices in the list of all_temp_files nodes.
        #: This is maintained for efficiency purposes.
        self.nodes_indices: Dict[str, int] = {}

        #: List of nodes in the DAG that are not the sink.
        #: We assume that there is only one sink.
        #: This is maintained for efficiency purposes.
        self.nodes_except_sink: List[str] = []

        #: Dictionary that maps nodes (except the sink) to their indices in
        #: the list of all_temp_files nodes (except the sink). This is maintained for
        #: efficiency purposes.
        self.nodes_except_sink_indices: Dict[str, int] = {}

        #: List of nodes in the DAG that are neither the source nor the sink.
        #: We assume that there is only one source and one sink. This is
        #: maintained for efficiency purposes.
        self.nodes_except_source_sink: List[str] = []

        #: Dictionary that maps nodes (except the source and the sink) to their
        #: indices in the list of all_temp_files nodes (except the source and the sink).
        #: This is maintained for efficiency purposes.
        self.nodes_except_source_sink_indices: Dict[str, int] = {}

        #: List of edges in the DAG.
        self.all_edges: List[Tuple[str, str]] = []

        #: Dictionary that maps edges to their indices in the list of all_temp_files edges.
        #: This is maintained for efficiency purposes.
        self.edges_indices: Dict[Tuple[str, str]: int] = {}

        #: List of non-special edges in the DAG.
        self.edges_reduced: List[Tuple[str, str]] = []

        #: Dictionary that maps non-special edges to their indices in the
        #: list of all_temp_files edges. This is maintained for efficiency purposes.
        self.edges_reduced_indices: Dict[Tuple[str, str], int] = {}

        #: Dictionary that maps nodes to the special ('default') edges.
        self.special_edges: Dict[str, Tuple[str, str]] = {}

        #: List of the weights assigned to the edges in the DAG, arranged
        #: in the same order as the edges are in the list of all_temp_files edges.
        self.edge_weights: List[int] = []

    def initialize_dictionaries(self):
        """ """
        self.num_nodes = self.number_of_nodes()
        self.num_edges = self.number_of_edges()
        self.all_nodes = nodes = sorted(self.nodes())
        self.all_nodes_with_description = sorted(self.nodes.data(), key=lambda x: x[0])
        self.all_edges = self.edges()

        # We assume there is only one source and one sink.
        self.source = [node for node in nodes if (self.in_degree(node) == 0)][0]
        self.sink = [node for node in nodes if (self.out_degree(node) == 0)][0]
        self.nodes_except_sink = [node for node in self.all_nodes
                                if node != self.sink]
        self.nodes_except_source_sink = [node for node in self.all_nodes
                                      if (node != self.source and node != self.sink)]

        self.num_paths = (0 if has_cycles(self) else
                         num_paths(self, self.source, self.sink))

        # Initialize dictionaries that map nodes and edges to their indices
        # in the node list and edge list, respectively.
        for node_index, node in enumerate(self.all_nodes):
            self.nodes_indices[node] = node_index
        for node_index, node in enumerate(self.nodes_except_sink):
            self.nodes_except_sink_indices[node] = node_index
        for node_index, node in enumerate(self.nodes_except_source_sink):
            self.nodes_except_source_sink_indices[node] = node_index
        for edge_index, edge in enumerate(self.all_edges):
            self.edges_indices[edge] = edge_index

    def load_variables(self):
        """
        Loads the instance variables of this object with appropriate
        values. This method is useful when the DAG is loaded from a DOT file.

        """
        self.initialize_dictionaries()
        self.reset_edge_weights()

        logger.info("Initializing data structures for special edges...")
        self._init_special_edges()
        logger.info("Data structures initialized.")

    def reset_edge_weights(self):
        """Resets the weights assigned to the edges of the DAG."""
        self.edge_weights = [0] * self.num_edges

    def _init_special_edges(self):
        """
        To reduce the dimensionality to b = m-n+2 (b is the number of basis paths,
        m the number of edges, n the number of nodes), each node, except for
        the source and sink, chooses a 'special' edge. This edge is taken if
        flow enters the node, but no outgoing edge is 'visibly' selected.
        In other words, it is the 'default' edge for the node.
        
        This method initializes all_temp_files of the data structures necessary
        to keep track of these special edges.

        """
        self.edges_reduced = list(self.all_edges)

        for node in self.nodes_except_source_sink:
            out_edges = self.out_edges(node)
            out_edges = list(out_edges)
            if len(out_edges) > 0:
                # By default, we pick the first edge as 'special'.
                self.special_edges[node] = out_edges[0]
                self.edges_reduced.remove(out_edges[0])

        for edge in self.edges_reduced:
            self.edges_reduced_indices[edge] = list(self.all_edges).index(edge)

    @staticmethod
    def get_edges(nodes: List[str]) -> List[Tuple[str, str]]:
        """
        Parameters:
            nodes: List[str] :
                Nodes of a path in the directed acyclic graph
        Returns:
            List of edges that lie along the path.

        """
        return list(zip(nodes[:-1], nodes[1:]))

    def get_node_label(self, node: int) -> str:
        """gets node label from node ID

        Parameters:
            node: int :
                ID of the node of interest

        Returns:
            label corresponding to the node. (code corresponding to the node in LLVM IR)

        """
        return self.all_nodes_with_description[node][1]["label"]


def write_dag_to_dot_file(dag: Dag, location: str, dag_name: str = "",
                          edges_to_labels: Dict[Tuple[str, str], str] = None,
                          highlighted_edges: List[Tuple[str, str]] = None,
                          highlight_color: str = "red"):
    """
    Writes the directed acyclic graph provided to a file in DOT format.

    Parameters:
        dag : Dag :
            Dag to save to dot
        location : str :
            Location of the file.
        dag_name : str :
            Name of the directed acyclic graph, as will be written to
            the file. If this argument is not provided, the directed
            acyclic graph will not have a name. (Default value = "")
        edges_to_labels : Dict[Tuple[str, str], str]:
            Dictionary that maps an edge to the label that will annotate
            the edge when the DOT file is processed by a visualization tool.
            If this argument is not provided, these annotations will not
            be made. (Default value = None)
        highlighted_edges : List[Tuple[str, str]]:
            List of edges that will be highlighted when the DOT file is
            processed by a visualization tool. If this argument
            is not provided, no edges will be highlighted. (Default value = None)
        highlight_color : str:
            Color of the highlighted edges. This argument can be any value
            that is legal in the DOT format. If the `highlightedEdges` argument
            is not provided, this argument is ignored. (Default value = "red")

    """
    _, extension = os.path.splitext(location)
    if extension.lower() != ".dot":
        location = "%s.dot" % location

    dag_name = " %s" % dag_name.strip()
    contents = ["digraph%s {" % dag_name]

    for node in dag.all_nodes_with_description:
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


def construct_dag(location: str) -> tuple[Dag, bool]:
    """
    Constructs a `~gametime.nxHelper.Dag` object to represent
    the directed acyclic graph described in DOT format in the file provided.

    Parameters:
        location: str :
            Path to the file describing a directed acyclic graph in DOT format

    Returns:
        `~gametime.src.nx_helper.Dag`: 
            Object that represents the directed acyclic graph.

    """
    try:
        with open(location, "r") as f:
            graph_from_dot: nx.Graph = nx.nx_agraph.read_dot(f)

    except EnvironmentError as e:
        err_msg: str = ("Error opening the DOT file, located at %s, that contains "
                        "the directed acyclic graph to analyze: %s") % (location, e)
        raise GameTimeError(err_msg)

    if not graph_from_dot.is_directed():
        raise GameTimeError("CFG isn't directed")
        
    root = find_root_node(graph_from_dot)
    if root is None:
        raise GameTimeError("There is no node without incoming edge in CFG.")
    
    sink_nodes = [node for node, out_degree in graph_from_dot.out_degree() if out_degree == 0]
    if len(sink_nodes) != 1:
        raise GameTimeError("The number of sink nodes don't equal to 1.")

    modified=False
    if len(list(nx.simple_cycles(graph_from_dot))) > 0:
        logger.warning("The control-flow graph has cycles. Trying to remove them by removing back edges.")
        graph_from_dot = remove_back_edges_to_make_dag(graph_from_dot, root)
        modified = True

    dag: Dag = Dag(graph_from_dot)
    dag.load_variables()
    return dag, modified


def num_paths(dag: Dag, source: str, sink: str) -> int:
    """

    Parameters:
        dag:
            DAG represented by a `~gametime.src.nx_helper.Dag` object.
        source:
            Source node.
        sink:
            Sink node.
    Returns:
        int:
            Number of paths in the DAG provided. Note: Passed in DAG must be actually acyclic.

    """

    if has_cycles(dag):
        err_msg = ("The dag has cycles, so number of path is infinite. Get rid of cycles before analyzing")
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
    Parameters:
        dag: Dag :
            DAG represented by a `~gametime.src.nx_helper.Dag` object.
        source: str :
            source to start path with
        sink: str :
            sink to end path with           
    Returns:
        List[str]:
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
    Parameters:
        dag: Dag :
            DAG represented by a dag

    Returns:
        bool:
            `True` if, and only if, the DAG provided has cycles.

    """
    return len(list(nx.simple_cycles(dag))) > 0
