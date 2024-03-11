import subprocess
import unittest
import os

import clang_helper
import nx_helper


class TestClangHelper(unittest.TestCase):
    def setUp(self):
        self.orig_file = "/opt/project/test/test_helper/programs/test1/main.c"
        self.output_folder = "/opt/project/test/test_helper/programs/test1/temp/"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        os.chmod(self.output_folder, 0o777)

        # self.project_config.location_orig_file, self.project_config.location_temp_dir, f"{self.project_config.name_orig_no_extension}gt", flexpret_lib_path

    def test_generate_cfg_from_c_file(self):
        compile_command = ["clang", "-emit-llvm", "-o", self.output_folder + "compile-gt.bc", "-c", self.orig_file]
        exit_code = subprocess.run(compile_command)
        print(exit_code)

    def test_generate_bc_from_c_file_using_clang_helper(self):
        output_path: str = clang_helper.compile_to_llvm_for_analysis(self.orig_file, self.output_folder, "compile-gt","")
        self.assertEqual("compile-gt.bc", os.path.split(output_path)[1])

    def test_generate_dot_from_c_file_using_clang_helper(self):
        output_path: str = clang_helper.compile_to_llvm_for_analysis(self.orig_file, self.output_folder, "compile-gt", "")
        output_path = os.path.join(self.output_folder, clang_helper.generate_dot_file(output_path, self.output_folder))
        self.assertTrue(os.path.isfile(output_path))
        self.assertEqual(os.path.split(output_path)[1], ".main.dot")

    def test_read_dag_from_dot_file_compiled_from_c(self):
        output_path: str = clang_helper.compile_to_llvm_for_analysis(self.orig_file, self.output_folder, "compile-gt", "")
        output_path = os.path.join(self.output_folder, clang_helper.generate_dot_file(output_path, self.output_folder))
        dag: nx_helper.Dag = nx_helper.construct_dag(output_path)
        self.assertIsNotNone(dag)
        self.assertFalse(nx_helper.has_cycles(dag))
        self.assertIsNotNone(nx_helper.get_random_path(dag, dag.source, dag.sink))

    def test_read_loop_unrolled_dag_from_dot_file_compiled_from_c(self):
        output_path: str = clang_helper.compile_to_llvm_for_analysis(self.orig_file, self.output_folder, "compile-gt", "")
        output_path = clang_helper.inline_functions(output_path, self.output_folder,"inline-gt")
        output_path = clang_helper.unroll_loops(output_path, self.output_folder,"unroll-gt")
        output_path = os.path.join(self.output_folder, clang_helper.generate_dot_file(output_path, self.output_folder))
        dag: nx_helper.Dag = nx_helper.construct_dag(output_path)
        self.assertIsNotNone(dag)
        self.assertFalse(nx_helper.has_cycles(dag))
        self.assertIsNotNone(nx_helper.get_random_path(dag, dag.source, dag.sink))
        self.assertEqual(nx_helper.num_paths(dag, dag.source, dag.sink), 1)

    def test_compile(self):
        output_path: str = clang_helper.compile_to_llvm_for_analysis(self.orig_file, self.output_folder, "compile-gt", "")
        output_path = clang_helper.inline_functions(output_path, self.output_folder, "inline-gt")
        output_path = clang_helper.unroll_loops(output_path, self.output_folder, "unroll-gt")
        clang_helper.compile_to_object_flexpret(output_path, "", "", self.output_folder, "object-gt")


if __name__ == '__main__':
    unittest.main()
