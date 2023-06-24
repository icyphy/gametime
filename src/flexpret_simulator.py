#!/usr/bin/env python

import os
import time
import sys
import subprocess

from defaults import config
from gametime_error import GameTimeError
from simulator import Simulator

class FlexpretSimulator(Simulator):

    def __init__(self, projectConfig):
        super(FlexpretSimulator, self).__init__(projectConfig, "Flexpret")

    def _runSimulatorAndParseOutput(self, mem_file_dir_path, mem_file_name):

        # equivalent to: os.system(f"(cd {mem_file_dir_path} && fp-emu --measure +ispm={mem_file_name}.mem)")
        cwd = os.getcwd()
        os.chdir(cwd + mem_file_dir_path)
        os.system(f"fp-emu --measure +ispm={mem_file_name}.mem")
        os.chdir(cwd)

        out_file_path = cwd + mem_file_dir_path + "/measure.out"

        while not os.path.exists(out_file_path):
            print(out_file_path)
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