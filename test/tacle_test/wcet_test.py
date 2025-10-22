import unittest

import clang_helper
import shutil

from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from analyzer import Analyzer
from pulp_helper import generate_and_solve_core_problem
import os

# Import visualization functions
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from nx_helper import write_dag_to_dot_file

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
        
        # Visualize the weighted graph
        print("\n" + "="*60)
        print("GENERATING WEIGHTED GRAPH DOT FILE")
        print("="*60)
        
        # Estimate edge weights
        analyzer.estimate_edge_weights()
        
        # Create DOT file for external tools
        output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'visualizations')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename based on test class
        test_name = self.__class__.__name__.lower()
        dot_path = os.path.join(output_dir, f'{test_name}_weighted_graph.dot')
        
        # Create edge labels with weights
        edge_labels = {}
        edge_list = list(analyzer.dag.all_edges)
        for i in range(len(analyzer.dag.edge_weights)):
            if i < len(edge_list):
                edge = edge_list[i]
                weight = analyzer.dag.edge_weights[i]
                if abs(weight) > 0.01:  # Only label non-zero weights
                    edge_labels[edge] = f'{weight:.2f}'
                else:  # Add zero weights too to avoid KeyError
                    edge_labels[edge] = '0.00'
        
        print(f"\nCreating weighted graph DOT file...")
        write_dag_to_dot_file(analyzer.dag, dot_path, edges_to_labels=edge_labels)
        print(f"DOT file saved to: {dot_path}")
        print("="*60)

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
    # suite.addTests(loader.loadTestsFromTestCase(TestBinarysearchFlexpret))
    # suite.addTests(loader.loadTestsFromTestCase(TestBitcnt2Flexpret))
    # suite.addTests(loader.loadTestsFromTestCase(TestPrimeFlexpret))
    # suite.addTests(loader.loadTestsFromTestCase(TestIfElifElseX86))
    # suite.addTests(loader.loadTestsFromTestCase(TestBinarysearchARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestIfElifElseARM))
    suite.addTests(loader.loadTestsFromTestCase(TestIfElifElseFlexpret))
    # suite.addTests(loader.loadTestsFromTestCase(TestBitcnt2ARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestPrimeARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestCountNegativeARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestModexpARM))
    # suite.addTests(loader.loadTestsFromTestCase(TestInsertSortARM))

    runner = unittest.TextTestRunner()
    runner.run(suite)
