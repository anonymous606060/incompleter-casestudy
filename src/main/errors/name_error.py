from typing import Tuple

from main.utils.snippet import Snippet
from main.errors.error_base_class import ErrorBaseClass
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_var import DefineVar
from main.actions.defines.define_func import DefineFunc
from main.actions.modules.add_import import AddImport

import re

class _NameError(ErrorBaseClass):
    mappings = {
        r'name \'(\S+)\' is not defined': [ AddImport, DefineFunc, DefineVar ]
    }

    def __init__(self, path: str, snippet: Snippet, stack_trace: str) -> None:
        super().__init__(path=path, snippet=snippet, stack_trace=stack_trace)

    def find_action(self) -> ActionBaseClass:
        for err_msg_pattern, action_class_list in _NameError.mappings.items():
            if m := re.search(err_msg_pattern, self.err_msg):
                for ActionClass in action_class_list:
                    kwargs = {}
                    if ActionClass == AddImport:
                        kwargs['module_name'] = m.groups()[0]
                    elif ActionClass == DefineFunc:
                        kwargs['func_name'] = m.groups()[0]
                    elif ActionClass == DefineVar:
                        kwargs['var_name'] = m.groups()[0]

                    if (action := ActionClass(snippet=self.snippet, lineno=self.lineno, **kwargs)).check_criteria():
                        return action
        
        return None