#!/usr/bin/env python

import os

from gametime_error import GameTimeError
from defaults import config


class DebugConfiguration(object):
    """
    Stores debugging configuration information, which
    determines the debugging information that is shown and
    the temporary files that are dumped.

    """

    def __init__(self, keep_cil_temps=False, dump_ir=False,
                 keep_ilp_solver_output=False, dump_instruction_trace=False,
                 dump_path=False, dump_all_paths=False, dump_smt_trace=False,
                 dump_all_queries=False, keep_parser_output=False,
                 keep_simulator_output=False):
        #: Keep the temporary files that CIL generates during its analysis.
        self.KEEP_CIL_TEMPS = keep_cil_temps

        #: Dump the Phoenix intermediate representation of the function
        #: under analysis to a file.
        self.DUMP_IR = dump_ir

        #: Keep debugging information and files produced by
        #: the integer linear programming solver.
        self.KEEP_ILP_SOLVER_OUTPUT = keep_ilp_solver_output

        #: Dump information produced when an IR-level instruction
        #: is traced backward.
        self.DUMP_INSTRUCTION_TRACE = dump_instruction_trace

        #: Dump information about the path being traced.
        self.DUMP_PATH = dump_path

        #: Dump information about all_temp_files of the paths that have been traced
        #: during analysis to a file.
        self.DUMP_ALL_PATHS = dump_all_paths

        #: Dump information produced when an SMT query is created.
        self.DUMP_SMT_TRACE = dump_smt_trace

        #: Dump information about all_temp_files of the SMT queries that
        #: have been made during analysis to a file.
        self.DUMP_ALL_QUERIES = dump_all_queries

        #: Keep the debugging information and the temporary files
        #: produced by the parser.
        self.KEEP_PARSER_OUTPUT = keep_parser_output

        #: Keep the temporary files produced by a simulator when
        #: measuring the value of a path.
        self.KEEP_SIMULATOR_OUTPUT = keep_simulator_output


