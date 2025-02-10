#!/usr/bin/env python
import os
import time

import re
from backend.backend import Backend
from backend.generate_executable import generate_executable
from project_configuration import ProjectConfiguration
from defaults import logger
from typing import List
from gametime_error import GameTimeError
import command_utils

class FlexpretBackend(Backend):
        
    timing_func = """
static inline unsigned long read_cycle_count() {
    return rdcycle();
}
"""

    def __init__(self, project_config: ProjectConfiguration):
        super(FlexpretBackend, self).__init__(project_config, "Flexpret")

    def generate_executable_c(self, filepath: str, func_name: str, inputs: str, measure_folder: str) -> str:
        """
        Modifies the input program to use INPUTS and returns path to modifed C program.

        Parameters:
            filepath: str :
                Path to C file to modify with inputs.
            func_name: str :
                Name of function being analyzed.
            inputs: str :
                Path to the INPUTS file containing output of symbolic solver.
            measure_folder: str :
                The folder to store generated C code.

        Returns:
            str:
                Path to the modified C file.
        """
        exec_file = generate_executable(filepath, measure_folder, func_name, inputs, self.timing_func, True)
        return exec_file
              

    def compile_c_file (self, stored_folder: str, file_name: str) -> str:
        """Use same Make file mechanism as Flexpret to generate .mem file from .c

        Parameters:
            stored_folder: str :
                Folder to put all the generated tempraries.
            file_name: str :
                Name of function being analyzed.

        Returns:
            int:
                Measured cycle count for C_FILEPATH.
        """
        
        # Generate CMakeList.txt
        cmakelist_path = os.path.join(stored_folder, "CMakeLists.txt")
        cmakelist_content = f"""
cmake_minimum_required(VERSION 3.22)

# Set toolchain to RISC-V; must be done before call to project()
include($ENV{{FP_SDK_PATH}}/cmake/riscv-toolchain.cmake)

project(driver
  LANGUAGES C
  DESCRIPTION "A GameTime test for the WCET of a function"
  VERSION 1.0.0
)

set(DEBUG true)
set(CMAKE_BUILD_TYPE "Debug")

add_executable({file_name} {file_name}.c)

include($ENV{{FP_SDK_PATH}}/cmake/fp-app.cmake)

# Add sdk as subdirectory out-of-tree and link it
add_subdirectory($ENV{{FP_SDK_PATH}} BINARY_DIR)
target_link_libraries({file_name} fp-sdk)

fp_add_outputs({file_name})
        """
        
        with open(cmakelist_path, 'w', encoding='utf-8') as f:
            f.write(cmakelist_content)
        
        # Run cmake
        cwd = os.getcwd()
        os.chdir(stored_folder)
        # os.system('cmake -B build && make -C build')
        cmd = ["cmake", "-B", "build"]
        command_utils.run(cmd)
        cmd = ["make", "-C", "build"]
        command_utils.run(cmd)
        os.chdir(cwd)

        return stored_folder + "/build"

    def run_backend_and_parse_output(self, file_name: str, build_folder: str) -> int:
        """
        Run simulation on the .mem file generated. The measurements are stored in measure.out
        Equivalent to: os.system(f"(cd {dir path of .mem file} && fp-emu --measure +ispm={file_name}.mem)")

        Parameters:
            stored_folder: str :
                Folder to put all the generated tempraries.
            mem_filepath: str :
                Path to the .mem file
                :return the measurement value   

        Returns:
            int:
                Measured cycle count for MEM_FILEPATH.
        """
        cwd = os.getcwd()
        os.chdir(build_folder)
        cmd = [f"fp-emu +ispm={file_name}.mem > measure.out"]
        command_utils.run(cmd, shell=True)
        os.chdir(cwd)

        out_filepath = os.path.join(build_folder, "measure.out")
        while not os.path.exists(out_filepath):
            print('Waiting for measure.out file to be generated by FlexPRET')
            time.sleep(5)

        with open(out_filepath, "r") as out_file:
            lines = out_file.readlines()
        
        #flexpret console output has two extra lines at the end
        print_line = lines[0].split(" ")[-1] if lines else ''

        match = re.search(r'\d+$', print_line)
        
        if match:
            extracted_integer = int(match.group())
            return extracted_integer
        else:
            raise GameTimeError("The measure output file is ill-formatted")

    def measure(self, inputs: str, measure_folder: str) -> int:
        """
        Perform measurement using the backend.

        Parameters:
            inputs: str:
                the inputs to drive down a PATH in a file
            measure_folder: str :
                all generated files will be stored in MEASURE_FOLDER/{name of backend}

        Returns:
            int:
                The measured value of path
        """
        file_name = "driver"
        stored_folder: str = measure_folder
        filepath: str = self.project_config.location_orig_file
        func_name: str = self.project_config.func
        c_filepath: str = self.generate_executable_c(filepath, func_name, inputs, measure_folder)
        build_folder: str = self.compile_c_file(stored_folder, file_name)
        cycle_count: int = self.run_backend_and_parse_output(file_name, build_folder)
        return cycle_count