import unittest

import clang_helper
import shutil

from path_analyzer import PathAnalyzer
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from analyzer import Analyzer
import os
from smt_solver.extract_labels import find_labels
from smt_solver.smt import run_smt

class TestFlexpret(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("./programs/if_elif_else/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)

    def test_measure_basis_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()

        self.assertIsNotNone(paths[0], "no paths were found")
        analyzer.measure_basis_paths()
        for p in paths:
            print(p.get_measured_value())



if __name__ == '__main__':
    unittest.main()
