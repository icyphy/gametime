from pycparser import parse_file, c_generator
from pycparser.c_ast import FuncDef, Decl, FuncCall, ID, Compound, TypeDecl, IdentifierType, FuncDecl, ParamList, Return, Constant, Assignment, ExprList, BinaryOp, NamedInitializer, InitList, Struct, ArrayDecl
import os

pycparser_utils_path = '/home/c/Desktop/research/lf/code/pycparser/utils/fake_libc_include'

class KleeTransformer(object):
    def __init__(self, ast, function_name, hexvalues):
        self.ast = ast
        self.function_name = function_name
        self.generator = c_generator.CGenerator()
        self.arg_types = []
        self.arg_names = []
        self.new_main = None
        self.arguments = []
        self.hexvalues = hexvalues

    def visit_func(self, node):
        self.arg_types, self.arg_names = self.visit(node)
        self.new_main = self.gen_main(self.arg_types, self.arg_names)
        self.arguments = self.gen_arguments(self.arg_types, self.arg_names, self.hexvalues)

    def visit(self, node):
        if isinstance(node, FuncDef) and node.decl.name == self.function_name:
            params = node.decl.type.args.params
            arg_types = [param.type for param in params]
            arg_names = [param.name for param in params]
            return arg_types, arg_names
        
        for _, child in node.children():
            ret_val = self.visit(child)
            if ret_val:
                return ret_val

    def gen_main(self, arg_types, arg_names):
        main_arg_types = ['int', 'char **']
        main_arg_names = ['argc', 'argv']

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
                declname='main',
                quals=[],
                type=IdentifierType(names=['int']),
                align=None
            )
        )

        new_main = FuncDef(
            decl=Decl(
                name='main',
                quals=[],
                storage=[],
                funcspec=[],
                type=main_decl,  # Use the function declaration created above
                init=None,
                bitsize=None,
                align=None, 
            ),
            param_decls=None,
            body=self.gen_main_body(arg_types, arg_names)  # Here you would set the body of the function
        )


        return new_main

    def gen_main_body(self, arg_types, arg_names):
        body_items = []
        body_items.append(Decl(
                                name="start", 
                                quals=[], 
                                storage=[], 
                                funcspec=[],
                                type=TypeDecl(
                                    declname="start", 
                                    quals=[], 
                                    type=IdentifierType(
                                        names=["unsigned long long"]
                                    ),
                                    align=None,
                                ),
                                init=None, 
                                bitsize=None,
                                align=None,
                            )
                        )
        
        body_items.append(Decl(
                                name="end", 
                                quals=[], 
                                storage=[], 
                                funcspec=[],
                                type=TypeDecl(
                                    declname="end", 
                                    quals=[], 
                                    type=IdentifierType(
                                        names=["unsigned long long"]
                                    ),
                                    align=None,
                                ),
                                init=None, 
                                bitsize=None,
                                align=None,
                            )
                        )

        body_items.append(Assignment(
                                op="=", 
                                lvalue=ID(name="start"), 
                                rvalue=FuncCall(
                                        name=ID(name="read_cycle_count"), 
                                        args=None
                                    )
                                )
                            )     
        
        # Calling the function of interest
        body_items.append(
            FuncCall(
                name=ID(name=self.function_name),
                args=ID(name=', '.join(arg_names))
            )
        )

        body_items.append(Assignment(
                                op="=", 
                                lvalue=ID(name="end"), 
                                rvalue=FuncCall(
                                        name=ID(name="read_cycle_count"), 
                                        args=None
                                    )
                                )
                            )     
        body_items.append(FuncCall(name=ID(name="printf"), args=ExprList(exprs=[
            Constant(type="string", value='"%llu.\\n"'),
            ID(name="start"), 
        ])))    
        body_items.append(FuncCall(name=ID(name="printf"), args=ExprList(exprs=[
            Constant(type="string", value='"%llu.\\n"'),
            ID(name="end"), 
        ])))

        constant_zero = Constant(type='int', value='0')
        body_items.append(Return(expr=constant_zero))
        return Compound(block_items=body_items)

    def is_primitive(self, type_node):
        return isinstance(type_node, TypeDecl) and isinstance(type_node.type, IdentifierType)

    def is_struct(self, type_node):
        return isinstance(type_node, Struct)

    def is_array(self, type_node):
        return isinstance(type_node, ArrayDecl)
    
    # def generate_value_str(self, value, type_hint):
    #     if isinstance(value, dict):  # Assuming a struct initializer
    #         return "{ " + ", ".join([f"{v}" for k, v in value.items()]) + " }"
    #     elif isinstance(value, list):  # Assuming an array initializer
    #         return "{ " + ", ".join([self.generate_value_str(v, type_hint) for v in value]) + " }"
    #     elif isinstance(value, str):
    #         return f'"{value}"'  # For a string, return as a C string literal
    #     else:
    #         return str(value)  # For other primitive types

    def generate_primitive_declaration(self, name, type_node, value):
        generator = c_generator.CGenerator()
        type_str = generator.visit(type_node)
        return f"{type_str} {name} = {value};"

    def generate_struct_declaration(self, name, struct_type_node, value_dict):
        #TODO: see how KLEE output structs
        field_inits = ", ".join([f"{value}" for field, value in value_dict.items()])
        return f"struct {struct_type_node.name} {name} = {{ {field_inits} }};"

    def generate_array_declaration(self, name, array_type_node, values):
        #TODO: see how KLEE output nested array
        element_type_str = self.generate_element_type_str(array_type_node)
        #-2 to skip 0x and -1 to remove the trailing space
        values_hex = values[2:-1]
        #8 here because integer 32bit are 8 heximal degits
        values_chunk = []
        for i in range(0, len(values_hex), 8):
            values_chunk.append("0x" + values_hex[i:i+8])

        values_str = ", ".join(values_chunk)
        return f"{element_type_str} {name}[] = {{ {values_str} }};"

    def generate_element_type_str(self, array_type_node):
        generator = c_generator.CGenerator()
        # For arrays, recursively find the base type if it's a multi-dimensional array
        while isinstance(array_type_node, ArrayDecl):
            array_type_node = array_type_node.type
        return generator.visit(array_type_node)

    def gen_arguments(self, arg_types, arg_names, hex_values):
        declarations = []
        
        for type_node, name, value in zip(arg_types, arg_names, hex_values):
            if self.is_primitive(type_node):
                decl = self.generate_primitive_declaration(name, type_node, value)
            elif self.is_struct(type_node):
                decl = self.generate_struct_declaration(name, type_node, value)
            elif self.is_array(type_node):
                decl = self.generate_array_declaration(name, type_node, value)
            else:
                raise NotImplementedError(f"Type handling not implemented for {type(type_node)}")
            
            declarations.append(decl)

        return "\n".join(declarations)

    def create_declaration(type_name, var_name, initializer=None):
        type_decl = TypeDecl(declname=var_name, quals=[], type=IdentifierType(names=[type_name]))
        decl = Decl(name=var_name, quals=[], storage=[], funcspec=[], type=type_decl, init=initializer, bitsize=None)
        return decl

    def create_struct_declaration(struct_name, var_name, field_inits):
        # Create an initializer list for the struct fields
        inits = [NamedInitializer(name=[ID(name=field_name)], expr=Constant(type='int', value=field_value))
                for field_name, field_value in field_inits.items()]
        initializer = InitList(expressions=inits)
        
        # Create the struct declaration
        struct_type = Struct(name=struct_name, decls=None)
        type_decl = TypeDecl(declname=var_name, quals=[], type=struct_type)
        decl = Decl(name=var_name, quals=[], storage=[], funcspec=[], type=type_decl, init=initializer, bitsize=None)
        return decl

