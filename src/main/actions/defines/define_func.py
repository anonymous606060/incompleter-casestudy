from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_class import DefineClass
from typing import Any
import ast

class DefineFunc(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.func_name = kwargs['func_name']
        if 'class_scope' in kwargs:
            self.class_scope = kwargs['class_scope'] or 'global'
        else: 
            self.class_scope = 'global'

        # determining whether to define a class level or instance level method
        if 'func_level' in kwargs:
            self.func_level = kwargs['func_level']
        else:
            self.func_level = 'class'

        self.func_vararg = []
        self.func_kwarg = []
        self.func_args = []
        if 'func_args' in kwargs:
            self.func_args = kwargs['func_args']
        self.func_keywords = {}
        if 'func_keywords' in kwargs:
            self.func_keywords = kwargs['func_keywords']
        
        self.func_body = []
        if 'func_body' in kwargs: 
            self.func_body = kwargs['func_body']
        else:
            self.ret_val_id = None
            # return statement is added in check_criteria only if check_criteria is satisfied (otherwise, if we had called snippet.get_next_tbd_name() here in init, then we would end up wasting a few tbd numbers if check_criteria returns False)

        self.override_criteria = False
        if 'override_criteria' in kwargs.keys():
            self.override_criteria = kwargs['override_criteria']

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Func name: {}\nFunc args: {}\nFunc keywords: {}\nFunc body: {}\n'.format(self.func_name, self.func_args, self.func_keywords, self.func_body)

        return desc

    def check_criteria(self) -> bool:
        class FuncCallVisitor(ast.NodeVisitor):
            def __init__(self, **kwargs: dict) -> None:
                self.func_found = False
                self.found_node = None
                self.func_name = kwargs['func_name']
                self.func_vararg = kwargs['func_vararg']
                self.func_kwarg = kwargs['func_kwarg']
                self.func_args = kwargs['func_args']
                self.func_keywords = kwargs['func_keywords']

            def visit_Call(self, node):
                if self.func_found:
                    return node

                if isinstance(node.func, ast.Name) or isinstance(node.func, ast.Attribute):
                    if isinstance(node.func, ast.Name):
                        if node.func.id == self.func_name:
                            self.found_node = node
                            self.func_found = True
                        else:
                            # Recurse into node.func.args (for func calls that are args. e.g. foo(bar()) or foo(bar.func()) )
                            for (idx, child) in enumerate(node.args):
                                self.visit(child)
                            if 'keywords' in dir(node):
                                for (idx, child) in enumerate(node.keywords):
                                    self.visit(child.value)
                            return node
                    elif isinstance(node.func, ast.Attribute):
                        # Recursively look for the intended attribute (self.func_name)
                        if node.func.attr == self.func_name:
                            self.found_node = node
                            self.func_found = True

                            # We won't be recursing anymore at this point
                        else:
                            # Recurse into node.func first (for chain func calls. e.g. foo.bar() or foo.bar().func())
                            self.visit(node.func)

                            # Recurse into node.func.args (for func calls that are args. e.g. foo(bar()) or foo(bar.func()) )
                            for (idx, child) in enumerate(node.args):
                                self.visit(child)
                            if 'keywords' in dir(node):
                                for (idx, child) in enumerate(node.keywords):
                                    self.visit(child.value)

                            return node

                    if self.found_node.args:
                        for (arg_i, arg) in enumerate(self.found_node.args):
                            if isinstance(arg, ast.Starred):
                                self.func_vararg.append(ast.arg(arg='arg'+str(arg_i)))
                            else:
                                self.func_args.append(ast.arg(arg='arg'+str(arg_i)))
                    if self.found_node.keywords:
                        for kw in self.found_node.keywords:
                            if kw.arg:
                                self.func_keywords[ast.arg(arg=kw.arg)] = ast.Constant(value=None)
                            else:
                                if isinstance(kw.value, ast.Name):
                                    self.func_kwarg.append(ast.arg(arg=kw.value.id))
                                else:
                                    self.func_kwarg.append(ast.arg(arg='kwargs'))
                
                return node

        tree = ast.parse(self.snippet.get_mocked_original())

        func_visitor = FuncCallVisitor(func_name=self.func_name, func_vararg=self.func_vararg, func_kwarg=self.func_kwarg, func_args=self.func_args, func_keywords=self.func_keywords)
        func_visitor.visit(tree)

        if (self.override_criteria or func_visitor.func_found) and len(self.func_body) == 0:
            self.ret_val_id = self.snippet.get_next_tbd_name()
            self.func_body.append(ast.Return(value=ast.Call(
                func=ast.Name(id=self.ret_val_id, ctx=ast.Load()),
                args=[],
                keywords=[])
            ))

        return func_visitor.func_found

    def apply_pattern(self) -> str:
        class DefineLazyFuncTransformer(ast.NodeTransformer):
            def __init__(self, **kwargs: Any) -> None:
                self.snippet: Snippet = kwargs['snippet']
                self.lineno: int = kwargs['lineno']
                self.func_name: str = kwargs['func_name']
                self.class_scope: str = kwargs['class_scope']
                self.func_level: str = kwargs['func_level']
                self.func_vararg: str = kwargs['func_vararg']
                self.func_kwarg: str = kwargs['func_kwarg']
                self.func_args = kwargs['func_args']
                self.func_keywords = kwargs['func_keywords']
                self.func_body: str = kwargs['func_body']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node: ast.Module) -> ast.Module:
                func_def = ast.FunctionDef(
                    name=self.func_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        vararg=None,
                        kwarg=None,
                        args=[],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[]
                    ),
                    body=self.func_body,
                    decorator_list=[]
                )

                if len(self.func_args):
                    func_def.args.args += self.func_args
                if len(self.func_keywords):
                    func_def.args.args += list(self.func_keywords.keys())
                    func_def.args.defaults += list(self.func_keywords.values())
                if len(self.func_vararg):
                    func_def.args.vararg = self.func_vararg[0]
                if len(self.func_kwarg):
                    func_def.args.kwarg = self.func_kwarg[0]

                class RedefineFuncTransformer(ast.NodeTransformer):
                    def __init__(self, **kwargs):
                        self.func_def = kwargs['func_def']
                        self.exists = False

                    def visit_FunctionDef(self, node):
                        if node.name == self.func_def.name:
                            self.exists = True
                            return self.func_def
                        return node

                if self.class_scope == 'global':
                    redefine_func_transformer = RedefineFuncTransformer(func_def = func_def)
                    
                    new_children = []
                    for child in node.body:
                        new_children.append(redefine_func_transformer.visit(child))

                    if not redefine_func_transformer.exists:
                        node.body.insert(0, func_def)
                    else:
                        node.body = new_children
                else:
                    class DefineFuncInClassScopeTransformer(ast.NodeTransformer):
                        def __init__(self, **kwargs: dict) -> None:
                            self.class_name = kwargs['class_name']
                            self.func_level = kwargs['func_level']
                            self.func_def = kwargs['func_def']

                            if self.func_level == 'instance':
                                print('\n\nHERE\n\n')
                                self.func_def.args.args.insert(0, ast.arg(arg='self'))

                        def visit_ClassDef(self, node):
                            if node.name == self.class_name:
                                redefine_func_transformer = RedefineFuncTransformer(func_def = self.func_def)
                    
                                new_children = []
                                for child in node.body:
                                    new_children.append(redefine_func_transformer.visit(child))

                                if not redefine_func_transformer.exists:
                                    node.body.append(self.func_def)
                                else:
                                    node.body = new_children
                            return node
                    
                    node = DefineFuncInClassScopeTransformer(class_name=self.class_scope, func_level=self.func_level, func_def=func_def).visit(node)

                return node

        tree = ast.parse(self.snippet.get_latest())
        DefineLazyFuncTransformer(snippet=self.snippet, lineno=self.lineno, func_name=self.func_name, class_scope=self.class_scope, func_level=self.func_level, func_vararg=self.func_vararg, func_kwarg=self.func_kwarg, func_args=self.func_args, func_keywords=self.func_keywords, func_body=self.func_body).visit_Body(tree)

        if 'ret_val_id' in dir(self): 
            DefineClass(snippet=self.snippet, lineno=self.lineno, class_name=self.ret_val_id).apply_pattern()
            self.snippet.register_mock_definition(iter_n=self.snippet.get_current_iter(), target=self.func_name, value=self.ret_val_id)
        
        return

