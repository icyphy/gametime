import unittest

import clang_helper
import shutil

from path_analyzer import PathAnalyzer
from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from simulator.flexpret_simulator import flexpret_simulator
from analyzer import Analyzer
import os
import extract_labels
import smt

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
        #print([analyzer.dag.get_node_label(analyzer.dag.nodes_indices[node])  for path in paths for node in path.nodes])
        # extract bitcode from path
        labels = []
        for path in paths:
            bitcode = []
            for node in path.nodes:
                bitcode.append(analyzer.dag.get_node_label(analyzer.dag.nodes_indices[node]))
            labels_file = extract_labels.find_labels("".join(bitcode))
            smt.run_smt(labels_file)
            labels.append(bitcode_labels)
        print(labels)

        # path_analyzer = PathAnalyzer(analyzer.preprocessed_path, analyzer.project_config, analyzer.dag, paths[0], "path0")
        # output_file = path_analyzer.change_bt_based_on_path()
        # print(output_file)
        
        # self.assertIsNotNone(output_file)
        # self.assertTrue(len(output_file) != 0)
        # self.assertTrue(os.path.isfile(output_file))

        analyzer.measure_basis_paths()



if __name__ == '__main__':
    unittest.main()
