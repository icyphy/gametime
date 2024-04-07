import unittest

import clang_helper
import shutil

from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from analyzer import Analyzer
import os

class BaseX86Test(unittest.TestCase):
    def setUp(self):
        # This method must be overridden by subclasses
        pass
    
    def create_analyzer(self):
        return Analyzer(self.project_config)

    # def test_measure_basis_path(self):
    #     analyzer = self.create_analyzer()
    #     analyzer.create_dag()
    #     paths = analyzer.generate_basis_paths()

    #     self.assertIsNotNone(paths[0], "no paths were found")
    #     analyzer.measure_basis_paths()
    #     for p in paths:
    #         print(p.get_measured_value())

    def test_wcet_analyzer(self):
            analyzer = self.create_analyzer()
            analyzer.create_dag()

            basis_paths = analyzer.generate_basis_paths()
            self.assertIsNotNone(basis_paths[0], "no paths were found")
            analyzer.measure_basis_paths()

            generated_paths = analyzer.generate_paths()
            results = []

            for i in range(len(generated_paths)):
                output_name: str = f'path{i}'
                p = generated_paths[i]
                value = analyzer.measure_path(p, output_name)
                results.append(f"{p.name}: {value}")

            for p in basis_paths:
                print(f"basis path: {p.name} {p.get_measured_value()}")

            print(results)



class TestIfElifElse(BaseX86Test):
    def setUp(self):
        self.project_config = YAMLConfigurationParser.parse("./programs/if_elif_else/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)

class TestBitcnt2(BaseX86Test):
    def setUp(self):
        self.project_config: ProjectConfiguration = YAMLConfigurationParser.parse("./programs/bitcount/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)

class TestPrime(BaseX86Test):
    def setUp(self):
        self.project_config: ProjectConfiguration = YAMLConfigurationParser.parse("./programs/prime/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)

class TestModexp(BaseX86Test):
    def setUp(self):
        self.project_config: ProjectConfiguration = YAMLConfigurationParser.parse("./programs/modexp/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)

class TestBinarySearch(BaseX86Test):
    def setUp(self):
        self.project_config: ProjectConfiguration = YAMLConfigurationParser.parse("./programs/binarysearch/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)



if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    #Programs
    # suite.addTests(loader.loadTestsFromTestCase(TestIfElifElse))
    # suite.addTests(loader.loadTestsFromTestCase(TestBitcnt2))
    # suite.addTests(loader.loadTestsFromTestCase(TestPrime))
    suite.addTests(loader.loadTestsFromTestCase(TestBinarySearch))

    runner = unittest.TextTestRunner()
    runner.run(suite)
