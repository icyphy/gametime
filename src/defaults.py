#!/usr/bin/env python

"""Initializes the various variables, used in different
submodules of GameTime, with default values.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import logging
import loggingHelper
import os


# Initialize the GameTime logger (as described in
# http://docs.python.org/2/howto/logging-cookbook.html).
logger = logging.getLogger("gametime")
loggingHelper.initialize(logger)


# This import is done later, so that the module
# :module:`~gametime.configuration` can use the GameTime logger.
import configuration


#: Default directory that contains the source files of GameTime.
sourceDir = os.path.dirname(os.path.abspath(__file__))
#: Default configuration XML file.
configFile = os.path.join(sourceDir, "config.xml")

#: Default directory that contains the GameTime GUI.
guiDir = os.path.join(sourceDir, "gui")

logger.info("Reading GameTime configuration in %s..." % configFile)
logger.info("")
#: Default :class:`~gametime.configuration.Configuration` object
#: that represents the configuration of GameTime.
config = configuration.readConfigFile(configFile)
logger.info("Successfully configured GameTime.")
logger.info("")
