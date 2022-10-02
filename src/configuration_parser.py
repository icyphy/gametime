#!/usr/bin/env python
from abc import abstractmethod
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from src.project_configuration import ProjectConfiguration


class ConfigurationParser(object):

    @staticmethod
    @abstractmethod
    def parse(configuration_file_path: str) -> ProjectConfiguration:
        pass


class YAMLConfigurationParser(ConfigurationParser):

    @staticmethod
    def parse(configuration_file_path: str) -> ProjectConfiguration:
        with open(configuration_file_path) as raw_file:
            raw_config = load(raw_file, Loader=Loader)
            print(raw_config)


extension_parser_map = {".yaml": YAMLConfigurationParser}
