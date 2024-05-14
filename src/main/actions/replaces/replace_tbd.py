from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_class import DefineClass
from typing import Any
import ast
from enum import Enum

class ReplaceTBD(ActionBaseClass):
    class TO_ENUMS(Enum):
        ITERABLE = 0
        SUBSCRIPTABLE = 1

    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.from_val = kwargs['from_val']
        self.to_val = kwargs['to_val']

        # if self.to_val == ReplaceTBD.TO_ENUMS.ITERABLE:
        #     self.to_val = ast.BinOp(
        #         left=ast.List(
        #             elts=[
        #                 ast.Call(
        #                     func=ast.Name(id=self.from_val, ctx=ast.Load()),
        #                     args=[],
        #                     keywords=[])
        #                 ],
        #             ctx=ast.Load()),
        #         op=ast.Mult(),
        #         right=ast.Constant(value=100)
        #     )

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'TBD ID: {}\nTo value: {}\n'.format(self.tbd_id, self.to_val)

        return desc

    def check_criteria(self) -> bool:
        if self.from_val is not None and 'TBD' in self.from_val:
            return True
        return False

    def apply_pattern(self) -> str:
        class ReplaceTBDTransformer(ast.NodeTransformer):
            def __init__(self, **kwargs: Any) -> None:
                self.snippet: Snippet = kwargs['snippet']
                self.lineno: int = kwargs['lineno']
                self.from_val: str = kwargs['from_val']
                self.to_val: str = kwargs['to_val']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node: ast.Module) -> ast.Module:
                class ReplaceTBDCallTransformer(ast.NodeTransformer):
                    def __init__(self, **kwargs: dict) -> None:
                        self.snippet: Snippet = kwargs['snippet']
                        self.lineno: int = kwargs['lineno']
                        self.from_val: str = kwargs['from_val']
                        self.to_val: str = kwargs['to_val']

                    def visit_Call(self, node: ast.Module) -> ast.Module:
                        if (type(node.func) == ast.Name) and (self.from_val in node.func.id):
                            return self.to_val
                        return node
                        
                for child in node.body:
                    child = ReplaceTBDCallTransformer(snippet=self.snippet, lineno=self.lineno, from_val=self.from_val, to_val=self.to_val).visit(child)

                return node
                

        tree = ast.parse(self.snippet.get_latest())
        tree = ReplaceTBDTransformer(snippet=self.snippet, lineno=self.lineno, from_val=self.from_val, to_val=self.to_val).visit_Body(tree)

        return

