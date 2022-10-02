import unittest

from src.configuration_parser import YAMLConfigurationParser


class MyTestCase(unittest.TestCase):
    def test_YAML_parser(self):
        YAMLConfigurationParser.parse("configs/config.yaml")
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
