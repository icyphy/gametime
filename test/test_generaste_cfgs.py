import subprocess
import unittest
import os
from os.path import exists

import clang_helper
import nx_helper
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

    def test_generate_bc_from_c_file_using_clang_helper(self):
        output_path: str = clang_helper.compile_to_llvm(self.project_config)
        self.assertTrue(os.path.isfile(output_path))
        self.assertEqual(os.path.split(output_path)[1], "main.bc")

    def test_generate_dot_from_c_file_using_clang_helper(self):
        output_path: str = clang_helper.compile_to_llvm(self.project_config)
        output_path = clang_helper.generate_dot_file(output_path, self.project_config)
        self.assertTrue(os.path.isfile(output_path))
        self.assertEqual(os.path.split(output_path)[1], ".main.dot")

    def test_read_dag_from_dot_file_compiled_from_c(self):
        output_path: str = clang_helper.compile_to_llvm(self.project_config)
        output_path = clang_helper.generate_dot_file(output_path, self.project_config)
        dag: nx_helper.Dag = nx_helper.construct_dag(output_path)
        self.assertIsNotNone(dag)
        self.assertTrue(nx_helper.has_cycles(dag))
        self.assertIsNotNone(nx_helper.get_random_path(dag, dag.source, dag.sink))

    def test_read_loop_unrolled_dag_from_dot_file_compiled_from_c(self):
        output_path: str = clang_helper.compile_to_llvm(self.project_config)
        output_path: str = clang_helper.unroll_loops(output_path, self.project_config)
        output_path = clang_helper.generate_dot_file(output_path, self.project_config)
        dag: nx_helper.Dag = nx_helper.construct_dag(output_path)
        self.assertIsNotNone(dag)
        self.assertFalse(nx_helper.has_cycles(dag))
        self.assertIsNotNone(nx_helper.get_random_path(dag, dag.source, dag.sink))
        self.assertEqual(nx_helper.num_paths(dag, dag.source, dag.sink), 2)

    def test_read_write_dag(self):
        input_dag_path: str = clang_helper.compile_to_llvm(self.project_config)
        input_dag_path = clang_helper.generate_dot_file(input_dag_path, self.project_config)
        dag: nx_helper.Dag = nx_helper.construct_dag(input_dag_path)
        output_dag_path: str = self.project_config.get_temp_filename_with_extension(".dot", "test_output")
        nx_helper.write_dag_to_dot_file(dag, output_dag_path)
        self.assertTrue(exists(output_dag_path))

if __name__ == '__main__':
    unittest.main()
