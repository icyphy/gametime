#!/usr/bin/env python

"""Exposes functions to interact with, and modify an object of,
the :mod:`logging` Python class.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import logging
import sys


def initialize(logger):
    """Initializes the logger provided with
    :class:`~logging.Formatter` and :class:`~logging.StreamHandler`
    objects appropriate for GameTime.

    Arguments:
        logger:
            Logger to initialize.
    """
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter("%(message)s")

    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.INFO)
    stdoutHandler.setFormatter(formatter)
    logger.addHandler(stdoutHandler)

    stderrHandler = logging.StreamHandler(sys.stderr)
    stderrHandler.setLevel(logging.ERROR)
    stderrHandler.setFormatter(formatter)
    logger.addHandler(stderrHandler)
