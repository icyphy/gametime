import unittest

import yaml

from test_load_class_from_yaml import MyClass as MyClass

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# from src.project_configuration_parser import YAMLConfigurationParser


class MyTestCase(unittest.TestCase):
    # def test_YAML_parser(self):
    #     YAMLConfigurationParser.parse("configs/config.yaml")
    #     self.assertEqual(True, False)  # add assertion here

    def test_YAML_load_into_class(self):
        my_class: MyClass = yaml.load("""
        !!python/object:MyClass
        name: Andrew
        sad: True
        is_true: False
        """, Loader=Loader)
        self.assertEqual(my_class.name, "Andrew")


if __name__ == '__main__':
    unittest.main()
