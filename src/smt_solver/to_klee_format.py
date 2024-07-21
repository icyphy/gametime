import re
import os

def format_for_klee(c_file, c_file_path, c_file_gt_dir, n, total_number_of_labels):
    # Read the original C file
    with open(c_file_path, 'r') as f:
        c_code = f.read()

    # Regular expression pattern to find header includes (excluding commented lines)
    header_pattern = r'(?:^[^\n\S]*#include\s+(<.*?>|".*?"))'

    # Find all header includes
    header_matches = re.findall(header_pattern, c_code, flags=re.MULTILINE)

    # Separate headers from the rest of the code
    c_code = re.sub(header_pattern, lambda match: '', c_code, flags=re.MULTILINE)
    c_code = c_code.lstrip('\n')
    # Generate KLEE headers
    klee_headers = "#include </opt/homebrew/opt/klee/include/klee/klee.h>\n#include <stdbool.h>\n"

    # Generate global boolean variables and initialize them to false
    global_booleans = "\n"
    for i in range(n):
        global_booleans += f"bool conditional_var_{i} = false;\n"

    for i in range(total_number_of_labels - n):
        global_booleans += f"bool conditional_var_{i + n} = true;\n"

    # Generate main function
    main_function = "int main() {\n"
    function_pattern = r'(?:^[^\n\S]*\w+\s+\w+\s*\([^)]*\)\s*\{)'
    match = re.search(function_pattern, c_code, flags=re.MULTILINE)
    if match:
        function_declaration = match.group()

        # Extract function name
        function_name = function_declaration.split('(')[0].split()[-1]

        # Extract function arguments
        arguments = re.findall(r'\w+\s+\**\w+(?:\[\d*\])?\s*(?:\[\])?', function_declaration)

        for arg in arguments[1:]:  # Skip function name
            arg_type, *arg_name = arg.split()
            arg_name = arg_name[0] if arg_name else ""
            main_function += f"    {arg_type} {arg_name};\n"  # Define variables
            arg_name = arg_name.split("[")[0]
            main_function += f"    klee_make_symbolic(&{arg_name}, sizeof({arg_name}), \"{arg_name}\");\n"  # Make symbolic

        main_function += f"    {function_name}("
        main_function += ', '.join([(arg.split()[-1]).split("[")[0] for arg in arguments[1:]]) + ");\n"  # Call original function with symbolic variables

        for i in range(total_number_of_labels):
            main_function += f"    klee_assert(conditional_var_{i});\n"  # Assert global variables

        main_function += "    return 0;\n}"

        # Write the formatted code to the output file
        klee_file = os.path.join(c_file_gt_dir, c_file + "_klee_format.c") 
        with open(klee_file, 'w') as f:
            f.write(klee_headers + '\n')
            for header in header_matches:
                f.write(f"#include {header}\n")  # Write header includes
            f.write(global_booleans + '\n' + c_code + '\n' + main_function)
        return klee_file
    else:
        print("No function found in the input file.")