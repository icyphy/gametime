#!/usr/bin/env python
import glob
import os
import re
import warnings
from abc import abstractmethod
from typing import Any, List, Type

from yaml import load

from defaults import logger
from gametime_error import GameTimeError, GameTimeWarning

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from src.project_configuration import ProjectConfiguration, DebugConfiguration


class ConfigurationParser(object):

    @staticmethod
    @abstractmethod
    def parse(configuration_file_path: str) -> ProjectConfiguration:
        pass


class YAMLConfigurationParser(ConfigurationParser):

    @staticmethod
    def parse(configuration_file_path: str) -> ProjectConfiguration:
        # Check configuration_file_path exits on the OS
        if not os.path.exists(configuration_file_path):
            err_msg = "Cannot find project configuration file: %s" % configuration_file_path
            raise GameTimeError(err_msg)

        # Read from configuration_file_path into a dict
        raw_config: dict[str, Any] = {}
        with open(configuration_file_path) as raw_file:
            raw_config = load(raw_file, Loader=Loader)

        # Check if yaml file contains gametime-project
        if 'gametime-project' not in raw_config.keys():
            err_msg = "Cannot find project configuration in file: %s" % configuration_file_path
            raise GameTimeError(err_msg)

        raw_config = raw_config['gametime-project']

        # Find the directory that contains the project configuration YAML file.
        project_config_dir = os.path.dirname(os.path.abspath(configuration_file_path))

        # Initialize the instantiation variables for
        # the ProjectConfiguration object.
        location_file, func = "", ""
        start_label, end_label = "", ""
        included, merged, inlined, unroll_loops = [], [], [], False
        randomize_initial_basis = False
        maximum_error_scale_factor = 10
        determinant_threshold, max_infeasible_paths = 0.001, 100
        model_as_nested_arrays, prevent_basis_refinement = False, False
        ilp_solver_name, smt_solver_name = "", ""

        # Process information about the file to be analyzed.
        file_configs: dict[str, Any] = raw_config.get("file", {})
        for key in file_configs.keys():
            match key:
                case "location":
                    location_file = os.path.normpath(os.path.join(project_config_dir, file_configs[key]))
                case "analysis-function":
                    func = file_configs[key]
                case "start-label":
                    start_label = file_configs[key]
                case "end-label":
                    end_label = file_configs[key]
                case _:
                    warnings.warn("Unrecognized tag : %s" % key, GameTimeWarning)

        # Process the preprocessing variables and flags.
        preprocess_configs: dict[str, Any] = raw_config.get("preprocess", {})
        for key in preprocess_configs.keys():
            match key:
                case "unroll-loops":
                    unroll_loops = bool(preprocess_configs[key])
                case "include":
                    if preprocess_configs[key]:
                        included = get_dir_paths(preprocess_configs[key], project_config_dir)
                case "merge":
                    if preprocess_configs[key]:
                        merged = get_file_paths(preprocess_configs[key], project_config_dir)
                case "inline":
                    inlined = preprocess_configs[key]
                case _:
                    warnings.warn("Unrecognized tag : %s" % key, GameTimeWarning)

        # Process the analysis variables and flags.
        analysis_config: dict[str, Any] = raw_config.get("analysis", {})
        for key in analysis_config.keys():
            match key:
                case "randomize-initial-basis":
                    randomize_initial_basis = bool(analysis_config[key])
                case "maximum-error-scale-factor":
                    maximum_error_scale_factor = float(analysis_config[key])
                case "determinant-threshold":
                    determinant_threshold = float(analysis_config[key])
                case "max-infeasible-paths":
                    max_infeasible_paths = int(analysis_config[key])
                case "model-as-nested-arrays":
                    model_as_nested_arrays = bool(analysis_config[key])
                case "prevent-basis-refinement":
                    prevent_basis_refinement = bool(analysis_config[key])
                case "ilp-solver":
                    ilp_solver_name = analysis_config[key]
                case "smt-solver":
                    smt_solver_name = analysis_config[key]
                case "flexpret_path":
                    flexpret_path = analysis_config[key]
                case "gametime_path":
                    gametime_path = analysis_config[key]
                case _:
                    warnings.warn("Unrecognized tag : %s" % key, GameTimeWarning)

        # Initialize the instantiation variables for the
        # DebugConfiguration object.
        keep_cil_temps, dump_ir, keep_ilp_solver_output = False, False, False
        dump_instruction_trace, dump_path, dump_all_paths = False, False, False
        dump_smt_trace, dump_all_queries = False, False
        keep_parser_output, keep_simulator_output = False, False

        debug_config: dict[str, Any] = raw_config.get("debug", {})
        for key in debug_config.keys():
            value = bool(debug_config[key])
            match key:
                case "keep-cil-temps":
                    keep_cil_temps = value
                case "dump-ir":
                    dump_ir = value
                case "keep-ilp-solver-output":
                    keep_ilp_solver_output = value
                case "dump-instruction-trace":
                    dump_instruction_trace = value
                case "dump-path":
                    dump_path = value
                case "dump-all_temp_files-paths":
                    dump_all_paths = value
                case "dump-smt-trace":
                    dump_smt_trace = value
                case "dump-all_temp_files-queries":
                    dump_all_queries = value
                case "keep-parser-output":
                    keep_parser_output = value
                case "keep-simulator-output":
                    keep_simulator_output = value
                case _:
                    warnings.warn("Unrecognized tag : %s" % key, GameTimeWarning)

        debug_configuration: DebugConfiguration = DebugConfiguration(keep_cil_temps, dump_ir,
                                                                     keep_ilp_solver_output, dump_instruction_trace,
                                                                     dump_path, dump_all_paths, dump_smt_trace,
                                                                     dump_all_queries, keep_parser_output,
                                                                     keep_simulator_output)

        project_config: ProjectConfiguration = ProjectConfiguration(location_file, func, smt_solver_name,
                                                                    start_label, end_label, included,
                                                                    merged, inlined, unroll_loops,
                                                                    randomize_initial_basis,
                                                                    maximum_error_scale_factor,
                                                                    determinant_threshold, max_infeasible_paths,
                                                                    model_as_nested_arrays, prevent_basis_refinement,
                                                                    ilp_solver_name, debug_configuration, flexpret_path,
                                                                    gametime_path)
        logger.info("Successfully loaded project.")
        logger.info("")
        return project_config


