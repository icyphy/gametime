#!/usr/bin/env python

"""Exposes functions to perform a source-to-source transformation that
inlines user-specified functions in the C file currently being analyzed.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import os
import subprocess

from defaults import config, sourceDir


def _generateInlinerCommand(projectConfig):
    """Generates the system call that runs the CIL inliner with
    appropriate inputs.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.

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

    # Set the environment variable that configures the Cilly driver to load
    # the features that will be needed for the inliner.
    os.environ["CIL_FEATURES"] = "cil.default-features,cil.inliner"

    command = []

    command.append(os.path.join(config.TOOL_CIL, "bin/cilly.bat"))

    inlined = projectConfig.inlined
    for funcName in inlined:
        command.append("--inline=%s" % funcName)

    command.append(projectConfig.locationTempFile)

    command.append("-I'%s'" % projectConfig.locationOrigDir)
    for includePath in projectConfig.included:
        command.append("-I'%s'" % includePath)

    command.append("--save-temps='%s'" % projectConfig.locationTempDir)
    command.append("-c")
    command.append("-o")
    command.append("'%s.out'" % projectConfig.locationTempNoExtension)

    return command

def runInliner(projectConfig):
    """Conducts the sequence of system calls that will perform
    a source-to-source transformation of the C file currently being
    analyzed, inlining user-specified functions.

    Arguments:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.

    Returns:
        Zero if the inlining was successful; a non-zero value otherwise.
    """
    command = _generateInlinerCommand(projectConfig)
    return subprocess.call(command, shell=True)
