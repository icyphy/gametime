#!/usr/bin/env python

"""Exposes classes and functions to maintain a representation of,
and to interact with, the FLEXPRET simulator.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""

import os
import re
import shutil
import subprocess
from tempfile import NamedTemporaryFile

from defaults import config
from file_helper import create_dir, remove_files
from gametime_error import GameTimeError
from simulator import Simulator


class FlexpretSimulator(Simulator):
    """Maintains a representation of the PTARM simulator."""

    def __init__(self, projectConfig):
        super(FlexpretSimulator, self).__init__(projectConfig, "FLEXPRET")

    def _createCompiledFile(self, path):
        pass

    def _runSimulatorAndParseOutput(self, compile_file):
        """Runs the simulator on a test case and dumps the output to
        a temporary file in the temporary directory used for simulation.
        This method then parses this output to determine the cycle count
        of the simulation.
        Arguments:
            asmFileLocation:
                Location of the file that contains the assembler contents
                of the binary file produced by the compilation of a temporary
                file that contains the test case.
        Returns:
            Cycle count of a simulation of the test case.
        """
        os.system(f"../../../../ emulator / fp - emu + ispm = {compile_file}.mem")

        # # Write the output to a file for later perusal.
        # pretOutputFileLocationNoExt, _ = os.path.splitext(asmFileLocation)
        # pretOutputFileLocation = "%s.pret.out" % pretOutputFileLocationNoExt
        # with open(pretOutputFileLocation, "w") as pretOutputFile:
        #     pretOutputFile.write("".join(pretOutput))
        #
        # # Parse the output data for the start and end cycle counts.
        # # Find the start/end address and extract the start/end index.
        # addressString = (r"T0\|FE\|([0-9]+)> Fetched from PC: 0x{} "
        #                   "Binary: 0x[0-9a-f]+")
        # startString = addressString.format(startAddress)
        # match = re.search(startString, pretOutput)
        # startIndex = match.group(1)
        # endString = addressString.format(endAddress)
        # match = re.search(endString, pretOutput)
        # endIndex = match.group(1)
        #
        # # Use the start/end index to extract the start/end cycle count.
        # cycleString = r"T0\|WB\|{}> Thread virtual cycle count: ([0-9]+)"
        # startString = cycleString.format(startIndex)
        # match = re.search(startString, pretOutput)
        # startCycle = int(match.group(1))
        # endString = cycleString.format(endIndex)
        # match = re.search(endString, pretOutput)
        # endCycle = int(match.group(1))
        #
        # totalCycles = endCycle - startCycle
        # return totalCycles
        return 0

    def _removeTemps(self):
        """Removes the temporary files and directory that were created
        during the most recent simulation, if any.
        """
        remove_files([".*"], self._measurementDir)
        os.system("../../../../scripts/c/riscv-clean.sh")

    def measure(self, compiled_file_path):
        os.system("cd flexpret")
        # Create the temporary directory where the temporary files generated
        # during measurement will be stored.
        create_dir(self._measurementDir)

        try:
            compiledFileLocation = self._createCompiledFile(path)
            cycleCount = self._runSimulatorAndParseOutput(compiledFileLocation)
        except EnvironmentError as e:
            errMsg = ("Error in measuring the cycle count of a path "
                      "when simulated on the Flexpret simulator: %s" % e)
            raise GameTimeError(errMsg)

        if not self.projectConfig.debugConfig.KEEP_SIMULATOR_OUTPUT:
            self._removeTemps()
        return cycleCount