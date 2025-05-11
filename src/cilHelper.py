#!/usr/bin/env python

"""Exposes miscellaneous functions to interface with the CIL tool."""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import os
import subprocess

from defaults import config, sourceDir
from fileHelper import removeFiles


def _generateCilCommand(projectConfig, keepLineNumbers):
    """Generates the system call to run CIL on the file currently
    being analyzed.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
        keepLineNumbers:
            `True` if, and only if, the resulting file should contain
            preprocessor directives that maintain the line numbers from
            the original source file (and other included source files).

    Returns:
        Appropriate system call as a list that contains the program
        to be run and the proper arguments.
    """
    # Set the environment variable that allows the Cilly driver to find
    # the path to the configuration file for the Findlib OCaml module.
    os.environ["OCAMLFIND_CONF"] = os.path.join(sourceDir,
                                                "ocaml/conf/findlib.conf")

    # Set the environment variable that allows the Cilly driver to find
    # the path to the folder that contains the compiled OCaml files.
    os.environ["OCAMLPATH"] = os.path.join(sourceDir, "ocaml/lib")

    command = []

    command.append(os.path.join(config.TOOL_CIL, "bin/cilly.bat"))

    command.append("--dooneRet")
    command.append("--domakeCFG")
    command.append("--dosimpleMem")
    command.append("--disallowDuplication")
    if not keepLineNumbers:
        command.append("--noPrintLn")

    command.append("--dopartial")
    command.append("--partial_root_function=%s" % projectConfig.func)

    command.append(projectConfig.locationTempFile)

    command.append("-I'%s'" % projectConfig.locationOrigDir)
    for includePath in projectConfig.included:
        command.append("-I'%s'" % includePath)

    command.append("--save-temps='%s'" % projectConfig.locationTempDir)
    command.append("-c")
    command.append("-o")
    command.append("'%s.out'" % projectConfig.locationTempNoExtension)

    return command

def runCil(projectConfig, keepLineNumbers=False):
    """Conducts the sequence of system calls that will run CIL on the
    file currently being analyzed.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
        keepLineNumbers:
            `True` if, and only if, the resulting file should contain
            preprocessor directives that maintain the line numbers from
            the original source file (and other included source files).

    Returns:
        Zero if the calls were successful; a non-zero value otherwise.
    """
    command = _generateCilCommand(projectConfig, keepLineNumbers)
    print " ".join(command)
    return subprocess.call(command, shell=True)

def removeTempCilFiles(projectConfig):
    """Removes the temporary files created by CIL during its analysis.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
    """
    # Remove the files with extension ".cil.*".
    otherTempFiles = r".*\.cil\..*"
    removeFiles([otherTempFiles], projectConfig.locationTempDir)

    # By this point, we have files that are named the same as the
    # temporary file for GameTime, but that have different extensions.
    # Remove these files.
    otherTempFiles = r".*-gt\.[^c]+"
    removeFiles([otherTempFiles], projectConfig.locationTempDir)
