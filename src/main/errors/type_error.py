from typing import Tuple

from main.utils.snippet import Snippet
from main.errors.error_base_class import ErrorBaseClass
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_callable import DefineCallable
from main.actions.defines.define_iterable_subscriptable import DefineIterableOrSubscriptable
from main.actions.defines.define_operator import DefineOperator
from main.actions.defines.define_str import DefineString
from main.actions.defines.define_int import DefineInteger
from main.actions.defines.define_length import DefineLength

import re
import ast
from enum import Enum

class _TypeError(ErrorBaseClass):
    mappings = {
        r'\'(\S+)\' object cannot be interpreted as an integer': [ DefineInteger ],
        r'.*(?:expected|should be|must be|can only concatenate).*(?:str|string).*(?:not|got)\s[\'\"]?([^\'\"]+)[\'\"]?.*': [ DefineString ],
        r'object of type \'?([^\']+)\'? has no len()': [ DefineLength ],
        r'\'(\S+)\' object is not callable': [ DefineCallable ],
        r'.*\'(\S+)\'.*not.*(mapping|iterable|subscriptable|support item assignment)': [ DefineIterableOrSubscriptable ],
        r'(?:unsupported operand type\(s\) for |bad operand type for unary )?\'?([^\']+)\'?(?:\:| not supported between instances of) \'(\S+)\'(?: and \'(\S+)\')?': [ DefineOperator ],
    }

    def __init__(self, path: str, snippet: Snippet, stack_trace: str) -> None:
        super().__init__(path=path, snippet=snippet, stack_trace=stack_trace)

    def find_action(self) -> ActionBaseClass:
        for err_msg_pattern, action_class_list in _TypeError.mappings.items():
            if m := re.search(err_msg_pattern, self.err_msg):
                # print('Matched pattern: {}\n'.format(err_msg_pattern))
                # print(self.snippet.get_latest().split('\n')[self.lineno+1])

                kwargs = {}
                if err_msg_pattern in [ r'\'(\S+)\' object is not callable', r'.*\'(\S+)\'.*not.*(mapping|iterable|subscriptable|support item assignment)', r'object of type \'?([^\']+)\'? has no len()' ]:
                    kwargs['class_name'] = m.groups()[0]
                elif err_msg_pattern in [ r'(?:unsupported operand type\(s\) for |bad operand type for unary )?\'?([^\']+)\'?(?:\:| not supported between instances of) \'(\S+)\'(?: and \'(\S+)\')?' ]:
                    kwargs['operator'] = m.groups()[0]
                    kwargs['class1'] = m.groups()[1]
                    if len(m.groups()) > 2:
                        kwargs['class2'] = m.groups()[2]
                elif err_msg_pattern in [ r'.*(?:expected|should be|must be|can only concatenate).*(?:str|string).*(?:not|got)\s[\'\"]?([^\'\"]+)[\'\"]?.*', r'\'(\S+)\' object cannot be interpreted as an integer' ]:
                    kwargs['class_name'] = m.groups()[-1]
                
                for ActionClass in action_class_list:
                    if (action := ActionClass(snippet=self.snippet, lineno=self.lineno, **kwargs)).check_criteria():
                        return action
        
        return None