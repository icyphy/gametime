#!/usr/bin/env python
import logging
import os
import shutil
import time
import stat

import clang_helper
from simulator.simulator import Simulator
from project_configuration import ProjectConfiguration
from defaults import logger
from typing import List
import subprocess
from project_configuration_parser import YAMLConfigurationParser

class ServerSimulator(Simulator):

    def __init__(self, project_config: ProjectConfiguration):
        super(ServerSimulator, self).__init__(project_config, "Server")

    def generate_executable(self, filepath: str, func_name: str, inputs: List[any], measure_folder: str) -> str:
        # Define the path to your C++ executable
        cpp_executable = f"./{self.project_config.gametime_path}/src/simulator/server_simulator/generate_executable"
        #TODO: remove it after testing
        cpp_executable = f"./generate_executable"

        # Define the arguments for your C++ program
        bitcode_file_path =  clang_helper.compile_to_llvm(filepath, measure_folder, "orig")
        function_name = func_name
        values = inputs

        # Prepare the command with all arguments
        command = [cpp_executable, bitcode_file_path, function_name] + list(map(str, values))

        # Run the C++ program
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Capture the output and errors, if any
        output = process.stdout
        errors = process.stderr

        # Check if the process has executed successfully
        if process.returncode == 0:
            print("Program executed successfully")
            print("Output:", output)
        else:
            print("Program failed with return code", process.returncode)
            print("Errors:", errors)

        modified_bitcode_file_path = f"{measure_folder}/modified_output.bc"

        return clang_helper.bc_to_executable(modified_bitcode_file_path, measure_folder, "driver", [], [])

    def run_simulator_and_parse_output(self, stored_folder: str, executable_path: str) -> int:
        os.system(f"{executable_path} > {stored_folder}/measure.out")

        out_file_path = os.path.join(stored_folder, "measure.out")
        while not os.path.exists(out_file_path):
            print('Waiting for measure.out file')
            time.sleep(5)

        out_file = open(out_file_path, "r")
        start = int(out_file.readline())
        end = int(out_file.readline())
        out_file.close()
        return end - start

    def measure(self, inputs: List[any], measure_folder: str) -> int:
        """
        Perform measurement using the simulator.
        :param inputs: the inputs to drive down a PATH
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
            err_msg: str = ("Error in measuring the cycle count of a path when simulated on the Flexpret simulator: %s" % e)
            logger.info(err_msg)
        return cycle_count
    
if __name__ == '__main__':
    proj_config = YAMLConfigurationParser.parse(f"{os.getcwd()}/config.yaml")

    server_simulator = ServerSimulator(proj_config)

    print(server_simulator.measure([1, 2], os.getcwd()))