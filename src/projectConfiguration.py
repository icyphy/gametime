#!/usr/bin/env python

"""Exposes classes, functions, and modules to maintain information
necessary to configure a GameTime project.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import glob
import os
import re
from xml.dom import minidom

from defaults import config, logger
from gametimeError import GameTimeError
import pulpHelper


class DebugConfiguration(object):
    """Stores debugging configuration information, which
    determines the debugging information that is shown and
    the temporary files that are dumped.

    Attributes:
        keepCilTemps:
            True if the temporary files that CIL generates during
            its analysis are to be kept; False otherwise.
        dumpIr:
            True if the Phoenix intermediate representation of the function
            under analysis is to be dumped to a file; False otherwise.
        keepIlpSolverOutput:
            True if debugging information and files produced by
            the integer linear programming solver are to be kept;
            False otherwise.
        dumpInstructionTrace:
            True if information produced when an IR-level instruction is
            traced backward is to be dumped; False otherwise.
        dumpPath:
            True if information about the path being traced is to be dumped;
            False otherwise.
        dumpAllPaths:
            True if information about all of the paths that have been traced
            during analysis are to be dumped to a file; False otherwise.
        dumpSmtTrace:
            True if information produced during the creation of an SMT query
            is to be dumped; False otherwise.
        dumpAllQueries:
            True if information about all of the SMT queries that have been
            made during analysis are to be dumped to a file; False otherwise.
        keepParserOutput:
            True if the debugging information and temporary files produced by
            the parser are to be kept; False otherwise.
        keepSimulatorOutput:
            True if temporary files produced by a simulator when measuring
            the value of a path are to be kept; False otherwise.
    """

    def __init__(self, keepCilTemps=False, dumpIr=False,
                 keepIlpSolverOutput=False, dumpInstructionTrace=False,
                 dumpPath=False, dumpAllPaths=False, dumpSmtTrace=False,
                 dumpAllQueries=False, keepParserOutput=False,
                 keepSimulatorOutput=False):
        #: Keep the temporary files that CIL generates during its analysis.
        self.KEEP_CIL_TEMPS = keepCilTemps

        #: Dump the Phoenix intermediate representation of the function
        #: under analysis to a file.
        self.DUMP_IR = dumpIr

        #: Keep debugging information and files produced by
        #: the integer linear programming solver.
        self.KEEP_ILP_SOLVER_OUTPUT = keepIlpSolverOutput

        #: Dump information produced when an IR-level instruction
        #: is traced backward.
        self.DUMP_INSTRUCTION_TRACE = dumpInstructionTrace

        #: Dump information about the path being traced.
        self.DUMP_PATH = dumpPath

        #: Dump information about all of the paths that have been traced
        #: during analysis to a file.
        self.DUMP_ALL_PATHS = dumpAllPaths

        #: Dump information produced when an SMT query is created.
        self.DUMP_SMT_TRACE = dumpSmtTrace

        #: Dump information about all of the SMT queries that
        #: have been made during analysis to a file.
        self.DUMP_ALL_QUERIES = dumpAllQueries

        #: Keep the debugging information and the temporary files
        #: produced by the parser.
        self.KEEP_PARSER_OUTPUT = keepParserOutput

        #: Keep the temporary files produced by a simulator when
        #: measuring the value of a path.
        self.KEEP_SIMULATOR_OUTPUT = keepSimulatorOutput


class ProjectConfiguration(object):
    """Stores information necessary to configure a GameTime project.

    Attributes:
        locationFile:
            Absolute path of the file to be analyzed.
        func:
            Name of the function to analyze.
        smtSolverName:
            Name of the SMT solver used to check the satisfiability of
            SMT queries.
        startLabel:
            Label to start analysis at, if any.
        endLabel:
            Label to end analysis at, if any.
        included:
            List of the locations of directories that contain other files
            that need to be compiled and linked, but not preprocessed, with
            the file that contains the function to be analyzed,
            such as header files.
        merged:
            List of the locations of other files to be merged and preprocessed
            with the file that contains the function to be analyzed.
        inlined:
            List of the names of functions to inline.
        unrollLoops:
            True if loops present in the function being analyzed are
            to be unrolled; False otherwise.
        randomizeInitialBasis:
            True if the basis that GameTime starts the analysis with
            is to be randomized; False otherwise.
        maximumErrorScaleFactor:
            Maximum error allowed when expressing a path in terms of
            basis paths.
        determinantThreshold:
            Threshold below which the determinant of the basis matrix
            is considered "too small".
        maxInfeasiblePaths:
            Maximum number of infeasible candidate paths that can be
            explored before a row of a basis matrix is considered "bad".
        modelAsNestedArrays:
            True if multi-dimensional arrays should be modeled as
            nested arrays, or arrays whose elements can also
            be arrays, in an SMT query; False otherwise.
        preventBasisRefinement:
            True if the refinement of the basis into a 2-barycentric
            spanner should be prevented; False otherwise.
        ilpSolverName:
            Name of the integer linear programming solver used to
            solve integer linear programs to generate candidate paths.
        debugConfig:
            Debugging configuration.
    """

    def __init__(self, locationFile, func, smtSolverName,
                 startLabel="", endLabel="", included=None, merged=None,
                 inlined=None, unrollLoops=False, randomizeInitialBasis=False,
                 maximumErrorScaleFactor = 10,
                 determinantThreshold=0.001, maxInfeasiblePaths=100,
                 modelAsNestedArrays=False, preventBasisRefinement=False,
                 ilpSolverName="", debugConfig=None):
        ### FILE INFORMATION ###
        # Location of the directory that contains the file to be analyzed.
        self.locationOrigDir = ""

        # Location of the file to be analyzed.
        self.locationOrigFile = locationFile

        # Location of the file to be analyzed, without the extension.
        self.locationOrigNoExtension = ""

        # Name of the file to be analyzed.
        self.nameOrigFile = ""

        # Name of the file to be analyzed, without the extension.
        self.nameOrigNoExtension = ""

        # Location of the temporary folder that will store the temporary files
        # generated by the GameTime toolflow.
        self.locationTempDir = ""

        # Pre-constructed location of the temporary file that will be analyzed
        # by GameTime.
        self.locationTempFile = ""

        # Location of the temporary file that will be analyzed by GameTime,
        # without the extension.
        self.locationTempNoExtension = ""

        # Name of the temporary file that will be analyzed by GameTime.
        self.nameTempFile = ""

        # Name of the temporary file that will be analyzed by GameTime,
        # without the extension.
        self.nameTempNoExtension = ""

        # Location of the temporary XML file that stores
        # the project configuration information.
        self.locationXmlFile = ""

        # Name of the temporary XML file that stores
        # the project configuration information.
        self.nameXmlFile = ""

        # Name of the function to analyze.
        self.func = func

        # Label to start analysis at, if any.
        self.startLabel = startLabel

        # Label to end analysis at, if any.
        self.endLabel = endLabel

        ### PREPROCESSING VARIABLES AND FLAGS ###
        # List of the locations of directories that contain other files
        # that need to be compiled and linked, but not preprocessed, with
        # the file that contains the function to be analyzed,
        # such as header files.
        self.included = included or []

        # List of the locations of other files to be merged and preprocessed
        # with the file that contains the function to be analyzed.
        self.merged = merged or []

        # List of the names of functions to inline.
        self.inlined = inlined or []

        # Whether to unroll loops present in the function being analyzed.
        self.UNROLL_LOOPS = unrollLoops

        ### ANALYSIS VARIABLES AND FLAGS ###
        # Whether to randomize the basis that GameTime starts
        # the analysis with.
        self.RANDOMIZE_INITIAL_BASIS = randomizeInitialBasis
        
        # Maximum error allowed when expressing a path in terms of
        # basis paths.
        self.MAXIMUM_ERROR_SCALE_FACTOR = maximumErrorScaleFactor

        # Threshold below which the determinant of the basis matrix
        # is considered "too small".
        self.DETERMINANT_THRESHOLD = determinantThreshold

        # Maximum number of infeasible candidate paths that can be explored
        # before a row of a basis matrix is considered "bad".
        self.MAX_INFEASIBLE_PATHS = maxInfeasiblePaths

        # Whether to model multi-dimensional arrays as nested arrays,
        # or arrays whose elements can also be arrays, in an SMT query.
        self.MODEL_AS_NESTED_ARRAYS = modelAsNestedArrays

        # Whether to prevent the refinement of the basis into
        # a 2-barycentric spanner.
        self.PREVENT_BASIS_REFINEMENT = preventBasisRefinement

        #TODO: comment here
        self.OVER_COMPLETE_BASIS = False
        self.OB_EXTRACTION = False

        # PuLP solver object that represents the integer linear
        # programming solver used to solve integer linear programs
        # to generate candidate paths.
        self.ilpSolver = None

        # Solver object that represents the SMT solver used to check
        # the satisfiability of SMT queries.
        self.smtSolver = None

        # ModelParser object used to parse the models generated by
        # the SMT solver in response to satisfiable SMT queries.
        self.smtModelParser = None

        ### DEBUGGING ###
        # Debugging configuration.
        self.debugConfig = debugConfig or DebugConfiguration()

        ### INITIALIZATION ###
        # Infer the file path without the file extension.
        locationOrigWithExtension = self.locationOrigFile
        locationOrigNoExtension, extension = \
        os.path.splitext(locationOrigWithExtension)

        if extension.lower() == ".c":
            self.locationOrigNoExtension = locationOrigNoExtension
        else:
            errMsg = ("Error running the project configuration "
                      "reader: the name of the file to analyze "
                      "does not end with a `.c` extension.")
            raise GameTimeError(errMsg)

        # Infer the directory that contains the file to analyze.
        locationOrigDir = os.path.dirname(locationOrigWithExtension)
        self.locationOrigDir = locationOrigDir

        # Infer the name of the file, both with
        # and without the extension.
        nameOrigFile = os.path.basename(locationOrigWithExtension)
        self.nameOrigFile = nameOrigFile
        self.nameOrigNoExtension = os.path.splitext(nameOrigFile)[0]

        # Infer the name of the temporary directory where
        # GameTime stores its temporary files during its toolflow.
        self.locationTempDir = ("%s%s" %
                                (locationOrigNoExtension, config.TEMP_SUFFIX))

        # Create the temporary directory, if not already present.
        locationTempDir = self.locationTempDir
        if not os.path.exists(locationTempDir):
            os.mkdir(locationTempDir)

        # Infer the name and location of the temporary file to be analyzed
        # by GameTime, both with and without the extension.
        nameOrigNoExtension = self.nameOrigNoExtension
        nameTempNoExtension = ("%s%s" %
                               (nameOrigNoExtension, config.TEMP_SUFFIX))
        self.nameTempNoExtension = nameTempNoExtension
        nameTempFile = "%s.c" % nameTempNoExtension
        self.nameTempFile = nameTempFile

        locationTempFile = \
        os.path.normpath(os.path.join(locationTempDir, nameTempFile))
        self.locationTempFile = locationTempFile
        self.locationTempNoExtension = os.path.splitext(locationTempFile)[0]

        # Infer the name and location of the temporary XML file that
        # stores the project configuration information.
        nameXmlFile = "%s.xml" % config.TEMP_PROJECT_CONFIG
        self.nameXmlFile = nameXmlFile
        self.locationXmlFile = \
        os.path.normpath(os.path.join(locationTempDir, nameXmlFile))

        # Initialize the PuLP solver object that interfaces with
        # the ILP solver whose name is provided.
        self.setIlpSolver(ilpSolverName)
        #self.setIlpSolver("cplex")

        # Initialize the Solver and ModelParser objects.
        self.setSmtSolverAndModelParser(smtSolverName)

    def setIlpSolver(self, ilpSolverName):
        """
        Sets the PuLP solver object associated with this
        :class:`~gametime.projectConfiguration.ProjectConfiguration`
        object to one that can interface with the integer
        linear programming solver whose name is provided.

        Arguments:
            ilpSolverName:
                Name of an integer linear programming solver.
        """
        def _ilpSolverErrMsg(ilpSolverName):
            """
            Arguments:
                ilpSolverName:
                    Name of an integer linear programming solver.

            Returns:
                Error message that informs the user that the integer
                linear programming solver, whose name is provided, cannot
                be used for this GameTime project.
            """
            if ilpSolverName == "":
                return ("The default integer linear programming solver "
                        "of the PuLP package was not found. "
                        "This GameTime project cannot use it as its "
                        "backend integer linear programming solver.")
            ilpSolverName = pulpHelper.getProperName(ilpSolverName)
            return ("The integer linear programming solver %s "
                    "was not found. This GameTime project cannot use %s "
                    "as its backend integer linear programming solver." %
                    (ilpSolverName, ilpSolverName))

        ilpSolverName = ilpSolverName.lower()
        if not pulpHelper.isIlpSolverName(ilpSolverName):
            errMsg = ("Incorrect option specified for the integer "
                      "linear programming solver: %s") % ilpSolverName
            raise GameTimeError(errMsg)
        else:
            ilpSolver = pulpHelper.getIlpSolver(ilpSolverName, self)
            if ilpSolver is not None:
                self.ilpSolver = ilpSolver
            else:
                raise GameTimeError(_ilpSolverErrMsg(ilpSolverName))

    def setSmtSolverAndModelParser(self, smtSolverName):
        """
        Sets the SMT solver and model parser objects associated with this
        :class:`~gametime.projectConfiguration.ProjectConfiguration`
        object to ones that can interface with the SMT solver
        whose name is provided.

        Arguments:
            smtSolverName:
                Name of an SMT solver.
        """
        smtSolverName = smtSolverName.lower()
        if smtSolverName.startswith("boolector"):
            if config.SOLVER_BOOLECTOR == "":
                errMsg = ("The Boolector executable was not found "
                          "during the configuration of GameTime. "
                          "This GameTime project cannot use Boolector "
                          "as its backend SMT solver.")
                raise GameTimeError(errMsg)
            else:
                from smt.solvers.boolectorSolver import BoolectorSolver
                from smt.solvers.boolectorSolver import SatSolver
                satSolverName = smtSolverName[len("boolector"):]
                satSolverName = satSolverName.split("-")[-1]
                boolectorSatSolver = \
                SatSolver.getSatSolver(satSolverName)
                self.smtSolver = BoolectorSolver(boolectorSatSolver)

                from smt.parsers.boolectorModelParser \
                import BoolectorModelParser
                self.smtModelParser = BoolectorModelParser()
        elif smtSolverName == "z3":
            if config.SOLVER_Z3 == "":
                errMsg = ("The Z3 Python frontend was not found "
                          "during the configuration of GameTime. "
                          "This GameTime project cannot use Z3 "
                          "as its backend SMT solver.")
                raise GameTimeError(errMsg)
            else:
                from smt.solvers.z3Solver import Z3Solver
                self.smtSolver = Z3Solver()
                from smt.parsers.z3ModelParser import Z3ModelParser
                self.smtModelParser = Z3ModelParser()
        elif smtSolverName == "":
            errMsg = "SMT solver not specified."
            raise GameTimeError(errMsg)
        else:
            errMsg = ("Incorrect option specified for "
                      "the SMT solver: %s") % smtSolverName
            raise GameTimeError(errMsg)

    def writeToXmlFile(self, locationXmlFile=None):
        """
        Writes the project configuration information to an XML file.

        Arguments:
            locationXmlFile:
                Location of the XML file. If this is not provided,
                the XML file will be located in the temporary
                directory where GameTime stores its temporary files.
        """
        locationXmlFile = locationXmlFile or self.locationXmlFile

        xmlDoc = minidom.Document()

        # Begin the construction of the XML node tree with the root node.
        projectRoot = xmlDoc.createElement("gametime-project")
        xmlDoc.appendChild(projectRoot)

        # Create the XML node that stores information about
        # the file to be analyzed.
        fileNode = xmlDoc.createElement("file")
        projectRoot.appendChild(fileNode)

        locationNode = xmlDoc.createElement("location")
        locationNode.appendChild(xmlDoc.createTextNode(self.locationOrigFile))
        fileNode.appendChild(locationNode)

        funcNode = xmlDoc.createElement("analysis-function")
        funcNode.appendChild(xmlDoc.createTextNode(self.func))
        fileNode.appendChild(funcNode)

        startLabelNode = xmlDoc.createElement("start-label")
        startLabelNode.appendChild(xmlDoc.createTextNode(self.startLabel))
        fileNode.appendChild(startLabelNode)

        endLabelNode = xmlDoc.createElement("end-label")
        endLabelNode.appendChild(xmlDoc.createTextNode(self.endLabel))
        fileNode.appendChild(endLabelNode)

        # Create the XML node that stores the preprocessing
        # variables and flags.
        preprocessingNode = xmlDoc.createElement("preprocess")
        projectRoot.appendChild(preprocessingNode)

        includeNode = xmlDoc.createElement("include")
        includeNode.appendChild(xmlDoc.createTextNode(" ".join(self.included)))
        preprocessingNode.appendChild(includeNode)

        mergeNode = xmlDoc.createElement("merge")
        mergeNode.appendChild(xmlDoc.createTextNode(" ".join(self.merged)))
        preprocessingNode.appendChild(mergeNode)

        inlineNode = xmlDoc.createElement("inline")
        inlineNode.appendChild(xmlDoc.createTextNode(" ".join(self.inlined)))
        preprocessingNode.appendChild(inlineNode)

        if self.UNROLL_LOOPS:
            unrollLoopsNode = xmlDoc.createElement("unroll-loops")
            preprocessingNode.appendChild(unrollLoopsNode)

        # Create the XML node that stores the analysis variables and flags.
        analysisNode = xmlDoc.createElement("analysis")
        projectRoot.appendChild(analysisNode)

        if self.RANDOMIZE_INITIAL_BASIS:
            randomizeInitialBasisNode = \
            xmlDoc.createElement("randomize-initial-basis")
            analysisNode.appendChild(randomizeInitialBasisNode)

        maximumErrorScaleFactorNode = \
        xmlDoc.createElement("maximum-error-scale-factor")
        basisErrorNode = xmlDoc.createTextNode("%g" %
                                               self.MAXIMUM_ERROR_SCALE_FACTOR)
        maximumErrorScaleFactorNode.appendChild(basisErrorNode)

        determinantThresholdNode = \
        xmlDoc.createElement("determinant-threshold")
        thresholdAmountNode = xmlDoc.createTextNode("%g" %
                                                    self.DETERMINANT_THRESHOLD)
        determinantThresholdNode.appendChild(thresholdAmountNode)
        analysisNode.appendChild(determinantThresholdNode)

        maxInfeasiblePathsNode = xmlDoc.createElement("max-infeasible-paths")
        numInfeasiblePathsNode = \
        xmlDoc.createTextNode("%g" % self.MAX_INFEASIBLE_PATHS)
        maxInfeasiblePathsNode.appendChild(numInfeasiblePathsNode)
        analysisNode.appendChild(maxInfeasiblePathsNode)

        if self.MODEL_AS_NESTED_ARRAYS:
            modelAsNestedArraysNode = \
            xmlDoc.createElement("model-as-nested-arrays")
            analysisNode.appendChild(modelAsNestedArraysNode)

        if self.PREVENT_BASIS_REFINEMENT:
            preventBasisRefinementNode = \
            xmlDoc.createElement("prevent-basis-refinement")
            analysisNode.appendChild(preventBasisRefinementNode)

        ilpSolverNode = xmlDoc.createElement("ilp-solver")
        ilpSolverName = pulpHelper.getIlpSolverName(self.ilpSolver)
        ilpSolverNode.appendChild(xmlDoc.createTextNode(ilpSolverName))
        analysisNode.appendChild(ilpSolverNode)

        smtSolverNode = xmlDoc.createElement("smt-solver")
        smtSolverNode.appendChild(xmlDoc.createTextNode(str(self.smtSolver)))
        analysisNode.appendChild(smtSolverNode)

        # Create the XML node that stores the debug flags.
        debugNode = xmlDoc.createElement("debug")
        projectRoot.appendChild(debugNode)

        if self.debugConfig.KEEP_CIL_TEMPS:
            keepCilTempsNode = xmlDoc.createElement("keep-cil-temps")
            debugNode.appendChild(keepCilTempsNode)

        if self.debugConfig.DUMP_IR:
            dumpIrNode = xmlDoc.createElement("dump-ir")
            debugNode.appendChild(dumpIrNode)

        if self.debugConfig.KEEP_ILP_SOLVER_OUTPUT:
            keepIlpSolverOutputNode = \
            xmlDoc.createElement("keep-ilp-solver-output")
            debugNode.appendChild(keepIlpSolverOutputNode)

        if self.debugConfig.DUMP_PATH:
            dumpPathNode = xmlDoc.createElement("dump-path")
            debugNode.appendChild(dumpPathNode)

        if self.debugConfig.DUMP_ALL_PATHS:
            dumpAllPathsNode = xmlDoc.createElement("dump-all-paths")
            debugNode.appendChild(dumpAllPathsNode)

        if self.debugConfig.DUMP_INSTRUCTION_TRACE:
            dumpInstrTraceNode = xmlDoc.createElement("dump-instruction-trace")
            debugNode.appendChild(dumpInstrTraceNode)

        if self.debugConfig.DUMP_SMT_TRACE:
            dumpSmtTraceNode = xmlDoc.createElement("dump-smt-trace")
            debugNode.appendChild(dumpSmtTraceNode)

        if self.debugConfig.DUMP_ALL_QUERIES:
            dumpAllQueriesNode = xmlDoc.createElement("dump-all-queries")
            debugNode.appendChild(dumpAllQueriesNode)

        if self.debugConfig.KEEP_PARSER_OUTPUT:
            keepParserOutputNode = xmlDoc.createElement("keep-parser-output")
            debugNode.appendChild(keepParserOutputNode)

        if self.debugConfig.KEEP_SIMULATOR_OUTPUT:
            keepSimulatorOutputNode = \
            xmlDoc.createElement("keep-simulator-output")
            debugNode.appendChild(keepSimulatorOutputNode)

        try:
            locationHandler = open(locationXmlFile, "w")
        except EnvironmentError as e:
            errMsg = ("Error creating the project configuration "
                      "XML file: %s") % e
            raise GameTimeError(errMsg)
        else:
            with locationHandler:
                # Create the pretty-printed text version of the XML node tree.
                prettyPrinted = xmlDoc.toprettyxml(indent="    ")
                locationHandler.write(prettyPrinted)


def _getText(node):
    """
    Arguments:
        node:
            Node to extract the text from.

    Returns:
        Text from the node provided.
    """
    return " ".join(child.data.strip() for child in node.childNodes
                    if child.nodeType == child.TEXT_NODE)

def getDirPaths(dirPathsStr, dirLocation=None):
    """
    Gets a list of directory paths from the string provided, where
    the directory paths are separated by whitespaces or commas.

    Arguments:
        dirPathsStr:
            String of directory paths.
        dirLocation:
            Directory to which the directory paths may be relative.

    Returns:
        List of directory paths in the string.
    """
    dirPaths = re.split(r"[\s,]+", dirPathsStr)

    result = []
    for dirPath in dirPaths:
        if dirLocation is not None:
            dirPath = os.path.join(dirLocation, dirPath)
        result.append(os.path.normpath(dirPath))
    return result

def getFilePaths(filePathsStr, dirLocation=None):
    """
    Gets a list of file paths from the string provided, where the file
    paths are separated by whitespaces or commas. The paths can also be
    Unix-style globs.

    Arguments:
        filePathsStr:
            String of file paths.
        dirLocation:
            Directory to which the file paths may be relative.

    Returns:
        List of file paths in the string.
    """
    filePaths = re.split(r"[\s,]+", filePathsStr)

    result = []
    for filePath in filePaths:
        if dirLocation is not None:
            filePath = os.path.join(dirLocation, filePath)
        for location in glob.iglob(filePath):
            result.append(os.path.normpath(location))
    return result

def getFuncNames(funcNamesStr):
    """
    Gets a list of function names from the string provided, where
    the function names are separated by whitespaces or commas.

    Arguments:
        funcNamesStr:
            String of function names.

    Returns:
        List of function names in the string.
    """
    return re.split(r"[\s,]+", funcNamesStr)

def readProjectConfigFile(location):
    """
    Reads project configuration information from the XML file provided.

    Arguments:
        location:
            Location of the XML file that contains project
            configuration information.

    Returns:
        :class:`~gametime.projectConfiguration.ProjectConfiguration` object
        that contains information from the XML file whose location is provided.
    """
    logger.info("Reading project configuration in %s..." % location)

    if not os.path.exists(location):
        errMsg = "Cannot find project configuration file: %s" % location
        raise GameTimeError(errMsg)

    try:
        projectConfigDom = minidom.parse(location)
    except EnvironmentError as e:
        errMsg = "Error reading from project configuration file: %s" % e
        raise GameTimeError(errMsg)

    # Check that the root element is properly named.
    rootNode = projectConfigDom.documentElement
    if rootNode.tagName != 'gametime-project':
        raise GameTimeError("The root element in the XML file should be "
                            "named `gametime-project'.")

    # Check that no child element of the root element has an illegal tag.
    rootChildNodes = [node for node in rootNode.childNodes
                      if node.nodeType == node.ELEMENT_NODE]
    for childNode in rootChildNodes:
        childNodeTag = childNode.tagName
        if childNodeTag not in ["file", "preprocess", "analysis", "debug"]:
            raise GameTimeError("Unrecognized tag: %s" % childNodeTag)

    # Find the directory that contains the project configuration XML file.
    projectConfigDir = os.path.dirname(os.path.abspath(location))

    # Initialize the instantiation variables for
    # the ProjectConfiguration object.
    locationFile, func = "", ""
    startLabel, endLabel = "", ""
    included, merged, inlined, unrollLoops = [], [], [], False
    randomizeInitialBasis = False
    maximumErrorScaleFactor = 10
    determinantThreshold, maxInfeasiblePaths = 0.001, 100
    modelAsNestedArrays, preventBasisRefinement = False, False
    ilpSolverName, smtSolverName = "", ""

    # Process information about the file to be analyzed.
    fileNode = (projectConfigDom.getElementsByTagName("file"))[0]

    for node in fileNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "location":
                locationFile = \
                os.path.normpath(os.path.join(projectConfigDir, nodeText))
            elif nodeTag == "analysis-function":
                func = nodeText
            elif nodeTag == "start-label":
                startLabel = nodeText
            elif nodeTag == "end-label":
                endLabel = nodeText
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the preprocessing variables and flags.
    preprocessingNode = \
    (projectConfigDom.getElementsByTagName("preprocess"))[0]

    for node in preprocessingNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "unroll-loops":
                unrollLoops = True
            elif nodeTag == "include":
                if nodeText != "":
                    included = getDirPaths(nodeText, projectConfigDir)
            elif nodeTag == "merge":
                if nodeText != "":
                    merged = getFilePaths(nodeText, projectConfigDir)
            elif nodeTag == "inline":
                if nodeText != "":
                    inlined = getFuncNames(nodeText)
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Process the analysis variables and flags.
    analysisNode = (projectConfigDom.getElementsByTagName("analysis"))[0]

    for node in analysisNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName
            if nodeTag == "randomize-initial-basis":
                randomizeInitialBasis = True
            elif nodeTag == "maximum-error-scale-factor":
                maximumErrorScaleFactor = float(nodeText)
            elif nodeTag == "determinant-threshold":
                determinantThreshold = float(nodeText)
            elif nodeTag == "max-infeasible-paths":
                maxInfeasiblePaths = int(nodeText)
            elif nodeTag == "model-as-nested-arrays":
                modelAsNestedArrays = True
            elif nodeTag == "prevent-basis-refinement":
                preventBasisRefinement = True
            elif nodeTag == "ilp-solver":
                ilpSolverName = nodeText
            elif nodeTag == "smt-solver":
                smtSolverName = nodeText
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Initialize the instantiation variables for the
    # DebugConfiguration object.
    keepCilTemps, dumpIr, keepIlpSolverOutput = False, False, False
    dumpInstructionTrace, dumpPath, dumpAllPaths = False, False, False
    dumpSmtTrace, dumpAllQueries = False, False
    keepParserOutput, keepSimulatorOutput = False, False

    # Process the debug flags.
    debugNode = (projectConfigDom.getElementsByTagName("debug"))[0]

    for node in debugNode.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodeText = _getText(node)
            nodeTag = node.tagName

            if nodeTag == "keep-cil-temps":
                keepCilTemps = True
            elif nodeTag == "dump-ir":
                dumpIr = True
            elif nodeTag == "keep-ilp-solver-output":
                keepIlpSolverOutput = True
            elif nodeTag == "dump-instruction-trace":
                dumpInstructionTrace = True
            elif nodeTag == "dump-path":
                dumpPath = True
            elif nodeTag == "dump-all-paths":
                dumpAllPaths = True
            elif nodeTag == "dump-smt-trace":
                dumpSmtTrace = True
            elif nodeTag == "dump-all-queries":
                dumpAllQueries = True
            elif nodeTag == "keep-parser-output":
                keepParserOutput = True
            elif nodeTag == "keep-simulator-output":
                keepSimulatorOutput = True
            else:
                raise GameTimeError("Unrecognized tag: %s" % nodeTag)

    # Instantiate a DebugConfiguration object.
    debugConfig = DebugConfiguration(keepCilTemps, dumpIr,
                                     keepIlpSolverOutput, dumpInstructionTrace,
                                     dumpPath, dumpAllPaths, dumpSmtTrace,
                                     dumpAllQueries, keepParserOutput,
                                     keepSimulatorOutput)

    # We have obtained all the information we need from the XML
    # file provided. Instantiate a ProjectConfiguration object.
    projectConfig = ProjectConfiguration(locationFile, func, smtSolverName,
                                         startLabel, endLabel,
                                         included, merged, inlined, unrollLoops,
                                         randomizeInitialBasis,
                                         maximumErrorScaleFactor,
                                         determinantThreshold,
                                         maxInfeasiblePaths,
                                         modelAsNestedArrays,
                                         preventBasisRefinement,
                                         ilpSolverName, debugConfig)
    logger.info("Successfully loaded project.")
    logger.info("")
    return projectConfig
