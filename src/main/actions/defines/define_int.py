from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_func import DefineFunc
from typing import Any
import ast

class DefineInteger(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.class_name = None
        if 'class_name' in kwargs: 
            self.class_name = kwargs['class_name']

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Integer Class name: {}\n'.format(self.class_name)

        return desc

    def check_criteria(self) -> bool:
        return True

    def apply_pattern(self) -> str:
        # subclass 'int' class
        self.__subclass_int()

        return

    def __subclass_int(self) -> None:
        class IntegerSubclasser(ast.NodeTransformer):
            def __init__(self, **kwargs):
                self.class_name = kwargs['class_name']
                self.snippet = kwargs['snippet']
                self.lineno = kwargs['lineno']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node):
                for (idx, child) in enumerate(node.body):
                    node.body[idx] = self.visit(child)                
                return node

            def visit_ClassDef(self, node):
                if node.name == self.class_name:
                    node.bases.append(ast.Name(id='int', ctx=ast.Load()))
                return node
        
        tree = ast.parse(self.snippet.get_latest())
        tree = IntegerSubclasser(class_name=self.class_name, snippet=self.snippet, lineno=self.lineno).visit_Body(tree)

        return None

# import ast
# import astunparse  

# class DefineInteger(ActionBaseClass):
#     def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
#         super().__init__(snippet, lineno)
#         self.class_name = kwargs.get('class_name', '')

#     def check_criteria(self) -> bool:
#         return True

#     def apply_pattern(self) -> str:
#         class ClassInstantiationReplacer(ast.NodeTransformer):
#             def __init__(self, class_name):
#                 self.class_name_to_remove = class_name

#             def visit_Assign(self, node):
#                 if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == self.class_name_to_remove:
#                     return ast.Assign(targets=node.targets, value=ast.Constant(value=0))
#                 return node

#             def visit_ClassDef(self, node):
#                 if node.name == self.class_name_to_remove:
#                     return None
#                 return node

#             def visit_Return(self, node):
#                 if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == self.class_name_to_remove:
#                     return ast.Return(value=ast.Constant(value=0))
#                 return node

#         if self.class_name:
#             tree = ast.parse(self.snippet.get_latest())
#             replacer = ClassInstantiationReplacer(self.class_name)
#             modified_tree = replacer.visit(tree)
#             ast.fix_missing_locations(modified_tree) 
#             modified_code = astunparse.unparse(modified_tree)
#             self.snippet.add(modified_code) 
#             return modified_code
#         else:
#             return self.snippet.get_latest()