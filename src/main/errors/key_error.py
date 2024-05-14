from typing import Tuple

from main.utils.snippet import Snippet
from main.errors.error_base_class import ErrorBaseClass
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_key import DefineKey

import re

class _KeyError(ErrorBaseClass):
    mappings = {
        r'(\S+)': [ DefineKey ]
    }

    def __init__(self, path: str, snippet: Snippet, stack_trace: str) -> None:
        super().__init__(path=path, snippet=snippet, stack_trace=stack_trace)

    def find_action(self) -> ActionBaseClass:
        for err_msg_pattern, action_class_list in _KeyError.mappings.items():
            if m := re.search(err_msg_pattern, self.err_msg):
                for ActionClass in action_class_list:
                    kwargs = {}
                    if ActionClass == DefineKey:
                        kwargs['key'] = m.groups()[0]

                    if (action := ActionClass(snippet=self.snippet, lineno=self.lineno, **kwargs)).check_criteria():
                        return action
        
        return None