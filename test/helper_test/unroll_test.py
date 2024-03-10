import shutil
import subprocess
import unittest
import os


class TestClangHelper(unittest.TestCase):
    def setUp(self):
        self.orig_file = "/opt/project/test/test_helper/programs/test1/main.c"
        self.output_folder = "/opt/project/test/test_helper/programs/test1/temp/"
        if os.path.exists(self.output_folder) and os.path.isdir(self.output_folder):
            shutil.rmtree(self.output_folder)
        os.makedirs(self.output_folder)
        os.chmod(self.output_folder, 0o777)


    def test_generate_cfg_from_c_file(self):
        # compile_command = ["clang", "-Xclang",
        #                    "-O3", "-Otime", "-mllvm", "-disable-llvm-optzns", "-emit-llvm",
        #                    "-o", self.output_folder + "compile-gt.bc", "-c", self.orig_file]

        compile_command = ["clang", "-O2", "-mllvm", "-disable-llvm-optzns", "-emit-llvm",
                           "-o", self.output_folder + "compile-gt.bc", "-c", self.orig_file]

        # All the way to one block?
        # compile_command = ["clang", "-O3", "-emit-llvm",
        #                    "-o", self.output_folder + "compile-gt.bc", "-c", self.orig_file]

        exit_code = subprocess.run(compile_command)
        os.chdir(self.output_folder)

        compile_command = commands = ["llvm-dis", "compile-gt.bc", "-o", "compile-gt.ll"]
        exit_code = subprocess.run(compile_command)


        # compile_command = ["opt",
        #                    "-O3",
        #         "-loop-unroll",
        #         "-S", "compile-gt.bc",
        #        "-o", "unrolled.bc"]
        # exit_code = subprocess.run(compile_command)


        compile_command = ["opt",
                "-mem2reg",
                "-simplifycfg",
                "-loops",
                "-loop-simplify",
                "-loop-rotate",
                "-lcssa",
                "-indvars",
                "-loop-unroll",
                "-unroll-threshold=10000000",
                "-unroll-count=1000",
                "-S", "compile-gt.bc",
                "-o", "unrolled.bc"]
        exit_code = subprocess.run(compile_command)

        # compile_command =  ["opt", "-enable-new-pm=0", "-dot-cfg", "-S", "compile-gt.bc", "-disable-output"]
        compile_command = ["opt", "-enable-new-pm=0", "-dot-cfg", "-S", "unrolled.bc", "-disable-output"]
        exit_code = subprocess.run(compile_command)
        print(exit_code)


if __name__ == '__main__':
    unittest.main()