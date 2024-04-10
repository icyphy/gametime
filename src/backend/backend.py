#!/usr/bin/env python

"""Exposes classes and functions to maintain a representation of, and
to interact with, a backend, which will be used to measure values
that correspond to different paths in the code that is being analyzed.
"""
from project_configuration import ProjectConfiguration
from typing import List
"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


class Backend(object):
    """Maintains a representation of a backend, which will be used
    to measure values that correspond to different paths in the code
    that is being analyzed.
    """

    def __init__(self, project_config: ProjectConfiguration, name: str=""):
        """
        :param project_config: GameTime project configuration for the code that is being analyzed
        :param name: name of the backend that this object represents
        """
        #: Name of the backend that this object represents.
        self.name: str = name

        #: GameTime project configuration for the code that is being analyzed.
        self.project_config: ProjectConfiguration = project_config
    
    def measure(self, inputs: str, measure_folder: str) -> int:
        """
        Perform measurement using the backend.
        :param inputs: the inputs to drive down a PATH in a txt file
        :param measure_folder: all generated files will be stored in MEASURE_FOLDER/{name of backend}
        :return the measured value of path
        """
        return 0