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

class ArmBackend(Backend):
    timing_func = """
static inline unsigned long long read_cycle_count() {
    unsigned long long val;
    asm volatile("mrs %0, PMCCNTR_EL0" : "=r" (val));
    return val;
}
"""    

    def __init__(self, project_config: ProjectConfiguration):
        super(ArmBackend, self).__init__(project_config, "Arm")

    def generate_executable(self, filepath: str, func_name: str, inputs: str, measure_folder: str) -> str:
        exec_file = generate_executable(filepath, measure_folder, func_name, inputs, self.timing_func)
        modified_bitcode_file_path = clang_helper.compile_to_llvm_for_exec(exec_file, measure_folder, "modified_output", self.project_config.included, self.project_config.compile_flags)

        return clang_helper.bc_to_executable(modified_bitcode_file_path, measure_folder, "driver", self.project_config.included, self.project_config.compile_flags)

    def run_backend_and_parse_output(self, stored_folder: str, executable_path: str) -> int:
        # Assuming the modified bc now print the cycle count to the console.
        os.system(f"{executable_path} > {stored_folder}/measure.out")

        out_file_path = os.path.join(stored_folder, "measure.out")
        while not os.path.exists(out_file_path):
            print('Waiting for measure.out file')
            time.sleep(5)

        out_filepath = os.path.join(stored_folder, "measure.out")
        while not os.path.exists(out_filepath):
            print('Waiting for measure.out file')
            time.sleep(5)

        with open(out_filepath, "r") as out_file:
            lines = out_file.readlines()
        
        last_line = lines[-1] if lines else ''

        match = re.search(r'\d+$', last_line)
        
        if match:
            extracted_integer = int(match.group())
            return extracted_integer
        else:
            raise GameTimeError("The measure output file is ill-formatted")

    def measure(self, inputs: str, measure_folder: str) -> int:
        """
        Perform measurement using the backend.
        :param inputs: the inputs to drive down a PATH in a file
        :param measure_folder: all generated files will be stored in MEASURE_FOLDER/{name of backend}
        :return the measured value of path
        """
        stored_folder: str = measure_folder
        filepath: str = self.project_config.location_orig_file
        func_name: str = self.project_config.func
        executable_path: str = self.generate_executable(filepath, func_name, inputs, measure_folder)
        cycle_count: int = -1
        try:
            cycle_count: int = self.run_backend_and_parse_output(stored_folder, executable_path)
        except EnvironmentError as e:
            err_msg: str = ("Error in measuring the cycle count of a path in Arm: %s" % e)
            logger.info(err_msg)
        return cycle_count