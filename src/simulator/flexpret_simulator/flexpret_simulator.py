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


class FlexpretSimulator(Simulator):

    def __init__(self, project_config: ProjectConfiguration):
        super(FlexpretSimulator, self).__init__(project_config, "Flexpret")

    def object_file_to_mem (self, stored_folder: str, file_name: str) -> str:
        """
        Use same Make file mechanism as Flexpret to generate .mem file from .o

        :param stored_folder: the file path of the folder where .mem file will be stored
        :param file_name: the file name of the .o file, and the .mem file will have the same name
        :return file path of generated .mem file
        """
        # copy the MAKEFILE in FLEXPRET repository to the same folder as .o file
        #TODO: change the template path to the one user could provide
        makefile_template_path = os.path.join(self.project_config.gametime_path, "src", "simulator", "flexpret_simulator", "Makefile")

        makefile_path = os.path.join(stored_folder, "Makefile")
        shutil.copy(makefile_template_path, makefile_path)
        os.chmod(makefile_path, stat.S_IRWXO)

        # gather all the files needed to run Make, particularly all the possible .c/.o files
        context_path_from_flexpret_simulator = f'{self.project_config.location_orig_dir}'
        context_folder = os.listdir(context_path_from_flexpret_simulator)
        context_files = []
        for entry in context_folder:
            if ((not entry == self.project_config.name_orig_file) and entry.endswith('.c')) or entry.endswith('.o'):
                context_files.append(f'{context_path_from_flexpret_simulator}/{entry}')

        # add the generated .o file
        context_files.append(file_name + ".o")
        app_sources = " ".join(context_files)

        # run make to generate .mem file
        cwd = os.getcwd()
        os.chdir(stored_folder)
        # the three ".." is to get from the stored folder file to the simulated file,
        # stored_folder = {simulated_file_path}/{app name}gt/{path name}/{Flexpret}
        os.system(f'make FLEXPRET_ROOT_DIR={os.path.join("..", "..", "..", self.project_config.gametime_file_path, self.project_config.gametime_flexpret_path)} '
                  f'NAME={file_name} APP_SOURCES={app_sources}')

        os.chdir(cwd)

        mem_file_path = os.path.join(stored_folder, f"{file_name}.mem")
        while not os.path.exists(mem_file_path):
            logger.info('Waiting for .mem file to be generated by FlexPRET')
            time.sleep(5)

        return mem_file_path

    def run_simulator_and_parse_output(self, stored_folder: str, file_name: str) -> int:
        """
        Run simulation on the .mem file generated. The measurements are stored in measure.out
        Equivalent to: os.system(f"(cd {dir path of .mem file} && fp-emu --measure +ispm={file_name}.mem)")

        :param stored_folder: the file path of the folder where .mem file is stored
        :param file_name: the file name of the .mem file
        :return the measurement value
        """
        cwd = os.getcwd()
        os.chdir(stored_folder)
        os.system(f"fp-emu --measure +ispm={file_name}.mem")
        os.chdir(cwd)

        out_file_path = os.path.join(stored_folder, "measure.out")
        while not os.path.exists(out_file_path):
            print('Waiting for measure.out file to be generated by FlexPRET')
            time.sleep(5)

        out_file = open(out_file_path, "r")
        line = out_file.readline()
        out = [int(x) for x in line.split()]
        out_file.close()
        return out[0]

    def measure(self, path_bc_filepath: str, measure_folder: str, file_name: str) -> int:
        """
        Perform measurement using the Flexpret simulator.

        :param path_bc_filepath: the file path to the generated .bc file used for simulation; should correspond to a PATH
        :param measure_folder: all generated files will be stored in MEASURE_FOLDER/Flexpret
        :param file_name: the file name of the measured file, and all generated files will use when applicable
        :return the measured value of path
        """
        stored_folder: str = measure_folder
        path_object_filepath: str = clang_helper.compile_to_object_flexpret(path_bc_filepath, self.project_config.gametime_path,
                                                                            self.project_config.gametime_flexpret_path, stored_folder, file_name)
        cycle_count: int = -1
        try:
            self.object_file_to_mem(stored_folder, file_name)
            cycle_count: int = self.run_simulator_and_parse_output(stored_folder, file_name)
        except EnvironmentError as e:
            err_msg: str = ("Error in measuring the cycle count of a path when simulated on the Flexpret simulator: %s" % e)
            logger.info(err_msg)
        return cycle_count