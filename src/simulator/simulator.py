#!/usr/bin/env python

"""Exposes classes and functions to maintain a representation of, and
to interact with, a simulator, which will be used to measure values
that correspond to different paths in the code that is being analyzed.
"""
from project_configuration import ProjectConfiguration
from typing import List
"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


class Simulator(object):
    """Maintains a representation of a simulator, which will be used
    to measure values that correspond to different paths in the code
    that is being analyzed.
    """

    def __init__(self, project_config: ProjectConfiguration, name: str=""):
        """
        :param project_config: GameTime project configuration for the code that is being analyzed
        :param name: name of the simulator that this object represents
        """
        #: Name of the simulator that this object represents.
        self.name: str = name

        #: GameTime project configuration for the code that is being analyzed.
        self.project_config: ProjectConfiguration = project_config

    #TODO: retire this
    def measure(self, path_bc_filepath: str, measure_folder: str, file_name: str) -> int:
        """
        Perform measurement using the simulator.

        :param path_bc_filepath: the file path to the generated .bc file used for simulation; should correspond to a PATH
        :param measure_folder: all generated files will be stored in MEASURE_FOLDER/{name of simulator}
        :param file_name: the file name of the measured file, and all generated files will use when applicable
        :return the measured value of path
        """
        return 0
    
    def measure(self, inputs: List[any], measure_folder: str) -> int:
        """
        Perform measurement using the simulator.
        :param inputs: the inputs to drive down a PATH
        :param measure_folder: all generated files will be stored in MEASURE_FOLDER/{name of simulator}
        :return the measured value of path
        """
        return 0