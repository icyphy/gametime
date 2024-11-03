import os
import subprocess
import sys
import re

def run_command(command, description):
    """
    Run a shell command and handle errors.
    """
    try:
        print(f"Running: {description}")
        subprocess.check_call(command, shell=True)
        print(f"{description} completed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"Error: {description} failed with exit code {e.returncode}.")
        sys.exit(1)

def compile_to_bitcode(c_file, output_bc):
    """
    Compile the C file to LLVM bitcode (.bc file) using clang.
    """
    command = f"clang -emit-llvm -Xclang -disable-O0-optnone -c {c_file} -o {output_bc}"
    run_command(command, f"Compiling {c_file} to LLVM bitcode")

def generate_llvm_ir(output_bc, output_ir):
    """
    Generate LLVM Intermediate Representation (.ll file) from LLVM bitcode.
    """
    command = f"llvm-dis {output_bc} -o {output_ir}"
    run_command(command, f"Generating LLVM IR from bitcode {output_bc}")

def unroll_llvm_ir(input_ir, output_ir):
    """
    Generate LLVM Intermediate Representation (.ll file) from LLVM bitcode.
    """
    command = f"opt -loop-unroll -S {input_ir} -o {output_ir}"
    run_command(command, f"Generating LLVM IR from {input_ir}")
    

def generate_llvm_dag(output_bc):
    """
    Generate LLVM DAG (.dot file) using llc and opt tools.
    """
    # Use llc to create DAG
    command = f"opt -dot-cfg -S -enable-new-pm=0 -disable-output {output_bc}"
    run_command(command, f"Generating LLVM DAG from bitcode {output_bc}")

def modify_loop_branches_to_next_block(input_file_path, output_file_path):
    """
    Modifies an LLVM IR file to replace branches with `!llvm.loop` annotations
    to point to the block that appears immediately after the block containing
    the `!llvm.loop` expression.

    Args:
        input_file_path (str): Path to the input LLVM IR file.
        output_file_path (str): Path to save the modified LLVM IR file.
    """
    with open(input_file_path, 'r') as file:
        llvm_ir_code = file.read()

    # Define regex patterns for identifying branch instructions with !llvm.loop and block labels
    block_pattern = re.compile(r'^(\d+):', re.MULTILINE)  # Matches lines with block labels (e.g., "3:")
    branch_with_loop_pattern = re.compile(r'br label %(\d+), !llvm.loop')

    # Find all blocks in the order they appear
    blocks = [int(match.group(1)) for match in block_pattern.finditer(llvm_ir_code)]
    
    # Split the code into lines for processing
    lines = llvm_ir_code.splitlines()
    new_lines = []
    
    # Iterate through each line, looking for `!llvm.loop` branches
    current_block = None
    for i, line in enumerate(lines):
        # Check if the line starts a new block
        block_match = block_pattern.match(line)
        if block_match:
            current_block = int(block_match.group(1))

        # If a `!llvm.loop` branch is found, modify it to point to the next block
        loop_branch_match = branch_with_loop_pattern.search(line)
        if loop_branch_match and current_block is not None:
            # Find the index of the current block in the blocks list
            current_block_index = blocks.index(current_block)
            # Ensure there is a next block after the current one
            if current_block_index + 1 < len(blocks):
                # Get the label of the next block
                next_block_num = blocks[current_block_index + 1]
                # Replace the branch target to point to this next block
                line = line.replace(f'br label %{loop_branch_match.group(1)}', f'br label %{next_block_num}')
        
        # Append the modified or unmodified line to the result
        new_lines.append(line)

    # Join the modified lines back together
    modified_llvm_ir_code = "\n".join(new_lines)

    # Write the modified LLVM IR code to the output file
    with open(output_file_path, 'w') as file:
        file.write(modified_llvm_ir_code)

    print(f"Modified LLVM IR code saved to {output_file_path}")

def assemble_bitcode(input_file, output_file):
    run_command(f"llvm-as {input_file} -o {output_file}", "Assemble LLVM IR after unrolling")

# Usage example
# modify_loop_branches_to_next_block("input.ll", "output.ll")


# Usage example
# modify_loop_branches_to_next_block("input.ll", "output.ll")


def main():
    if len(sys.argv) != 2:
        print("Usage: python convert_to_llvm.py <source_file.c>")
        sys.exit(1)

    c_file = sys.argv[1]

    if not os.path.isfile(c_file):
        print(f"Error: {c_file} does not exist.")
        sys.exit(1)

    base_filename = os.path.splitext(c_file)[0]
    output_bc = f"{base_filename}.bc"
    output_ir = f"{base_filename}.ll"
    unrolled_output_ir = f"{base_filename}_unrolled.ll"
    unrolled_mod_output_ir = f"{base_filename}_unrolled_mod.ll"
    output_dag = f"{base_filename}.dot"

    # 1. Compile C file to LLVM Bitcode
    compile_to_bitcode(c_file, output_bc)

    # 2. Generate LLVM IR from Bitcode
    generate_llvm_ir(output_bc, output_ir)
    
    unroll_llvm_ir(output_ir, unrolled_output_ir)
    
    modify_loop_branches_to_next_block(unrolled_output_ir, unrolled_mod_output_ir)

    # 3. Generate LLVM DAG from Bitcode
    generate_llvm_dag(unrolled_mod_output_ir)

    print(f"Files generated:\n- Bitcode: {output_bc}\n- LLVM IR: {output_ir}\n- LLVM IR: {unrolled_output_ir}\n- LLVM DAG: {output_dag}")

if __name__ == "__main__":
    main()

def unroll(bc_filepaths: list[str], output_file_folder: str, output_name: str):

    output_ir = f"{output_name}.ll"
    unrolled_output_ir = f"{output_name}_unrolled.ll"
    unrolled_mod_output_ir = f"{output_name}_unrolled_mod.ll"
    unrolled_mod_output_bc = os.path.join(output_file_folder, f"{output_name}_unrolled_mod.bc") 

    generate_llvm_ir(bc_filepaths, output_ir)
    
    unroll_llvm_ir(output_ir, unrolled_output_ir)
    
    modify_loop_branches_to_next_block(unrolled_output_ir, unrolled_mod_output_ir)

    generate_llvm_dag(unrolled_mod_output_ir)
    
    assemble_bitcode(unrolled_mod_output_ir, bc_filepaths)
    
    return bc_filepaths