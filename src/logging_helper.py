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


def initialize(logger: logging.Logger) -> None:
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

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)
