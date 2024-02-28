import llvmlite.binding as llvm
import os

def count_conditional_branches(bc_file):

    # Initialize LLVM
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    # Parse LLVM assembly code
    context = llvm.get_global_context()
    # Load the LLVM bitcode file
    with open(bc_file, 'rb') as f:
        module = llvm.parse_bitcode(f.read())

    conditional_branch_count = 0
    for func in module.functions:
        for block in func.blocks:
            for instr in block.instructions:
                if instr.opcode == 'br':
                    num_operands = sum(1 for _ in instr.operands)
                    if num_operands == 3:
                        conditional_branch_count += 1
    return conditional_branch_count

