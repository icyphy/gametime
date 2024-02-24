import subprocess
import count_branches
import to_klee_format

def compile_c_to_bitcode(c_file):
    # Command to compile C file to LLVM bitcode
    bc_file = c_file[:-2] + ".bc"
    compile_command = ['clang', '-emit-llvm', '-c', c_file, '-o', bc_file]
    # Run compilation command
    subprocess.run(compile_command, check=True)
    return bc_file

def compile_and_run_cplusplus(cplusplus_file, output_file, input_c_file):
    # Get llvm-config flags
    llvm_config_command = ['llvm-config', '--cxxflags', '--ldflags', '--libs', 'core', 'support', 'bitreader', 'bitwriter', 'irreader']
    llvm_config_output = subprocess.run(llvm_config_command, capture_output=True, text=True, check=True).stdout.strip().split()

    # Compile C++ file
    compile_command = ['clang++', '-o', output_file, cplusplus_file] + llvm_config_output
    subprocess.run(compile_command, check=True)

    # Run the compiled program
    run_command = ['./' + output_file, input_c_file]
    subprocess.run(run_command, check=True)

def run_klee(klee_file):
    run_klee_command = ['klee', klee_file]
    subprocess.run(run_klee_command, check=True)

def main():
    # file to generate input for
    c_file = 'get_sign.c'
    # compile to bitcode
    bc_file = compile_c_to_bitcode(c_file)
    # count number of branches
    num_of_branches = count_branches.count_conditional_branches(bc_file)
    # format c file to klee 
    klee_file = to_klee_format.format_for_klee(c_file, num_of_branches)
    # insert assignments of global variables
    cplusplus_file = 'modify_bitcode_2.cpp'
    output_file = 'modify_bitcode'
    compile_and_run_cplusplus(cplusplus_file, output_file, klee_file)
    modified_klee_file_bc = klee_file[:-2] + "_mod.bc"
    # run klee
    run_klee(modified_klee_file_bc)


if __name__ == "__main__":
    main()
