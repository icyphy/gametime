import re
import sys

def process_llvm_ir(input_file, output_file):
    with open(input_file, 'r') as file:
        ir_content = file.read()

    # Replace all occurrences of 'noinline' with 'alwaysinline'
    ir_content = re.sub(r'\bnoinline\b', 'alwaysinline', ir_content)

    # Remove all occurrences of 'optnone'
    ir_content = re.sub(r'\boptnone\b', '', ir_content)

    # Write the modified content to the output file
    with open(output_file, 'w') as file:
        file.write(ir_content)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python modify_llvm_ir.py <input_file.ll> <output_file.ll>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        process_llvm_ir(input_file, output_file)
        print(f"Processed LLVM IR file saved to {output_file}")

# python3 modify_llvm_ir.py combined.ll combined.ll
