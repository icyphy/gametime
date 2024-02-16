import unittest

import clang_helper
import shutil

from path_analyzer import PathAnalyzer
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from simulator.flexpret_simulator import flexpret_simulator
from analyzer import Analyzer

class TestFlexpret(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("./programs/add/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)

    def test_measure_basis_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        analyzer.measure_basis_paths()

if __name__ == '__main__':
    unittest.main()
