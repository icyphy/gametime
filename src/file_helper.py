#!/usr/bin/env python

"""Exposes miscellaneous functions to perform operations
on files and directories, such as creation, removal and movement.
"""
from typing import List

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import errno
import os
import re
import shutil

from gametime_error import GameTimeError


def create_dir(location: str) -> None:
    """Creates the leaf directory in the path specified, along with any
    intermediate-level directories needed to contain the directory.
    This is a wrapper around the :func:`~os.makedirs` function of
    the :mod:`os` module, but does not raise an exception if
    the directory is already present,

    Parameters
    ----------
    location: str :
        Location of the directory to be created

    """
    try:
        if not os.path.isdir(location):
            os.makedirs(location)
    except EnvironmentError as e:
        if e.errno != errno.EEXIST:
            raise GameTimeError("Cannot create directory located at %s: %s" %
                                (location, e))

def remove_file(location: str) -> None:
    """Removes the file at the provided location. This is a wrapper around
    the :func:`~os.remove` function of the :mod:`os` module, but does not

    Parameters
    ----------
    location: str :
        Location of the file to be removed

    """
    try:
        if os.path.exists(location):
            os.remove(location)
    except EnvironmentError as e:
        raise GameTimeError("Cannot remove file located at %s: %s" %
                            (location, e))

def remove_files(patterns: List[str], dir_location: str) -> None:
    """Removes the files from the directory whose location is provided,
    whose names match any of the patterns in the list provided.

    Parameters
    ----------
    patterns: List[str] :
        List of patterns to match filenames against
    dir_location: str :
        Location of the directory to remove files from

    """
    for filename in os.listdir(dir_location):
        for pattern in patterns:
            if re.search(pattern, filename):
                os.remove(os.path.join(dir_location, filename))

def remove_all_except(patterns: List[str], dir_location: str) -> None:
    """Removes all_temp_files of the files and directories from the directory whose
    location is provided, *except* for those files whose names match any
    of the patterns in the list provided.

    Parameters
    ----------
    patterns: List[str] :
        List of patterns to match filenames against
    dir_location: str :
        Location of the directory to remove files from

    """
    # Code from http://stackoverflow.com/a/1073382/1834042.
    root: str
    dirs: list[str]
    files: list[str]
    for root, dirs, files in os.walk(dir_location):
        for filename in files:
            for pattern in patterns:
                if not re.search(pattern, filename):
                    os.unlink(os.path.join(root, filename))
        for dirname in dirs:
            shutil.rmtree(os.path.join(root, dirname))

def move_files(patterns: List[str], source_dir: str, dest_dir: str, overwrite: bool = True) -> None:
    """Moves the files, whose names match any of the patterns in the list
    provided, from the source directory whose location is provided to
    the destination directory whose location is provided. If a file in
    the destination directory has the same name as a file that is being moved
    from the source directory, the former is overwritten if `overwrite` is
    set to `True`; otherwise, the latter will not be moved.

    Parameters
    ----------
    patterns: List[str] :
        List of patterns to match filenames against
    source_dir: str :
        Location of the source directory
    dest_dir: str :
        Location of the destination directory
    overwrite: bool :
        Whether to overwrite a file in the destination directory that has the same name as a file that is being moved from the source directory. (Default value = True)

    """
    for filename in os.listdir(source_dir):
        for pattern in patterns:
            if re.search(pattern, filename):
                source_file: str = os.path.join(source_dir, filename)
                dest_file: str = os.path.join(dest_dir, filename)
                if overwrite and os.path.exists(dest_file):
                    os.remove(dest_file)
                if overwrite or not os.path.exists(dest_file):
                    shutil.move(source_file, dest_file)