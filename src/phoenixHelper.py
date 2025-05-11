#!/usr/bin/env python

"""Exposes functions to interact with the program analysis
code written in Phoenix.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import os
import subprocess

from defaults import config
from fileHelper import removeFiles


import traceback

def _generatePhoenixCommand(projectConfig):
    """Generates the system call that provides the appropriate arguments
    to the Phoenix program analysis code.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.

    Returns:
        Appropriate system call as a list that contains the program
        to be run and the proper arguments.
    """
    locationTempFile = projectConfig.locationTempFile
    locationTempFileNoExt, _ = os.path.splitext(locationTempFile)

    command = []
    command.append("cl")

    command.append("-c")

    command.append("-nologo")
    command.append("-Ob1")
    command.append("-O2")
    command.append("-d2plugin:%s" % config.TOOL_PHOENIX)
    command.append(locationTempFile)
    command.append("-Fo\"%s.obj\"" % locationTempFileNoExt)
    command.append("-Fe\"%s.exe\"" % locationTempFileNoExt)

    return command

def _removeTempPhoenixFiles(projectConfig):
    """Removes the temporary files created by the Phoenix analysis code.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
    """
    # By this point, we have files that are named the same as the
    # temporary file for GameTime, but that have different extensions.
    # Remove these files.
    otherTempFiles = r".*-gt\.[^c]+"
    removeFiles([otherTempFiles], projectConfig.locationTempDir)

def _runPhoenix(projectConfig, mode):
    """Conducts the sequence of system calls that will run
    the Phoenix program analysis code in a specific mode.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
        mode:
            Mode that the Phoenix program analysis code should work in.

    Returns:
        Zero if the program analysis was successful; a non-zero
        value otherwise.
    """
    command = _generatePhoenixCommand(projectConfig)

    projectConfig.writeToXmlFile()
    procArgs = "\n".join([config.configFile,
                          projectConfig.locationXmlFile,
                          mode])
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, shell=True)
    proc.communicate(procArgs)

    _removeTempPhoenixFiles(projectConfig)
    return proc.returncode

def createDag(projectConfig):
    """Conducts the sequence of system calls that will create the directed
    acyclic graph (DAG) that corresponds to the function unit currently
    being analyzed.

    Returns:
        Zero if the program analysis was successful; a non-zero
        value otherwise.
    """
    return _runPhoenix(projectConfig, config.TEMP_PHX_CREATE_DAG)

def findConditions(projectConfig):
    """Conducts the sequence of system calls that will find the conditions
    along a path in the directed acyclic graph (DAG) that corresponds to
    the function unit currently being analyzed.

    Returns:
        Zero if the program analysis was successful; a non-zero
        value otherwise.
    """
    return _runPhoenix(projectConfig, config.TEMP_PHX_FIND_CONDITIONS)
