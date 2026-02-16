from pycparser import parse_file, c_generator
from pycparser.c_ast import (
    FuncDef,
    Decl,
    FuncCall,
    ID,
    Compound,
    TypeDecl,
    IdentifierType,
    FuncDecl,
    ParamList,
    Return,
    Constant,
    Assignment,
    ExprList,
    BinaryOp,
    NamedInitializer,
    InitList,
    Struct,
    ArrayDecl,
    Cast,
    Typename,
    Typedef,
)
import os
import sys
import pycparser_fake_libc

pycparser_utils_path = pycparser_fake_libc.directory

# Map C type names to their sizes in bytes (for little-endian byte reordering)
TYPE_SIZES = {
    "int": 4, "unsigned int": 4, "int32_t": 4, "uint32_t": 4,
    "short": 2, "unsigned short": 2, "int16_t": 2, "uint16_t": 2,
    "char": 1, "unsigned char": 1, "int8_t": 1, "uint8_t": 1,
    "long": 8, "unsigned long": 8, "long long": 8, "unsigned long long": 8,
    "int64_t": 8, "uint64_t": 8,
}


def _mem_bytes_to_literal_hex(hex_str):
    """Convert raw memory-order hex bytes to C integer literal hex (no 0x prefix).

    KLEE outputs bytes in host memory order. On little-endian machines, bytes
    need to be reversed to produce the correct C integer literal. On big-endian
    machines, bytes are already in the right order.

    Note: The endianness that matters here is that of the machine running KLEE,
    not the target machine that runs the WCET tests. KLEE's byte output reflects
    the host it ran on; C integer literals are endianness-agnostic.

    Example (little-endian): "01000000" (LE bytes for 1) -> "00000001" (0x00000001 = 1)
    Example (big-endian):    "00000001" -> "00000001" (no change needed)
    """
    if sys.byteorder == "little":
        byte_pairs = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
        byte_pairs.reverse()
        return "".join(byte_pairs)
    return hex_str


