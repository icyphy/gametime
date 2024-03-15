#!/usr/bin/env python

""" Functions to help interacting with clang on the command
line. Allows creation of dags
"""
import os
import subprocess
from typing import List

from defaults import logger
from file_helper import remove_files
from project_configuration import ProjectConfiguration


def compile_to_llvm_for_exec(c_file_path: str, output_file_folder: str, output_name: str, extra_libs: List[str]=[], extra_flags: List[str]=[]) -> str:
    # compile bc file
    file_to_compile: str = c_file_path
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

    commands: List[str] = ["clang", "-emit-llvm", "-O0", "-o", output_file, "-c", file_to_compile] + extra_flags
    for lib in extra_libs:
        commands.append(f"-I{lib}")
    subprocess.run(commands, check=True)

    # translate for .ll automatically. (optional)
    ll_output_file: str = os.path.join(output_file_folder, f"{output_name}.ll")
    commands = ["llvm-dis", output_file, "-o", ll_output_file]
    subprocess.run(commands, check=True)
    return output_file

def compile_to_llvm_for_analysis(c_file_path: str, output_file_folder: str, output_name: str, extra_libs: List[str]=[], extra_flags: List[str]=[]) -> str:
    # compile bc file
    file_to_compile: str = c_file_path
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

    commands: List[str] = ["clang", "-emit-llvm", "-O0","-Xclang", "-disable-O0-optnone", "-o", output_file, "-c", file_to_compile] + extra_flags
    for lib in extra_libs:
        commands.append(f"-I{lib}")
    subprocess.run(commands, check=True)

    # translate for .ll automatically. (optional)
    ll_output_file: str = os.path.join(output_file_folder, f"{output_name}.ll")
    commands = ["llvm-dis", output_file, "-o", ll_output_file]
    subprocess.run(commands, check=True)
    return output_file


def bc_to_object(path_bc_filepath: str, output_file_folder: str, output_name: str, extra_flags: List[str]=[]) -> str:
    """ Compile .bc file to .o file using clang through executing shell commands

    :param path_bc_filepath: file path to the .bc file used for compilation
    :param gametime_path: Relative path to the GameTime repo from the simulation running folder.
    :param gametime_flexpret_path: Relative path to the GameTime repo from the simulated file.
    :param output_file_folder:  file path to the output folder where to .o file is saved to
    :param output_name: string for the name of compiled output WITHOUT extension
    :return: path of the output .o file
    """
    output_file: str = os.path.join(output_file_folder, f"{output_name}.o")
    # compile bc file

    commands = ["clang", "-o", output_file, "-c", path_bc_filepath] + extra_flags

    subprocess.check_call(commands)

    ## object dump
    dump_file: str = os.path.join(output_file_folder, f"{output_name}.dump")
    commands = ["llvm-objdump", "-S", "-d", output_file]
    dumping = subprocess.Popen(commands, stdout=subprocess.PIPE)
    subprocess.check_output(["tee", dump_file], stdin=dumping.stdout)
    dumping.wait()
    return output_file

def bc_to_executable(bc_file_path: str, output_folder: str, executable_name: str, extra_libs: List[str]=[], extra_flags: List[str]=[]) -> str:
    """ Compile .bc file to executable using clang.
    :param bc_file_path: path of the .bc file to compile
    :param output_folder: the folder path where the executable will be stored
    :param executable_name: string for the name of the executable WITHOUT extension
    :param extra_flags: additional flags to pass to clang during compilation
    :param extra_libs: paths to any additional libraries or include directories required for compilation
    :return: path of the output executable file
    """

    # Set the path for the output executable file
    executable_file = os.path.join(output_folder, executable_name)

    # Prepare the clang command
    clang_commands = ["clang", bc_file_path, "-o", executable_file] + extra_flags

    # Add extra include directories or libraries
    for lib in extra_libs:
        clang_commands.extend(["-I", lib])

    # Run clang to compile the bitcode into an executable
    subprocess.run(clang_commands, check=True)

    return executable_file


