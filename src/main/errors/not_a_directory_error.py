from typing import Tuple

from path_config import DATA_DIR
from main.utils.snippet import Snippet
from main.errors.error_base_class import ErrorBaseClass
from main.actions.action_base_class import ActionBaseClass
from main.actions.files.create_dir import CreateDir

import re
import os

class _NotADirectoryError(ErrorBaseClass):
    mappings = {
        r'\[Errno 20\] Not a directory: \'?(\S+)\'?': [ CreateDir ]
    }

    def __init__(self, path: str, snippet: Snippet, stack_trace: str) -> None:
        super().__init__(path=path, snippet=snippet, stack_trace=stack_trace)

    def find_action(self) -> ActionBaseClass:
        for err_msg_pattern, action_class_list in _NotADirectoryError.mappings.items():
            if m := re.search(err_msg_pattern, self.err_msg):
                for ActionClass in action_class_list:
                    kwargs = {}
                    if ActionClass == CreateDir:
                        dir_name = m.groups()[0]
                        kwargs['dir_name'] = dir_name

                    if (action := ActionClass(snippet=self.snippet, lineno=self.lineno, **kwargs)).check_criteria():
                        return action
        
        return None