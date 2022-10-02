#!/usr/bin/env python

import os

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