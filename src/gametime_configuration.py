import os
from typing import Any
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from gametime_error import GameTimeError


class Endianness(object):
    """This class represents the endianness of the target machine."""

    # Big-endian.
    BIG = 0
    # Little-endian.
    LITTLE = 1


class GametimeConfiguration(object):
    """Stores information necessary to configure GameTime."""

    def __init__(self):
        """Constructor for the GametimeConfiguration class."""

        ### GAMETIME INFORMATION ###
        # URL of the website for GameTime.
        self.WEBSITE_URL: str = ""

        # Current version number of GameTime.
        self.VERSION: str = ""

        # URL that provides information about
        # the latest version of GameTime.
        self.LATEST_VERSION_INFO_URL: str = ""

        ### FILE INFORMATION ###
        # Full location of the configuration file.
        self.config_file: str = ""

        # Directory that contains the configuration file.
        self.config_dir: str = ""

        ### MEMORY LAYOUT INFORMATION ###
        # Word size on the machine that GameTime is being run on (in bits).
        # This value should be changed if GameTime will be run on a
        # non-32-bit machine.
        self.WORD_BITSIZE: int = 32

        # Word size on the machine that GameTime is being run on (in bytes).
        # This value should be changed and the solution should be recompiled,
        # if GameTime will be run on a non-32-bit machine.
        self.WORD_BYTESIZE: int = 4

        # Endianness of the target machine.
        self.ENDIANNESS: int = Endianness.LITTLE

        ### ANNOTATIONS ###
        # Annotation that is used when additional conditions need to be
        # provided to GameTime.
        self.ANNOTATION_ASSUME: str = ""

        # Annotation that is used when a simulation is performed.
        self.ANNOTATION_SIMULATE: str = ""

        ### SPECIAL IDENTIFIERS ###
        # The special identifiers and for the names and prefixes of temporary
        # files and folders are described in the default GameTime
        # configuration XML file provided in the source directory.
        self.IDENT_AGGREGATE: str = ""
        self.IDENT_CONSTRAINT: str = ""
        self.IDENT_EFC: str = ""
        self.IDENT_FIELD: str = ""
        self.IDENT_TEMPINDEX: str = ""
        self.IDENT_TEMPPTR: str = ""
        self.IDENT_TEMPVAR: str = ""

        self.TEMP_PROJECT_CONFIG: str = ""
        self.TEMP_FOLDER: str = ""
        self.TEMP_MERGED: str = ""
        self.TEMP_LOOP_CONFIG: str = ""

        self.TEMP_SUFFIX: str = ""

        self.TEMP_SUFFIX_MERGED: str = ""
        self.TEMP_SUFFIX_UNROLLED: str = ""
        self.TEMP_SUFFIX_INLINED: str = ""
        self.TEMP_SUFFIX_LINE_NUMS: str = ""

        self.TEMP_PHX_CREATE_DAG: str = ""
        self.TEMP_DAG: str = ""
        self.TEMP_DAG_ID_MAP: str = ""

        self.TEMP_PHX_IR: str = ""
        self.TEMP_PHX_FIND_CONDITIONS: str = ""

        self.TEMP_PATH_ILP_PROBLEM: str = ""
        self.TEMP_PATH_NODES: str = ""
        self.TEMP_PATH_CONDITIONS: str = ""
        self.TEMP_PATH_CONDITION_EDGES: str = ""
        self.TEMP_PATH_CONDITION_TRUTHS: str = ""
        self.TEMP_PATH_LINE_NUMBERS: str = ""
        self.TEMP_PATH_ARRAY_ACCESSES: str = ""
        self.TEMP_PATH_AGG_INDEX_EXPRS: str = ""
        self.TEMP_PATH_PREDICTED_VALUE: str = ""
        self.TEMP_PATH_MEASURED_VALUE: str = ""
        self.TEMP_PATH_ALL: str = ""

        self.TEMP_PATH_QUERY: str = ""
        self.TEMP_PATH_QUERY_ALL: str = ""

        self.TEMP_CASE: str = ""

        self.TEMP_BASIS_MATRIX: str = ""
        self.TEMP_MEASUREMENT: str = ""
        self.TEMP_BASIS_VALUES: str = ""
        self.TEMP_DAG_WEIGHTS: str = ""
        self.TEMP_DISTRIBUTION: str = ""


def read_gametime_config_yaml(yaml_config_path: str) -> GametimeConfiguration:
    """
    Creates GametimeConfiguration from yaml files

    Parameters:
        yaml_config_path: str :
            path of the yaml config file that contains

    Returns:
        GametimeConfiguration
            GametimeConfiguration object that contains information from YAML file at yaml_config_path

    """
    # Check file exists
    if not os.path.exists(yaml_config_path):
        err_msg: str = "Cannot find gametime configuration file: %s" % yaml_config_path
        raise GameTimeError(err_msg)

    # Initialize new GametimeConfiguration
    with open(yaml_config_path) as raw_gametime_file:
        gametime_confg: GametimeConfiguration = load(raw_gametime_file, Loader=Loader)

    return gametime_confg
