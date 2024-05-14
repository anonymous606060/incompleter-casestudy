from path_config import DATA_DIR
from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from typing import Any
import ast
import os
import pickle

class AddImport(ActionBaseClass):
    STDLIBS = [ '__future__', '__main__', '_thread', '_tkinter', 'abc', 'aifc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'doctest', 'email', 'encodings', 'ensurepip', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt', 'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'sitecustomize', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'tomllib', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'usercustomize', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', 'zoneinfo' ]

    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.module_name = kwargs['module_name']
        self.package_list = self.__get_popular_package_list()
        self.import_dict = self.__get_local_package_index()

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Module name: {}\n'.format(self.module_name)

        return desc

    def __get_popular_package_list(self) -> dict:
        with open(os.path.join(DATA_DIR, 'package_meta/popular_packages_list.pickle'), 'rb') as package_list_pickle:
            if package_list := pickle.load(package_list_pickle):
                return package_list
        return None

    def __get_local_package_index(self) -> dict:
        with open(os.path.join(DATA_DIR, 'package_meta/import_dict.pickle'), 'rb') as import_dict_pickle:
            if import_dict := pickle.load(import_dict_pickle):
                return import_dict
        return None

    def check_criteria(self) -> bool:
        if self.module_name in AddImport.STDLIBS:
            if self.module_name not in self.import_dict.keys():
                self.import_dict[self.module_name] = ast.Import(names=[ast.alias(name=self.module_name)])
            return True
        else:
            if self.import_dict is None:
                return False

            # Add import for a module only if it is in the top pypi packages list
            if self.module_name in self.import_dict.keys():
                import_ast = self.import_dict[self.module_name]
                if 'names' in dir(import_ast):
                    for alias in import_ast.names:
                        if alias.name in self.package_list:
                            return True
                        elif alias.name.split('.')[0] in self.package_list:
                            return True

            # If self.module_name is directly not present in the import_dict keys, check if the alias name of the corresponding ast of the entry is the self.module_name
            for module, import_ast in self.import_dict.items():
                if 'names' in dir(import_ast):
                    for alias in import_ast.names:
                        if alias.name == self.module_name and alias.name in self.package_list:
                            self.import_dict[self.module_name] = ast.Import(
                                                                    names = [
                                                                        ast.alias(name=self.module_name)
                                                                    ]
                                                                )
                            return True

        return False

    def apply_pattern(self) -> str:
        class AddImportTransformer(ast.NodeTransformer):
            def __init__(self, **kwargs: Any) -> None:
                self.snippet: Snippet = kwargs['snippet']
                self.lineno: int = kwargs['lineno']
                self.module_name: str = kwargs['module_name']
                self.import_dict: dict = kwargs['import_dict']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node: ast.Module) -> ast.Module:
                node.body.insert(0, self.import_dict[self.module_name])

                return node

        tree = ast.parse(self.snippet.get_latest())
        AddImportTransformer(snippet=self.snippet, lineno=self.lineno, module_name=self.module_name, import_dict=self.import_dict).visit_Body(tree)