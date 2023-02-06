import unittest

from project_configuration_parser import YAMLConfigurationParser
from src import ProjectConfiguration, Analyzer


class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_c/config.yaml")

    def test_preprocessing_completes_without_error(self):
        analyzer = Analyzer(self.project_config)

