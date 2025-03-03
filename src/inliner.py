import os
import re
import subprocess
import sys

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True, errors='replace')
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    return result.stdout


def link_bitcode(bitcode_files, output_file):
    run_command(f"llvm-link {' '.join(bitcode_files)} -o {output_file}")

def disassemble_bitcode(input_file, output_file):
    run_command(f"llvm-dis {input_file} -o {output_file}")

def assemble_bitcode(input_file, output_file):
    run_command(f"llvm-as {input_file} -o {output_file}")

def inline_bitcode(input_file, output_file):
    run_command(f"opt -passes=\"always-inline,inline\" -inline-threshold=10000000 {input_file} -o {output_file}")

def modify_llvm_ir(input_file, output_file, skip_function):
    run_command(f"opt -load-pass-plugin=custom_passes/custom_inline_pass.so -passes=custom-inline -analysed_func={skip_function} {input_file} -o {output_file}")



def inline_functions(bc_filepaths: list[str], output_file_folder: str, output_name: str, analyzed_function: str) -> str:
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")
    file_to_analyze = bc_filepaths[0]
    combined_bc = f"{file_to_analyze[:-3]}_linked.bc"
    combined_ll = f"{file_to_analyze[:-3]}_linked.ll"
    combined_mod_ll = f"{file_to_analyze[:-3]}_linked_mod.ll"
    combined_mod_bc = f"{file_to_analyze[:-3]}_linked_mod.bc"
    combined_inlined_mod_bc = f"{file_to_analyze[:-3]}_linked_inlined_mod.bc"
    combined_inlined_mod_ll = f"{file_to_analyze[:-3]}_linked_inlined_mod.ll"


    
    if len(bc_filepaths) > 1:
        # Step 1: Link all bitcode files into a single combined bitcode file
        link_bitcode(bc_filepaths, combined_bc)
    else:
        combined_bc = bc_filepaths[0]

    # Step 2: Disassemble the combined bitcode file to LLVM IR
    disassemble_bitcode(combined_bc, combined_ll)

    # Step 3: Modify the LLVM IR file
    modify_llvm_ir(combined_ll, combined_mod_ll, analyzed_function)

    # Step 4: Assemble the modified LLVM IR back to bitcode
    assemble_bitcode(combined_mod_ll, combined_mod_bc)

    # Step 5: Inline the functions in the modified bitcode
    inline_bitcode(combined_mod_bc, combined_inlined_mod_bc)
    
    # Step 6: Disassemble the combined bitcode file to LLVM IR for debugging
    disassemble_bitcode(combined_inlined_mod_bc, combined_inlined_mod_ll)
        
    return combined_inlined_mod_bc
