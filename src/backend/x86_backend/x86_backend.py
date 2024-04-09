#!/usr/bin/env python
import logging
import os
import shutil
import time
import stat

import clang_helper
from backend.backend import Backend
from backend.generate_executable import generate_executable
from project_configuration import ProjectConfiguration
from defaults import logger

class X86Backend(Backend):
    timing_func = """
unsigned long long read_cycle_count() {
    unsigned int lo, hi;
    __asm__ __volatile__ ("RDTSC" : "=a" (lo), "=d" (hi));
    return ((unsigned long long)hi << 32) | lo;
}
"""

    def __init__(self, project_config: ProjectConfiguration):
        super(X86Backend, self).__init__(project_config, "X86")

    def generate_executable(self, filepath: str, func_name: str, inputs: str, measure_folder: str) -> str:
        # # Define the path to your C++ executable
        # cpp_executable = f"./{self.project_config.gametime_path}/src/backend/x86_backend/generate_executable"

        # # Define the arguments for your C++ program
        # bitcode_file_path =  clang_helper.compile_to_llvm_for_exec(filepath, measure_folder, "orig")
        # function_name = func_name
        # values = inputs

        # # Prepare the command with all arguments
        # command = [cpp_executable, bitcode_file_path, function_name, values, measure_folder]
        # print(command)

        # # Run the C++ program
        # process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # # Capture the output and errors, if any
        # output = process.stdout
        # errors = process.stderr

        # # Check if the process has executed successfully
        # if process.returncode == 0:
        #     print("Program executed successfully")
        #     print("Output:", output)
        # else:
        #     print("Program failed with return code", process.returncode)
        #     print("Errors:", errors)
        exec_file = generate_executable(filepath, measure_folder, func_name, inputs, self.timing_func)
        modified_bitcode_file_path = clang_helper.compile_to_llvm_for_exec(exec_file, measure_folder, "modified_output", [], [])

        return clang_helper.bc_to_executable(modified_bitcode_file_path, measure_folder, "driver", [], [])

    def run_simulator_and_parse_output(self, stored_folder: str, executable_path: str) -> int:
        # Assuming the modified bc now print the cycle count to the console.
        os.system(f"{executable_path} > {stored_folder}/measure.out")

        out_file_path = os.path.join(stored_folder, "measure.out")
        while not os.path.exists(out_file_path):
            print('Waiting for measure.out file')
            time.sleep(5)

        out_file = open(out_file_path, "r")
        start = int(out_file.readline()[:-2])
        end = int(out_file.readline()[:-2])
        out_file.close()
        return end - start

    def measure(self, inputs: str, measure_folder: str) -> int:
        """
        Perform measurement using the simulator.
        :param inputs: the inputs to drive down a PATH in a file
        :param measure_folder: all generated files will be stored in MEASURE_FOLDER/{name of simulator}
        :return the measured value of path
        """
        stored_folder: str = measure_folder
        filepath: str = self.project_config.location_orig_file
        func_name: str = self.project_config.func
        executable_path: str = self.generate_executable(filepath, func_name, inputs, measure_folder)
        cycle_count: int = -1
        try:
            cycle_count: int = self.run_simulator_and_parse_output(stored_folder, executable_path)
        except EnvironmentError as e:
            err_msg: str = ("Error in measuring the cycle count of a path in X86: %s" % e)
            logger.info(err_msg)
        return cycle_count