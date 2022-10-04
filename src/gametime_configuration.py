import os
from typing import Any
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from defaults import logger
from gametime_error import GameTimeError


class Endianness(object):
    """This class represents the endianness of the target machine."""
    # Big-endian.
    BIG = 0
    # Little-endian.
    LITTLE = 1


class GametimeConfiguration(object):
    """Stores information necessary to configure GameTime.
    """

    def __init__(self):
        """Constructor for the GametimeConfiguration class."""

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


def read_gametime_config_yaml(yaml_config_path: str) -> GametimeConfiguration:
    """Creates GametimeConfiguration from yaml files
    Arguments:
        yaml_config_path: path of the yaml config file that contains
            gamtime configuration information

    Returns:
        GametimeConfiguration object that contains information from YAML file at
            yaml_config_path
    """
    # Check file exists
    if not os.path.exists(yaml_config_path):
        err_msg = "Cannot find gametime configuration file: %s" % yaml_config_path
        raise GameTimeError(err_msg)

    # Initialize new GametimeConfiguration
    # gametime_confg: GametimeConfiguration = GametimeConfiguration()
    with open(yaml_config_path) as raw_gametime_file:
        gametime_confg: GametimeConfiguration = load(raw_gametime_file, Loader=Loader)

    # gametime_confg.__dict__.update(**raw_gametime_config)
    return gametime_confg