def generate_executable(input_file, input_folder, function_name, hex_values_file, timing_function_body):
    #hex_values should be a list and each if either an element (primitive type), a list (array), a dict (struct, key is field name and value is value)
    # MyStruct myInstance = {
    #     .integerMember = 0x1A, // Hexadecimal for 26
    #     .charMember = 0x41,    // Hexadecimal for 'A'
    #     .floatMember = 0x1.Ap2 // Hexadecimal floating-point literal for 1.5 * 2^2 = 6.0
    # };
    hexvalues = []
    with open(hex_values_file, 'r') as file:
        for line in file:
            hexvalues.append(line)

    ast = parse_file(input_file, use_cpp=True,
                     cpp_path='clang',
                     cpp_args=['-E', r'-I{}'.format(pycparser_utils_path)])
    
    transformer = KleeTransformer(ast, function_name, hexvalues)
    transformer.visit_func(ast)

    # Read the original C file content
    with open(input_file, 'r') as file:
        original_c_content = file.read()

    #TODO: generate global variables, add the global timing function
    original_c_content += timing_function_body
    original_c_content += transformer.arguments

    generator = c_generator.CGenerator()
    original_c_content += generator.visit(transformer.new_main)

    # Write the modified code to a new file
    output_file = os.path.join(input_folder + "driver.c") 
    with open(output_file, 'w') as f:
        f.write(original_c_content)

    print(f"Modified code written to {output_file}")
    return output_file

