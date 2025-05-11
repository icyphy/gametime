#!/usr/bin/env python

"""Exposes functions to perform a source-to-source transformation
that merges the source file, which contains the code under analysis,
with other user-specified external files.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import os
import subprocess

from defaults import config, sourceDir
from gametimeError import GameTimeError


def _generateOtherSourcesFile(projectConfig):
    """Creates a file that contains the paths of other files to be
    merged with the source file.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.

    Returns:
        Path to the file that contains the paths of other files
        to be merged with the source file.
    """
    otherSourcesFilePath = os.path.join(projectConfig.locationTempDir,
                                        config.TEMP_MERGED)

    # Create the file.
    try:
        otherSourcesFileHandler = open(otherSourcesFilePath, "w")
    except EnvironmentError as e:
        errMsg = ("Error creating a temporary file located at %s, "
                  "which stores the paths of the other files to be "
                  "merged with the source file: %s" %
                  (otherSourcesFilePath, e))
        raise GameTimeError(errMsg)
    else:
        with otherSourcesFileHandler:
            for filePath in projectConfig.merged:
                otherSourcesFileHandler.write("%s\n" % filePath)

    return otherSourcesFilePath

def _generateMergerCommand(projectConfig, otherSourcesFilePath):
    """Generates the system call that performs a source-to-source
    transformation to merge the source file, which contains
    the code under analysis, with other user-specified external files.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
        otherSourcesFilePath:
            Path to the file that contains the paths to
            user-specified external files.

    Returns:
        Appropriate system call as a list that contains the program
        to be run and the proper arguments.
    """
    # Set the environment variable that allows the Cilly driver to find
    # the path to the configuration file for the Findlib OCaml module.
    os.environ["OCAMLFIND_CONF"] = os.path.join(sourceDir,
                                                "ocaml/conf/findlib.conf")

    # Set the environment variable that allows the Cilly driver to find
    # the path to the directory that contains the compiled OCaml files.
    os.environ["OCAMLPATH"] = os.path.join(sourceDir, "ocaml/lib")

    command = []

    command.append(os.path.join(config.TOOL_CIL, "bin/cilly.bat"))

    command.append("--merge")
    command.append("--extrafiles='%s'" % otherSourcesFilePath)

    command.append(projectConfig.locationTempFile)

    command.append("-I'%s'" % projectConfig.locationOrigDir)
    for includePath in projectConfig.included:
        command.append("-I'%s'" % includePath)

    command.append("--save-temps='%s'" % projectConfig.locationTempDir)
    command.append("-o")
    command.append("'%s.out'" % projectConfig.locationTempNoExtension)

    return command

def runMerger(projectConfig):
    """Conducts the sequence of system calls that will perform
    a source-to-source transformation to merge the source file,
    which contains the code under analysis, with other user-specified
    external files.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.

    Returns:
        Zero if the merging was successful; a non-zero value otherwise.
    """
    # Trigger the environment variable that prevents Cilly from
    # compiling and linking the file that is produced by merging.
    os.environ["CILLY_DONT_COMPILE_AFTER_MERGE"] = "1"

    otherSourcesFilePath = _generateOtherSourcesFile(projectConfig)
    command = _generateMergerCommand(projectConfig, otherSourcesFilePath)
    return subprocess.call(command, shell=True)
