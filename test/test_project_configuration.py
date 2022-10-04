import unittest

import yaml

from project_configuration_parser import YAMLConfigurationParser
from test_load_class_from_yaml import MyClass as MyClass

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class MyTestCase(unittest.TestCase):
    def test_YAML_parser(self):
        YAMLConfigurationParser.parse("configs/config.yaml")
        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
