from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_func import DefineFunc
from typing import Any
import ast

class DefineLength(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.class_name = kwargs['class_name']

    def __str__(self) -> str:
        desc = super().__str__()
        desc += '\nImplementing __len__ for class: {}'.format(self.class_name)

        return desc

    def check_criteria(self) -> bool:
        return True

    def apply_pattern(self) -> str:
        kwargs = {
            'func_name': '__len__',
            'class_scope': self.class_name,
            'func_level': 'instance',
            'override_criteria': True       # for ensuring that a TBD return object is returned
        }
        
        define_length_action = DefineFunc(snippet=self.snippet, lineno=self.lineno, **kwargs)
        define_length_action.check_criteria()
        define_length_action.apply_pattern()