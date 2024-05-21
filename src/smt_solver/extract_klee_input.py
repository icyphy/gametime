import os
import subprocess

import re

# def write_klee_input_to_file(filename):
#     # Define a regular expression pattern to extract int values
#     pattern = re.compile(r'uint\s+:\s+(-?\d+)')

#     # Open the input file
#     with open(filename, 'r') as infile:
#         data = infile.read()

#     # Find all int values using regex
#     int_values = pattern.findall(data)
#     print(int_values)
#     # Write int values to a new text file
#     values_filename = filename[:-4] + "_values.txt"
#     with open(values_filename, 'w') as outfile:
#         for value in int_values:
#             outfile.write(value + '\n')

#     print(f"Values extracted and written to {values_filename}")

def write_klee_input_to_file(filename):
    """As part of preprocessing, runs CIL on the source file under
        analysis to unroll loops. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.

        Parameters
        ----------
        filename:
            A file containing all of the basic block labels of the path to be analyzed,
            which is generated before running the SMT solver
        Returns
        -------
        List[String]
            A List of basic block labels
        """
    # Define a regular expression pattern to extract hex values
    pattern = re.compile(r'object \d+: hex : (0x[0-9a-fA-F]+)')

    # Open the input file
    with open(filename, 'r') as infile:
        data = infile.read()

    # Find all hex values using regex
    hex_values = pattern.findall(data)
    print(hex_values)
    # Write hex values to a new text file
    values_filename = filename[:-4] + "_values.txt"
    with open(values_filename, 'w') as outfile:
        for value in hex_values:
            outfile.write(value + '\n')

    print(f"Hex values extracted and written to {values_filename}")


def find_test_file(klee_last_dir):
    """As part of preprocessing, runs CIL on the source file under
        analysis to unroll loops. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.

        Parameters
        ----------
        filename:
            A file containing all of the basic block labels of the path to be analyzed,
            which is generated before running the SMT solver
        Returns
        -------
        List[String]
            A List of basic block labels
        """
    # Iterate over files in the klee-last directory
    # get the current working directory
    #current_working_directory = os.getcwd()
    # print output to the console
    #print("Hallo", current_working_directory)
    for root, dirs, files in os.walk(klee_last_dir):
        for file in files:
            # Check if the file is a KLEE test case input file
            if file.endswith('.ktest'):
                ktest_file = os.path.join(root, file)
                assert_err_file = os.path.splitext(ktest_file)[0] + '.assert.err'
                # Check if the assert.err file exists
                if not os.path.exists(assert_err_file):
                    return ktest_file
    return None

def run_ktest_tool(ktest_file, output_file):
    # Run ktest-tool on the ktest file and save the output to the output file
    with open(output_file, 'w') as f:
        subprocess.run(['klee.ktest-tool', ktest_file], stdout=f, text=True)

#def cleanup_klee():


def find_and_run_test(c_file_gt_dir, output_dir):
    #klee_last_dir = 'klee-last'  # Path to the klee-last directory
    klee_last_dir = os.path.join(c_file_gt_dir, "klee-last")
    ktest_file = find_test_file(klee_last_dir)
    if ktest_file:
        i = 0
        while True:
            output_file = os.path.join(output_dir,f"klee_input_{i}.txt") 
            if not os.path.exists(output_file):
                break
            i += 1
        run_ktest_tool(ktest_file, output_file)
        print(f"Input saved to {output_file}")
        write_klee_input_to_file(output_file)
        return True      
    else:
        print("No ktest file without corresponding assert.err file found.")
        return False