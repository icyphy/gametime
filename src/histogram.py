#!/usr/bin/env python

"""Exposes functions to create, and interact with, a histogram
computed from the values of feasible paths generated by GameTime.
"""
from path import Path

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import numpy as np

from defaults import logger
from gametime_error import GameTimeError


def compute_histogram(paths: list[Path], bins=10, path_value_range=None, measured=False):
    """Computes a histogram from the values of a list of
    feasible paths generated by GameTime. This function is
    a wrapper around the function :func:`~numpy.histogram` from
    the module :mod:`numpy`. Refer to the documentation of this
    function for more information about the computed histogram.

    Arguments:
        paths:
            List of feasible paths generated by GameTime, each
            represented by a :class:`~gametime.path.Path` object.
        bins:
            Same purpose as the same-named argument of the function
            :func:`numpy.histogram`.
        range:
            Same purpose as the same-named argument of the function
            :func:`numpy.histogram`.
        measured:
            `True` if, and only if, the values that will be used for
            the histogram are the measured values of the feasible paths.

    Returns:
        Tuple, whose first element is an array of the values of
        the histogram, and whose second element is an array of
        the left edges of the bins.
    """
    path_values = [path.measured_value if measured else path.predicted_value
                  for path in paths]
    if path_value_range is None:
        path_value_range = (min(path_values), max(path_values))
    return np.histogram(path_values, bins=bins, range=path_value_range)

def write_histogram_to_file(location, paths, bins=10, path_value_range=None, measured=False):
    logger.info("Creating histogram...")

    hist, bin_edges = compute_histogram(paths, bins, path_value_range, measured)
    try:
        histogram_file_handler = open(location, "w")
    except EnvironmentError as e:
        err_msg = ("Error writing the histogram to the file located "
                  "at %s: %s" % (location, e))
        raise GameTimeError(err_msg)
    else:
        with histogram_file_handler:
            for binEdge, sample in zip(bin_edges, hist):
                histogram_file_handler.write("%s\t%s\n" % (binEdge, sample))

    logger.info("Histogram created.")
