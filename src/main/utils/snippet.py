from path_config import DATA_DIR

import os
import re
import gc
import sys
import ast
import json
import shutil
import psutil
import signal

from typing import List, Dict, Tuple, Any
from pathlib import Path

import subprocess
from subprocess import Popen, PIPE

from multiprocessing import Process, Queue
from main.utils.session import Session

class Snippet:
    TIMEOUT = 1080 #seconds
    timedout_counter = 0

    def __init__(self, snippet_path: str, snippet_dir: str, bugs=False) -> None:
        self.current_iter = 0
        self.fixpoint_tolerance = 1 #check progress with respect to (current-tolerance)th iteration. This value should be 1 for most error types. For ModuleNotFoundError, the tolerance is set to 2 (from errors.module_not_found_error) because after trying the pattern InstallModule, we want to get a second chance with the pattern RemoveImport.

        self.snippet_path: str = snippet_path
        self.snippet_name: str = snippet_path.split('/')[-1]


        if bugs:
            # If --bugs flag is set, change cwd to the directory
            self.tmp_dir = snippet_dir #"/mnt/c/Users/aramis/git/BugsInPy/framework/bin/temp1/youtube-dl"
            self.tmp_path = self.__create_tmp_path() #snippet_path #"test/snippet_check.py"
        else:
            self.tmp_path: str = self.__create_tmp_path()
            self.tmp_dir: str = '/'.join(self.tmp_path.split('/')[:-1])
        
        self.latest: int = 0
        self.history: List[str] = [ self.__place_original_start_marker(self.__clean_snippet(self.__read_snippet())) ]
        
        self.err_history: List[str] = []
        self.action_sequence: List[str] = []

        self.mocked_values: Dict[str, Any] = {}
        self.def_history: Dict[int, str] = {} # e.g. { iteration_number: defined_identifier }
        
        self.tbd_counter = 0
        self.tbd_tracker: Dict[str, str] = {} # e.g. { TBD#: identifier }

        self.preprocessed_tbds = set()

        # Since this function relies on the tbd_counter, we need to call the __replace_iterables_subscriptables_with_tbd function after defining tbd_counter
        # self.__replace_iterables_subscriptables_with_tbd()

        self.bugs = bugs

    def __read_snippet(self) -> str:
        if not Path(self.snippet_path).exists(): raise FileNotFoundError('Snippet path does not exist\nSnippet path: {}\n'.format(self.snippet_path))
        snippet_file = open(self.snippet_path, 'r')
        return snippet_file.read()

    def __clean_snippet(self, code: str) -> str:
        lines = code.split('\n')
        cleaned_lines = []

        for line in lines:
            line = re.sub(r'(?m)^ *#.*\n?', '', line) # removing lines that only have comments
            if len(line) > 0 and not line.isspace():
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def __place_original_start_marker(self, code: str) -> str:
        return '__original_start_marker = None # pragma: no cover\n' + code

    def __replace_iterables_subscriptables_with_tbd(self) ->str:
        from main.actions.action_base_class import ActionBaseClass
        from main.actions.defines.define_class import DefineClass
        from main.actions.defines.define_iterable_subscriptable import DefineIterableOrSubscriptable

        containers_tracker = {}

        class ListReplace(ast.NodeTransformer):
            def __init__(self, **kwargs: dict) -> None:
                self.snippet = kwargs['snippet']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node):
                for (idx, child) in enumerate(node.body):
                    node.body[idx] = self.visit(child)
                return node

            def visit_List(self, node):
                tbd_name = self.snippet.get_next_tbd_name()

                self.snippet.preprocessed_tbds.add(tbd_name)
                
                containers_tracker[tbd_name] = {
                    'type': 'List',
                    'elts': ast.Dict(keys=[ast.Constant(value=idx) for idx in range(len(node.elts))], values=[elt for elt in node.elts])
                }

                return ast.Call(
                    func=ast.Name(id=tbd_name, ctx=ast.Load()),
                    args=[],
                    keywords=[])

        class TupleReplace(ast.NodeTransformer):
            def __init__(self, **kwargs: dict) -> None:
                self.snippet = kwargs['snippet']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node):
                for (idx, child) in enumerate(node.body):
                    node.body[idx] = self.visit(child)
                return node

            def visit_Tuple(self, node):
                tbd_name = self.snippet.get_next_tbd_name()
                containers_tracker[tbd_name] = {
                    'type': 'Tuple',
                    'elts': ast.Tuple(elts=[elt for elt in node.elts])
                }
                
                return ast.Call(
                    func=ast.Name(id=tbd_name, ctx=ast.Load()),
                    args=[],
                    keywords=[])

        class SetReplace(ast.NodeTransformer):
            def __init__(self, **kwargs: dict) -> None:
                self.snippet = kwargs['snippet']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node):
                for (idx, child) in enumerate(node.body):
                    node.body[idx] = self.visit(child)
                return node

            def visit_Set(self, node):
                tbd_name = self.snippet.get_next_tbd_name()
                containers_tracker[tbd_name] = {
                    'type': 'Set',
                    'elts': ast.Set(elts=[elt for elt in node.elts])
                }
                
                return ast.Call(
                    func=ast.Name(id=tbd_name, ctx=ast.Load()),
                    args=[],
                    keywords=[])

        class DictReplace(ast.NodeTransformer):
            def __init__(self, **kwargs: dict) -> None:
                self.snippet = kwargs['snippet']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node):
                for (idx, child) in enumerate(node.body):
                    node.body[idx] = self.visit(child)
                return node

            def visit_Dict(self, node):
                tbd_name = self.snippet.get_next_tbd_name()

                self.snippet.preprocessed_tbds.add(tbd_name)
                
                containers_tracker[tbd_name] = {
                    'type': 'Dict',
                    'elts': ast.Dict(keys=[key for key in node.keys], values=[value for value in node.values])
                }
                
                return ast.Call(
                    func=ast.Name(id=tbd_name, ctx=ast.Load()),
                    args=[],
                    keywords=[])

        latest_code = self.get_latest()
        tree = ast.parse(latest_code)
        ListReplace(snippet=self).visit_Body(tree)

        # latest_code = self.get_latest()
        # tree = ast.parse(latest_code)
        # TupleReplace(snippet=self).visit_Body(tree)
        
        # latest_code = self.get_latest()
        # tree = ast.parse(latest_code)
        # SetReplace(snippet=self).visit_Body(tree)

        latest_code = self.get_latest()
        tree = ast.parse(latest_code)
        DictReplace(snippet=self).visit_Body(tree)

        for (tbd_name, tbd_container) in containers_tracker.items():
            DefineClass(snippet=self, class_name=tbd_name).apply_pattern()
            DefineIterableOrSubscriptable(snippet=self, class_name=tbd_name, container_values=tbd_container['elts']).apply_pattern()

        return

    # def __create_tmp_path(self) -> str:
    #     tmp_path = os.path.join(DATA_DIR, 'tmp', Session.working_dir, self.snippet_path.split('/')[-1])
    #     tmp_file = Path(tmp_path)
    #     tmp_file.parent.mkdir(parents=True, exist_ok=True)

    #     return tmp_path

    def __create_tmp_path(self) -> str:
        dir_path, filename = os.path.split(self.snippet_path)
        first_dot_index = filename.find('.') if '.' in filename else len(filename)
        new_filename = filename[:first_dot_index] + '_tmp' + filename[first_dot_index:]
        tmp_path = os.path.join(dir_path, new_filename)
        tmp_file = Path(tmp_path)
        tmp_file.parent.mkdir(parents=True, exist_ok=True)

        #empty file if it exists
        with tmp_file.open('w') as file:
            pass
        
        return tmp_path

    def __create_tmp_file(self, content=None) -> str:
        if content is None: content = self.get_latest()

        with open(self.tmp_path, 'w+') as tmp_file:
            try:
                tmp_file.write(content)
            except Exception as e:
                print('__create_tmp_file Exception: ' + e)

    def __delete_tmp_file(self) -> None:
        try:
            os.remove(self.tmp_path)
        except Exception as e:
            print('__delete_tmp_file Exception: ' + e)

    def cleanup(self) -> None:
        for file in os.listdir(self.tmp_dir):
            file_path = os.path.join(self.tmp_dir, file)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)

    def add(self, code_str) -> None:
        lines = code_str.split('\n')
        for idx in range(len(lines)):
            if '__original_start_marker' in lines[idx]:
                lines[idx] = lines[idx] + ' # pragma: no cover'

        self.history.append('\n'.join(lines))
        self.current_iter += 1

    def get_current_iter(self) -> int:
        return self.current_iter

    def get_latest(self) -> str:
        return self.history[-1]

    def get_mocked_original(self) -> str:
        all_lines = self.get_latest().split('\n')
        start_idx = 0
        for (idx, line) in enumerate(all_lines):
            if '__original_start_marker' in line:
                start_idx = idx
        return '\n'.join(all_lines[start_idx:])

    def get_next_tbd_name(self) -> str:
        tbd_name = 'TBD'+str(self.tbd_counter)
        self.tbd_counter += 1
        return tbd_name

    def is_infinite(self) -> bool:
        proc_q = Queue()
        proc = Process(target=self.run_latest, args=(proc_q, ))
        proc.start()
        proc.join(timeout=60)
        if proc.is_alive():
            # print('\nEXECUTION TIMEOUT\n')
            proc.terminate()
            return True
        else:
            return False

    def run_timed_latest(self) -> Tuple[str, str]:
        try:
            proc_q = Queue()
            proc = Process(target=self.run_latest, args=(proc_q, ))
            proc.start()
            proc.join(timeout=Snippet.TIMEOUT)
            if proc.is_alive():
                # print('\nEXECUTION TIMEOUT\n')
                Snippet.timedout_counter += 1
                proc.terminate()
                return None, None
            else:
                out = proc_q.get()
                err = proc_q.get()
                return out, err
        except Exception as e:
            print('Exception: {}'.format(e))
        
        return None, None

    def run_latest(self, proc_q) -> Tuple[str, str]:
        try:
            # setup tmp_file at tmp_path before running
            self.__create_tmp_file()
            
            # print('\nRunning: {}\n'.format(self.tmp_path))
            proc = Popen([sys.executable, self.tmp_path], stdout=PIPE, stderr=PIPE, cwd=self.tmp_dir)
            proc.wait()
            out, err = proc.communicate()
            out = out.decode('ISO-8859-1')
            err = err.decode('ISO-8859-1')

            # cleanup tmp_file at tmp_path after running
            self.__delete_tmp_file()

            proc_q.put(out)
            proc_q.put(err)
            
            return out, err
        except FileNotFoundError as e:
            print('FileNotFoundError: when trying to run snippet {}#{}\n'.format(self.snippet_path, str(self.latest)))
            proc_q.put(None)
            proc_q.put(None)
            return None, None

    def compute_timed_latest_coverage(self) -> Tuple[float, float]:
        try:
            os.environ['TBD#'] = str(self.tbd_counter)

            proc_q = Queue()
            proc = Process(target=self.compute_latest_coverage, args=(proc_q, ))
            proc.daemon = False
            proc.start()
            proc.join(timeout=Snippet.TIMEOUT)
            if proc.is_alive():
                # print('\nCOVERAGE EXECUTION TIMEOUT\n')
                proc.terminate()
                return None, None, None, None
            else:
                out = proc_q.get()
                err = proc_q.get()
                stmt_cov = proc_q.get()
                br_cov = proc_q.get()

                gc.collect()
                return out, err, stmt_cov, br_cov
        except Exception as e:
            print('Exception: {}'.format(e))
        finally:
            gc.collect()
        
        gc.collect()
        return None, None, None, None

    def compute_latest_coverage(self, proc_q) -> Tuple[float, float]:
        latest_code = self.get_latest()
        latest_code_lines = latest_code.split('\n')

        # Preparing latest code snippet to exclude mock parts of the code from coverage measurement
        for idx in range(len(latest_code_lines)):
            if '__original_start_marker' in latest_code_lines[idx]:
                break
            latest_code_lines[idx] += ' # pragma: no cover'
        latest_code = '\n'.join(latest_code_lines)

        try:
            # setup tmp_file at tmp_path before running
            self.__create_tmp_file(content=latest_code)

            proc = Popen(['coverage', 'run', '--branch', self.tmp_path], stdout=PIPE, stderr=PIPE, cwd=self.tmp_dir)
            out, err = proc.communicate()

            proc = Popen(['coverage', 'json'], stdout=PIPE, stderr=PIPE, cwd=self.tmp_dir)
            proc.communicate()
            
            stmt_cov, br_cov = None, None
            if os.path.exists(os.path.join(self.tmp_dir, 'coverage.json')):
                cov_json = json.load(open(os.path.join(self.tmp_dir, 'coverage.json')))
                if cov_json['totals']['percent_covered'] is not None:
                    stmt_cov = cov_json['totals']['percent_covered']/100
                
                if cov_json['totals']['covered_branches'] is not None and cov_json['totals']['num_branches'] is not None:
                    if cov_json['totals']['num_branches'] == 0:
                        br_cov = 1.0
                    else:
                        br_cov = cov_json['totals']['covered_branches']/cov_json['totals']['num_branches']

            # print('\nStmt cov: {}, Br cov: {}'.format(str(stmt_cov), str(br_cov)))

            # cleanup tmp_file at tmp_path after running
            # self.__delete_tmp_file()

            proc_q.put(out.decode('ISO-8859-1'))
            proc_q.put(err.decode('ISO-8859-1'))
            proc_q.put(stmt_cov)
            proc_q.put(br_cov)
            return 0
        except FileNotFoundError as e:
            print('FileNotFoundError: when trying to compute coverage for snippet {}#{}\n'.format(self.snippet_path, str(self.latest)))
            
        proc_q.put(None)
        proc_q.put(None)
        proc_q.put(None)
        proc_q.put(None)
        return -1

    def __kill_child_processes(self, pid):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                process.send_signal(signal.SIGTERM)
        except psutil.NoSuchProcess:
            return

    def add_to_err_history(self, err_line, err_type, err_msg):
        self.err_history.append(err_type + ': ' + err_msg + '~' + err_line)

    def has_progress(self):
        if len(self.err_history) > self.fixpoint_tolerance:
            if self.err_history[-1] == self.err_history[-self.fixpoint_tolerance-1]:
                return False
        return True

    def add_to_action_sequence(self, action_class_name):
        self.action_sequence.append(action_class_name)

    def register_mock_definition(self, iter_n: int, target: str, value: Any) -> None:
        self.def_history[iter_n] = target
        self.mocked_values[target] = value
        
        self.tbd_tracker[value] = target

    def get_mocked_value(self, target: str) -> Any:
        return self.mocked_values[target]
    