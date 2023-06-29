#!/usr/bin/env python

""" Functions to help interacting with clang on the command
line. Allows creation of dags
"""
import os
import subprocess
from typing import List

from file_helper import remove_files
from project_configuration import ProjectConfiguration
from defaults import logger


def compile_to_llvm(project_config: ProjectConfiguration, output_name: str = None) -> str:
    """ Compile .c file to .bc and .ll file using clang through executing
    shell commands. Should work for programs residing in a single file,
    but can be unreliable with larger programs. Recommended to use this as a
    reference rather and the user should generate their own .bc and .ll before
    passing into gametime for analysis on more complex behavior.

    :param output_name: string for the name of compiled output WITHOUT extension
        EXAMPLE: if you want to compile to ./maingt/foo.bc, set output_file to "foo"
    :param project_config: configuration object of the current gametime
        analysis
    :return: path of the output .bc file
    """
    if output_name is None:
        output_name = "compile-gt"

    # compile bc file
    file_to_compile: str = project_config.locationOrigFile
    output_file: str = project_config.get_temp_filename_with_extension(".bc", output_name)

    commands: List[str] = ["clang", "-Xclang",
                           "-O1", "-mllvm", "-disable-llvm-optzns", "-emit-llvm",
                           f"-I{project_config.gametime_path}/{project_config.flexpret_path}/programs/lib/include",
                           # "--target=riscv32", "-march=rv32i",
                           # "-disable-O0-optnone", "-emit-llvm", "-O0",
                           # "-g",
                           "-o", output_file, "-c", file_to_compile]
    subprocess.run(commands, check=True)

    # translate for .ll automatically. (optional)
    ll_output_file: str = project_config.get_temp_filename_with_extension(".ll", output_name)
    commands = ["llvm-dis", output_file, "-o", ll_output_file]
    subprocess.run(commands, check=True)
    return output_file


def compile_to_object(bc_file: str, project_config: ProjectConfiguration, output_name: str = "riscv-gt") -> str:
    # compile bc file
    output_file: str = project_config.get_temp_filename_with_extension(".o", output_name)
    commands: List[str] = ["clang", "--target=riscv32", "-march=rv32i", bc_file, "-c", "-o", output_file]
    subprocess.check_call(commands)

    ## object dump
    dump_file: str = project_config.get_temp_filename_with_extension(".dump", output_name)
    commands = ["llvm-objdump", "-S", "-d", output_file]
    dumping = subprocess.Popen(commands, stdout=subprocess.PIPE)
    subprocess.check_output(["tee", dump_file], stdin=dumping.stdout)
    dumping.wait()
    return output_file

def dump_object(object_file: str, project_config: ProjectConfiguration) -> str:
    output_file: str = project_config.get_temp_filename_with_extension(".dmp", "dumped")
    cur_cwd: str = os.getcwd()
    os.chdir(project_config.locationTempDir)  # opt generates .dot in cwd
    commands: List[str] = ["riscv32-unknown-elf-objdump", "--target=riscv32", "-march=rv32i", bc_file, "-c", "-o", output_file]
    subprocess.check_call(commands)
    os.chdir(cur_cwd)
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
    os.chdir(project_config.locationTempDir)  # opt generates .dot in cwd
    commands: List[str] = ["opt", "-enable-new-pm=0", "-dot-cfg", "-S", bc_file, "-disable-output"]
    subprocess.check_call(commands)
    os.chdir(cur_cwd)
    return output_file


def inline_functions(input_file: str, project_config: ProjectConfiguration, output_file: str = None) -> str:
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
        output_file = project_config.get_temp_filename_with_extension(".bc", "inlined-gt")

    commands = ["opt",
                "-always-inline",
                "-inline", "-inline-threshold=10000000",
                "-S", input_file,
                "-o", output_file]

    logger.info(subprocess.run(commands, check=True))
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
        output_file = project_config.get_temp_filename_with_extension(".bc", "unrolled-gt")

    commands = ["opt",
                # "-indvars",
                "-mem2reg",
                "-simplifycfg",
                "-loops",
                "-lcssa", "-loop-simplify",
                "-loop-rotate",
                "-loop-unroll",  # "-unroll-threshold=10000000", "-unroll-count=1000",
                "-S", input_file,
                "-o", output_file]

    logger.info(subprocess.run(commands, check=True))
    return output_file


def remove_temp_cil_files(project_config: ProjectConfiguration, all_temp_files=False) -> None:
    """Removes the temporary files created by CIL during its analysis.

    Arguments:
        project_config:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
        all_temp_files:
            :bool: flag to clear all files in temporary directory (if True)
            or only -gt files (if False).
    """
    # Remove the files with extension ".cil.*".
    if all_temp_files:
        remove_files([r".*"], project_config.locationTempDir)
        return

    other_temp_files = r".*\.dot"
    remove_files([other_temp_files], project_config.locationTempDir)

    other_temp_files = r".*\.bc"
    remove_files([other_temp_files], project_config.locationTempDir)

    other_temp_files = r".*\.ll"
    remove_files([other_temp_files], project_config.locationTempDir)

    # By this point, we have files that are named the same as the
    # temporary file for GameTime, but that have different extensions.
    # Remove these files.
    other_temp_files = r".*-gt\.[^c]+"
    remove_files([other_temp_files], project_config.locationTempDir)

