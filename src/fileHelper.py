#!/usr/bin/env python

"""Exposes miscellaneous functions to perform operations
on files and directories, such as creation, removal and movement.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import errno
import os
import re
import shutil

from gametimeError import GameTimeError


def createDir(location):
    """Creates the leaf directory in the path specified, along with any
    intermediate-level directories needed to contain the directory.
    This is a wrapper around the :func:`~os.makedirs` function of
    the :mod:`os` module, but does not raise an exception if
    the directory is already present,

    Arguments:
        location:
            Location of the directory to be created.
    """
    try:
        if not os.path.isdir(location):
            os.makedirs(location)
    except EnvironmentError as e:
        if e.errno != errno.EEXIST:
            raise GameTimeError("Cannot create directory located at %s: %s" %
                                (location, e))

def removeFile(location):
    """Removes the file at the provided location. This is a wrapper around
    the :func:`~os.remove` function of the :mod:`os` module, but does not
    raise an exception if the file is not present.

    Arguments:
        location:
            Location of the file to be removed.
    """
    try:
        if os.path.exists(location):
            os.remove(location)
    except EnvironmentError as e:
        raise GameTimeError("Cannot remove file located at %s: %s" %
                            (location, e))

def removeFiles(patterns, dirLocation):
    """Removes the files from the directory whose location is provided,
    whose names match any of the patterns in the list provided.

    Arguments:
        patterns:
            List of patterns to match filenames against.
        dirLocation:
            Location of the directory to remove files from.
    """
    for filename in os.listdir(dirLocation):
        for pattern in patterns:
            if re.search(pattern, filename):
                os.remove(os.path.join(dirLocation, filename))

def removeAllExcept(patterns, dirLocation):
    """Removes all of the files and directories from the directory whose
    location is provided, *except* for those files whose names match any
    of the patterns in the list provided.

    Arguments:
        patterns:
            List of patterns to match filenames against.
        dirLocation:
            Location of the directory to remove files and
            directories from.
    """
    # Code from http://stackoverflow.com/a/1073382/1834042.
    for root, dirs, files in os.walk(dirLocation):
        for filename in files:
            for pattern in patterns:
                if not re.search(pattern, filename):
                    os.unlink(os.path.join(root, filename))
        for dirname in dirs:
            shutil.rmtree(os.path.join(root, dirname))

def moveFiles(patterns, sourceDir, destDir, overwrite=True):
    """Moves the files, whose names match any of the patterns in the list
    provided, from the source directory whose location is provided to
    the destination directory whose location is provided. If a file in
    the destination directory has the same name as a file that is being moved
    from the source directory, the former is overwritten if `overwrite` is
    set to `True`; otherwise, the latter will not be moved.

    Arguments:
        patterns:
            List of patterns to match filenames against.
        sourceDir:
            Location of the source directory.
        destDir:
            Location of the destination directory.
        overwrite:
            Whether to overwrite a file in the destination directory that
            has the same name as a file that is being moved from the source
            directory. If `True`, the former is overwritten; if `False`,
            the latter will not be moved.
    """
    for filename in os.listdir(sourceDir):
        for pattern in patterns:
            if re.search(pattern, filename):
                sourceFile = os.path.join(sourceDir, filename)
                destFile = os.path.join(destDir, filename)
                if overwrite and os.path.exists(destFile):
                    os.remove(destFile)
                if overwrite or not os.path.exists(destFile):
                    shutil.move(sourceFile, destFile)
