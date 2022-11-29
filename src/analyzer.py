#!/usr/bin/env python
import os
import shutil
from typing import List, Set, Tuple

import clang_helper
from defaults import config, logger
from file_helper import remove_all_except
from gametime_error import GameTimeError
from nx_helper import Dag
from project_configuration import ProjectConfiguration

"""Defines a class that maintains information about the code being analyzed,
such as the name of the file that contains the code being analyzed and
the basis paths in the code.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""

class Analyzer(object):
    """Maintains information about the code being analyzed, such as
    the name of the file that contains the code being analyzed
    and the basis paths of the code.

    Attributes:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
    """

    def __init__(self, project_config: ProjectConfiguration):
        ### CONFIGURATIONS ###
        #: :class:`~gametime.projectConfiguration.ProjectConfiguration` object
        #: that represents the configuration of a GameTime project.
        self.projectConfig: ProjectConfiguration = project_config

        ### GRAPH INFORMATION ###
        #: Data structure for the DAG of the code being analyzed.
        self.dag: Dag = Dag()

        ### PATHS INFORMATION ###
        #: Dimension of the vector representing each path.
        self.pathDimension: int = 0

        #: Basis matrix.
        self.basisMatrix = None

        #: Set whose elements are lists of edges that must not be taken
        #: together along any path through the DAG. For example, the element
        #: [e1, e2] means "if you take e1, you cannot take e2" and
        #: "if you take e2, you cannot take e1".
        self.pathExclusiveConstraints: List[List[Tuple[str, str]]] = []

        #: List whose elements are lists of edges that must be taken together,
        #: if at least one is taken along a path through the DAG. For example,
        #: the element [e1, e2] means "if you take e1, then you take e2".
        self.pathBundledConstraints: List[List[Tuple[str, str]]] = []

        # Number of `bad' rows in the basis matrix.
        self.numBadRows: int = 0

        # List of the Path objects associated with all basis paths
        # generated so far.
        self.basisPaths = []

        # List of lists, each of which is a list of IDs of the nodes in
        # the DAG along each basis path. Each ID is a string. The lists are
        # arranged in the same order as the Path objects associated with
        # the basis paths are arranged in the `basisPaths' list.
        # This list is maintained for efficiency purposes.
        self.basisPathsNodes = []

        # Specify default parameters for the values used with
        # --ob_extraction flag. The values are outputted only
        # when the flag is used.
        # Value of mu_max computed for the observed measurements
        self.inferredMuMax: int = 0
        # The in predictions is error is 2 * inferredMuMax * errorScaleFactor
        self.errorScaleFactor: int = 0

        # Finally, preprocess the file before analysis.
        self._preprocess()

    def _preprocess(self):
        """Preprocesses the file before analysis. The preprocessing steps are:
        1. Create a temporary directory that will contain the files
        generated during analysis.
        2. Copy the source file being analyzed into this temporary directory.
        3. Run CIL on the copied source file to perform, for example, loop
        unrolling and function inlining.
        """
        # Check if the file to be analyzed exists.
        orig_file = self.projectConfig.locationOrigFile
        project_temp_dir = self.projectConfig.locationTempDir
        if not os.path.exists(orig_file):
            shutil.rmtree(project_temp_dir)
            err_msg = "File to analyze not found: %s" % orig_file
            raise GameTimeError(err_msg)

        # Remove any temporary directory created during a previous run
        # of the same GameTime project, and create a fresh new
        # temporary directory.
        if os.path.exists(project_temp_dir):
            if self.projectConfig.UNROLL_LOOPS:
                # If a previous run of the same GameTime project produced
                # a loop configuration file, and the current run involves
                # unrolling the loops that are configured in the file,
                # do not remove the file.
                remove_all_except([config.TEMP_LOOP_CONFIG], project_temp_dir)
            else:
                remove_all_except([], project_temp_dir)
        else:
            os.mkdir(project_temp_dir)

        # Make a temporary copy of the original file to preprocess.
        preprocessed_file = self.projectConfig.locationTempFile
        shutil.copyfile(orig_file, preprocessed_file)

        # TODO: Make merger work
        # # Preprocessing pass: merge other source files.
        # if len(self.projectConfig.merged) > 0:
        #     self._run_merger()

        # Preprocessing pass: unroll loops.
        if self.projectConfig.UNROLL_LOOPS:
            self._run_loop_unroller()

        # Preprocessing pass: inline functions.
        if len(self.projectConfig.inlined) > 0:
            self._run_inliner()

        # TODO: Not sure what this entials and what we need to do here.
        # Preprocessing pass: run the file through CIL once more,
        # to reduce the C file to the subset of constructs used by CIL
        # for ease of analysis.
        # self._runCil()

        # We are done with the preprocessing.
        logger.info("Preprocessing complete.")
        logger.info("")

    ### PREPROCESSING HELPER FUNCTIONS ###
    # TODO: Make this work (see self._preprocess)
    # def _run_merger(self):
    #     """As part of preprocessing, runs CIL on the source file under
    #     analysis to merge other source files. A copy of the file that
    #     results from the CIL preprocessing is made and renamed for use by
    #     other preprocessing phases, and the file itself is renamed and
    #     stored for later perusal.
    #     """
    #     preprocessed_file: str = self.projectConfig.locationTempFile
    #     # Infer the name of the file that results from the CIL preprocessing.
    #     cil_file = "%s.cil.c" % self.projectConfig.locationTempNoExtension
    #
    #     logger.info("Preprocessing the file: merging other source files...")
    #
    #     if merger.runMerger(self.projectConfig):
    #         errMsg = "Error running the merger."
    #         raise GameTimeError(errMsg)
    #     else:
    #         shutil.copyfile(cil_file, preprocessed_file)
    #         shutil.move(cil_file,
    #                     "%s%s.c" % (self.projectConfig.locationTempNoExtension,
    #                                 config.TEMP_SUFFIX_MERGED))
    #         if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
    #             cilHelper.removeTempCilFiles(self.projectConfig)
    #
    #         logger.info("")
    #         logger.info("Other source files merged.")

    def _run_loop_unroller(self):
        """As part of preprocessing, runs CIL on the source file under
        analysis to unroll loops. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.
        """
        preprocessed_file: str = self.projectConfig.locationTempFile
        # Infer the name of the file that results from the CIL preprocessing.
        cilFile = "%s.cil.c" % self.projectConfig.locationTempNoExtension

        logger.info("Preprocessing the file: unrolling loops in the code...")

        if clang_helper.unroll_loops(self.projectConfig):
            err_msg = "Error running the loop unroller."
            raise GameTimeError(err_msg)
        else:
            shutil.copyfile(cilFile, preprocessed_file)
            shutil.move(cilFile,
                        "%s%s.c" % (self.projectConfig.locationTempNoExtension,
                                    config.TEMP_SUFFIX_UNROLLED))
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                cilHelper.remove_temp_cil_files(self.projectConfig)

            logger.info("")
            logger.info("Loops in the code have been unrolled.")

    def _run_inliner(self):
        """As part of preprocessing, runs CIL on the source file under
        analysis to inline functions. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.
        """
        preprocessedFile = self.projectConfig.locationTempFile
        # Infer the name of the file that results from the CIL preprocessing.
        cilFile = "%s.cil.c" % self.projectConfig.locationTempNoExtension

        logger.info("Preprocessing the file: inlining...")

        if inliner.runInliner(self.projectConfig):
            errMsg = "Error running the inliner."
            raise GameTimeError(errMsg)
        else:
            shutil.copyfile(cilFile, preprocessedFile)
            shutil.move(cilFile,
                        "%s%s.c" % (self.projectConfig.locationTempNoExtension,
                                    config.TEMP_SUFFIX_INLINED))
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                cilHelper.remove_temp_cil_files(self.projectConfig)

            logger.info("")
            logger.info("Inlining complete.")

    # TODO: Figure out what this is supposed to do (see self._preprocess)
    # def _runCil(self):
    #     """As part of preprocessing, runs CIL on the source file under
    #     analysis to to reduce the C file to the subset of constructs
    #     used by CIL for ease of analysis. The file that results from
    #     the CIL preprocessing is renamed for use by the rest of
    #     the GameTime toolflow. Another copy, with preprocessor directives
    #     that maintain the line numbers from the original source file
    #     (and other merged source files), is also made.
    #     """
    #     preprocessedFile = self.projectConfig.locationTempFile
    #     # Infer the name of the file that results from the CIL preprocessing.
    #     cilFile = "%s.cil.c" % self.projectConfig.locationTempNoExtension
    #
    #     logger.info("Preprocessing the file: running CIL to produce code "
    #                 "simplified for analysis...")
    #
    #     if cilHelper.runCil(self.projectConfig, keepLineNumbers=True):
    #         errMsg = "Error running CIL in the final preprocessing phase."
    #         raise GameTimeError(errMsg)
    #     else:
    #         shutil.move(cilFile,
    #                     "%s%s.c" % (self.projectConfig.locationTempNoExtension,
    #                                 config.TEMP_SUFFIX_LINE_NUMS))
    #         if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
    #             cilHelper.removeTempCilFiles(self.projectConfig)
    #
    #     if cilHelper.runCil(self.projectConfig):
    #         errMsg = "Error running CIL in the final preprocessing phase."
    #         raise GameTimeError(errMsg)
    #     else:
    #         shutil.move(cilFile, preprocessedFile)
    #         if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
    #             cilHelper.removeTempCilFiles(self.projectConfig)
    #
    #     logger.info("")
    #     logger.info("Final preprocessing phase complete.")
