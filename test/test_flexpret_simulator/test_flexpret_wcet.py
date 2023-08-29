import unittest

from path import Path
from path_analyzer import PathAnalyzer
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from simulator.flexpret_simulator import flexpret_simulator
from src import Analyzer

class FlexpretTest(unittest.TestCase):

    def compile_wcet_path_analyzer(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        analyzer.measure_basis_paths()
        generated_paths = analyzer.generate_paths()
        results = []
        fp_simulator = flexpret_simulator.FlexpretSimulator(self.project_config)
        for i in range(len(generated_paths)):
            output_name: str = f'path{i}'
            p: Path = generated_paths[i]
            path_analyzer = PathAnalyzer(analyzer.preprocessed_path, analyzer.project_config, analyzer.dag, p, output_name)
            value = path_analyzer.measure_path(fp_simulator)
            p.set_measured_value(value)
            results.append(value)
        print(results)

    def compile_wcet_analyzer(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()
        self.assertIsNotNone(paths[0], "no paths were found")
        analyzer.measure_basis_paths()
        generated_paths = analyzer.generate_paths()
        results = []
        for i in range(len(generated_paths)):
            output_name: str = f'path{i}'
            p: Path = generated_paths[i]
            value = analyzer.measure_path(p, output_name)
            p.set_measured_value(value)
            results.append(value)
        print(results)

class TestAdd(FlexpretTest):
    def setUp(self):
        print("setup test add")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/add/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestCalloc(FlexpretTest):
    def setUp(self):
        print("setup test calloc")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/calloc/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestFib(FlexpretTest):
    def setUp(self):
        print("setup test fib")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/fib/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestGlobal(FlexpretTest):
    def setUp(self):
        print("setup test global")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/global/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestGpio(FlexpretTest):
    def setUp(self):
        print("setup test gpio")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/gpio/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestHwlock(FlexpretTest):
    def setUp(self):
        print("setup test hwlock")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/hwlock/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestLbu(FlexpretTest):
    def setUp(self):
        print("setup test lbu")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/lbu/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestMalloc(FlexpretTest): # cycle issue
    def setUp(self):
        print("setup test malloc")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/malloc/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestRealloc(FlexpretTest):
    def setUp(self):
        print("setup test realloc")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/realloc/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestSyscall(FlexpretTest):
    def setUp(self):
        print("setup test syscall")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/syscall/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()

class TestTime(FlexpretTest):
    def setUp(self):
        print("setup test time")
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/time/config.yaml")

    def test_compile_wcet_path_analyzer(self):
        self.compile_wcet_path_analyzer()

    def test_compile_wcet_analyzer(self):
        self.compile_wcet_analyzer()




if __name__ == '__main__':
    unittest.main()