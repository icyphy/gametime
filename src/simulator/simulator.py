#!/usr/bin/env python

"""Exposes classes and functions to maintain a representation of, and
to interact with, a simulator, which will be used to measure values
that correspond to different paths in the code that is being analyzed.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import os

from defaults import config, logger
from gametime_error import GameTimeError


class Simulator(object):
    """Maintains a representation of a simulator, which will be used
    to measure values that correspond to different paths in the code
    that is being analyzed.
    Attributes:
        projectConfig:
            GameTime project configuration for the code that
            is being analyzed.
        name:
            Name of the simulator that this object represents.
    """

    def __init__(self, projectConfig, name=""):
        #: Name of the simulator that this object represents.
        self.name = name

        #: GameTime project configuration for the code that is being analyzed.
        self.projectConfig = projectConfig

        #: Path to the temporary directory that will store the temporary files that are generated during measurement.
        self._measurementDir = os.path.join(projectConfig.locationTempDir,
                                            "%s-%s" % (config.TEMP_MEASUREMENT,
                                                       self.name.lower()))