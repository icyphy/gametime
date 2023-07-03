#!/usr/bin/env python

import os
import shutil
import time
import stat

from simulator.simulator import Simulator

class FlexpretSimulator(Simulator):

    def __init__(self, projectConfig):
        super(FlexpretSimulator, self).__init__(projectConfig, "Flexpret")

    def object_file_to_mem (self, object_file_name):

        # cwd = os.getcwd()
        # os.chdir(f'{self.projectConfig.gametime_path}/src/simulator/flexpret_simulator')
        # flexpret_path_from_flexpret_simulator = f'../../../{self.projectConfig.flexpret_path}'
        # context_path_from_flexpret_simulator = f'{self.projectConfig.locationOrigDir}'
        # context_folder = os.listdir(context_path_from_flexpret_simulator)
        # context_files = []
        # for entry in context_folder:
        #     if ((not entry == self.projectConfig.nameOrigFile) and entry.endswith('.c')) or entry.endswith('.o'):
        #         context_files.append(f'{context_path_from_flexpret_simulator}/{entry}')
        # context_files.append(f'{self.projectConfig.get_temp_filename_with_extension(".o", object_file_name)}')
        # app_sources = " ".join(context_files)
        #
        # print("cwd", os.getcwd())
        # print("flexpret", flexpret_path_from_flexpret_simulator)
        # print("app", app_sources)
        #
        # os.system(f'make')
        # # os.system(f'make FLEXPRET_ROOT_DIR={flexpret_path_from_flexpret_simulator} NAME={object_file_name} APP_SOURCES={app_sources}')
        # os.chdir(cwd)

        makefile_template_path = os.path.join(self.projectConfig.gametime_path, "src", "simulator", "flexpret_simulator", "Makefile")
        path_makefile_path = self.projectConfig.get_temp_filename_with_extension("", "Makefile")
        shutil.copy(makefile_template_path, path_makefile_path)
        os.chmod(path_makefile_path, stat.S_IRWXO)

        context_path_from_flexpret_simulator = f'{self.projectConfig.locationOrigDir}'
        context_folder = os.listdir(context_path_from_flexpret_simulator)
        context_files = []
        for entry in context_folder:
            if ((not entry == self.projectConfig.nameOrigFile) and entry.endswith('.c')) or entry.endswith('.o'):
                context_files.append(f'{context_path_from_flexpret_simulator}/{entry}')
        context_files.append(object_file_name + ".o")
        app_sources = " ".join(context_files)

        cwd = os.getcwd()
        os.chdir(self.projectConfig.locationTempDir)
        os.system(f'make -d FLEXPRET_ROOT_DIR={os.path.join("..", self.projectConfig.gametime_file_path, self.projectConfig.gametime_flexpret_path)} '
                  f'NAME={object_file_name} APP_SOURCES={app_sources}')
        #
        # os.system("make -d")

        print("cwd", os.getcwd())
        print("flexpret root", os.path.join("..", self.projectConfig.gametime_file_path, self.projectConfig.gametime_flexpret_path))
        print("o file name", object_file_name)
        print("app src", app_sources)
        os.chdir(cwd)

        mem_file_path = self.projectConfig.get_temp_filename_with_extension(".mem")
        # while not os.path.exists(mem_file_path):
        #     print('Waiting for mem file to be generated by FlexPRET')
        #     time.sleep(1)
        print('Waiting for mem file to be generated by FlexPRET')
        time.sleep(10)
        return mem_file_path

    # LINKER_SCRIPT ?= $(FP_LIB_DIR) / linker / flexpret.ld
    # CFLAGS = -g -static -O0 -march=rv32i -mabi=ilp32 -nostartfiles -specs=nosys.specs $(APP_DEFS)
    # INCS = $(LIB_INCS) $(APP_INCS)
    # LFLAGS = -T $(LINKER_SCRIPT) -L$(FP_LIB_DIR)/linker -Xlinker -Map=$(NAME).map
    # $(CC) $(LFLAGS) $(CFLAGS) $(INCS) -o $ *.riscv $(STARTUP_SOURCES) $(APP_SOURCES) $(LIB_SOURCES)

    #No -L -T flag, still ok
    def _runSimulatorAndParseOutput(self, mem_file_dir_path, mem_file_name):

        # equivalent to: os.system(f"(cd {mem_file_dir_path} && fp-emu --measure +ispm={mem_file_name}.mem)")
        cwd = os.getcwd()
        os.chdir(cwd + mem_file_dir_path)
        os.system(f"fp-emu --measure +ispm={mem_file_name}.mem")
        os.chdir(cwd)

        out_file_path = cwd + mem_file_dir_path + "/measure.out"

        while not os.path.exists(out_file_path):
            print('Waiting for out file to be generated by FlexPRET')
            time.sleep(1)

        out_file = open(out_file_path, "r")
        line = out_file.readline()
        out = [int(x) for x in line.split()]
        out_file.close()
        return out[0]

    def _removeTemps(self, mem_file_dir_path):
        os.remove(mem_file_dir_path + "/measure.out")

    def measure(self, mem_file_dir_path, mem_file_name):

        cycleCount = -1
        try:
            cycleCount = self._runSimulatorAndParseOutput(mem_file_dir_path, mem_file_name)
            # self._removeTemps(mem_file_dir_path)
        except EnvironmentError as e:
            errMsg = ("Error in measuring the cycle count of a path "
                      "when simulated on the Flexpret simulator: %s" % e)
            print(errMsg)
        return cycleCount

# #python3 flexpret_simulator.py programs/tests/c-tests/add add
# mem_file_dir_path = str(sys.argv[1])
# mem_file_name = str(sys.argv[2])
# flexpretSimulator = FlexpretSimulator()
# count = flexpretSimulator.measure(mem_file_dir_path, mem_file_name)
# print("count is", count)