import unittest

import shutil

from path import Path
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from src import Analyzer

class TestFlexpret(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("test_flexpret_simulator/programs/add/config.yaml")
        shutil.rmtree(self.project_config.locationTempDir)

    def test_compile_c(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        basis_paths = analyzer.generate_basis_paths()
        analyzer.measure_basis_paths()
        generated_paths = analyzer.generate_paths()
        results = []
        for i in range(len(generated_paths)):
            output_name: str = f'path{i}'
            p: Path = analyzer.basisPaths[i]
            value = analyzer.measure_path(p, output_name)
            p.set_measured_value(value)
            results.append(value)
        print(results)


if __name__ == '__main__':
    unittest.main()