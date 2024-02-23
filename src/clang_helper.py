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


def compile_to_llvm(c_file_path: str, output_file_folder: str, output_name: str, extra_libs: List[str]=[]) -> str:
    """ Compile .c file to .bc and .ll file using clang through executing
    shell commands. Should work for programs residing in a single file,
    but can be unreliable with larger programs. Recommended to use this as a
    reference rather and the user should generate their own .bc and .ll before
    passing into gametime for analysis on more complex behavior.

    :param c_file_path: path of the .c file to compile
    :param output_file_folder: the folder path where .bc and .ll files will be stored
    :param output_name: string for the name of compiled output WITHOUT extension
    :param extra_lib: path to all the extra libraries required to compile the file. plugged into the -I flag of clang
    :return: path of the output .bc file
    """

    # compile bc file
    file_to_compile: str = c_file_path
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

    extra_libs.append('/opt/riscv/riscv32-unknown-elf/include')

    commands: List[str] = ["clang",
                           "--sysroot=/opt/riscv/riscv32-unknown-elf",
                           "-target", "riscv32-unknown-elf", 
                           "-march=rv32i", "-mabi=ilp32",
                           "-Xclang", 
                           "-O0", 
                           '-g',
                           '-D_REENT_SMALL',
                           '-DPRINTF_ALIAS_STANDARD_FUNCTION_NAMES_SOFT',
                           '-DPRINTF_SUPPORT_DECIMAL_SPECIFIERS=0',
                           '-DPRINTF_SUPPORT_EXPONENTIAL_SPECIFIERS=0',
                           '-DSUPPORT_MSVC_STYLE_INTEGER_SPECIFIERS=0',
                           '-DPRINTF_SUPPORT_WRITEBACK_SPECIFIER=0',
                           '-DPRINTF_SUPPORT_LONG_LONG=0',
                           '-D__EMULATOR__',
                           '-DDEBUG',
                           '-D__DYNAMIC_REENT__',
                           "-emit-llvm",
                           "-o", output_file, "-c", file_to_compile]
    for lib in extra_libs:
        commands.append(f"-I{lib}")
    subprocess.run(commands, check=True)

    # translate for .ll automatically. (optional)
    ll_output_file: str = os.path.join(output_file_folder, f"{output_name}.ll")
    commands = ["llvm-dis", output_file, "-o", ll_output_file]
    subprocess.run(commands, check=True)
    return output_file


def compile_to_object_flexpret(path_bc_filepath: str, gametime_path: str, gametime_flexpret_path: str, output_file_folder: str, output_name: str) -> str:
    """ Compile .bc file to .o file using clang through executing shell commands that is interpretable by FLEXPRET simulator

    :param path_bc_filepath: file path to the .bc file used for compilation
    :param gametime_path: Relative path to the GameTime repo from the simulation running folder.
    :param gametime_flexpret_path: Relative path to the GameTime repo from the simulated file.
    :param output_file_folder:  file path to the output folder where to .o file is saved to
    :param output_name: string for the name of compiled output WITHOUT extension
    :return: path of the output .o file
    """
    output_file: str = os.path.join(output_file_folder, f"{output_name}.o")
    # compile bc file

    commands = ["clang",  
                "-target", "riscv32-unknown-elf",
                "-mabi=ilp32", "-nostartfiles",
                "-march=rv32i",
                "-o", output_file, "-c", path_bc_filepath]

    subprocess.check_call(commands)

    ## object dump
    dump_file: str = os.path.join(output_file_folder, f"{output_name}.dump")
    commands = ["llvm-objdump", "-S", "-d", output_file]
    dumping = subprocess.Popen(commands, stdout=subprocess.PIPE)
    subprocess.check_output(["tee", dump_file], stdin=dumping.stdout)
    dumping.wait()
    return output_file

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
    commands: List[str] = ["opt", "-enable-new-pm=0", "-dot-cfg", "-S", bc_file, "-disable-output"]
    subprocess.check_call(commands)
    os.chdir(cur_cwd)
    return output_file


def inline_functions(input_file: str, output_file_folder: str, output_name: str) -> str:
    """ Unrolls the provided input file and output the unrolled version in
    the output file using llvm's opt utility. Could be unreliable if input_file
    is not compiled with `compile_to_llvm` function. If that is the case, the
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
    is not compiled with `compile_to_llvm` function. If that is the case, the
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

#TODO: remove it or move it to somewhere more suitable
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

