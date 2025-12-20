import re
import os


def format_for_klee(
    c_file, c_file_path, c_file_gt_dir, n, total_number_of_labels, func_name
):
    # Read the original C file
    with open(c_file_path, "r") as f:
        c_code = f.read()

    # Regular expression pattern to find header includes (excluding commented lines)
    header_pattern = r'(?:^[^\n\S]*#include\s+(<.*?>|".*?"))'

    # Find all header includes
    header_matches = re.findall(header_pattern, c_code, flags=re.MULTILINE)

    # Separate headers from the rest of the code
    c_code = re.sub(header_pattern, lambda match: "", c_code, flags=re.MULTILINE)
    c_code = c_code.lstrip("\n")

    # Generate KLEE headers
    klee_headers = (
        "#include </opt/homebrew/include/klee/klee.h>\n#include <stdbool.h>\n"
    )

    # Generate global boolean variables and initialize them to false/true
    global_booleans = "\n"
    for i in range(n):
        global_booleans += f"bool conditional_var_{i} = false;\n"

    for i in range(total_number_of_labels - n):
        global_booleans += f"bool conditional_var_{i + n} = true;\n"

    # Generate main function
    main_function = "int main() {\n"
    function_pattern = rf"^[^\n\S]*\w+\s+{func_name}\s*\(([^)]*)\)\s*\{{"
    match = re.search(function_pattern, c_code, flags=re.MULTILINE)
    if match:
        function_declaration = match.group()
        args_str = match.group(1)
        # Split arguments by comma, handle possible extra spaces
        arguments = [arg.strip() for arg in args_str.split(",") if arg.strip()]
        arg_names = []
        for arg in arguments:
            # Improved regex: captures type, name, and array dimensions (if any)
            m = re.match(r"([\w\s\*]+?)\s+(\w+)(\s*\[[^\]]*\])?", arg)
            if m:
                arg_type = m.group(1).strip()
                arg_name = m.group(2).strip()
                array_dim = m.group(3) or ""
                # Declare the variable with array size if present
                main_function += f"    {arg_type} {arg_name}{array_dim};\n"
                # Symbolic initialization
                if array_dim:
                    main_function += f'    klee_make_symbolic({arg_name}, sizeof({arg_name}), "{arg_name}");\n'
                else:
                    main_function += f'    klee_make_symbolic(&{arg_name}, sizeof({arg_name}), "{arg_name}");\n'
                # For function call, just use the variable name (no brackets or array_dim)
                arg_names.append(arg_name)
        # Call the original function with symbolic variables
        main_function += f"    {func_name}("
        main_function += ", ".join(arg_names) + ");\n"
        # Add KLEE assertions for global variables
        for i in range(total_number_of_labels):
            main_function += f"    klee_assert(conditional_var_{i});\n"
        main_function += "    return 0;\n}"
        # Write the formatted code to the output file
        klee_file = os.path.join(c_file_gt_dir, c_file + "_klee_format.c")
        with open(klee_file, "w") as f:
            f.write(klee_headers + "\n")
            for header in header_matches:
                f.write(f"#include {header}\n")  # Write header includes
            f.write(global_booleans + "\n" + c_code + "\n" + main_function)
        return klee_file
    else:
        print("No function found in the input file.")
        return None
