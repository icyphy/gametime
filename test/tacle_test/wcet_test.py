import unittest

import clang_helper
import shutil

from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from analyzer import Analyzer
from pulp_helper import generate_and_solve_core_problem
import os

class BaseTest(unittest.TestCase):
    config_path = None  
    backend_value = None

    def setUp(self):
        if not self.config_path:
            raise ValueError("Configuration path must be set in subclass")
        self.project_config = YAMLConfigurationParser.parse(self.config_path)
        shutil.rmtree(self.project_config.location_temp_dir)

        if self.backend_value:
            self.project_config.backend = self.backend_value
    
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
        # analyzer.measure_basis_paths()

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

##### Backend classes
class TestFlexpretBackend(BaseTest):
    backend_value = "Flexpret"
class TestX86Backend(BaseTest):
    backend_value = "X86"
class TestARMBackend(BaseTest):
    backend_value = "ARM"


#### Benchmarks
class TestIfElifElseFlexpret(TestFlexpretBackend):
    config_path = "./programs/if_elif_else/config.yaml"
class TestIfElifElseX86(TestX86Backend):
    config_path = "./programs/if_elif_else/config.yaml"
class TestIfElifElseARM(TestARMBackend):
    config_path = "./programs/if_elif_else/config.yaml"



class TestBitcnt2Flexpret(TestFlexpretBackend):
    config_path = "./programs/bitcount/config.yaml"
class TestBitcnt2X86(TestX86Backend):
    config_path = "./programs/bitcount/config.yaml"
class TestBitcnt2ARM(TestARMBackend):
    config_path = "./programs/bitcount/config.yaml"



class TestPrimeFlexpret(TestFlexpretBackend):
    config_path = "./programs/prime/config.yaml"
class TestPrimeX86(TestX86Backend):
    config_path = "./programs/prime/config.yaml"
class TestPrimeARM(TestARMBackend):
    config_path = "./programs/prime/config.yaml"



class TestModexpFlexpret(TestFlexpretBackend):
    config_path = "./programs/modexp/config.yaml"
class TestModexpX86(TestX86Backend):
    config_path = "./programs/modexp/config.yaml"
class TestModexpARM(TestARMBackend):
    config_path = "./programs/modexp/config.yaml"


class TestBinarysearchFlexpret(TestFlexpretBackend):
    config_path = "./programs/binarysearch/config.yaml"
class TestBinarysearchX86(TestX86Backend):
    config_path = "./programs/binarysearch/config.yaml"
class TestBinarysearchARM(TestARMBackend):
    config_path = "./programs/binarysearch/config.yaml"


class TestCountNegativeFlexpret(TestFlexpretBackend):
    config_path = "./programs/countnegative/config.yaml"
class TestCountNegativeX86(TestX86Backend):
    config_path = "./programs/countnegative/config.yaml"
class TestCountNegativeARM(TestARMBackend):
    config_path = "./programs/countnegative/config.yaml"

class TestInsertSortFlexpret(TestFlexpretBackend):
    config_path = "./programs/insertsort/config.yaml"
class TestInsertSortX86(TestX86Backend):
    config_path = "./programs/insertsort/config.yaml"
class TestInsertSortARM(TestARMBackend):
    config_path = "./programs/insertsort/config.yaml"

class TestBSortFlexpret(TestFlexpretBackend):
    config_path = "./programs/bsort/config.yaml"

class TestDeg2RadFlexpret(TestFlexpretBackend):
    config_path = "./programs/deg2rad/config.yaml"
    




if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    #Programs
    suite.addTests(loader.loadTestsFromTestCase(TestBinarysearchFlexpret))
    # suite.addTests(loader.loadTestsFromTestCase(TestBitcnt2Flexpret))
    # suite.addTests(loader.loadTestsFromTestCase(TestPrimeFlexpret))
    # suite.addTests(loader.loadTestsFromTestCase(TestIfElifElseX86))
    # suite.addTests(loader.loadTestsFromTestCase(TestBinarysearchARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestIfElifElseARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestBitcnt2ARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestPrimeARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestCountNegativeARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestModexpARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestInsertSortARM))

    runner = unittest.TextTestRunner()
    runner.run(suite)
