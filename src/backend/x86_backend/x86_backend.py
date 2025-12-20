#!/usr/bin/env python
import os
import time
import re

import clang_helper
from backend.backend import Backend
from backend.generate_executable import generate_executable
from project_configuration import ProjectConfiguration
from defaults import logger
from gametime_error import GameTimeError


class X86Backend(Backend):
    timing_func = """
static inline unsigned long long read_cycle_count() {
    unsigned int lo, hi;
    __asm__ __volatile__ ("RDTSC" : "=a" (lo), "=d" (hi));
    return ((unsigned long long)hi << 32) | lo;
}
"""

    def __init__(self, project_config: ProjectConfiguration):
        super(X86Backend, self).__init__(project_config, "X86")

    def generate_executable(
        self, filepath: str, func_name: str, inputs: str, measure_folder: str
    ) -> str:
        """
        Modifies the input program to use INPUTS and generates the executable code. Stored at MEASURE_FOLDER/driver

        Parameters:
            filepath: str :
                Path to C file to modify with inputs.
            func_name: str :
                Name of function being analyzed.
            inputs: str :
                Path to the INPUTS file containing output of symbolic solver.
            measure_folder: str :
                The folder to store generated executable.

        Returns:
            str:
                Path to the executable code.
        """
        exec_file = generate_executable(
            filepath, measure_folder, func_name, inputs, self.timing_func
        )
        modified_bitcode_file_path = clang_helper.compile_to_llvm_for_exec(
            exec_file,
            measure_folder,
            "modified_output",
            self.project_config.included,
            self.project_config.compile_flags,
        )
        return clang_helper.bc_to_executable(
            modified_bitcode_file_path,
            measure_folder,
            "driver",
            self.project_config.included,
            self.project_config.compile_flags,
        )

    def run_backend_and_parse_output(
        self, stored_folder: str, executable_path: str
    ) -> int:
        """
        Runs the executable in EXECUTABLE_PATH in host machine and extracts the outputs from program.
        Temperaries are stored in STORED_FOLDER.

        Parameters:
            stored_folder: str :
                Folder to put all the generated tempraries.
            executable_path: str :
                Path to executable.

        Returns:
            int:
                Measured cycle count for EXECUTABLE_PATH.
        """
        # Assuming the modified bc now print the cycle count to the console.
        os.system(f"{executable_path} > {stored_folder}/measure.out")

        out_filepath = os.path.join(stored_folder, "measure.out")
        while not os.path.exists(out_filepath):
            print("Waiting for measure.out file")
            time.sleep(5)

        with open(out_filepath, "r") as out_file:
            lines = out_file.readlines()

        last_line = lines[-1] if lines else ""

        match = re.search(r"\d+$", last_line)

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
        stored_folder: str = measure_folder
        filepath: str = self.project_config.location_orig_file
        func_name: str = self.project_config.func
        executable_path: str = self.generate_executable(
            filepath, func_name, inputs, measure_folder
        )
        cycle_count: int = -1
        try:
            cycle_count: int = self.run_backend_and_parse_output(
                stored_folder, executable_path
            )
        except EnvironmentError as e:
            err_msg: str = "Error in measuring the cycle count of a path in X86: %s" % e
            logger.info(err_msg)
        return cycle_count
