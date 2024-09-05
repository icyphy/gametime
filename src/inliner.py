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

def compile_to_bitcode(files):
    bitcode_files = []
    for file in files:
        bc_file = file.replace('.c', '.bc')
        run_command(f"clang -emit-llvm -O0 -c {file} -o {bc_file}")
        bitcode_files.append(bc_file)
    return bitcode_files

def link_bitcode(bitcode_files, output_file):
    print("BITCODE_FILES: ",bitcode_files)
    run_command(f"llvm-link {' '.join(bitcode_files)} -o {output_file}")

def disassemble_bitcode(input_file, output_file):
    run_command(f"llvm-dis {input_file} -o {output_file}")

def modify_llvm_ir(input_file, output_file):
    with open(input_file, 'r') as file:
        ir_content = file.read()

    # Replace all occurrences of 'noinline' with 'alwaysinline'
    ir_content = re.sub(r'\bnoinline\b', 'alwaysinline', ir_content)

    # Remove all occurrences of 'optnone'
    ir_content = re.sub(r'\boptnone \b', '', ir_content)

    # Write the modified content to the output file
    with open(output_file, 'w') as file:
        file.write(ir_content)

def assemble_bitcode(input_file, output_file):
    run_command(f"llvm-as {input_file} -o {output_file}")

def inline_bitcode(input_file, output_file):
    run_command(f"opt -always-inline -inline -inline-threshold=10000000 {input_file} -o {output_file}")

def generate_cfg(input_file):
    run_command(f"opt -dot-cfg {input_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_files.py <file1.c> <file2.c> ...")
        sys.exit(1)

    c_files = sys.argv[1:]
    combined_bc = "combined.bc"
    combined_ll = "combined.ll"
    combined_mod_ll = "combined_mod.ll"
    combined_mod_bc = "combined_mod.bc"
    inlined_bc = "inlined.bc"

    # Step 1: Compile all C files to bitcode
    bitcode_files = compile_to_bitcode(c_files)

    # Step 2: Link all bitcode files into a single combined bitcode file
    link_bitcode(bitcode_files, combined_bc)

    # Step 3: Disassemble the combined bitcode file to LLVM IR
    disassemble_bitcode(combined_bc, combined_ll)

    # Step 4: Modify the LLVM IR file
    modify_llvm_ir(combined_ll, combined_mod_ll)

    # Step 5: Assemble the modified LLVM IR back to bitcode
    assemble_bitcode(combined_mod_ll, combined_mod_bc)

    # Step 6: Inline the functions in the modified bitcode
    inline_bitcode(combined_mod_bc, inlined_bc)

    # Step 7: Generate the CFG for the inlined bitcode
    generate_cfg(inlined_bc)

    print("Processing complete. Output files:")
    print(f"  Combined bitcode: {combined_bc}")
    print(f"  Combined LLVM IR: {combined_ll}")
    print(f"  Modified LLVM IR: {combined_mod_ll}")
    print(f"  Modified bitcode: {combined_mod_bc}")
    print(f"  Inlined bitcode: {inlined_bc}")
    print("CFG files generated in the current directory.")

def inline_functions(bc_filepaths: str, output_file_folder: str, output_name: str) -> str:
    output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")
    
    combined_bc = "combined.bc"
    combined_ll = "combined.ll"
    combined_mod_ll = "combined_mod.ll"
    combined_mod_bc = "combined_mod.bc"
    
    # Step 2: Link all bitcode files into a single combined bitcode file
    link_bitcode(bc_filepaths, combined_bc)

    # Step 3: Disassemble the combined bitcode file to LLVM IR
    disassemble_bitcode(combined_bc, combined_ll)

    # Step 4: Modify the LLVM IR file
    modify_llvm_ir(combined_ll, combined_mod_ll)

    # Step 5: Assemble the modified LLVM IR back to bitcode
    assemble_bitcode(combined_mod_ll, combined_mod_bc)

    # Step 6: Inline the functions in the modified bitcode
    inline_bitcode(combined_mod_bc, output_file)
    
    return output_file

    
# python3 inline.py ext_func.c helper.c

# inlined_file = clang_helper.inline_functions(input_file, self.project_config.location_temp_dir,
#                                                     f"{self.project_config.name_orig_no_extension}gt-inlined")

# output_file: str = os.path.join(output_file_folder, f"{output_name}.bc")

#     commands: List[str] = ["opt",
#                 "-always-inline",
#                 "-inline", "-inline-threshold=10000000",
#                 "-S", bc_filepath,
#                 "-o", output_file]

#     logger.info(subprocess.run(commands, check=True))
#     return output_file