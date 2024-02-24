import re

def format_for_klee(original_file, n):
    # Read the original C file
    with open(original_file, 'r') as f:
        c_code = f.read()

    # Regular expression pattern to find function declarations
    function_pattern = r'\w+\s+\w+\s*\([^)]*\)\s*\{'

    # Find the first function declaration
    match = re.search(function_pattern, c_code)
    if match:
        function_declaration = match.group()

        # Extract function name
        function_name = function_declaration.split('(')[0].split()[-1]

        # Extract function arguments
        arguments = re.findall(r'\w+\s+\w+', function_declaration)

        # Generate KLEE headers
        klee_headers = "#include </opt/homebrew/Cellar/klee/3.0_2/include/klee/klee.h>\n#include <stdbool.h>\n"

        # Generate global boolean variables and initialize them to false
        global_booleans = "\n"
        for i in range(n):
            global_booleans += f"bool conditional_var_{i} = false;\n"

        # Generate main function
        main_function = "int main() {\n"
        for arg in arguments[1:]:  # Skip function name
            arg_type, arg_name = arg.split()
            main_function += f"    {arg_type} {arg_name};\n"  # Define variables
            main_function += f"    klee_make_symbolic(&{arg_name}, sizeof({arg_name}), \"{arg_name}\");\n"  # Make symbolic
        
        main_function += f"    {function_name}("
        main_function += ', '.join([arg.split()[-1] for arg in arguments[1:]]) + ");\n"  # Call original function with symbolic variables
        

        for i in range(n):
            main_function += f"    klee_assert(conditional_var_{i});\n"  # Assert global variables
        
        main_function += "    return 0;\n}"
        # Write the formatted code to the output file
        klee_file = original_file[:-2] + "_klee_format.c"
        with open(klee_file, 'w') as f:
            f.write(klee_headers + global_booleans + '\n' + c_code + '\n' + main_function)
        return klee_file
    else:
        print("No function found in the input file.")
    
