import subprocess
from smt_solver.to_klee_format import format_for_klee
from smt_solver.extract_klee_input import find_and_run_test
import os
from defaults import logger
import clang_helper

def compile_c_to_bitcode(c_file):
    # Command to compile C file to LLVM bitcode
    bc_file = c_file[:-2] + ".bc"
    compile_command = ['clang', '-emit-llvm', '-c', c_file, '-o', bc_file]
    # Run compilation command
    subprocess.run(compile_command, check=True)
    return bc_file

def compile_and_run_cplusplus(cplusplus_file, output_file, input_c_file, labels_file):
    # Get llvm-config flags
    llvm_config_command = ['llvm-config', '--cxxflags', '--ldflags', '--libs', 'core', 'support', 'bitreader', 'bitwriter', 'irreader']
    llvm_config_output = subprocess.run(llvm_config_command, capture_output=True, text=True, check=True).stdout.strip().split()

    # Compile C++ file
    compile_command = ['clang++', '-o', output_file, cplusplus_file] + llvm_config_output
    subprocess.run(compile_command, check=True)

    # Run the compiled program
    run_command = ['./' + output_file, input_c_file, labels_file]
    subprocess.run(run_command, check=True)

def run_klee(klee_file):
    run_klee_command = ['klee', klee_file]
    subprocess.run(run_klee_command, check=True)

def extract_labels_from_file(filename):
    labels = []
    with open(filename, 'r') as file:
        for line in file:
            try:
                label = float(line.strip())
                labels.append(label)
            except ValueError:
                print(f"Ignoring non-numeric value: {line.strip()}")
    return labels
def run_smt(labels_file):
    # get the current working directory
    current_working_directory = os.getcwd()
    # print output to the console
    print(current_working_directory)
    # file to generate input for
    c_file = './programs/add/add.c'
    # compile to bitcode
    bc_file = compile_c_to_bitcode(c_file)
    # count number of branches
    labels = extract_labels_from_file(labels_file)
    print(labels)
    num_of_branches = len(labels)
    # format c file to klee 
    klee_file = format_for_klee(c_file, num_of_branches)
    # insert assignments of global variables
    cplusplus_file = '../../src/smt_solver/modify_bitcode_2.cpp'
    output_file = '../../src/smt_solver/modify_bitcode'
    compile_and_run_cplusplus(cplusplus_file, output_file, klee_file, labels_file)
    modified_klee_file_bc = klee_file[:-2] + "_mod.bc"
    # run klee
    run_klee(modified_klee_file_bc)
    # extract klee input
    find_and_run_test()


