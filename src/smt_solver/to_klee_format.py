import os

from pycparser import parse_file, c_generator
from pycparser.c_ast import FuncDef, Decl, FuncCall, ID, Compound, TypeDecl, IdentifierType, FuncDecl, ParamList, Return, Constant, ArrayDecl

headers = ["#include </snap/klee/9/usr/local/include/klee/klee.h>", "#include <stdbool.h>"]
pycparser_utils_path="/home/c/Desktop/research/lf/code/pycparser/utils/fake_libc_include"

class KleeTransformer(object):
    def __init__(self, ast, function_name, total_path_labels, total_number_of_labels):
        self.ast = ast
        self.function_name = function_name
        self.total_path_labels = total_path_labels
        self.total_number_of_labels = total_number_of_labels
        self.generator = c_generator.CGenerator()
        self.new_main = None

    def visit_func(self, node):
        arg_types, arg_names = self.visit(node)
        self.new_main = self.gen_main(arg_types, arg_names)

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
        for arg_type, arg_name in zip(arg_types, arg_names):
            # Declaration of the variable

            body_items.append(
                Decl(
                    name=arg_name,
                    quals=[],
                    storage=[],
                    funcspec=[],
                    type=arg_type,
                    init=None,
                    bitsize=None,
                    align=None, 
                )
            )

            # Making the variable symbolic
            body_items.append(
                FuncCall(
                    name=ID(name='klee_make_symbolic'),
                    args=ID(name=f'&{arg_name}, sizeof({arg_name}), "{arg_name}"')
                )
            )

        # Calling the function of interest
        body_items.append(
            FuncCall(
                name=ID(name=self.function_name),
                args=ID(name=', '.join(arg_names))
            )
        )

        # klee_assert after function call
        for i in range(self.total_number_of_labels):
            body_items.append(
                FuncCall(
                    name=ID(name='klee_assert'),
                    args=ID(name=f'conditional_var_{i}')
                )
            )

        constant_zero = Constant(type='int', value='0')
        body_items.append(Return(expr=constant_zero))
        return Compound(block_items=body_items)

def format_for_klee(c_file, c_file_path, c_file_gt_dir, function_name, total_path_labels, total_number_of_labels):
    ast = parse_file(c_file_path, use_cpp=True,
                     cpp_path='clang',
                     cpp_args=['-E', r'-I{}'.format(pycparser_utils_path)])
    
    transformer = KleeTransformer(ast, function_name, total_path_labels, total_number_of_labels)
    transformer.visit_func(ast)

    # Read the original C file content
    with open(c_file_path, 'r') as file:
        original_c_content = file.read()

    klee_headers = "\n".join(headers)

    global_booleans = "\n"
    for i in range(total_path_labels):
        global_booleans += f"bool conditional_var_{i} = false;\n"

    for i in range(total_number_of_labels - total_path_labels):
        global_booleans += f"bool conditional_var_{i + total_path_labels} = true;\n"
    
    original_c_content = klee_headers + global_booleans + original_c_content

    generator = c_generator.CGenerator()
    original_c_content += generator.visit(transformer.new_main)

    klee_file = os.path.join(c_file_gt_dir, c_file + "_klee_format.c") 
    with open(klee_file, 'w') as output_file:
        output_file.write(original_c_content)

    return klee_file