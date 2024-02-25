import os
import subprocess

def find_test_file(klee_last_dir):
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
    # Run ktest-tool on the ktest file and save the output to the output file
    with open(output_file, 'w') as f:
        subprocess.run(['ktest-tool', ktest_file], stdout=f, text=True)

def find_and_run_test():
    klee_last_dir = 'klee-last'  # Path to the klee-last directory
    ktest_file = find_test_file(klee_last_dir)
    if ktest_file:
        output_file = 'klee_input.txt'  # Output file to save the ktest-tool output
        run_ktest_tool(ktest_file, output_file)
        print(f"Output saved to {output_file}")
    else:
        print("No ktest file without corresponding assert.err file found.")