def get_dir_paths(dir_paths_str: str, dir_location: str = None) -> List[str]:
    """
    Gets a list of directory paths from the string provided, where
    the directory paths are separated by whitespaces or commas.

    Arguments:
        dir_paths_str:
            String of directory paths.
        dir_location:
            Directory to which the directory paths may be relative.

    Returns:
        List of directory paths in the string.
    """
    dir_paths = re.split(r"[\s,]+", dir_paths_str)

    result = []
    for dir_path in dir_paths:
        if dir_location is not None:
            dir_path = os.path.join(dir_location, dir_path)
        result.append(os.path.normpath(dir_path))
    return result


def get_file_paths(file_paths_str: str, dir_location: str = None) -> List[str]:
    """
    Gets a list of file paths from the string provided, where the file
    paths are separated by whitespaces or commas. The paths can also be
    Unix-style globs.

    Arguments:
        file_paths_str:
            String of file paths.
        dir_location:
            Directory to which the file paths may be relative.

    Returns:
        List of file paths in the string.
    """
    file_paths = re.split(r"[\s,]+", file_paths_str)

    result = []
    for file_path in file_paths:
        if dir_location is not None:
            file_path = os.path.join(dir_location, file_path)
        for location in glob.iglob(file_path):
            result.append(os.path.normpath(location))
    return result


extension_parser_map: dict[str, Type[ConfigurationParser]] = {".yaml": YAMLConfigurationParser}
