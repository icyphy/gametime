import unittest

import clang_helper
import shutil

from path_analyzer import PathAnalyzer
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from backend.flexpret_backend import flexpret_backend
from analyzer import Analyzer
import os
from smt_solver.extract_labels import find_labels
from smt_solver.smt import run_smt

class TestFlexpret(unittest.TestCase):
    def setUp(self):
        self.project_config: ProjectConfiguration = \
            YAMLConfigurationParser.parse("./programs/add/config.yaml")
        shutil.rmtree(self.project_config.location_temp_dir)

    def test_measure_basis_path(self):
        analyzer = Analyzer(self.project_config)
        analyzer.create_dag()
        paths = analyzer.generate_basis_paths()

        self.assertIsNotNone(paths[0], "no paths were found")
        output_dir = os.path.join(self.project_config.location_temp_dir, "output")
        os.mkdir(output_dir)
        labels = []
        for path in paths:
            bitcode = []
            for node in path.nodes:
                bitcode.append(analyzer.dag.get_node_label(analyzer.dag.nodes_indices[node]))
            labels_file = find_labels("".join(bitcode), output_dir)
            run_smt(self.project_config, labels_file, output_dir)


if __name__ == '__main__':
    unittest.main()
