import unittest

from project_configuration_parser import YAMLConfigurationParser
from project_configuration import ProjectConfiguration
from analyzer import Analyzer

class AnalyzerTest(unittest.TestCase):

    def preprocessing_completes_without_error(self):
        analyzer = Analyzer(self.project_config)

    def basis_path_generation(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        print(list(map(str, paths)))

class Test1(AnalyzerTest):
    def setUp(self):
        print("setup test1")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_analyzer/programs/test1/config.yaml")

    def preprocessing_completes_without_error(self):
        self.preprocessing_completes_without_error()

    def test_basis_path_generation(self):
        self.basis_path_generation()

if __name__ == '__main__':
    unittest.main()

