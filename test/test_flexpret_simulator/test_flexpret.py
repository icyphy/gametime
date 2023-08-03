import unittest

import clang_helper
import shutil

from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from simulator.flexpret_simulator import flexpret_simulator
from src import Analyzer

class TestFlexpret(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/add/config.yaml")
        shutil.rmtree(self.project_config.locationTempDir)

    def test_compile_c(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        file_name = "path0-gt"
        output_file = analyzer.change_bt_based_on_path(paths[0], file_name)
        clang_helper.compile_to_object(output_file, self.project_config, file_name)

    def test_compile_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        file_name = "path0-gt"
        output_file = analyzer.change_bt_based_on_path(paths[0], file_name)
        clang_helper.compile_to_object(output_file, self.project_config, file_name)

        fp_simulator = flexpret_simulator.FlexpretSimulator(self.project_config)
        value = fp_simulator.measure(file_name)
        print(value)

if __name__ == '__main__':
    unittest.main()
