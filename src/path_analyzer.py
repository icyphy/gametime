import os
import file_helper
from nx_helper import Dag
from path import Path
from project_configuration import ProjectConfiguration
from gametime.src.backend.backend import Backend

class PathAnalyzer(object):

    def __init__(self, preprocessed_path: str, project_config: ProjectConfiguration, dag: Dag, path: Path, path_name: str):
        """
        used to run the entire simulation on the given path.

        :param preprocessed_path: the path to file being analyzed
        :param project_config: configuration of gametime
        :param dag: DAG representation of file being analyzed
        :param path: Path object corresponding to the path to drive
        :param path_name: all output files will be in folder with path_name; all generated files will have name path_name + "-gt"
        """
        #TODO for abdalla: create the KLEE to get the inputs file here and store it or down below in measure_path
        self.preprocessed_path: str = preprocessed_path
        self.project_config: ProjectConfiguration = project_config
        self.dag = dag
        self.path: Path = path
        self.output_folder: str = os.path.join(self.project_config.location_temp_dir, path_name)
        self.path_name: str = path_name
        self.output_name: str =  f'{path_name}-gt'
        file_helper.create_dir(self.output_folder)
        self.measure_folders: dict[str, str] = {}

    def measure_path(self, backend: Backend) -> int:
        """
        run the entire simulation on the given path

        :param backend: Backend object used for simulation
        :return the total measurement of path given by backend
        """
        temp_folder_backend: str = os.path.join(self.output_folder, backend.name)

        if backend.name not in self.measure_folders.keys():
            self.measure_folders[backend.name] = temp_folder_backend

        file_helper.create_dir(temp_folder_backend)
        #TODO for abdalla: put that file here and remove the = 0 line
        # measured_value: int = backend.measure({PLACEHOLDER_FOR_KLEE_INPUT_FILEPATH}, temp_folder_backend)
        measured_value = 0
        return measured_value

    def remove_measure(self, backend: Backend):
        file_helper.remove_all_except([], self.measure_folders.get(backend.name))

    def remove_all_measure(self):
        file_helper.remove_all_except([], self.output_folder)
