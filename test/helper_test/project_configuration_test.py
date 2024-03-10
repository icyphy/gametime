import unittest

import yaml

from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from gametime.test.helper_test.load_class_from_yaml_test import MyClass as MyClass

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class TestParsing(unittest.TestCase):


    def test_YAML_parser(self):
        config: ProjectConfiguration = YAMLConfigurationParser.parse("test_helper/programs/test1/config.yaml")
        print(config.name_orig_file, config.name_xml_file, config.location_temp_dir)
        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
