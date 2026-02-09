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
    command = f"opt -passes=loop-unroll -S {input_ir} -o {output_ir}"
    run_command(command, f"Generating LLVM IR from {input_ir}")


def generate_llvm_dag(output_bc):
    """
    Generate LLVM DAG (.dot file) using opt.
    """
    command = f"opt -passes=dot-cfg -S -disable-output {output_bc}"
    run_command(command, f"Generating LLVM DAG from bitcode {output_bc}")


def modify_loop_branches_to_next_block(input_file_path, output_file_path):
    """
    Modifies an LLVM IR file to replace branches with `!llvm.loop` annotations
    to point to the block that appears immediately after the block containing
    the `!llvm.loop` expression. This breaks loop back edges so the IR becomes
    a DAG suitable for WCET path analysis.

    Handles both numbered blocks (e.g., "243:") and named blocks
    (e.g., "bsort_return.exit:", ".loopexit:").

    Example:
        Given this IR where block 243 branches back to the loop header %201:

            243:
              store i32 %247, ptr %4, align 4
              br label %201, !llvm.loop !10    <-- back edge

            bsort_return.exit:                 <-- next sequential block
              %248 = load i32, ptr %3, align 4

        The back edge is redirected to the next sequential block:

            243:
              store i32 %247, ptr %4, align 4
              br label %bsort_return.exit, !llvm.loop !10   <-- redirected

    Args:
        input_file_path (str): Path to the input LLVM IR file.
        output_file_path (str): Path to save the modified LLVM IR file.
    """
    with open(input_file_path, "r") as file:
        llvm_ir_code = file.read()

    # Match both numbered blocks (e.g., "243:") and named blocks (e.g., "bsort_return.exit:", ".loopexit:")
    block_pattern = re.compile(
        r"^(\d+|[a-zA-Z_.]\S*)\s*:", re.MULTILINE
    )
    branch_with_loop_pattern = re.compile(r"br label %(\S+), !llvm.loop")

    # Find all blocks in the order they appear (as strings)
    blocks = [match.group(1) for match in block_pattern.finditer(llvm_ir_code)]

    # Split the code into lines for processing
    lines = llvm_ir_code.splitlines()
    new_lines = []

    # Iterate through each line, looking for `!llvm.loop` branches
    current_block = None
    for i, line in enumerate(lines):
        # Check if the line starts a new block
        block_match = block_pattern.match(line)
        if block_match:
            current_block = block_match.group(1)

        # If a `!llvm.loop` branch is found, modify it to point to the next block
        loop_branch_match = branch_with_loop_pattern.search(line)
        if loop_branch_match and current_block is not None:
            # Find the index of the current block in the blocks list
            if current_block in blocks:
                current_block_index = blocks.index(current_block)
                # Ensure there is a next block after the current one
                if current_block_index + 1 < len(blocks):
                    next_block_label = blocks[current_block_index + 1]
                    old_target = loop_branch_match.group(1)
                    line = line.replace(
                        f"br label %{old_target}",
                        f"br label %{next_block_label}",
                    )

        # Append the modified or unmodified line to the result
        new_lines.append(line)

    # Join the modified lines back together
    modified_llvm_ir_code = "\n".join(new_lines)

    # Write the modified LLVM IR code to the output file
    with open(output_file_path, "w") as file:
        file.write(modified_llvm_ir_code)

    print(f"Modified LLVM IR code saved to {output_file_path}")


def assemble_bitcode(input_file, output_file):
    run_command(
        f"llvm-as {input_file} -o {output_file}", "Assemble LLVM IR after unrolling"
    )


def unroll(bc_filepath: str, output_file_folder: str, output_name: str):

    output_ir = f"{bc_filepath[:-3]}.ll"
    unrolled_output_ir = f"{bc_filepath[:-3]}_unrolled.ll"
    unrolled_mod_output_ir = f"{bc_filepath[:-3]}_unrolled_mod.ll"
    unrolled_mod_output_bc = f"{bc_filepath[:-3]}_unrolled_mod.bc"

    generate_llvm_ir(bc_filepath, output_ir)

    unroll_llvm_ir(output_ir, unrolled_output_ir)

    modify_loop_branches_to_next_block(unrolled_output_ir, unrolled_mod_output_ir)

    assemble_bitcode(unrolled_mod_output_ir, unrolled_mod_output_bc)

    return unrolled_mod_output_bc
