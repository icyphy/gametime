#!/usr/bin/env python

"""Exposes classes and functions to supplement those provided by
the NetworkX graph package.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import os

from os import linesep as lsep
from random import randrange

import networkx as nx

from defaults import logger
from gametimeError import GameTimeError


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
        self.source = ""

        #: Sink of the DAG.
        self.sink = ""

        #: Number of nodes in the DAG.
        self.numNodes = 0

        #: Number of edges in the DAG.
        self.numEdges = 0

        #: Number of paths in the DAG.
        self.numPaths = 0

        #: List of nodes in the DAG.
        self.allNodes = []

        #: Dictionary that maps nodes to their indices in the list of all nodes.
        #: This is maintained for efficiency purposes.
        self.nodesIndices = {}

        #: List of nodes in the DAG that are not the sink.
        #: We assume that there is only one sink.
        #: This is maintained for efficiency purposes.
        self.nodesExceptSink = []

        #: Dictionary that maps nodes (except the sink) to their indices in
        #: the list of all nodes (except the sink). This is maintained for
        #: efficiency purposes.
        self.nodesExceptSinkIndices = {}

        #: List of nodes in the DAG that are neither the source nor the sink.
        #: We assume that there is only one source and one sink. This is
        #: maintained for efficiency purposes.
        self.nodesExceptSourceSink = []

        #: Dictionary that maps nodes (except the source and the sink) to their
        #: indices in the list of all nodes (except the source and the sink).
        #: This is maintained for efficiency purposes.
        self.nodesExceptSourceSinkIndices = {}

        #: List of edges in the DAG.
        self.allEdges = []

        #: Dictionary that maps edges to their indices in the list of all edges.
        #: This is maintained for efficiency purposes.
        self.edgesIndices = {}

        #: List of non-special edges in the DAG.
        self.edgesReduced = []

        #: Dictionary that maps non-special edges to their indices in the
        #: list of all edges. This is maintained for efficiency purposes.
        self.edgesReducedIndices = {}

        #: Dictionary that maps nodes to the special ('default') edges.
        self.specialEdges = {}

        #: List of the weights assigned to the edges in the DAG, arranged
        #: in the same order as the edges are in the list of all edges.
        self.edgeWeights = []

    def initializeDictionaries(self):
        self.numNodes = self.number_of_nodes()
        self.numEdges = self.number_of_edges()
        self.allNodes = nodes = sorted(self.nodes(), key=int)
        self.allEdges = self.edges()

        # We assume there is only one source and one sink.
        self.source = [node for node in nodes if self.in_degree(node) == 0][0]
        self.sink = [node for node in nodes if self.out_degree(node) == 0][0]
        self.nodesExceptSink = [node for node in self.allNodes
                                 if node != self.sink]
        self.nodesExceptSourceSink = [node for node in self.allNodes
                                       if node != self.source and
                                       node != self.sink]

        self.numPaths = (0 if hasCycles(self) else
                         numPaths(self, self.source, self.sink))


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


    def loadVariables(self):
        """Loads the instance variables of this object with appropriate
        values. This method is useful when the DAG is loaded from a DOT file.
        """
        self.initializeDictionaries()
        self.resetEdgeWeights()

        logger.info("Initializing data structures for special edges...")
        self._initSpecialEdges()
        logger.info("Data structures initialized.")

    def resetEdgeWeights(self):
        """Resets the weights assigned to the edges of the DAG."""
        self.edgeWeights = [0] * self.numEdges

    def _initSpecialEdges(self):
        """To reduce the dimensionality to b = n-m+2, each node, except for
        the source and sink, chooses a 'special' edge. This edge is taken if
        flow enters the node, but no outgoing edge is 'visibly' selected.
        In other words, it is the 'default' edge for the node.

        This method initializes all of the data structures necessary
        to keep track of these special edges.
        """
        self.edgesReduced = list(self.allEdges)

        for node in self.nodesExceptSourceSink:
            out_edges = self.out_edges(node)
            if len(out_edges) > 0:
                # By default, we pick the first edge as 'special'.
                self.specialEdges[node] = out_edges[0]
                self.edgesReduced.remove(out_edges[0])

        for edge in self.edgesReduced:
            self.edgesReducedIndices[edge] = self.allEdges.index(edge)

    @staticmethod
    def getEdges(nodes):
        """
        Arguments:
            nodes:
                Nodes of a path in the directed acyclic graph.

        Returns:
            List of edges that lie along the path.
        """
        return zip(nodes[:-1], nodes[1:])


def writeDagToDotFile(dag, location, dagName="", edgesToLabels=None,
                      highlightedEdges=None, highlightColor="red"):
    """Writes the directed acyclic graph provided to a file in DOT format.

    Arguments:
        location:
            Location of the file.
        dagName:
            Name of the directed acyclic graph, as will be written to
            the file. If this argument is not provided, the directed
            acyclic graph will not have a name.
        edgesToLabels:
            Dictionary that maps an edge to the label that will annotate
            the edge when the DOT file is processed by a visualization tool.
            If this argument is not provided, these annotations will not
            be made.
        highlightedEdges:
            List of edges that will be highlighted when the DOT file is
            processed by a visualization tool. If this argument
            is not provided, no edges will be highlighted.
        highlightColor:
            Color of the highlighted edges. This argument can be any value
            that is legal in the DOT format. If the `highlightedEdges` argument
            is not provided, this argument is ignored.
    """
    _, extension = os.path.splitext(location)
    if extension.lower() != ".dot":
        location = "%s.dot" % location

    dagName = " %s" % dagName.strip()
    contents = []
    contents.append("digraph%s {" % dagName)
    for edge in dag.edges():
        line = "  %s -> %s" % edge
        attributes = []
        if edgesToLabels:
            attributes.append("label = \"%s\"" % edgesToLabels[edge])
        if highlightedEdges and edge in highlightedEdges:
            attributes.append("color = \"%s\"" % highlightColor)
        if len(attributes) > 0:
            line += " [%s]" % ", ".join(attributes)
        contents.append("%s;" % line)
    contents.append("}")

    try:
        dagDotFileHandler = open(location, "w")
    except EnvironmentError as e:
        errMsg = ("Error writing the DAG to a file located at %s: %s" %
                  (location, e))
        raise GameTimeError(errMsg)
    else:
        with dagDotFileHandler:
            dagDotFileHandler.write("\n".join(contents))

def constructDag(location):
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
        dagDotFileHandler = open(location, "r")
    except EnvironmentError as e:
        errMsg = ("Error opening the DOT file, located at %s, that contains "
                  "the directed acyclic graph to analyze: %s") % (location, e)
        raise GameTimeError(errMsg)
    else:
        with dagDotFileHandler:
            dagDotFileLines = dagDotFileHandler.readlines()

    # This is a hacky way of parsing the file, but for this
    # small and constant a use case, we should be fine: we should not
    # have to generate a parser from a grammar. If, however, for some
    # reason, the format with which the Phoenix and Python code communicate
    # changes, this should be modified or made more robust.
    dagDotFileLines = dagDotFileLines[1:-1]
    dagDotFileLines = [line.replace(lsep, "") for line in dagDotFileLines]
    dagDotFileLines = [line.replace(";", "") for line in dagDotFileLines]
    dagDotFileLines = [line.replace("->", "") for line in dagDotFileLines]
    dagDotFileLines = [line.strip() for line in dagDotFileLines]

    # Construct the graph.
    dag = Dag()
    for line in dagDotFileLines:
        edge = line.split(" ")
        edge = [node for node in edge if node != ""]
        dag.add_edge(edge[0], edge[1])
    dag.loadVariables()
    return dag

def numPaths(dag, source, sink):
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
    """
    # Dictionary that maps each node to the number of paths in the 
    # DAG provided from the input source node to that node.
    nodesToNumPaths = {}
    nodesToNumPaths[source] = 1

    # Topologically sort the nodes in the graph.
    nodesToVisit = nx.topological_sort(dag)
    if nodesToVisit.pop(0) != source:
        errMsg = ("The source node should be the first node in "
                  "a topological sort of the control-flow graph.")
        raise GameTimeError(errMsg)

    while len(nodesToVisit) > 0:
        currNode = nodesToVisit.pop(0)
        numPathsToNode = 0
        for inEdge in dag.in_edges(currNode):
            inNeighbor = inEdge[0]
            numPathsToNode += nodesToNumPaths[inNeighbor]
        nodesToNumPaths[currNode] = numPathsToNode

    return nodesToNumPaths[sink]

def getRandomPath(dag, source, sink):
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
    resultPath = [source]

    currNode = source
    while currNode != sink:
        currNodeNeighbors = dag.neighbors(currNode)
        numNeighbors = len(currNodeNeighbors)
        if numNeighbors == 1:
            neighbor = currNodeNeighbors[0]
            resultPath.append(neighbor)
            currNode = neighbor
        elif numNeighbors > 1:
            randPos = randrange(numNeighbors)
            randNeighbor = currNodeNeighbors[randPos]
            resultPath.append(randNeighbor)
            currNode = randNeighbor
        else:
            # Restart.
            resultPath, currNode = [], source
    return resultPath

def hasCycles(dag):
    """
    Arguments:
        dag:
            DAG represented by a :class:`~gametime.nxHelper.Dag` object.
        source:
            Source node.
        sink:
            Sink node.

    Returns:
        `True` if, and only if, the DAG provided has cycles.
    """
    return len(list(nx.simple_cycles(dag))) > 0
