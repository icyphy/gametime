import os
import re
import file_helper
from nx_helper import Dag
from path import Path
from project_configuration import ProjectConfiguration
from backend.backend import Backend
from smt_solver.extract_labels import find_labels
from smt_solver.smt import run_smt

class PathAnalyzer(object):

    def __init__(self, preprocessed_path: str, project_config: ProjectConfiguration, dag: Dag, path: Path, path_name: str, repeat: int = 1):
        """
        used to run the entire simulation on the given path.

        Parameters:
            preprocessed_path :
                the path to file being analyzed
            project_config :
                configuration of gametime
            dag :
                DAG representation of file being analyzed
            path :
                Path object corresponding to the path to drive
            path_name :
                all output files will be in folder with path_name; all generated files will have name path_name + "-gt"
        """
       
        self.preprocessed_path: str = preprocessed_path
        self.project_config: ProjectConfiguration = project_config
        self.dag = dag
        self.path: Path = path
        self.output_folder: str = os.path.join(self.project_config.location_temp_dir, path_name)
        self.path_name: str = path_name
        self.output_name: str =  f'{path_name}-gt'
        file_helper.create_dir(self.output_folder)
        self.measure_folders: dict[str, str] = {}
        bitcode = []
        for node in path.nodes:
            bitcode.append(self.dag.get_node_label(self.dag.nodes_indices[node]))
        labels_file = find_labels("".join(bitcode), self.output_folder)

        all_labels_file = os.path.join(project_config.location_temp_dir, "labels_0.txt")
        with open(all_labels_file, "r") as out_file:
            lines = out_file.readlines()


        all_labels_file = os.path.join(project_config.location_temp_dir, "labels_0.txt")
        total_num_labels = 0
        number_line_pattern = re.compile(r'^\s*\d+\s*$')

        with open(all_labels_file, "r") as out_file:
            for line_number, line in enumerate(out_file, 1):  # Using enumerate to get line number
                if number_line_pattern.match(line):  # Check if the line matches the pattern
                    total_num_labels += 1
                else:
                    raise ValueError(f"Error on line {line_number}: '{line.strip()}' is not a valid line with exactly one number.")


        self.is_valid = run_smt(self.project_config, labels_file, self.output_folder, total_num_labels)
        self.values_filepath = f"{self.output_folder}/klee_input_0_values.txt"
        self.repeat = repeat

    def measure_path(self, backend: Backend) -> int:
        """
        run the entire simulation on the given path

        Parameters:
            backend: Backend :
                Backend object used for simulation

        Returns:
            the total measurement of path given by backend
        """
        if not self.is_valid:
            return float('inf')
        temp_folder_backend: str = os.path.join(self.output_folder, backend.name)

        if backend.name not in self.measure_folders.keys():
            self.measure_folders[backend.name] = temp_folder_backend

        file_helper.create_dir(temp_folder_backend)
        measured_values = []
        for _ in range(self.repeat):
            measured_values.append(backend.measure(self.values_filepath, temp_folder_backend))
        return max(measured_values)

