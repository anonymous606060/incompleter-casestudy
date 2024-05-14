from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from typing import Any
import ast

class DefineClass(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.class_name = kwargs['class_name']

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Class name: {}\n'.format(self.var_name)

        return desc

    def check_criteria(self) -> bool:
        return True

    def apply_pattern(self) -> str:
        class DefineClassTransformer(ast.NodeTransformer):
            def __init__(self, **kwargs: Any) -> None:
                self.snippet: Snippet = kwargs['snippet']
                self.lineno: int = kwargs['lineno']
                self.class_name: str = kwargs['class_name']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node: ast.Module) -> ast.Module:
                node.body.insert(0, ast.ClassDef(
                        name=self.class_name,
                        bases=[],
                        keywords=[],
                        body=[
                            ast.FunctionDef(
                                name='__init__',
                                args=ast.arguments(
                                    posonlyargs=[],
                                    args=[
                                        ast.arg(arg='self')
                                    ],
                                    vararg=ast.arg(arg='args'),
                                    kwarg=ast.arg(arg='kwargs'),
                                    kwonlyargs=[],
                                    kw_defaults=[],
                                    defaults=[]),
                                body=[
                                    ast.Pass()],
                                decorator_list=[])
                        ],
                        decorator_list=[]
                    )
                )
                
                return node

        tree = ast.parse(self.snippet.get_latest())
        DefineClassTransformer(snippet=self.snippet, lineno=self.lineno, class_name=self.class_name).visit_Body(tree)

        self.snippet.register_mock_definition(iter_n=self.snippet.get_current_iter(), target=self.class_name, value='class')
        
        return

