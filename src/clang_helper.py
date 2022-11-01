#!/usr/bin/env python

""" Functions to help interacting with clang on the command
line. Allows creation of dags
"""
from types import NoneType

import os
import subprocess
from typing import List

from defaults import config
from project_configuration import ProjectConfiguration


def compile_to_llvm(project_config: ProjectConfiguration) -> str:
    """ Compile .c file to .bc file using clang through executing
    shell commands.

    :param project_config: configuration object of the current gametime
        analysis
    :return: path of the output .bc file
    """
    temp_dir: str = project_config.locationTempDir
    file_to_compile: str = project_config.locationOrigFile
    output_file: str = "%s.bc" % project_config.nameOrigNoExtension
    output_file = os.path.join(temp_dir, output_file)

    commands: List[str] = ["clang", "-emit-llvm", "-o", output_file, "-c", file_to_compile]
    subprocess.run(commands, check=True)
    return output_file