def dump_object(object_file: str, output_file_folder: str, o_file_dir: str) -> str:
    """ Dump the .o file to dumped.dmp

    :param object_file: the name of the .o file to dump
    :param output_file_folder: the folder path where .dmp files will be stored
    :param o_file_dir: directory containing the .o file
    :return: path of the output dumped.dmp file
    """

    output_file: str = os.path.join(output_file_folder, "dumped.dmp")
    cur_cwd: str = os.getcwd()
    os.chdir(o_file_dir)  # opt generates .dmp in cwd
    commands: List[str] = ["riscv32-unknown-elf-objdump", "--target=riscv32", "-march=rv32i", object_file, "-c", "-o", output_file]
    subprocess.check_call(commands)
    os.chdir(cur_cwd)
    return output_file

def generate_dot_file(bc_file: str, bc_file_folder: str) -> str:
    """ Create dag from .bc file using opt through executing shell commands

    :param bc_file: location of the compiled llvm .bc file
    :param bc_file_folder: the folder path where .bc files is stored and where .main.dot file will be stored
    :return: path of the output .dot file
    """
    output_file: str = ".main.dot"
    cur_cwd: str = os.getcwd()
    os.chdir(bc_file_folder)  # opt generates .dot in cwd
    commands: List[str] = ["opt", "-dot-cfg", "-S", bc_file, "-disable-output"]
    subprocess.check_call(commands)
    os.chdir(cur_cwd)
    return output_file


def inline_functions(input_file: str, output_file_folder: str, output_name: str) -> str:
    """ Unrolls the provided input file and output the unrolled version in
    the output file using llvm's opt utility. Could be unreliable if input_file
    is not compiled with `compile_to_llvm_for_analysis` function. If that is the case, the
    user might want to generate their own unrolled .bc/.ll file rather than
    relying on this built-in function.

    :param input_file: Input .bc/.ll function to loop unroll
    :param output_file_folder: folder to write unrolled .bc file. Outputs in a
        human-readable form already.
    :param output_name: file to write unrolled .bc file. Outputs in a
        human-readable form already.
    :return: output_file that is passed in
    """
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

    commands: List[str] = ["opt",
                "-always-inline",
                "-inline", "-inline-threshold=10000000",
                "-S", input_file,
                "-o", output_file]

    logger.info(subprocess.run(commands, check=True))
    return output_file
    # return input_file


def unroll_loops(input_file: str, output_file_folder: str, output_name: str) -> str:
    """ Unrolls the provided input file and output the unrolled version in
    the output file using llvm's opt utility. Could be unreliable if input_file
    is not compiled with `compile_to_llvm_for_analysis` function. If that is the case, the
    user might want to generate their own unrolled .bc/.ll file rather than
    relying on this built-in function.

    :param input_file: Input .bc/.ll function to loop unroll
    :param output_file_folder: folder to write unrolled .bc file. Outputs in a
        human-readable form already.
    :param output_name: file to write unrolled .bc file. Outputs in a
        human-readable form already.
    :return: output_file that is passed in or the default output_file
    """
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

    # commands: List[str] = ["opt",
    #             "-S", input_file,
    #             "-o", output_file]

    # commands: List[str] = ["opt",
    #             "-mem2reg",
    #             "-simplifycfg",
    #             "-loops",
    #             "-lcssa",
    #             "-loop-simplify",
    #             "-loop-rotate",
    #             "-indvars",
    #             "-loop-unroll",
    #             # "-unroll-threshold=10000000",
    #             # "-unroll-count=1000",
    #             "-unroll-allow-partial",
    #             "-S", input_file,
    #             "-o", output_file]

    # logger.info(subprocess.run(commands, check=True))
    # return output_file
    return input_file

#TODO: update this
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
        remove_files([r".*"], project_config.location_temp_dir)
        return

    other_temp_files = r".*\.dot"
    remove_files([other_temp_files], project_config.location_temp_dir)

    other_temp_files = r".*\.bc"
    remove_files([other_temp_files], project_config.location_temp_dir)

    other_temp_files = r".*\.ll"
    remove_files([other_temp_files], project_config.location_temp_dir)

    # By this point, we have files that are named the same as the
    # temporary file for GameTime, but that have different extensions.
    # Remove these files.
    other_temp_files = r".*-gt\.[^c]+"
    remove_files([other_temp_files], project_config.location_temp_dir)

