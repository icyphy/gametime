#!/usr/bin/env python

""" Functions to help interacting with clang on the command
line. Allows creation of dags
"""
import os
import subprocess
from typing import List

from project_configuration import ProjectConfiguration
from defaults import logger


def compile_to_llvm(project_config: ProjectConfiguration) -> str:
    """ Compile .c file to .bc and .ll file using clang through executing
    shell commands. Should work for programs residing in a single file,
    but can be unreliable with larger programs. Recommended to use this as a
    reference rather and the user should generate their own .bc and .ll before
    passing into gametime for analysis on more complex behavior.

    :param project_config: configuration object of the current gametime
        analysis
    :return: path of the output .bc file
    """
    # compile bc file
    file_to_compile: str = project_config.locationOrigFile
    output_file: str = project_config.get_temp_filename_with_extension(".bc")
    commands: List[str] = ["clang",  "-Xclang", "-disable-O0-optnone", "-emit-llvm", "-O0", "-o", output_file, "-c", file_to_compile]
    subprocess.run(commands, check=True)

    # translate for .ll automatically. (optional)
    ll_output_file: str = project_config.get_temp_filename_with_extension(".ll")
    commands = ["llvm-dis", output_file, "-o", ll_output_file]
    subprocess.run(commands, check=True)
    return output_file

def generate_dot_file(bc_file: str, project_config: ProjectConfiguration) -> str:
    """ Create dag from .bc file using opt through executing shell commands

    :param bc_file: location of the compiled llvm .bc file
    :param project_config: configuration object of the current gametime
        analysis
    :return: path of the output .dot file (/maingt/.main.dot)
    """
    output_file: str = project_config.get_temp_filename_with_extension(".dot", ".main")
    cur_cwd: str = os.getcwd()
    os.chdir(project_config.locationTempDir) # opt generates .dot in cwd
    commands: List[str] = ["opt", "-enable-new-pm=0", "-dot-cfg", "-S", bc_file, "-disable-output"]
    subprocess.check_call(commands)
    os.chdir(cur_cwd)
    return output_file

def unroll_loops(input_file: str, project_config: ProjectConfiguration, output_file: str = None) -> str:
    """ Unrolls the probided input file and output the unrolled version in
    the output file using llvm's opt utility. Could be unreliable if input_file
    is not compiled with `compile_to_llvm` function. If that is the case, the
    user might want to generate their own unrolled .bc/.ll file rather than
    relying on this built-in function.

    :param input_file: Input .bc/.ll function to loop unroll
    :param project_config: ProjectConfiguration for this project
    :param output_file: file to write unrolled .bc file. Outputs in a
        human-readable form already.
    :return: output_file that is passed in or the default output_file
    """
    if output_file is None:
        output_file = project_config.get_temp_filename_with_extension(".bc", "unrolled")

    commands = ["opt",
                "-mem2reg", "-simplifycfg", "-loops",
                "-lcssa", "-loop-simplify", "-loop-rotate",
                "-inline", "-inline-threshold=1000000",
                "-loop-unroll", "-S", input_file,
                "-o", output_file]

    logger.info(subprocess.run(commands, check=True))
    return output_file
