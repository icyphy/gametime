import os
import file_helper
from nx_helper import Dag
from path import Path
from project_configuration import ProjectConfiguration
from simulator.simulator import Simulator

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
        self.preprocessed_path: str = preprocessed_path
        self.project_config: ProjectConfiguration = project_config
        self.dag = dag
        self.path: Path = path
        self.output_folder: str = os.path.join(self.project_config.location_temp_dir, path_name)
        self.path_name: str = path_name
        self.output_name: str =  f'{path_name}-gt'
        file_helper.create_dir(self.output_folder)
        self.measure_folders: dict[str, str] = {}

    def measure_path(self, simulator: Simulator) -> int:
        """
        run the entire simulation on the given path

        :param simulator: Simulator object used for simulation
        :return the total measurement of path given by simulator
        """
        temp_folder_simulator: str = os.path.join(self.output_folder, simulator.name)

        if simulator.name not in self.measure_folders.keys():
            self.measure_folders[simulator.name] = temp_folder_simulator

        file_helper.create_dir(temp_folder_simulator)
        path_bc_filepath: str = self.change_bt_based_on_path()
        measured_value: int = simulator.measure(path_bc_filepath, temp_folder_simulator,  self.output_name)
        return measured_value

    def remove_measure(self, simulator: Simulator):
        file_helper.remove_all_except([], self.measure_folders.get(simulator.name))

    def remove_all_measure(self):
        file_helper.remove_all_except([], self.output_folder)

    def change_bt_based_on_path(self) -> str:
        """
        Change LLVM code to drive program down a path specified by the
        path parameter. Writes the LLVM file back to the temporary folder.

        :return the file path to generated .bc file
        """
        # read from file
        with open(self.preprocessed_path, "r") as preprocessed_file:
            program_str: str = preprocessed_file.read()

        # assemble path
        prev_condition: str = ""
        prev_block_number: int = 0

        for node in self.path.nodes:
            node_label: str = self.dag.get_node_label(self.dag.nodes_indices[node])
            block_number: str = node_label[node_label.find("%"):node_label.find(":")]  # find %4 for {%4:...
            if prev_condition:  # update prev condition to point to this node
                prev_block_begin_index: int = program_str.find("{}:".format(prev_block_number))
                prev_block: str = program_str[prev_block_begin_index:]
                condition_begin_index: int = prev_block.find(prev_condition)
                prev_condition_index: int = prev_block_begin_index + condition_begin_index
                program_str: str = program_str[:prev_condition_index] \
                              + "br label {}".format(block_number) \
                              + program_str[prev_condition_index + len(prev_condition):]

            index: int = node_label.rfind("br")  # find the last branch (assume last branch contains conditions)
            if index == -1:  # in case it is sink (no more branches)
                continue
            condition: str = node_label[index:]
            index: int = condition.find('\\')
            condition = condition[:index]
            if condition.count("label") > 1:  # branch rather than jump
                prev_condition = condition
            else:
                prev_condition = ""
            prev_block_number = int(block_number[1:])

        # write to file
        output_path: str = os.path.join(self.output_folder, f"{self.output_name}.bc")
        with open(output_path, "w") as output_file:
            output_file.write(program_str)

        return output_path
