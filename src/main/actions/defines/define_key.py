from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_class import DefineClass
from typing import Any
import ast

class DefineKey(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.class_name = None
        if 'class_name' in kwargs.keys():
            self.class_name = kwargs['class_name']

        self.key = int(kwargs['key']) if kwargs['key'].isnumeric() else kwargs['key']
        if isinstance(self.key, str) and '\'' in self.key:
            self.key = self.key.replace('\'', '')
        elif isinstance(self.key, str):
            if self.key in 'True':
                self.key = True
            elif self.key in 'False':
                self.key = False
            else:
                try:
                    self.key = float(self.key)
                except ValueError:
                    try:
                        self.key = int(self.key)
                    except ValueError:
                        pass
        
        self.val_id = None
        if 'val_id' in kwargs.keys():
            self.val_id = kwargs['val_id']
        
        self.val = None
        if self.val_id is not None:
            self.val = self.val = ast.Call(
                func=ast.Name(id=self.val_id, ctx=ast.Load()),
                args=[],
                keywords=[])

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Key: {}\n'.format(self.key_name)

        return desc

    def check_criteria(self) -> bool:
        if self.val_id is None:
            self.val_id = self.snippet.get_next_tbd_name()
            self.val = ast.Call(
                func=ast.Name(id=self.val_id, ctx=ast.Load()),
                args=[],
                keywords=[])
                
            DefineClass(snippet=self.snippet, lineno=self.lineno, class_name=self.val_id).apply_pattern()

        return True

    def apply_pattern(self) -> str:
        class DefineKeyTransformer(ast.NodeTransformer):
            def __init__(self, **kwargs: Any) -> None:
                self.snippet: Snippet = kwargs['snippet']
                self.lineno: int = kwargs['lineno']
                self.class_name: str = kwargs['class_name']
                self.key: Any = kwargs['key']
                self.val: ast.Module = kwargs['val']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node: ast.Module) -> ast.Module:
                class InsertKeyIntoClassTransformer(ast.NodeTransformer):
                    def __init__(self, **kwargs: dict) -> None:
                        self.snippet = kwargs['snippet']
                        self.lineno = kwargs['lineno']
                        self.class_name = kwargs['class_name']
                        self.key = kwargs['key']
                        self.val = kwargs['val']

                    def visit_ClassDef(self, node) -> ast.Module:
                        class InsertKeyIntoDictTransformer(ast.NodeTransformer):
                            def __init__(self, **kwargs: dict) -> None:
                                self.key = kwargs['key']
                                self.val = kwargs['val']

                            def visit_Assign(self, node) -> ast.Module:
                                if len(node.targets) and 'value' in dir(node.targets[0]) and 'id' in dir(node.targets[0].value) and node.targets[0].value.id == 'self' and 'attr' in dir(node.targets[0]) and node.targets[0].attr == 'container':
                                    node.value.keys.append(ast.Constant(value=self.key))
                                    node.value.values.append(self.val)
                                return node
                        
                        if self.class_name is not None:
                            if node.name == self.class_name:
                                insert_key_into_dict_transformer = InsertKeyIntoDictTransformer(key=self.key, val=self.val)
                                for idx in range(len(node.body)):
                                    node.body[idx] = insert_key_into_dict_transformer.visit(node.body[idx])
                        else:
                            if self.lineno >= node.lineno and self.lineno <= node.end_lineno:
                                insert_key_into_dict_transformer = InsertKeyIntoDictTransformer(key=self.key, val=self.val)
                                for idx in range(len(node.body)):
                                    node.body[idx] = insert_key_into_dict_transformer.visit(node.body[idx])
                        
                        return node

                insert_key_into_class_transformer = InsertKeyIntoClassTransformer(snippet=self.snippet, lineno=self.lineno, class_name=self.class_name, key=self.key, val=self.val)
                for idx in range(len(node.body)):
                    node.body[idx] = insert_key_into_class_transformer.visit(node.body[idx])

                return node

        tree = ast.parse(self.snippet.get_latest())
        tree = DefineKeyTransformer(snippet=self.snippet, lineno=self.lineno, class_name=self.class_name, key=self.key, val=self.val).visit_Body(tree)
        
        return

