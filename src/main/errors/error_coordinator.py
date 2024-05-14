from typing import Tuple

from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass

from main.errors.error_base_class import ErrorBaseClass
from main.errors.name_error import _NameError
from main.errors.file_not_found_error import _FileNotFoundError
from main.errors.not_a_directory_error import _NotADirectoryError
from main.errors.module_not_found_error import _ModuleNotFoundError
from main.errors.import_error import _ImportError
from main.errors.attribute_error import _AttributeError
from main.errors.type_error import _TypeError
from main.errors.key_error import _KeyError
from main.errors.value_error import _ValueError

class ErrorCoordinator(ErrorBaseClass):
    mappings = {
        'NameError': _NameError,
        'FileNotFoundError': _FileNotFoundError,
        'NotADirectoryError': _NotADirectoryError,
        'ModuleNotFoundError': _ModuleNotFoundError,
        'ImportError': _ImportError,
        'AttributeError': _AttributeError,
        'TypeError': _TypeError,
        'KeyError': _KeyError,
        'ValueError': _ValueError
    }

    def __init__(self, path: str, snippet: Snippet, stack_trace: str) -> None:
        super().__init__(path=path, snippet=snippet, stack_trace=stack_trace)

        self.stack_trace_lines = self.stack_trace.split('\n')
        self.err_line = ''
        for idx, line in enumerate(self.stack_trace_lines):
            if self.err_msg in line:
                self.err_line = self.stack_trace_lines[idx-1]
                break
        self.snippet.add_to_err_history(self.err_line, self.err_type, self.err_msg)

    def find_action(self) -> ActionBaseClass:
        if self.err_type in ErrorCoordinator.mappings.keys():
            ErrorClass = ErrorCoordinator.mappings[self.err_type]
            return ErrorClass(path=self.path, snippet=self.snippet, stack_trace=self.stack_trace).find_action()
        else:
            # raise NotImplementedError('NotImplementedError: action pattern for error type {} has not been implemented yet.\n'.format(self.err_type))
            pass

        return None