class ExecutableTransformer(object):
    """
    Transformation class to modify input C code with desired inputs.
    """

    def __init__(self, ast, function_name, hexvalues):
        self.ast = ast
        self.function_name = function_name
        self.generator = c_generator.CGenerator()
        self.arg_types = []
        self.arg_names = []
        self.new_main = None
        self.arguments = []
        self.hexvalues = hexvalues
        self.typedef_map = self._build_typedef_map(ast)

    def _build_typedef_map(self, ast):
        """Build a map from typedef names to their resolved type nodes."""
        typedef_map = {}
        for node in ast.ext:
            if isinstance(node, Typedef):
                typedef_map[node.name] = node.type
        return typedef_map

    def _resolve_typedef(self, type_node):
        """If type_node is a typedef'd IdentifierType, resolve it to the underlying type."""
        if (isinstance(type_node, TypeDecl) and
                isinstance(type_node.type, IdentifierType)):
            type_name = " ".join(type_node.type.names)
            if type_name in self.typedef_map:
                return self.typedef_map[type_name]
        return type_node

    def visit_func(self, node):
        """
        Visit the AST rooted at node. Generated the new main function and arguments definition.

        Parameters:
            node :
                The root AST node being visited
        """
        self.arg_types, self.arg_names = self.visit(node)
        self.new_main = self.gen_main(self.arg_types, self.arg_names)
        self.arguments = self.gen_arguments(
            self.arg_types, self.arg_names, self.hexvalues
        )

    def visit(self, node):
        """
        Recursively viste the AST node until seeing the definition of the function being analyzed.

        Parameters:
            node :
                Current AST node being analysized.

        Returns:
            (argument types of function being analyzed, argument names of function being analyzed)
        """
        if isinstance(node, FuncDef) and node.decl.name == self.function_name:
            if node.decl.type.args is None:
                return [], []
            params = node.decl.type.args.params
            arg_types = [param.type for param in params]
            arg_names = [param.name for param in params]
            return arg_types, arg_names

        for _, child in node.children():
            ret_val = self.visit(child)
            if ret_val:
                return ret_val

    def gen_main(self, arg_types, arg_names):
        """
        Generate the new MAIN function node.

        Parameters:
            arg_types :
                Argument types of function being analyzed
            arg_names :
                Argument names of function being analyzed

        Returns:
            The new MAIN fucntion AST node.
        """
        main_arg_types = ["int", "char **"]
        main_arg_names = ["argc", "argv"]

        params = []
        for m_arg_type, m_arg_name in zip(main_arg_types, main_arg_names):
            params.append(
                Decl(
                    name=m_arg_name,
                    quals=[],
                    storage=[],
                    funcspec=[],
                    type=TypeDecl(
                        declname=m_arg_name,
                        quals=[],
                        type=IdentifierType(names=[m_arg_type]),
                        align=None,
                    ),
                    init=None,
                    bitsize=None,
                    align=None,
                )
            )

        # Create the function declaration (return type and parameters)
        main_decl = FuncDecl(
            args=ParamList(params) if params else None,
            type=TypeDecl(
                declname="main",
                quals=[],
                type=IdentifierType(names=["int"]),
                align=None,
            ),
        )

        new_main = FuncDef(
            decl=Decl(
                name="main",
                quals=[],
                storage=[],
                funcspec=[],
                type=main_decl,  # Use the function declaration created above
                init=None,
                bitsize=None,
                align=None,
            ),
            param_decls=None,
            body=self.gen_main_body(
                arg_types, arg_names
            ),  # Here you would set the body of the function
        )

        return new_main

    def gen_main_body(self, arg_types, arg_names):
        """
        Generate the new MAIN function body. Including print statement, timing function call, driver function call.

        Parameters:
            arg_types :
                Argument types of function being analyzed
            arg_names :
                Argument names of function being analyzed

        Returns:
            The new MAIN function AST node.
        """
        body_items = []
        body_items.append(
            Decl(
                name="start",
                quals=[],
                storage=[],
                funcspec=[],
                type=TypeDecl(
                    declname="start",
                    quals=[],
                    type=IdentifierType(names=["unsigned long long"]),
                    align=None,
                ),
                init=None,
                bitsize=None,
                align=None,
            )
        )

        body_items.append(
            Decl(
                name="end",
                quals=[],
                storage=[],
                funcspec=[],
                type=TypeDecl(
                    declname="end",
                    quals=[],
                    type=IdentifierType(names=["unsigned long long"]),
                    align=None,
                ),
                init=None,
                bitsize=None,
                align=None,
            )
        )

        body_items.append(
            Assignment(
                op="=",
                lvalue=ID(name="start"),
                rvalue=FuncCall(name=ID(name="read_cycle_count"), args=None),
            )
        )

        # Calling the function of interest
        body_items.append(
            FuncCall(
                name=ID(name=self.function_name), args=ID(name=", ".join(arg_names))
            )
        )

        body_items.append(
            Assignment(
                op="=",
                lvalue=ID(name="end"),
                rvalue=FuncCall(name=ID(name="read_cycle_count"), args=None),
            )
        )

        # printf in Flexpret doesn't support unsigned long long
        end_minus_start = BinaryOp(op="-", left=ID(name="end"), right=ID(name="start"))

        cast_expr = Cast(
            to_type=Typename(
                name=None,
                quals=[],
                type=TypeDecl(
                    declname=None,
                    quals=[],
                    type=IdentifierType(names=["uint32_t"]),
                    align=None,
                ),
                align=None,
            ),
            expr=end_minus_start,
        )

        body_items.append(
            FuncCall(
                name=ID(name="printf"),
                args=ExprList(
                    exprs=[
                        Constant(type="string", value='"%li\\n"'),
                        cast_expr,
                    ]
                ),
            )
        )

        constant_zero = Constant(type="int", value="0")
        body_items.append(Return(expr=constant_zero))
        return Compound(block_items=body_items)

    def is_primitive(self, type_node):
        """
        Return if the TYPE_NODE is primitive.

        Parameters:
            type_node :
                Pycparser type representation.

        Returns:
            If TYPE_NODE is primitive.
        """
        return isinstance(type_node, TypeDecl) and isinstance(
            type_node.type, IdentifierType
        )

    def is_struct(self, type_node):
        """
        Return if the TYPE_NODE is struct.

        Parameters:
            type_node :
                Pycparser type representation.

        Returns:
            If TYPE_NODE is struct.
        """
        return isinstance(type_node, Struct)

    def is_array(self, type_node):
        """
        Return if the TYPE_NODE is array.

        Parameters:
            type_node :
                Pycparser type representation.

        Returns:
            If TYPE_NODE is array.
        """
        return isinstance(type_node, ArrayDecl)

    def generate_primitive_declaration(self, name, type_node, value):
        """
        Generates the variable declaration of primitive variable.

        Parameters:
            name :
                Variable name
            type_node :
                Pycparser type node for this variable.
            value :
                Value of the variable.

        Returns:
            String representation of the variable declaration in C for primitive variables.
        """
        generator = c_generator.CGenerator()
        type_str = generator.visit(type_node)
        # Reverse bytes from KLEE's little-endian memory order to correct integer literal
        hex_str = value.strip()
        if hex_str.startswith("0x"):
            raw = hex_str[2:]
            type_name = " ".join(type_node.type.names) if hasattr(type_node, 'type') and hasattr(type_node.type, 'names') else "int"
            elem_size = TYPE_SIZES.get(type_name, len(raw) // 2)
            raw = raw[:elem_size * 2]
            value = "0x" + _mem_bytes_to_literal_hex(raw)
        return f"{type_str} {name} = {value};"

    def generate_struct_declaration(self, name, struct_type_node, value_dict):
        """
        Generates the variable declaration of struct variable.

        Parameters:
            name :
                Variable name
            struct_type_node :
                Pycparser type node for this variable.
            value_dict :
                Dict of struct field to value.

        Returns:
            String representation of the variable declaration in C for struct variables.
        """
        # TODO: see how KLEE output structs
        field_inits = ", ".join([f"{value}" for field, value in value_dict.items()])
        return f"struct {struct_type_node.name} {name} = {{ {field_inits} }};"

    def generate_array_declaration(self, name, array_type_node, values):
        """
        Generates the variable declaration of struct variable.

        Parameters:
            name :
                Variable name
            array_type_node :
                Pycparser type node for this variable.
            value_dict :
                Dict of struct field to value.

        Returns:
            String representation of the variable declaration in C for array variables.
        """
        # TODO: see how KLEE output nested array
        element_type_str = self.get_element_type_str(array_type_node)
        elem_size = TYPE_SIZES.get(element_type_str, 4)
        hex_digits_per_elem = elem_size * 2
        # Strip 0x prefix and trailing whitespace
        values_hex = values.strip()
        if values_hex.startswith("0x"):
            values_hex = values_hex[2:]
        # Chunk by element size and reverse bytes within each element
        values_chunk = []
        for i in range(0, len(values_hex), hex_digits_per_elem):
            chunk = values_hex[i : i + hex_digits_per_elem]
            values_chunk.append("0x" + _mem_bytes_to_literal_hex(chunk))

        values_str = ", ".join(values_chunk)
        return f"{element_type_str} {name}[] = {{ {values_str} }};"

    def generate_typedef_array_declaration(self, name, orig_type_node, resolved_array_node, value):
        """
        Generates the variable declaration for a typedef'd array type.

        Uses the typedef name for the declaration but generates a flat initializer
        list based on the resolved array element type and size.
        """
        # Get the typedef name from the original type node
        typedef_name = " ".join(orig_type_node.type.names)
        # Get the base element type from the resolved array
        element_type_str = self.get_element_type_str(resolved_array_node)
        elem_size = TYPE_SIZES.get(element_type_str, 4)
        hex_digits_per_elem = elem_size * 2

        # Strip 0x prefix and trailing whitespace
        values_hex = value.strip()
        if values_hex.startswith("0x"):
            values_hex = values_hex[2:]

        # Chunk by element size and reverse bytes within each element
        values_chunk = []
        for i in range(0, len(values_hex), hex_digits_per_elem):
            chunk = values_hex[i : i + hex_digits_per_elem]
            if len(chunk) == hex_digits_per_elem:
                values_chunk.append("0x" + _mem_bytes_to_literal_hex(chunk))

        values_str = ", ".join(values_chunk)
        return f"{typedef_name} {name} = {{{values_str}}};"

    def get_element_type_str(self, array_type_node):
        """
        Get the base type of array type.

        Parameters:
            array_type_node :
                Array pycparser type node.

        Returns:
            String representation of base type.
        """
        generator = c_generator.CGenerator()
        # For arrays, recursively find the base type if it's a multi-dimensional array
        while isinstance(array_type_node, ArrayDecl):
            array_type_node = array_type_node.type
        return generator.visit(array_type_node)

    def gen_arguments(self, arg_types, arg_names, hex_values):
        """
        Generate the string representation of all argument declarations

        Parameters:
            arg_types :
                List of argument types.

            arg_names :
                List of argument names.

            hex_values :
                List of hexidecimal values for arguments.


        Returns:
            String representation of the arguments declarations.
        """
        declarations = []

        for type_node, name, value in zip(arg_types, arg_names, hex_values):
            resolved = self._resolve_typedef(type_node)
            if self.is_array(resolved):
                decl = self.generate_typedef_array_declaration(
                    name, type_node, resolved, value
                )
            elif self.is_primitive(type_node):
                decl = self.generate_primitive_declaration(name, type_node, value)
            elif self.is_struct(type_node):
                decl = self.generate_struct_declaration(name, type_node, value)
            elif self.is_array(type_node):
                decl = self.generate_array_declaration(name, type_node, value)
            else:
                raise NotImplementedError(
                    f"Type handling not implemented for {type(type_node)}"
                )

            declarations.append(decl)

        return "\n".join(declarations)


def generate_executable(
    input_file,
    input_folder,
    function_name,
    hex_values_file,
    timing_function_body,
    include_flexpret=False,
):
    """
    Modify INPUT_FILE to ingest the values and generate an executable C file. Stored as INPUT_FOLDER/driver.c

    Parameters:
        input_file :
            Input C program.

        input_folder :
            The folder to output the modified C program.

        function_name :
            Name of function being analyzed.

        hex_values_file :
            Input values used to modify C program. Should be a list of hexidecimal values, 1 per line.

        timing_function_body :
            The timing function to use to get cycle count. Inserted before and after function call.

        include_flexpret :
            Flag for if we need to include Flexpret specific headers. (Default value = False)

    Returns:
        File path for the modified C program.
    """
    # hex_values should be a list and each if either an element (primitive type), a list (array), a dict (struct, key is field name and value is value)

    hexvalues = []
    with open(hex_values_file, "r") as file:
        for line in file:
            hexvalues.append(line)

    ast = parse_file(
        input_file,
        use_cpp=True,
        cpp_path="clang",
        cpp_args=["-E", r"-I{}".format(pycparser_utils_path)],
    )

    transformer = ExecutableTransformer(ast, function_name, hexvalues)
    transformer.visit_func(ast)

    # Read the original C file content
    with open(input_file, "r") as file:
        original_c_content = file.read()

    # Remove any existing main function definition to avoid conflicts
    import re as _re
    main_def_pat = r'(?:^[^\n\S]*(?:int|void)\s+main\s*\([^)]*\)\s*\{)'
    main_match = _re.search(main_def_pat, original_c_content, flags=_re.MULTILINE)
    if main_match:
        brace_start = original_c_content.index('{', main_match.start())
        depth = 0
        i = brace_start
        while i < len(original_c_content):
            if original_c_content[i] == '{':
                depth += 1
            elif original_c_content[i] == '}':
                depth -= 1
                if depth == 0:
                    original_c_content = original_c_content[:main_match.start()] + original_c_content[i+1:]
                    break
            i += 1
    # Also remove forward declarations of main
    original_c_content = _re.sub(r'^[^\n\S]*int\s+main\s*\([^)]*\)\s*;\s*\n?', '', original_c_content, flags=_re.MULTILINE)

    # This must be included in we want to run flexpret backend (for printf)
    if include_flexpret:
        original_c_content = "#include <flexpret/flexpret.h> \n" + original_c_content
    else:
        original_c_content = "#include <stdio.h>\n#include <stdint.h>\n#include <time.h>\n" + original_c_content

    # TODO: generate global variables, add the global timing function
    original_c_content += timing_function_body
    original_c_content += transformer.arguments

    generator = c_generator.CGenerator()
    original_c_content += generator.visit(transformer.new_main)

    # Write the modified code to a new file
    output_file = os.path.join(input_folder + "/" + "driver.c")
    with open(output_file, "w") as f:
        f.write(original_c_content)

    print(f"Modified code written to {output_file}")
    return output_file
