from abc import ABC, abstractmethod
from pathlib import Path
import ast

from main.utils.snippet import Snippet

class ActionBaseClass(ABC):
    def __init__(self, snippet: Snippet=None, lineno: int=0) -> None:
        self.snippet = snippet
        self.lineno: int = lineno

    def __str__(self) -> str:
        desc = 'Exception Causing Line No.: {}\n'.format(str(self.lineno))
        return desc

    @abstractmethod
    def check_criteria(self) -> bool:
        pass

    @abstractmethod
    def apply_pattern(self) -> str:
        pass

    @staticmethod
    def add_to_history(visit_method):
        def wrapper(self, *args, **kwargs):
            rewritten_tree = visit_method(self, *args, **kwargs)
            rewritten_snippet = ast.unparse(ast.fix_missing_locations(rewritten_tree))
            self.snippet.add(rewritten_snippet)
        return wrapper
            