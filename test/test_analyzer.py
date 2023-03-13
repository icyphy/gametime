import unittest

from project_configuration_parser import YAMLConfigurationParser
from src import ProjectConfiguration, Analyzer


class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        print("setup")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_c/config.yaml")

    def test_preprocessing_completes_without_error(self):
        print("world")
        analyzer = Analyzer(self.project_config)

    def test_basis_path_generation(self):
        print("hello")
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        print(list(map(str, (analyzer.generate_basis_paths()))))
