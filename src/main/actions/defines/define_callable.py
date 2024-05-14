from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_func import DefineFunc
from typing import Any
import ast

class DefineCallable(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.class_name = None
        if 'class_name' in kwargs: 
            self.class_name = kwargs['class_name']

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Callable Class name: {}\n'.format(self.class_name)

        return desc

    def check_criteria(self) -> bool:
        if self.class_name is not None and 'TBD' in self.class_name:
            return True
        return False

    def apply_pattern(self) -> None:
        # Define __call__ function inside the erroneous TBD class
        self.__define_call()

        return

    def __find_func_name(self) -> str:
        # e.g. Let's consider a statement: ident_0 = TBD#() --> In this function, we will try to find the original function name ident_0 from the TBD class name TBD#. We know that ident_0 will be a function name because we are in the DefineCallable action class. And, we need to find the original name of the function in order to get its argument information using DefineFunc#check_criteria (lookahead static analysis).
        class FuncNameFinderVisitor(ast.NodeVisitor):
            def __init__(self, **kwargs: dict) -> None:
                self.class_name = kwargs['class_name']
                self.func_name = None

            def visit_Assign(self, node) -> ast.Module:
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                    if node.value.func.id == self.class_name:
                        if type(node.targets[0]) == ast.Attribute:
                            self.func_name = node.targets[0].attr
                        elif type(node.targets[0]) == ast.Name:
                            self.func_name = node.targets[0].id
                return node

        tree = ast.parse(self.snippet.get_latest())
        func_name_finder_visitor = FuncNameFinderVisitor(class_name=self.class_name)
        func_name_finder_visitor.visit(tree)

        return func_name_finder_visitor.func_name

    def __define_call(self) -> None:
        kwargs = {}
        kwargs['class_scope'] = self.class_name
        kwargs['func_name'] = self.__find_func_name()
        kwargs['func_level'] = 'instance'

        arg_finder = DefineFunc(snippet=self.snippet, lineno=self.lineno, override_criteria = True, **kwargs)

        if kwargs['func_name'] is not None and arg_finder.check_criteria():
            # Using check_criteria to check if we can find the signature of the function
            arg_finder.func_name = '__call__'
            # arg_finder.func_args.insert(0, ast.arg(arg='self'))
            arg_finder.apply_pattern()
        else:
            arg_finder.check_criteria() # arg_finder.check_criteria will return False here because the function name was not found. But, we call check_criteria anyway to ensure that the function being defined has a body with a return TBD#() statement
            
            # At this point, we could not statically analyze the function's signature requirements statically from the function call (e.g. scenario 1. x = foo() --> foo() returns TBD# object --> x(arg0, arg1 ...) --> TBD# object was supposed to be a callable --> We need data flow analysis to realize that TBD# callable object is associate with the identifier x; scenario 2. function might be a decorating function which has not explicit calling signature --> @x\ndef foo(): ...). So, we go with a generic function signature that takes an arbitrary number of positional args (i.e. *args) and arbitrary number of keyword args (i.e. **kwargs). This is a fallback option which limits our ability to infer a more accurate function declaration syntax (which could have been later used to map to existing popular package functions).
            arg_finder.func_name = '__call__'
            # arg_finder.func_args.insert(0, ast.arg(arg='self'))
            arg_finder.func_vararg.append(ast.arg(arg='args'))
            arg_finder.func_kwarg.append(ast.arg(arg='kwargs'))
            arg_finder.apply_pattern()

        return