#!/usr/bin/env python

"""Exposes classes and functions to maintain information
necessary to configure GameTime.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import imp
import os
import sys

from xml.dom import minidom

from defaults import logger
from gametimeError import GameTimeError


class Endianness(object):
    """This class represents the endianness of the target machine."""
    # Big-endian.
    BIG = 0
    # Little-endian.
    LITTLE = 1


class Configuration(object):
    """Stores information necessary to configure GameTime.
    """
    def __init__(self):
        """Constructor for the Configuration class."""
        ### GAMETIME INFORMATION ###
        # URL of the website for GameTime.
        self.WEBSITE_URL = ""

        # Current version number of GameTime.
        self.VERSION = ""

        # URL that provides information about
        # the latest version of GameTime.
        self.LATEST_VERSION_INFO_URL = ""

        ### FILE INFORMATION ###
        # Full location of the configuration file.
        self.configFile = ""

        # Directory that contains the configuration file.
        self.configDir = ""

        ### MEMORY LAYOUT INFORMATION ###
        # Word size on the machine that GameTime is being run on (in bits).
        # This value should be changed if GameTime will be run on a
        # non-32-bit machine.
        self.WORD_BITSIZE = 32

        # Word size on the machine that GameTime is being run on (in bytes).
        # This value should be changed and the solution should be recompiled,
        # if GameTime will be run on a non-32-bit machine.
        self.WORD_BYTESIZE = 4

        # Endianness of the target machine.
        self.ENDIANNESS = Endianness.LITTLE

        ### ANNOTATIONS ###
        # Annotation that is used when additional conditions need to be
        # provided to GameTime.
        self.ANNOTATION_ASSUME = ""

        # Annotation that is used when a simulation is performed.
        self.ANNOTATION_SIMULATE = ""

        ### SPECIAL IDENTIFIERS ###
        # The special identifiers and for the names and prefixes of temporary
        # files and folders are described in the default GameTime
        # configuration XML file provided in the source directory.
        self.IDENT_AGGREGATE = ""
        self.IDENT_CONSTRAINT = ""
        self.IDENT_EFC = ""
        self.IDENT_FIELD = ""
        self.IDENT_TEMPINDEX = ""
        self.IDENT_TEMPPTR = ""
        self.IDENT_TEMPVAR = ""

        self.TEMP_PROJECT_CONFIG = ""
        self.TEMP_MERGED = ""
        self.TEMP_LOOP_CONFIG = ""

        self.TEMP_SUFFIX = ""

        self.TEMP_SUFFIX_MERGED = ""
        self.TEMP_SUFFIX_UNROLLED = ""
        self.TEMP_SUFFIX_INLINED = ""
        self.TEMP_SUFFIX_LINE_NUMS = ""

        self.TEMP_PHX_CREATE_DAG = ""
        self.TEMP_DAG = ""
        self.TEMP_DAG_ID_MAP = ""

        self.TEMP_PHX_IR = ""
        self.TEMP_PHX_FIND_CONDITIONS = ""

        self.TEMP_PATH_ILP_PROBLEM = ""
        self.TEMP_PATH_NODES = ""
        self.TEMP_PATH_CONDITIONS = ""
        self.TEMP_PATH_CONDITION_EDGES = ""
        self.TEMP_PATH_CONDITION_TRUTHS = ""
        self.TEMP_PATH_LINE_NUMBERS = ""
        self.TEMP_PATH_ARRAY_ACCESSES = ""
        self.TEMP_PATH_AGG_INDEX_EXPRS = ""
        self.TEMP_PATH_PREDICTED_VALUE = ""
        self.TEMP_PATH_MEASURED_VALUE = ""
        self.TEMP_PATH_ALL = ""

        self.TEMP_PATH_QUERY = ""
        self.TEMP_SMT_MODEL = ""
        self.TEMP_PATH_QUERY_ALL = ""

        self.TEMP_CASE = ""

        self.TEMP_BASIS_MATRIX = ""
        self.TEMP_MEASUREMENT = ""
        self.TEMP_BASIS_VALUES = ""
        self.TEMP_DAG_WEIGHTS = ""
        self.TEMP_DISTRIBUTION = ""

        ### TOOLS ###
        # Absolute location of the Phoenix DLL.
        self.TOOL_PHOENIX = ""

        # Absolute location of the directory that contains the CIL source code.
        self.TOOL_CIL = ""

        ### SMT SOLVERS ###
        # Absolute location of the Boolector executable.
        self.SOLVER_BOOLECTOR = ""

        # Absolute location of the Python frontend of Z3,
        # the SMT solver from Microsoft.
        self.SOLVER_Z3 = ""

        ### SIMULATORS AND AUXILIARY TOOLS ###
        # Absolute location of the directory that contains
        # the GNU ARM toolchain.
        self.SIMULATOR_TOOL_GNU_ARM = ""

        # Absolute location of the directory that contains
        # the PTARM simulator.
        self.SIMULATOR_PTARM = ""

def _getText(node):
    """
    Obtains the text from the node provided.

    @param node Node to obtain the text from.
    @retval Text from the node provided.
    """
    return " ".join(child.data.strip() for child in node.childNodes
                    if child.nodeType == child.TEXT_NODE)

def _getAbsolutePath(name):
    """
    Obtains the absolute path of the executable whose name is provided,
    if the executable is present in any of the directories in
    the PATH environment variable.

    (Based on code and suggestions at http://stackoverflow.com/q/775351)

    @param name Name of the executable.
    @retval Absolute path of the executable, if present in any of
    the directories in the PATH environment variable; None otherwise.
    """
    if name is "":
        return None

    extensions = os.environ.get("PATHEXT", "").split(os.pathsep)
    pathDirs = os.environ.get("PATH", "").split(os.pathsep)
    pathDirs.append(os.getcwd())
    for directory in pathDirs:
        basePath = os.path.normpath(os.path.join(directory, name))
        options = [basePath] + [(basePath + ext) for ext in extensions]
        for absPath in options:
            if os.access(absPath, os.X_OK):
                return absPath

def readConfigFile(location):
    """
    Reads GameTime configuration information from the XML file provided.

    @param location Location of the XML file that contains GameTime
    configuration information.
    @retval Configuration object that contains information from
    the file provided.
    """
    if not os.path.exists(location):
        errMsg = "Cannot find configuration file: %s " % location
        raise GameTimeError(errMsg)

    config = Configuration()
    try:
        configDom = minidom.parse(location)
    except EnvironmentError as e:
        errMsg = "Error reading configuration from configuration file: %s" % e
        raise GameTimeError(errMsg)

    # Check that the root element is properly named.
    rootNode = configDom.documentElement
    if rootNode.tagName != 'gametime-config':
        raise GameTimeError("The root element in the XML file should be "
                            "named `gametime-config`.")

    # Check that no child element of the root element has an illegal tag.
    rootChildNodes = [node for node in rootNode.childNodes
                      if node.nodeType == node.ELEMENT_NODE]
    for childNode in rootChildNodes:
        childNodeTag = childNode.tagName
        if childNodeTag not in ["gametime", "memory",
                                "annotations", "identifiers", "temps",
                                "tools", "smt-solvers", "simulators"]:
            raise GameTimeError("Unrecognized tag: %s" % childNodeTag)

    # Get the absolute path of the file and the directory
    # that contains the file.
    configFileRealPath = os.path.realpath(location)
    config.configFile = configFileRealPath
    config.configDir = os.path.dirname(config.configFile)

    # Process the information about GameTime.
    gametimeNode = configDom.getElementsByTagName("gametime")[0]

    for node in gametimeNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "website-url":
                config.WEBSITE_URL = nodeText
            elif nodeTag == "version":
                config.VERSION = nodeText
            elif nodeTag == "latest-version-info-url":
                config.LATEST_VERSION_INFO_URL = nodeText
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the memory layout information.
    memoryNode = configDom.getElementsByTagName("memory")[0]

    for node in memoryNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "bitsize":
                config.WORD_BITSIZE = int(nodeText)
                config.WORD_BYTESIZE = config.WORD_BITSIZE / 8
            elif nodeTag == "endianness":
                nodeText = nodeText.lower()
                if nodeText not in ["big", "little"]:
                    errMsg = ("Incorrect option for the endianness "
                              "of the target machine: %s") % nodeText
                    raise GameTimeError(errMsg)
                config.ENDIANNESS = Endianness.BIG if \
                nodeText == "big" else Endianness.LITTLE
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the annotations that can be added to the code under analysis.
    annotationsNode = configDom.getElementsByTagName("annotations")[0]

    for node in annotationsNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "assume":
                config.ANNOTATION_ASSUME = nodeText
            elif nodeTag == "simulate":
                config.ANNOTATION_SIMULATE = nodeText
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the special identifiers.
    identsNode = configDom.getElementsByTagName("identifiers")[0]

    for node in identsNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "aggregate":
                config.IDENT_AGGREGATE = nodeText
            elif nodeTag == "constraint":
                config.IDENT_CONSTRAINT = nodeText
            elif nodeTag == "efc":
                config.IDENT_EFC = nodeText
            elif nodeTag == "field":
                config.IDENT_FIELD = nodeText
            elif nodeTag == "tempindex":
                config.IDENT_TEMPINDEX = nodeText
            elif nodeTag == "tempptr":
                config.IDENT_TEMPPTR = nodeText
            elif nodeTag == "tempvar":
                config.IDENT_TEMPVAR = nodeText
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the names for temporary files and folders that
    # are generated during the GameTime toolflow.
    tempsNode = configDom.getElementsByTagName("temps")[0]

    for node in tempsNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "project-config":
                config.TEMP_PROJECT_CONFIG = nodeText
            elif nodeTag == "merged":
                config.TEMP_MERGED = nodeText
            elif nodeTag == "loop-config":
                config.TEMP_LOOP_CONFIG = nodeText

            elif nodeTag == "suffix":
                config.TEMP_SUFFIX = nodeText

            elif nodeTag == "suffix-merged":
                config.TEMP_SUFFIX_MERGED = nodeText
            elif nodeTag == "suffix-unrolled":
                config.TEMP_SUFFIX_UNROLLED = nodeText
            elif nodeTag == "suffix-inlined":
                config.TEMP_SUFFIX_INLINED = nodeText
            elif nodeTag == "suffix-line-nums":
                config.TEMP_SUFFIX_LINE_NUMS = nodeText

            elif nodeTag == "phx-create-dag":
                config.TEMP_PHX_CREATE_DAG = nodeText
            elif nodeTag == "dag":
                config.TEMP_DAG = nodeText
            elif nodeTag == "dag-id-map":
                config.TEMP_DAG_ID_MAP = nodeText

            elif nodeTag == "phx-ir":
                config.TEMP_PHX_IR = nodeText
            elif nodeTag == "phx-find-conditions":
                config.TEMP_PHX_FIND_CONDITIONS = nodeText

            elif nodeTag == "path-ilp-problem":
                config.TEMP_PATH_ILP_PROBLEM = nodeText
            elif nodeTag == "path-nodes":
                config.TEMP_PATH_NODES = nodeText
            elif nodeTag == "path-conditions":
                config.TEMP_PATH_CONDITIONS = nodeText
            elif nodeTag == "path-condition-edges":
                config.TEMP_PATH_CONDITION_EDGES = nodeText
            elif nodeTag == "path-condition-truths":
                config.TEMP_PATH_CONDITION_TRUTHS = nodeText
            elif nodeTag == "path-line-numbers":
                config.TEMP_PATH_LINE_NUMBERS = nodeText
            elif nodeTag == "path-array-accesses":
                config.TEMP_PATH_ARRAY_ACCESSES = nodeText
            elif nodeTag == "path-agg-index-exprs":
                config.TEMP_PATH_AGG_INDEX_EXPRS = nodeText
            elif nodeTag == "path-predicted-value":
                config.TEMP_PATH_PREDICTED_VALUE = nodeText
            elif nodeTag == "path-measured-value":
                config.TEMP_PATH_MEASURED_VALUE = nodeText
            elif nodeTag == "path-all":
                config.TEMP_PATH_ALL = nodeText

            elif nodeTag == "path-query":
                config.TEMP_PATH_QUERY = nodeText
            elif nodeTag == "smt-model":
                config.TEMP_SMT_MODEL = nodeText
            elif nodeTag == "path-query-all":
                config.TEMP_PATH_QUERY_ALL = nodeText

            elif nodeTag == "case":
                config.TEMP_CASE = nodeText

            elif nodeTag == "basis-matrix":
                config.TEMP_BASIS_MATRIX = nodeText
            elif nodeTag == "measurement":
                config.TEMP_MEASUREMENT = nodeText
            elif nodeTag == "basis-values":
                config.TEMP_BASIS_VALUES = nodeText
            elif nodeTag == "dag-weights":
                config.TEMP_DAG_WEIGHTS = nodeText
            elif nodeTag == "distribution":
                config.TEMP_DISTRIBUTION = nodeText
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the locations of useful tools.
    toolsNode = configDom.getElementsByTagName("tools")

    for node in toolsNode[0].childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            configDir = config.configDir
            location = os.path.normpath(os.path.join(configDir, nodeText))
            if not os.path.exists(location):
                errMsg = "Invalid location: %s" % location
                raise GameTimeError(errMsg)
            if nodeTag == "cil":
                config.TOOL_CIL = location
            elif nodeTag == "phoenix":
                config.TOOL_PHOENIX = location
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the locations of SMT solvers.
    smtSolversNode = configDom.getElementsByTagName("smt-solvers")

    for node in smtSolversNode[0].childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "boolector":
                boolectorPath = _getAbsolutePath(nodeText)
                if boolectorPath is None:
                    warnMsg = ("Unable to find the Boolector executable. "
                               "A GameTime project will not be able to "
                               "use Boolector as its backend SMT solver.")
                    logger.warn("WARNING: %s" % warnMsg)
                    logger.warn("")
                    config.SOLVER_BOOLECTOR = ""
                else:
                    config.SOLVER_BOOLECTOR = boolectorPath
            elif nodeTag == "z3":
                z3Path = _getAbsolutePath(nodeText)
                if z3Path is not None:
                    sys.path.append(os.path.dirname(z3Path))
                try:
                    z3Path = imp.find_module("z3")[1]
                    config.SOLVER_Z3 = z3Path
                except ImportError:
                    # The Z3 Python frontend is not present in
                    # either the PATH environment variable or
                    # the PYTHONPATH environment variable.
                    warnMsg = ("Unable to find the Z3 Python frontend. "
                               "A GameTime project will not be able to "
                               "use Z3 as its backend SMT solver.")
                    logger.warn("WARNING: %s" % warnMsg)
                    logger.warn("")
                    config.SOLVER_Z3 = ""
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the locations of simulators and useful auxiliary tools.
    simulatorsNode = configDom.getElementsByTagName("simulators")

    for node in simulatorsNode[0].childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "gnu-arm":
                gnuArmPath = _getAbsolutePath(nodeText)
                if gnuArmPath is None:
                    warnMsg = ("Unable to find the location of the directory "
                               "that contains the GNU ARM toolchain. "
                               "A GameTime project will not be able to "
                               "use the GNU ARM toolchain to measure "
                               "the cycle counts of test cases.")
                    logger.warn("WARNING: %s" % warnMsg)
                    logger.warn("")
                    config.SIMULATOR_TOOL_GNU_ARM = ""
                else:
                    config.SIMULATOR_TOOL_GNU_ARM = gnuArmPath
            elif nodeTag == "ptarm":
                ptarmPath = _getAbsolutePath(nodeText)
                if ptarmPath is None:
                    warnMsg = ("Unable to find the location of the directory "
                               "that contains the PTARM simulator. "
                               "A GameTime project will not be able to use "
                               "the PTARM simulator to measure the cycle "
                               "counts of test cases.")
                    logger.warn("WARNING: %s" % warnMsg)
                    logger.warn("")
                    config.SIMULATOR_PTARM = ""
                else:
                    config.SIMULATOR_PTARM = ptarmPath
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    return config
