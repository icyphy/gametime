#!/usr/bin/env python

""" Functions to help interacting with clang on the command
line. Allows creation of dags
"""

import os
import subprocess
from typing import List

from project_configuration import ProjectConfiguration


def compile_to_llvm(project_config: ProjectConfiguration) -> str:
    """ Compile .c file to .bc and .ll file using clang through executing
    shell commands.

    :param project_config: configuration object of the current gametime
        analysis
    :return: path of the output .bc file
    """
    # compile bc file
    file_to_compile: str = project_config.locationOrigFile
    output_file: str = project_config.get_temp_filename_with_extension(".bc")
    commands: List[str] = ["clang", "-emit-llvm", "-o", output_file, "-c", file_to_compile]
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
    :return: path of the output .dot file
    """
    output_file: str = project_config.get_temp_filename_with_extension(".dot", ".main")
    cur_cwd: str = os.getcwd()
    os.chdir(project_config.locationTempDir) # opt generates .dot in cwd
    commands: List[str] = ["opt", "-enable-new-pm=0", "-dot-cfg", "-S", bc_file, "-disable-output"]
    subprocess.check_call(commands)
    os.chdir(cur_cwd)
    return output_file
