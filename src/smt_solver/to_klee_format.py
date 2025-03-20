import re
import os

def format_for_klee(c_file, c_file_path, c_file_gt_dir, n, total_number_of_labels, func_name):
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
    klee_headers = "#include <klee/klee.h>\n#include <stdbool.h>\n"

    # Generate global boolean variables and initialize them to false/true
    global_booleans = "\n"
    for i in range(n):
        global_booleans += f"bool conditional_var_{i} = false;\n"

    for i in range(total_number_of_labels - n):
        global_booleans += f"bool conditional_var_{i + n} = true;\n"

    # Generate main function
    main_function = "int main() {\n"
    function_pattern = rf'^[^\n\S]*\w+\s+{func_name}\s*\([^)]*\)\s*\{{'
    match = re.search(function_pattern, c_code, flags=re.MULTILINE)
    if match:
        function_declaration = match.group()

        # Extract function name
        function_name = function_declaration.split('(')[0].split()[-1]

        # Extract function arguments
        arguments = re.findall(r'(\w+\s+\**\w+(?:\[[^\]]*\])*)', function_declaration)

        for arg in arguments[1:]:  # Skip function name
            # Extract type, name, and array dimensions
            match = re.match(r'(\w+(\s+\**)?)\s+(\w+)(\[[^\]]*\])?', arg)
            if match:
                arg_type = match.group(1).strip()  # Type (e.g., "int" or "int *")
                arg_name = match.group(3).strip()  # Name (e.g., "binarysearch_data")
                array_dim = match.group(4) or ""   # Array dimensions (e.g., "[15]")

                # Declare the variable
                main_function += f"    {arg_type} {arg_name}{array_dim};\n"

                # Adjust for symbolic arrays
                if array_dim:
                    # If dimensions are provided, remove brackets and calculate the full size
                    array_size = re.findall(r'\d+', array_dim)
                    if array_size:
                        size = int(array_size[0])  # Get size from [15]
                        main_function += f"    klee_make_symbolic({arg_name}, sizeof({arg_name}), \"{arg_name}\");\n"
                    else:
                        # In case of dynamic arrays or incomplete dimensions
                        main_function += f"    klee_make_symbolic({arg_name}, sizeof({arg_name}), \"{arg_name}\");\n"
                else:
                    main_function += f"    klee_make_symbolic(&{arg_name}, sizeof({arg_name}), \"{arg_name}\");\n"

        # Call the original function with symbolic variables
        main_function += f"    {function_name}("
        main_function += ', '.join([(arg.split()[-1]).split("[")[0] for arg in arguments[1:]]) + ");\n"

        # Add KLEE assertions for global variables
        for i in range(total_number_of_labels):
            main_function += f"    klee_assert(conditional_var_{i});\n"

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
        return None
