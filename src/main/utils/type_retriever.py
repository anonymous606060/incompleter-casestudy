import os
import ast
import glob
import pprint
pp = pprint.PrettyPrinter(depth=4)

os.environ["TOKENIZERS_PARALLELISM"] = "false" # To avoid deadlocks due to forks/parallelism

import numpy as np
from numpy import dot
from numpy.linalg import norm

from transformers import AutoTokenizer, AutoModel
import torch

from path_config import DATA_DIR
from main.utils.unixcoder import UniXcoder

def get_embeddings(code):
    global tokenizer, model

    # uniXcoder
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = UniXcoder("microsoft/unixcoder-base")
    tokens_ids = model.tokenize([code], max_length=128, mode="<encoder-only>")
    source_ids = torch.tensor(tokens_ids).to(device)
    tokens_embeddings, embeddings = model(source_ids)

    return embeddings.detach()

def find_similar(target_embeddings):
    global all_refs
    all_sim = {}

    for (ref_class, ref_embeddings) in all_refs.items():
        cos_sim = dot(target_embeddings, ref_embeddings.T)/(norm(target_embeddings)*norm(ref_embeddings.T))
        all_sim[ref_class] = cos_sim

    return all_sim

def keep_common():
    global all_refs, all_targets
    global all_ref_funcs, all_target_funcs
    for ref_class_name in list(all_refs.keys()):
        if ref_class_name in all_ref_funcs.keys():
            ref_func_set = all_ref_funcs[ref_class_name]
            for (target_class_name, target_func_set) in all_target_funcs.items():
                if len(ref_func_set.intersection(target_func_set)) > 0:
                    break
        else:
            all_refs.pop(ref_class_name)

def cache_embeddings():
    global all_refs, all_targets
    for ref_class_name in list(all_ref_funcs.keys()):
        all_refs[ref_class_name] = get_embeddings(all_refs[ref_class_name])
    for target_class_name in list(all_target_funcs.keys()):
        all_targets[target_class_name] = get_embeddings(all_targets[target_class_name])

global all_relevant_funcs
global all_refs, all_targets
global all_ref_funcs, all_target_funcs
class RefClassFinder(ast.NodeTransformer):
    def __init__(self):
        pass

    def visit_ClassDef(self, node):
        global all_refs
        
        new_body = []
        for child in node.body:
            new_child = RefFuncFinder(class_name=node.name).visit(child)
            if new_child is not None:
                new_body.append(new_child)
        node.body = new_body

        new_class_body = ast.unparse(ast.fix_missing_locations(node))
        new_class_lines = len(new_class_body.split('\n'))
        if new_class_lines > 1:
            all_refs[node.name] = new_class_body
        return node

class RefFuncFinder(ast.NodeTransformer):
    def __init__(self, **kwargs):
        self.class_name = kwargs['class_name']

    def visit_FunctionDef(self, node):
        global all_ref_funcs
        if not node.name.startswith('__') and node.name in all_relevant_funcs:
            if not self.class_name in all_ref_funcs.keys():
                all_ref_funcs[self.class_name] = set()
            all_ref_funcs[self.class_name].add(node.name)
            return node
        return None

class TargetClassFinder(ast.NodeTransformer):
    def __init__(self):
        pass

    def visit_ClassDef(self, node):
        global all_targets

        new_body = []
        for child in node.body:
            new_child = TargetFuncFinder(class_name=node.name).visit(child)
            if new_child is not None:
                new_body.append(new_child)
        node.body = new_body

        new_class_body = ast.unparse(ast.fix_missing_locations(node))
        new_class_lines = len(new_class_body.split('\n'))
        if new_class_lines > 1:
            all_targets[node.name] = new_class_body
        return node

class TargetFuncFinder(ast.NodeTransformer):
    def __init__(self, **kwargs):
        self.class_name = kwargs['class_name']

    def visit_FunctionDef(self, node):
        global all_target_funcs
        if not node.name.startswith('__'):
            if not self.class_name in all_target_funcs.keys():
                all_target_funcs[self.class_name] = set()
            all_target_funcs[self.class_name].add(node.name)
            all_relevant_funcs.append(node.name)
            return node
        return None

