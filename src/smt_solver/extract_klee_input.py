import os
import subprocess

import re

def write_klee_input_to_file(filename):
    """
    Extract hexadecimal values from a KLEE test input file and write them to a new file.

    Parameters:
        filename : str
            Path to the KLEE test input file.
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
    """
    Find the first KLEE test case input file in the specified directory that does not have a corresponding .assert.err file.

    Parameters:
        klee_last_dir : str
            Path to the directory containing KLEE output files.

    Returns:
        str or None
            Path to the found KLEE test case input file, or None if no such file is found.
    """
    # Iterate over files in the klee-last directory
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
    """
    Run the ktest-tool on a KLEE test case input file and save the output to a specified file.

    Parameters:
        ktest_file : str
            Path to the KLEE test case input file.
        output_file : str
            Path to the file where the output will be saved.
    """
    # Run ktest-tool on the ktest file and save the output to the output file
    with open(output_file, 'w') as f:
        subprocess.run(['klee.ktest-tool', ktest_file], stdout=f, text=True)



def find_and_run_test(c_file_gt_dir, output_dir):
    """
    Find a KLEE test case input file, run ktest-tool on it, and save the input to a new file.

    Parameters:
        c_file_gt_dir : str
            Path to the directory containing the KLEE output subdirectory 'klee-last'.
        output_dir : str
            Directory where the output file will be saved.

    Returns:
        bool:
            True if a KLEE test case input file is found and processed, False otherwise.
    """
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