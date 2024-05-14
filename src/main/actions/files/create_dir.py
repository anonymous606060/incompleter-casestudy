from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from typing import Any
import os
import ast
import time

from pathlib import Path

class CreateDir(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.dir_name = kwargs['dir_name']

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Dir name: {}'.format(self.dir_name)

        return desc

    def check_criteria(self) -> bool:
        return True

    def apply_pattern(self) -> str:
        try:
            # Remove any file with the same name as self.dir_name in case a file had already been created for tolerance==1
            if os.path.exists(os.path.join(self.snippet.tmp_dir, self.dir_name)):
                os.remove(os.path.join(self.snippet.tmp_dir, self.dir_name))

            # Create file with all intermediate directories
            if self.dir_name.startswith('/'):
                os.makedirs(self.dir_name, exist_ok=True)
            else:
                file_to_create = Path(os.path.join(self.snippet.tmp_dir, self.dir_name))
                file_to_create.parent.mkdir(exist_ok=True, parents=True)
                
                os.makedirs(os.path.join(self.snippet.tmp_dir, self.dir_name), exist_ok=True)
        except OSError as e:
            print('\nOSError: {}\n'.format(e))
        except Exception as e:
            print('\nException: {}\n'.format(e))

        tree = ast.parse(self.snippet.get_latest())
        return ast.unparse(ast.fix_missing_locations(tree))