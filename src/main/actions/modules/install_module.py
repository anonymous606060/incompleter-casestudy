from path_config import DATA_DIR
from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from typing import Any

from subprocess import Popen, DEVNULL
import os
import sys
import ast
import pickle

class InstallModule(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.module_name = kwargs['module_name']
        self.package_list = self.__get_popular_package_list()

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Module name: {}\n'.format(self.module_name)

        return desc

    def __get_popular_package_list(self) -> dict:
        with open(os.path.join(DATA_DIR, 'package_meta/popular_packages_list.pickle'), 'rb') as package_list_pickle:
            if package_list := pickle.load(package_list_pickle):
                return package_list
        return None

    def check_criteria(self) -> bool:
        # if self.package_list is not None:
        #     if self.module_name in self.package_list:
        #         return True
        # return False
        progress = False
        if self.snippet.fixpoint_tolerance == 1:
            progress = self.snippet.has_progress() # this should always be True (first attempt at applying InstallModule pattern)
            self.snippet.fixpoint_tolerance = 2    # setting 2 so that for a ModuleNotFoundError, we get a second chance to try RemoveImport. In the second try, InstallModule pattern's check_criteria will return False by comparing if we still have the exactly same ModuleNotFoundError message.
        else:
            self.snippet.fixpoint_tolerance = 1    # setting 1 when we have already tried InstallModule pattern and we get ModuleNotFoundError for the second time. This time, we set the tolerance to 1 and let RemoveImport take over.
            progress = self.snippet.has_progress() # this should always be False (second attempt should not apply InstallModule again since it did not work the first time. RemoveImport pattern should be applied.)

        return progress

    def apply_pattern(self) -> str:
        if 'sklearn' in self.module_name:
            self.module_name = 'scikit-learn'

        installer = Popen([sys.executable, '-m', 'pip', 'install', self.module_name], stdout=DEVNULL, stderr=DEVNULL)
        installer.wait()

        tree = ast.parse(self.snippet.get_latest())
        return ast.unparse(ast.fix_missing_locations(tree))

