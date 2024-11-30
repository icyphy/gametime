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
import command_utils


def compile_to_llvm_for_exec(c_filepath: str, output_file_folder: str, output_name: str, extra_libs: List[str]=[], extra_flags: List[str]=[], readable: bool = False) -> str:
    """
    Compile the C program into bitcode in OUTPUT_FILE_FOLDER.

    Parameters:
        c_filepath: str :
            Path to the input C program. Main function should be defined.
        output_file_folder: str :
            Storage folder for generated file.
        output_name: str :
            Name for generated bc.
        extra_libs: List[str] :
            Extra libraries needed for compilation. (Default value = [])
        extra_flags: List[str] :
            Extra flags needed for compilation. (Default value = [])
        readable: bool :
            If set to true, also generate readable LL file. (Default value = False)
    Returns:
        str:
            The path to bc.
    """
    # compile bc file
    file_to_compile: str = c_filepath
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

    commands: List[str] = ["clang", "-emit-llvm", "-O0", "-o", output_file, "-c", file_to_compile] + extra_flags
    for lib in extra_libs:
        commands.append(f"-I{lib}")
    command_utils.run(commands)

    if readable:
        # translate for .ll automatically.
        ll_output_file: str = os.path.join(output_file_folder, f"{output_name}.ll")
        commands = ["llvm-dis", output_file, "-o", ll_output_file]
        command_utils.run(commands)

    return output_file

def compile_list_to_llvm_for_analysis(c_filepaths: List[str] , output_file_folder: str, extra_libs: List[str]=[], extra_flags: List[str]=[], readable: bool = True) -> List[str]:
    compiled_files = []
    for c_filepath in c_filepaths:
        compiled_files.append(compile_to_llvm_for_analysis(c_filepath, output_file_folder, f"{c_filepath[:-2]}gt", extra_libs, extra_flags, readable))
    return compiled_files

def compile_to_llvm_for_analysis(c_filepath: str , output_file_folder: str, output_name: str, extra_libs: List[str]=[], extra_flags: List[str]=[], readable: bool = True) -> str:
    """
    Compile the C program into bitcode in OUTPUT_FILE_FOLDER using -O0 option to preserve maximum structure.

    Parameters:
        c_filepath: str :
            Path to the input C program.
        output_file_folder: str :
            Storage folder for generated file.
        output_name: str :
            Name for generated bc.
        extra_libs: List[str] :
            Extra libraries needed for compilation. (Default value = [])
        extra_flags: List[str] :
            Extra flags needed for compilation. (Default value = [])
        readable: bool :
            If set to true, also generate readable LL file. (Default value = False)
    Returns:
        str:
            The path to bc.
    """
    # compile bc file
    file_to_compile: str = c_filepath
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

    # "-Wno-implicit-function-declaration" is required so that clang
    # does not report "undeclared function '__assert_fail'"
    commands: List[str] = ["clang", "-emit-llvm", "-Xclang","-disable-O0-optnone", "-Wno-implicit-function-declaration", "-c", file_to_compile, "-o", output_file] + extra_flags
    for lib in extra_libs:
        commands.append(f"-I{lib}")
    command_utils.run(commands, shell=True)

    if readable:
        # translate for .ll automatically. (optional)
        ll_output_file: str = os.path.join(output_file_folder, f"{output_name}.ll")
        commands = ["llvm-dis", output_file, "-o", ll_output_file]
        command_utils.run(commands)
    return output_file

def bc_to_executable(bc_filepath: str, output_folder: str, output_name: str, extra_libs: List[str]=[], extra_flags: List[str]=[]) -> str:
    """
    Compile the LLVM bitcode program into executable in OUTPUT_FILE_FOLDER.

    Parameters:
        bc_filepath: str :
            Path to the input bitcode program.
        output_folder: str :
            Storage folder for generated file.
        output_name: str :
            Name for generated executable.
        extra_libs: List[str] :
            Extra libraries needed for compilation. (Default value = [])
        extra_flags: List[str] :
            Extra flags needed for compilation. (Default value = [])
    Returns:
        str:
            The path to executable.
    """
    # Set the path for the output executable file
    executable_file = os.path.join(output_folder, output_name)

    # Prepare the clang command
    clang_commands = ["clang", bc_filepath, "-o", executable_file] + extra_flags

    # Add extra include directories or libraries
    for lib in extra_libs:
        clang_commands.extend(["-I", lib])

    # Run clang to compile the bitcode into an executable
    command_utils.run(clang_commands)

    return executable_file


