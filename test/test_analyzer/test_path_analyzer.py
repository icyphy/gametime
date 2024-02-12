import os
import unittest

import clang_helper
from path_analyzer import PathAnalyzer
from project_configuration_parser import YAMLConfigurationParser
from project_configuration import ProjectConfiguration
from analyzer import Analyzer


class TestPathAnalyzer(unittest.TestCase):

    def generate_bc_file_from_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        path_analyzer = PathAnalyzer(analyzer.preprocessed_path, analyzer.project_config, analyzer.dag, paths[0], "path0")
        output_file = path_analyzer.change_bt_based_on_path()
        self.assertIsNotNone(output_file)
        self.assertTrue(len(output_file) != 0)
        self.assertTrue(os.path.isfile(output_file))

    def compile_from_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        file_name = "path0"
        path_analyzer = PathAnalyzer(analyzer.preprocessed_path, analyzer.project_config, analyzer.dag, paths[0], file_name)
        output_file = path_analyzer.change_bt_based_on_path()
        clang_helper.compile_to_object_flexpret(output_file, "", "", path_analyzer.output_folder, file_name)

class Test1(TestPathAnalyzer):
    def setUp(self):
        print("setup test1")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_analyzer/programs/test1/config.yaml")

    def test_generate_bc_file_from_path(self):
        self.generate_bc_file_from_path()

    def test_compile_from_path(self):
        self.compile_from_path()

if __name__ == '__main__':
    unittest.main()

