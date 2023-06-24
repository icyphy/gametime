import subprocess
import unittest
import os
from os.path import exists

import simulator
import flexpret_simulator
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser


class TestFlexpret(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_c/config.yaml")

    def test_simulate_add(self):
        mem_file_dir_path = "/test_flexpret_simulator/programs/add"
        mem_file_name = "add"
        fp_simulator = flexpret_simulator.FlexpretSimulator(self.project_config)
        count = fp_simulator.measure(mem_file_dir_path, mem_file_name)
        print("\n count is", count)