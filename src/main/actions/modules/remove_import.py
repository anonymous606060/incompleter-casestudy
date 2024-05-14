from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from typing import Any
import ast
import sys

class RemoveImport(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        if 'module_name' in kwargs.keys():
            self.module_name = kwargs['module_name']

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Module name: {}\n'.format(self.module_name)

        return desc

    def check_criteria(self) -> bool:
        return True

    @ActionBaseClass.add_to_history
    def apply_pattern(self) -> str:
        # Remove a particular module import statement so that the module itself can be mocked inside the snippet
        latest_code = self.snippet.get_latest().split('\n')
        latest_code[self.lineno-1] = '# {}'.format(latest_code[self.lineno-1])
        latest_code = '\n'.join(latest_code)

        return ast.parse(latest_code)
