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

    def test_measure_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        # analyzer.measure_basis_paths()
        print(paths[0])
        # file_name = "path0"
        # path_analyzer = PathAnalyzer(analyzer.preprocessed_path, analyzer.project_config, analyzer.dag, paths[0],
        #                              file_name)

        # fp_simulator = flexpret_simulator.FlexpretSimulator(self.project_config)
        # value = path_analyzer.measure_path(fp_simulator)
        # print(value)

if __name__ == '__main__':
    unittest.main()
