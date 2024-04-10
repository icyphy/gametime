import subprocess
from smt_solver.to_klee_format import format_for_klee
from smt_solver.extract_klee_input import find_and_run_test
import os
from defaults import logger
import clang_helper

def compile_and_run_cplusplus(modify_bit_code_cpp_file, modify_bit_code_exec_file, input_c_file, c_filename, labels_file, all_labels_file, func_name, output_dir, project_config):
    # Get llvm-config flags
    llvm_config_command = ['llvm-config', '--cxxflags', '--ldflags', '--libs', 'core', 'support', 'bitreader', 'bitwriter', 'irreader']
    llvm_config_output = subprocess.run(llvm_config_command, capture_output=True, text=True, check=True).stdout.strip().split()

    # Compile C++ file
    compile_command = ['clang++', '-o', modify_bit_code_exec_file, modify_bit_code_cpp_file] + llvm_config_output
    subprocess.run(compile_command, check=True)

    #TODO: add extra flag and includes through project configuration
    compiled_file = clang_helper.compile_to_llvm_for_analysis(input_c_file, output_dir, c_filename, project_config.included, project_config.compile_flags)
    inlined_file = clang_helper.inline_functions(compiled_file, output_dir, f"{c_filename}-inlined")
    input_bc_file = clang_helper.unroll_loops(inlined_file, output_dir,
                                                       f"{c_filename}-unrolled", project_config)
    

    # Run the compiled program
    # TODO: change modify bc to take in bc file, not c file
    run_command = ['./' + modify_bit_code_exec_file, input_bc_file, labels_file, all_labels_file, func_name]
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

def run_smt(project_config, labels_file, output_dir, total_number_of_labels):
    c_file = project_config.name_orig_no_extension
    c_file_path = project_config.location_orig_file
    # extract labels
    labels = extract_labels_from_file(labels_file)
    number_of_labels = len(labels)

    # format c file to klee 
    klee_file_path = format_for_klee(c_file, c_file_path, output_dir, project_config.func,  number_of_labels, total_number_of_labels)

    # insert assignments of global variables
    # TODO: Find a way to not hard code path
    modify_bit_code_cpp_file = '../../src/smt_solver/modify_bitcode.cpp'
    modify_bit_code_exec_file = '../../src/smt_solver/modify_bitcode'
    compile_and_run_cplusplus(modify_bit_code_cpp_file, modify_bit_code_exec_file, klee_file_path, c_file + "_klee_format", labels_file, os.path.join(project_config.location_temp_dir, "labels_0.txt"), project_config.func, output_dir, project_config)
    modified_klee_file_bc = klee_file_path[:-2] + "-unrolled" + "_mod.bc"

    # run klee
    run_klee(modified_klee_file_bc)

    # extract klee input
    return find_and_run_test(output_dir, output_dir)


