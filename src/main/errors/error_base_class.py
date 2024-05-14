from abc import ABC, abstractmethod
from typing import Tuple
import re

from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass

class ErrorBaseClass(ABC):
    def __init__(self, path: str, snippet: Snippet, stack_trace: str) -> None:
        if len(stack_trace) == 0: raise ValueError('Unable to instantiate Error object for empty stack trace')

        self.path = path
        self.snippet = snippet
        self.stack_trace = stack_trace
        
        self.lineno = self.__extract_lineno()
        self.err_type = self.__extract_type()
        self.err_msg = self.__extract_msg()

    def __reformat_snippet_name(self):
        snippet_name = self.path.split('/')[-1]
        return snippet_name.replace('.', '\.')

    def __extract_lineno(self) -> int:
        snippet_name = self.__reformat_snippet_name()
        lineno = -1
        if matches := re.finditer(r'File ".*?/{}", line (\d+)'.format(snippet_name), self.stack_trace):
            matches_list = list(matches)
            if len(matches_list):
                last_match = matches_list[-1]
                lineno = int(last_match.groups()[0])
        
        # if lineno == -1: raise ValueError('Unable to extract error line number from:\n\n{}\n'.format(self.stack_trace))

        return lineno

    def __extract_type(self) -> str:
        err_type = ''
        for line in self.stack_trace.split('\n'):
            if 'Error:' in line:
                err_type = line.split(':')[0]
        
        # if err_type == '': raise ValueError('Unable to extract error type from:\n\n{}\n'.format(self.stack_trace))

        return err_type.strip()

    def __extract_msg(self) -> str:
        err_msg = ''
        for line in self.stack_trace.split('\n'):
            if 'Error:' in line:
                err_msg = ':'.join(line.split(':')[1:])
        
        # if err_msg == '': raise ValueError('Unable to extract error message from:\n\n{}\n'.format(self.stack_trace))

        return err_msg.strip()

    @abstractmethod
    def find_action(self) -> ActionBaseClass:
        pass
