import unittest

import shutil

from path import Path
from path_analyzer import PathAnalyzer
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from simulator.flexpret_simulator import flexpret_simulator
from src import Analyzer

class TestFlexpret(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/add/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)

    def test_compile_wcet(self):
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

    def test_compile_wcet_simp(self):
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


if __name__ == '__main__':
    unittest.main()