target_src = """
class TBD6:

    def __init__(self, *args, **kwargs):
        pass

class TBD5:

    def __init__(self, *args, **kwargs):
        pass

class TBD4:

    def __init__(self, *args, **kwargs):
        pass

    def transform(self, arg0):
        return TBD5()

class TBD3:

    def __init__(self):
        self.container = {'count': TBD4()}
        self.keys = list(self.container.keys())
        self.iter_current = 0

    def __refresh_keys(self):
        self.keys = list(self.container.keys())
        for key in self.keys:
            if not isinstance(key, int):
                return
        sorted(self.keys)

    def __str__(self):
        self.__refresh_keys()
        ret_str = ''
        ret_str += '[ '
        for idx, (key, val) in enumerate(self.container.items()):
            ret_str += str(val)
            if idx < len(self.keys) - 1:
                ret_str += ', '
        ret_str += ' ]'
        return ret_str

    def __getitem__(self, key):
        self.__refresh_keys()
        ret_val = None
        if isinstance(key, slice):
            list_to_return = []
            start = key.start or 0
            stop = key.stop or len(self.container)
            step = key.step or 1
            if start < 0:
                start = self.keys[start]
            if stop < 0:
                stop = self.keys[stop]
            for i in range(start, stop, step):
                list_to_return.append(self.container[i])
            ret_val = list_to_return
        elif isinstance(key, int):
            if key < 0:
                key = self.keys[key]
            ret_val = self.container[key]
        elif isinstance(key, str):
            ret_val = self.container[key]
        return ret_val

    def __setitem__(self, key, val):
        self.__refresh_keys()
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop or len(self.container)
            step = key.step or 1
            if start < 0:
                start = self.keys[start]
            if stop < 0:
                stop = self.keys[stop]
            for i in range(0, stop, step):
                if i not in self.keys:
                    self.container[i] = 0
            for i in range(start, stop, step):
                self.container[i] = val
            return True
        elif isinstance(key, int):
            if key < 0:
                key = self.keys[key]
            for i in range(0, key):
                if i not in self.keys:
                    self.container[i] = 0
            self.container[key] = val
            return True
        elif isinstance(key, str):
            self.container[key] = val
            return True
        self.__refresh_keys()
        return False

    def __iter__(self):
        return iter(self.container)

    def __len__(self):
        return len(self.keys)

class TBD2:

    def __init__(self, *args, **kwargs):
        pass

class TBD1:

    def __init__(self):
        self.container = {'count': TBD2(), False: TBD6()}
        self.keys = list(self.container.keys())
        self.iter_current = 0

    def __refresh_keys(self):
        self.keys = list(self.container.keys())
        for key in self.keys:
            if not isinstance(key, int):
                return
        sorted(self.keys)

    def __str__(self):
        self.__refresh_keys()
        ret_str = ''
        ret_str += '[ '
        for idx, (key, val) in enumerate(self.container.items()):
            ret_str += str(val)
            if idx < len(self.keys) - 1:
                ret_str += ', '
        ret_str += ' ]'
        return ret_str

    def __getitem__(self, key):
        self.__refresh_keys()
        ret_val = None
        if isinstance(key, slice):
            list_to_return = []
            start = key.start or 0
            stop = key.stop or len(self.container)
            step = key.step or 1
            if start < 0:
                start = self.keys[start]
            if stop < 0:
                stop = self.keys[stop]
            for i in range(start, stop, step):
                list_to_return.append(self.container[i])
            ret_val = list_to_return
        elif isinstance(key, int):
            if key < 0:
                key = self.keys[key]
            ret_val = self.container[key]
        elif isinstance(key, str):
            ret_val = self.container[key]
        return ret_val

    def __setitem__(self, key, val):
        self.__refresh_keys()
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop or len(self.container)
            step = key.step or 1
            if start < 0:
                start = self.keys[start]
            if stop < 0:
                stop = self.keys[stop]
            for i in range(0, stop, step):
                if i not in self.keys:
                    self.container[i] = 0
            for i in range(start, stop, step):
                self.container[i] = val
            return True
        elif isinstance(key, int):
            if key < 0:
                key = self.keys[key]
            for i in range(0, key):
                if i not in self.keys:
                    self.container[i] = 0
            self.container[key] = val
            return True
        elif isinstance(key, str):
            self.container[key] = val
            return True
        self.__refresh_keys()
        return False

    def __iter__(self):
        return iter(self.container)

    def __len__(self):
        return len(self.keys)

    def groupby(self, arg0):
        return TBD3()
df = TBD1()

class TBD0:

    def __init__(self):
        self.container = {0: 'Mt'}
        self.keys = list(self.container.keys())
        self.iter_current = 0

    def __refresh_keys(self):
        self.keys = list(self.container.keys())
        for key in self.keys:
            if not isinstance(key, int):
                return
        sorted(self.keys)

    def __str__(self):
        self.__refresh_keys()
        ret_str = ''
        ret_str += '[ '
        for idx, (key, val) in enumerate(self.container.items()):
            ret_str += str(val)
            if idx < len(self.keys) - 1:
                ret_str += ', '
        ret_str += ' ]'
        return ret_str

    def __getitem__(self, key):
        self.__refresh_keys()
        ret_val = None
        if isinstance(key, slice):
            list_to_return = []
            start = key.start or 0
            stop = key.stop or len(self.container)
            step = key.step or 1
            if start < 0:
                start = self.keys[start]
            if stop < 0:
                stop = self.keys[stop]
            for i in range(start, stop, step):
                list_to_return.append(self.container[i])
            ret_val = list_to_return
        elif isinstance(key, int):
            if key < 0:
                key = self.keys[key]
            ret_val = self.container[key]
        elif isinstance(key, str):
            ret_val = self.container[key]
        return ret_val

    def __setitem__(self, key, val):
        self.__refresh_keys()
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop or len(self.container)
            step = key.step or 1
            if start < 0:
                start = self.keys[start]
            if stop < 0:
                stop = self.keys[stop]
            for i in range(0, stop, step):
                if i not in self.keys:
                    self.container[i] = 0
            for i in range(start, stop, step):
                self.container[i] = val
            return True
        elif isinstance(key, int):
            if key < 0:
                key = self.keys[key]
            for i in range(0, key):
                if i not in self.keys:
                    self.container[i] = 0
            self.container[key] = val
            return True
        elif isinstance(key, str):
            self.container[key] = val
            return True
        self.__refresh_keys()
        return False

    def __iter__(self):
        return iter(self.container)

    def __len__(self):
        return len(self.keys)
__original_start_marker = None # pragma: no cover
df[df['count'] == df.groupby(TBD0())['count'].transform(max)]
"""

if __name__ == "__main__":
    global all_relevant_funcs
    global all_refs, all_targets
    global all_ref_funcs, all_target_funcs
    all_relevant_funcs = []
    all_refs = {}
    all_targets = {}
    all_ref_funcs = {}
    all_target_funcs = {}

    tree = ast.parse(target_src)
    TargetClassFinder().visit(tree)
    
    for package in os.scandir(os.path.join(DATA_DIR, 'package_meta/ref_packages/')):
        if package.is_dir():
            for py_file in glob.glob(os.path.join(package.path, '**/*.py'), recursive=True):
                with open(py_file, 'r') as py_file_code:
                    ref_src = py_file_code.read()
                    tree = ast.parse(ref_src)
                    RefClassFinder().visit(tree)

    keep_common()
    cache_embeddings()

    # pp.pprint(all_ref_funcs)
    # pp.pprint(all_target_funcs)

    for (target_class, target_embeddings) in all_targets.items():
        all_sim = find_similar(target_embeddings)
        print('Target class: {}\n'.format(target_class))
        pp.pprint(all_sim)