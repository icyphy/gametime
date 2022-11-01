import subprocess
import unittest
import os

import clang_helper
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser


class TestGenerateCFG(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_c/config.yaml")

    def test_generate_cfg_from_c_file(self):
        source_path = os.path.relpath("test_c")
        source_file = os.path.join(source_path, "main.c")
        compile_command = ["clang", "-emit-llvm", "-o", "test_c/object.bc", "-c", source_file]
        exit_code = subprocess.run(compile_command)
        print(exit_code)
        print(source_file, os.path.isfile(source_file))
        self.assertEqual(True, True)  # add assertion here

    def test_generate_cfg_from_c_file_using_clang_helper(self):
        output_path: str = clang_helper.compile_to_llvm(self.project_config)
        self.assertTrue(os.path.isfile(output_path))
        self.assertEqual(os.path.split(output_path)[1], "main.bc")


if __name__ == '__main__':
    unittest.main()
