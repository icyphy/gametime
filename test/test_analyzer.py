import os
import unittest

import clang_helper
from project_configuration_parser import YAMLConfigurationParser
from src import ProjectConfiguration, Analyzer


class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        print("setup")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_c/config.yaml")

    def test_preprocessing_completes_without_error(self):
        analyzer = Analyzer(self.project_config)

    def test_basis_path_generation(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        print(list(map(str, (analyzer.generate_basis_paths()))))

    def test_generate_bc_file_from_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        output_file = analyzer.change_bt_based_on_path(paths[0])
        self.assertIsNotNone(output_file)
        self.assertTrue(len(output_file) != 0)
        self.assertTrue(os.path.isfile(output_file))

    def test_compile_from_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        output_file = analyzer.change_bt_based_on_path(paths[0])
        clang_helper.compile_to_object(output_file, self.project_config)

