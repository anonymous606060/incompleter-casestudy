from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_class import DefineClass
from typing import Any
import ast

class DefineVar(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.var_name = kwargs['var_name']
        if 'func_scope' in kwargs: self.func_scope = kwargs['func_scope'] or 'global'
        else: self.func_scope = 'global'
        if 'class_scope' in kwargs: self.class_scope = kwargs['class_scope'] or 'global'
        else: self.class_scope = 'global'
        
        # Lazy definition
        self.var_val_id = None
        self.var_val = None

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Variable name: {}\nVariable value: {}\n'.format(self.var_name, self.var_val)

        return desc

    def __is_class(self, var_name) -> bool:
        all_upper = True
        for c in var_name.split():
            if c.islower():
                all_upper = False
                break
        if not all_upper and var_name[0].isupper():
            return True
        return False

    def check_criteria(self) -> bool:
        # if len(self.class_scope) > 0:
        #     if self.class_scope == 'global' or 'TBD' in self.class_scope:
        #         return True
        # return False
        
        self.var_val_id = self.snippet.get_next_tbd_name()
        
        # Assuming that variable names starting with an uppercase letter are class names and variable names starting with a non-uppercase letter is an object
        if self.__is_class(self.var_name):
            self.var_val = ast.Name(id=self.var_val_id, ctx=ast.Load())
        else:
            self.var_val = ast.Call(
                func=ast.Name(id=self.var_val_id, ctx=ast.Load()),
                args=[],
                keywords=[]
            )

        return True

    def apply_pattern(self) -> str:
        class DefineLazyVarTransformer(ast.NodeTransformer):
            def __init__(self, **kwargs: Any) -> None:
                self.snippet: Snippet = kwargs['snippet']
                self.lineno: int = kwargs['lineno']
                self.var_name: str = kwargs['var_name']
                self.class_scope: str = kwargs['class_scope']
                self.func_scope: str = kwargs['func_scope']
                self.var_val_id: str = kwargs['var_val_id']
                self.var_val: ast.Module = kwargs['var_val']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node: ast.Module) -> ast.Module:
                var_def = ast.Assign(
                    targets = [],
                    value=self.var_val
                )

                if self.class_scope == 'global' and self.func_scope == 'global':
                    var_def.targets.append(ast.Name(id=self.var_name, ctx=ast.Store()))
                    node.body.insert(0, var_def)
                elif self.class_scope != 'global':
                    class DefineVarInClassScopeTransformer(ast.NodeTransformer):
                        def __init__(self, **kwargs: dict) -> None:
                            self.var_name = kwargs['var_name']
                            self.class_name = kwargs['class_name']
                            self.func_scope = kwargs['func_scope']
                            self.var_def = kwargs['var_def']

                        def visit_ClassDef(self, node) -> ast.Module:
                            if node.name == self.class_name:
                                if self.func_scope == 'global':
                                    self.var_def.targets.append(ast.Name(id=self.var_name, ctx=ast.Store()))
                                    node.body.insert(0, self.var_def)
                                else:
                                    class DefineVarInFuncScopeTransformer(ast.NodeTransformer):
                                        def __init__(self, **kwargs: dict) -> None:
                                            self.var_name = kwargs['var_name']
                                            self.func_name = kwargs['func_name']
                                            self.var_def = kwargs['var_def']

                                        def visit_FunctionDef(self, node) -> ast.Module:
                                            if node.name == self.func_name:
                                                self.var_def.targets.append(ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=self.var_name, ctx=ast.Store()))
                                                node.body.insert(0, self.var_def)
                                            return node

                                    node = DefineVarInFuncScopeTransformer(var_name=self.var_name, func_name=self.func_scope, var_def=self.var_def).visit(node)
                            return node
                    
                    node = DefineVarInClassScopeTransformer(var_name=self.var_name, class_name=self.class_scope, func_scope=self.func_scope, var_def=var_def).visit(node)
                
                return node

        tree = ast.parse(self.snippet.get_latest())
        DefineLazyVarTransformer(snippet=self.snippet, lineno=self.lineno, var_name=self.var_name, class_scope=self.class_scope, func_scope=self.func_scope, var_val_id=self.var_val_id, var_val=self.var_val).visit_Body(tree)

        DefineClass(snippet=self.snippet, lineno=self.lineno, class_name=self.var_val_id).apply_pattern()
        self.snippet.register_mock_definition(iter_n=self.snippet.get_current_iter(), target=self.var_name, value=self.var_val_id)
        
        return

