import unittest

import clang_helper
import shutil

from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from simulator.flexpret_simulator import flexpret_simulator
from src import Analyzer

# make
# riscv32-unknown-elf-gcc -T
# ../flexpret//programs/lib/linker/flexpret.ld -L
# ../flexpret//programs/lib/linker -Xlinker -Map=riscv-gt.map
# -g -static -O0 -march=rv32i -mabi=ilp32 -nostartfiles --specs=nosys.specs
# -I../flexpret//programs/lib/include  -o riscv-gt.riscv ../flexpret//programs/lib/start.S
# ../flexpret//programs/lib/startup.c riscv-gt.o ../flexpret//programs/lib/syscalls.c ../flexpret//programs/lib/flexpret_thread.c
# ../flexpret//programs/lib/flexpret_lock.c ../flexpret//programs/lib/tinyalloc/tinyalloc.c ../flexpret//programs/lib/flexpret_exceptions.c

class TestFlexpret(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/add/config.yaml")
        shutil.rmtree(self.project_config.locationTempDir)

    def test_compile_c(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        output_file = analyzer.change_bt_based_on_path(paths[0])
        object_file_path = clang_helper.compile_to_object(output_file, self.project_config)
        object_file_name = object_file_path[object_file_path.rfind('/')+1:-2]
        print(object_file_name)

    def test_compile_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        output_file = analyzer.change_bt_based_on_path(paths[0])
        object_file_path = clang_helper.compile_to_object(output_file, self.project_config)
        object_file_name = object_file_path[object_file_path.rfind('/') + 1:-2]

        fp_simulator = flexpret_simulator.FlexpretSimulator(self.project_config)
        generated_mem_file_name = fp_simulator.object_file_to_mem(object_file_name)
        value = fp_simulator.measure(generated_mem_file_name)
        print(value)

if __name__ == '__main__':
    unittest.main()