def dump_object(object_filepath: str, output_folder: str, output_name: str) -> str:
    """
    Dump the .o file to OUTPUT_NAME.dmp

    Parameters:
        object_filepath: str :
            The name of the .o file to dump
        output_folder: str :
            The folder path where .dmp files will be stored
        output_name: str :
            Name for dumped .dmp files.

    Returns:
        str:
            Path of the output OUTPUT_NAME.dmp file

    """

    output_file: str = os.path.join(output_folder, f"{output_name}.dmp")

    commands: List[str] = ["riscv32-unknown-elf-objdump", "--target=riscv32", "-march=rv32i", object_filepath, "-c", "-o", output_file]
    command_utils.run(commands)
    return output_file

def generate_dot_file(bc_filename: str, bc_file_folder: str, output_name: str = "main") -> str:
    """
    Create dag from .bc file using opt through executing shell commands

    Parameters:
        bc_filename: str :
            location of the compiled llvm .bc file
        bc_file_folder: str :
            the folder path where .bc files is stored and where .main.dot file will be stored
        output_name: str :
            Name of the generated dot file (Default value = "main")

    Returns:
        str:
            Path of the output .dot file

    """
    output_file: str = f".{output_name}.dot"
    cur_cwd: str = os.getcwd()
    os.chdir(bc_file_folder)  # opt generates .dot in cwd
    commands: List[str] = ["opt", "-passes=dot-cfg", "-S", "-disable-output", bc_filename]
    command_utils.run(commands)
    os.chdir(cur_cwd)
    return output_file


def inline_functions(bc_filepath: str, output_file_folder: str, output_name: str) -> str:
    """
    Unrolls the provided input file and output the unrolled version in
    the output file using llvm's opt utility. Could be unreliable if input_file
    is not compiled with `compile_to_llvm_for_analysis` function. If that is the case, the
    user might want to generate their own unrolled .bc/.ll file rather than
    relying on this built-in function.

    Parameters:
        bc_filepath: str :
            Input .bc/.ll function to loop unroll
        output_file_folder: str :
            folder to write unrolled .bc file. Outputs in a
            human-readable form already.
        output_name: str :
            file to write unrolled .bc file. Outputs in a
            human-readable form already.
        
    Returns:
        str:
            Path of the output .bc file

    """
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

    commands: List[str] = ["opt",
                "-passes=\"always-inline,inline\""
                "-inline-threshold=10000000",
                "-S", bc_filepath,
                "-o", output_file]
        
    command_utils.run(commands)
    return output_file


def unroll_loops(bc_filepath: str, output_file_folder: str, output_name: str, project_config: ProjectConfiguration) -> str:
    """
    Unrolls the provided input file and output the unrolled version in
    the output file using llvm's opt utility. Could be unreliable if input_file
    is not compiled with `compile_to_llvm_for_analysis` function. If that is the case, the
    user might want to generate their own unrolled .bc/.ll file rather than
    relying on this built-in function.

    Parameters:
        input_file: str :
            Input .bc/.ll function to loop unroll
        output_file_folder: str :
            folder to write unrolled .bc file. Outputs in a
            human-readable form already.
        output_name: str :
            file to write unrolled .bc file. Outputs in a
            human-readable form already.
        project_config: ProjectConfiguration :
            ProjectConfiguration this helper is calling from.

    Returns:
        str:
            Path of the output .bc file

    """
    # return bc_filepath
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")
    
    # Related but unused passes: 
    # -unroll-threshold=10000000, -unroll-count=4, 
    # -unroll-allow-partial, -instcombine,
    # -reassociate, -indvars, -mem2reg
    commands: List[str] = ["opt",
                "-passes='simplifycfg,loops,lcssa,loop-simplify,loop-rotate,indvars,loop-unroll'"
                "-S", bc_filepath,
                "-o", output_file]

    command_utils.run(commands)

    return output_file

def remove_temp_cil_files(project_config: ProjectConfiguration, all_temp_files=False) -> None:
    """
    Removes the temporary files created by CIL during its analysis.

    Parameters:
        project_config :
            ProjectConfiguration this helper is calling from.

        all_temp_files:
            True if all files in temperary directory should be removed.
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