class ProjectConfiguration(object):
    """
    Stores information necessary to configure a GameTime project.
    """

    def __init__(self, location_file,  func, location_additional_files=None,
                 start_label="", end_label="", included=None, merged=None,
                 inlined=None, unroll_loops=False, randomize_initial_basis=False,
                 maximum_error_scale_factor=10,
                 determinant_threshold=0.001, max_infeasible_paths=100,
                 model_as_nested_arrays=False, prevent_basis_refinement=False,
                 ilp_solver_name="", debug_config=None, gametime_flexpret_path="", 
                 gametime_path="", gametime_file_path="", compile_flags=[], backend=""):
        ### FILE INFORMATION ###
        # Location of the directory that contains the file to be analyzed.
        self.location_orig_dir = ""

        # Location of the file to be analyzed.
        self.location_orig_file = location_file
        
        # Location of the additional files to be analyzed.
        self.location_additional_files = location_additional_files or []

        # Location of the file to be analyzed, without the extension.
        self.location_orig_no_extension = ""

        # Name of the file to be analyzed.
        self.name_orig_file = ""

        # Name of the file to be analyzed, without the extension.
        self.name_orig_no_extension = ""

        # Location of the temporary folder that will store the temporary files
        # generated by the GameTime toolflow.
        self.location_temp_dir = ""

        # Pre-constructed location of the temporary file that will be analyzed
        # by GameTime.
        self.location_temp_file = ""

        # Location of the temporary file that will be analyzed by GameTime,
        # without the extension.
        self.location_temp_no_extension = ""

        # Name of the temporary file that will be analyzed by GameTime.
        self.name_temp_file = ""

        # Name of the temporary file that will be analyzed by GameTime,
        # without the extension.
        self.name_temp_no_extension = ""

        # Location of the temporary XML file that stores
        # the project configuration information.
        self.location_xml_file = ""

        # Name of the temporary XML file that stores
        # the project configuration information.
        self.name_xml_file = ""

        # Name of the function to analyze.
        self.func = func

        # Label to start analysis at, if any.
        self.start_label = start_label

        # Label to end analysis at, if any.
        self.end_label = end_label

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
        self.UNROLL_LOOPS = unroll_loops

        ### ANALYSIS VARIABLES AND FLAGS ###
        # Whether to randomize the basis that GameTime starts
        # the analysis with.
        self.RANDOMIZE_INITIAL_BASIS = randomize_initial_basis

        # Maximum error allowed when expressing a path in terms of
        # basis paths.
        self.MAXIMUM_ERROR_SCALE_FACTOR = maximum_error_scale_factor

        # Threshold below which the determinant of the basis matrix
        # is considered "too small".
        self.DETERMINANT_THRESHOLD = determinant_threshold

        # Maximum number of infeasible candidate paths that can be explored
        # before a row of a basis matrix is considered "bad".
        self.MAX_INFEASIBLE_PATHS = max_infeasible_paths

        # Whether to model multi-dimensional arrays as nested arrays,
        # or arrays whose elements can also be arrays, in an SMT query.
        self.MODEL_AS_NESTED_ARRAYS = model_as_nested_arrays

        # Whether to prevent the refinement of the basis into
        # a 2-barycentric spanner.
        self.PREVENT_BASIS_REFINEMENT = prevent_basis_refinement

        # TODO: comment here
        self.OVER_COMPLETE_BASIS = False
        self.OB_EXTRACTION = False

        # PuLP solver object that represents the integer linear
        # programming solver used to solve integer linear programs
        # to generate candidate paths.
        self.ilp_solver = None

        ### DEBUGGING ###
        # Debugging configuration.
        self.debug_config = debug_config or DebugConfiguration()

        ### INITIALIZATION ###
        # Infer the file path without the file extension.
        location_orig_with_extension = self.location_orig_file
        location_orig_no_extension, extension = \
            os.path.splitext(location_orig_with_extension)

        if extension.lower() == ".c":
            self.location_orig_no_extension = location_orig_no_extension
        else:
            err_msg = ("Error running the project configuration "
                      "reader: the name of the file to analyze "
                      "does not end with a `.c` extension.")
            raise GameTimeError(err_msg)

        # Infer the directory that contains the file to analyze.
        location_orig_dir = os.path.dirname(location_orig_with_extension)
        self.location_orig_dir = location_orig_dir

        # Infer the name of the file, both with
        # and without the extension.
        name_orig_file = os.path.basename(location_orig_with_extension)
        self.name_orig_file = name_orig_file
        self.name_orig_no_extension = os.path.splitext(name_orig_file)[0]

        # Infer the name of the temporary directory where
        # GameTime stores its temporary files during its toolflow.
        self.location_temp_dir = ("%s%s" %
                                (location_orig_no_extension, config.TEMP_SUFFIX))

        # Create the temporary directory, if not already present.
        location_temp_dir = self.location_temp_dir
        if not os.path.exists(location_temp_dir):
            os.mkdir(location_temp_dir)

        # Infer the name and location of the temporary file to be analyzed
        # by GameTime, both with and without the extension.
        name_orig_no_extension = self.name_orig_no_extension
        name_temp_no_extension = ("%s%s" %
                                  (name_orig_no_extension, config.TEMP_SUFFIX))
        self.name_temp_no_extension = name_temp_no_extension
        name_temp_file = "%s.c" % name_temp_no_extension
        self.name_temp_file = name_temp_file

        location_temp_file = \
            os.path.normpath(os.path.join(location_temp_dir, name_temp_file))
        self.location_temp_file = location_temp_file
        self.location_temp_no_extension = os.path.splitext(location_temp_file)[0]

        # Infer the name and location of the temporary XML file that
        # stores the project configuration information.
        name_xml_file = "%s.xml" % config.TEMP_PROJECT_CONFIG
        self.name_xml_file = name_xml_file
        self.location_xml_file = \
            os.path.normpath(os.path.join(location_temp_dir, name_xml_file))

        # Initialize the PuLP solver object that interfaces with
        # the ILP solver whose name is provided.
        self.set_ilp_solver(ilp_solver_name)
        # self.setIlpSolver("cplex")

        # Relative path to the FlexPRET repo from the GameTime repo. Needed to run FlexPRET Simulator.
        self.gametime_flexpret_path = gametime_flexpret_path

        # Relative path to the GameTime repo from the simulation running folder. Needed to run FlexPRET Simulator.
        self.gametime_path = gametime_path

        # Relative path to the GameTime repo from the simulated file. Needed to run FlexPRET Simulator.
        self.gametime_file_path = gametime_file_path

        # Additional flags needed when compiling the program
        self.compile_flags = compile_flags

        # Backend to execute against
        self.backend = backend

    def set_ilp_solver(self, ilp_solver_name):
        """

        Parameters:
            ilp_solver_name: str:
                ILP solver name to use

        """
        # TODO: Make it real
        self.ilp_solver = ilp_solver_name.lower()

    def get_temp_filename_with_extension(self, extension: str, name: str = None) -> str:
        """
        Return path of temporary file with name and extension. Extension should
        be preceded by a period. For example, calling this function with extension
        ".bc" should return something like ".... maingt/main.bc"

        Parameters:
            extension: str :
                extension of the temporary file name
            name: str :
                name of the temporary file (defaults to self.nameOrigNoExtension) (Default value = None)

        Returns:
            str:
                path of the temporary file

        """
        if name is None:
            name = self.name_orig_no_extension
        filename: str = name + extension
        temp_filename: str = os.path.join(self.location_temp_dir, filename)
        return temp_filename

    def get_orig_filename_with_extension(self, extension: str, name: str = None) -> str:
        """
        Return path of file with name and extension. Extension should
        be preceded by a period. For example, calling this function with extension
        ".bc" should return something like ".... /main.bc"

        Parameters:
            extension: str :
                extension of the file
            name: str :
                name of the file (defaults to self.nameOrigNoExtension) (Default value = None)
        Returns:
            str:
                path of the file in the original directory.
        """
        if name is None:
            name = self.name_orig_no_extension
        filename: str = name + extension
        orig_filename: str = os.path.join(self.location_orig_dir, filename)
        return orig_filename

