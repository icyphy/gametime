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
import logging_helper
import os

# Initialize the GameTime logger (as described in
# http://docs.python.org/2/howto/logging-cookbook.html).
logger: logging.Logger = logging.getLogger("gametime")
logging_helper.initialize(logger)

# This import is done later, so that the module
# :module:`~gametime.configuration` can use the GameTime logger.
import gametime_configuration

#: Default directory that contains the source files of GameTime.
source_dir: str = os.path.dirname(os.path.abspath(__file__))
#: Default configuration YAML file.
config_file: str = os.path.join(source_dir, "config.yaml.in")

#: Default directory that contains the GameTime GUI.
gui_dir: str = os.path.join(source_dir, "gui")

logger.info("Reading GameTime configuration in %s..." % config_file)
logger.info("")
#: Default :class:`~gametime.configuration.GametimeConfiguration` object
#: that represents the configuration of GameTime.
config: gametime_configuration.GametimeConfiguration = gametime_configuration.read_gametime_config_yaml(config_file)

logger.info("Successfully configured GameTime.")
logger.info("")
