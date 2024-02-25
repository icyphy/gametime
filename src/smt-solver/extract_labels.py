import re

def find_labels(bitcode_string):

    # Use regular expression to find the labels
    labels = re.findall(r'%(\d+):', bitcode_string)
    # Convert labels to integers and store them in a list
    i = 0
    while True:
        filename = f"labels_{i}.txt"
        try:
            with open(filename, 'x') as f:
                for label in labels:
                    f.write(f"{label}\n")
            break
        except FileExistsError:
            i += 1

    return filename

# from llvmlite import ir
# import llvmlite.binding as llvm
# import re

# def find_labels(bc_file):
#     # Initialize LLVM
#     llvm.initialize()
#     llvm.initialize_native_target()
#     llvm.initialize_native_asmprinter()

#     # Parse LLVM assembly code
#     context = llvm.get_global_context()
#     # Load the LLVM bitcode file
#     with open(bc_file, 'rb') as f:
#         module = llvm.parse_bitcode(f.read())
#     labels = []
#     # Iterate over the functions in the module
#     for func in module.functions:
#         # Iterate over the basic blocks in the function
#         for block in func.blocks:
#             lines = str(block).split('\n')
#             try:
#                 i = 1 if lines[0] == '' else 0
#                 if m := re.match(r'^(\d+):', lines[i]):
#                     labels.append(m.group(1))
#             except:
#                 return None
    
#     return labels

# # Example usage
# #bitcode_file = "a_klee_format.bc"  # Replace with the path to your LLVM bitcode file
# #labels_list = find_labels(bitcode_file)
# #print(labels_list)

