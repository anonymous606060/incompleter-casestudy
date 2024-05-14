import ast
import astunparse
from main.utils.snippet import Snippet
from main.errors.error_coordinator import ErrorCoordinator
import json
import os
import re

# Infers the type of a class based on several deductions
class TypeInferrer(ast.NodeVisitor):
    def __init__(self):
        self.unroll_dict = {}
        self.current_class = None
        self.class_methods = {}
        self.class_attributes = {}
        self.class_container_init = {}

    def visit_ClassDef(self, node):
        self.current_class = node.name
        # self.unroll_dict[node.name] = {'deductions': [], 'type': 'unknown'}
        base_classes = [base.id for base in node.bases if isinstance(base, ast.Name)] 
        self.unroll_dict[node.name] = {
            'deductions': [],
            'type': 'unknown',
            'base_classes': base_classes
        }
        self.class_methods[node.name] = []
        self.class_attributes[node.name] = {}
        self.generic_visit(node)
        self.infer_class_type(node.name)
        self.current_class = None

    def visit_FunctionDef(self, node):
        if self.current_class:
            self.class_methods[self.current_class].append(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if self.current_class and isinstance(node.targets[0], ast.Attribute) and \
           isinstance(node.targets[0].value, ast.Name) and \
           node.targets[0].value.id == 'self' and node.targets[0].attr == 'container':
            self.class_container_init[self.current_class] = node.value
            
    def is_primitive(self, class_name):
        deductions = self.unroll_dict[class_name]['deductions']
        base_classes = self.unroll_dict[class_name].get('base_classes', [])

        # Check for direct inheritance from primitive types
        if 'int' in base_classes:
            deductions.append(f'{class_name} subclasses int')
            self.unroll_dict[class_name]['type'] = 'int'
        elif 'str' in base_classes:
            deductions.append(f'{class_name} subclasses str')
            self.unroll_dict[class_name]['type'] = 'str'

    def mock_container_keys(self, class_name):
        container_node = self.class_container_init.get(class_name, None)
        if container_node and isinstance(container_node, ast.Dict):
            # Extract keys from the dictionary assignment
            keys = [key.value for key in container_node.keys if isinstance(key, ast.Constant)]
            return keys
        return None

    def is_collection(self, class_name):
        essential_methods = ['__init__', '__iter__', '__len__', '__getitem__', '__setitem__']
        methods = self.class_methods[class_name]
        deductions = self.unroll_dict[class_name]['deductions']

        # Check if essential methods are implemented
        # if not all(method in methods for method in essential_methods):
        #     return

        # Retrieve the keys from the 'container' attribute, if it exists
        container_keys = self.mock_container_keys(class_name)

        # Check if any unique methods are implemented
        if any(method in methods for method in ['append', 'extend', 'insert', 'remove', 'index', 'count', 'sort', 'reverse']):
            deductions.append('implements list-specific methods')
            self.unroll_dict[class_name]['type'] = 'list'
        elif any(method in methods for method in ['get', 'items', 'keys', 'popitem', 'setdefault', 'update', 'values']):
            deductions.append('implements dict-specific methods')
            self.unroll_dict[class_name]['type'] = 'dict'
        elif any(method in methods for method in ['add', 'discard', 'union', 'intersection', 'difference', 'symmetric_difference', 
                                                'intersection_update', 'difference_update', 'symmetric_difference_update']):
            deductions.append('implements set-specific methods')
            self.unroll_dict[class_name]['type'] = 'set'

        # Parse through container keys to determine type if no unique methods are implemented
        elif container_keys:
            if all(isinstance(key, int) for key in container_keys) and \
                    sorted(container_keys) == list(range(min(container_keys), max(container_keys)+1)):
                deductions.append('key structure suggests list-like behavior')
                self.unroll_dict[class_name]['type'] = 'list'
            else:
                deductions.append('key structure suggests dict-like behavior')
                self.unroll_dict[class_name]['type'] = 'dict'
        elif all(method in methods for method in essential_methods):
            deductions.append('defaulting to list due to general format and absence of unique collection methods')
            self.unroll_dict[class_name]['type'] = 'list'
        else:
            return

    def is_callable(self, class_name):
        if '__call__' in self.class_methods[class_name]:
            self.unroll_dict[class_name]['deductions'].append(f'{class_name} implements __call__, marking as callable')
            self.unroll_dict[class_name]['type'] = 'callable'

    def infer_class_type(self, class_name):
        self.is_primitive(class_name)
        if self.unroll_dict[class_name]['type'] == 'unknown':
            self.is_collection(class_name)
        if self.unroll_dict[class_name]['type'] == 'unknown':
            self.is_callable(class_name)
        if self.unroll_dict[class_name]['type'] == 'unknown':
            self.unroll_dict[class_name]['deductions'].append('no specific type patterns recognized')
            self.unroll_dict[class_name]['type'] = 'object'

def analyze_code_to_unroll_dict(code):
    tree = ast.parse(code)
    inferrer = TypeInferrer()
    inferrer.visit(tree)
    return inferrer.unroll_dict, inferrer.class_container_init

# def extract_initialization_expression(node, type_str):
#     if isinstance(node, ast.Dict):
#         if type_str == 'dict':
#             keys = [astunparse.unparse(k).strip() for k in node.keys]
#             values = [astunparse.unparse(v).strip() for v in node.values]
#             items = [f"{k}: {v}" for k, v in zip(keys, values)]
#             return "{" + ", ".join(items) + "}"
#         elif type_str in ['list', 'set']:
#             values = [astunparse.unparse(v).strip() for v in node.values]
#             if type_str == 'list':
#                 return "[" + ", ".join(values) + "]"
#             else:  # set
#                 return "{" + ", ".join(values) + "}"
#     # Empty structures to be safe
#     if type_str == 'dict':
#         return "{}"
#     elif type_str == 'list':
#         return "[]"
#     elif type_str == 'set':
#         return "set()"

def extract_initialization_expression(node, type_str):
    if type_str == 'dict':
        keys = [astunparse.unparse(k).strip() for k in getattr(node, 'keys', []) if k is not None]
        values = [astunparse.unparse(v).strip() for v in getattr(node, 'values', []) if v is not None]
        
        if keys and values and len(keys) == len(values):
            items = [f"{k}: {v}" for k, v in zip(keys, values)]
            return "{" + ", ".join(items) + "}"
        else:
            return "{}"
    elif type_str in ['list', 'set']:
        values = [astunparse.unparse(v).strip() for v in getattr(node, 'values', []) if v is not None]
        
        if type_str == 'list':
            return "[" + ", ".join(values) + "]"
        else:  
            return "{" + ", ".join(values) + "}"
    if type_str == 'dict':
        return "{}"
    elif type_str == 'list':
        return "[]"
    elif type_str == 'set':
        return "set()"
class InstantiationTracker(ast.NodeVisitor):
    def __init__(self):
        self.instantiated_classes = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.instantiated_classes.add(node.func.id)
        self.generic_visit(node)

def apply_single_replacement(code_snippet, class_name, type_info, class_container_init):
    """
    Apply a single replacement based on the inferred type information.
    Args:
        code_snippet (str): The current state of the code snippet.
        class_name (str): The name of the class to replace.
        type_info (dict): The inferred type information for the class.
        class_container_init (dict): Initializations of class containers.
    
    Returns:
        (str, bool): Tuple of the updated code snippet and a flag indicating success.
    """
    # Determine the replacement based on the inferred type
    if type_info['type'] in ['list', 'dict', 'set']:
        replacement = extract_initialization_expression(class_container_init.get(class_name, ast.Dict()), type_info['type'])
    elif type_info['type'] == 'int':
        replacement = '0'
    elif type_info['type'] == 'str':
        replacement = '""'
    else:
        return code_snippet, False 
    
    updated_code_snippet = code_snippet.replace(f"{class_name}()", replacement)

    return updated_code_snippet

def remove_unused_classes(code_snippet):
    """
    Remove class definitions that are no longer needed in the code snippet.
    
    Args:
        code_snippet (str): The current state of the code snippet after replacements.
    
    Returns:
        str: The cleaned-up code snippet.
    """
    tree = ast.parse(code_snippet)
    tracker = InstantiationTracker()
    tracker.visit(tree)
    new_body = [node for node in tree.body if not (isinstance(node, ast.ClassDef) and node.name not in tracker.instantiated_classes)]
    tree.body = new_body
    
    return astunparse.unparse(tree)

def test_snippet(snippet_obj, updated_code_snippet):
    """
    Test the updated code snippet for functionality.
    
    Args:
        snippet_obj (Snippet): The Snippet object being tested.
        updated_code_snippet (str): The updated code snippet after applying a single replacement.
    
    Returns:
        bool: True if the snippet runs successfully (no errors), False otherwise.
    """
    snippet_obj.history[-1] = updated_code_snippet
    
    try:
        out, err, stmt_cov, br_cov = snippet_obj.compute_timed_latest_coverage()
        
        # Check if there are errors in the execution
        if err is None:
            # Timeout
            return False
        else:
            if len(err) > 0:
                err_coord = ErrorCoordinator(path=snippet_obj.snippet_path, snippet=snippet_obj, stack_trace=err)
                if len(err_coord.err_type):
                    return False
                else:
                    return True
            else:
                return True
    except Exception as e:
        return False
    finally:
        snippet_obj.history.pop()

class TBDAssociationFinder(ast.NodeVisitor):
    """
    This AST Node Visitor will find associations with TBD objects for record keeping
    """
    def __init__(self, preprocessed_tbds=[]):
        self.associations = {}
        self.preprocessed_tbds = preprocessed_tbds  

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                attribute_name = target.attr
                value_str = ast.unparse(node.value).strip()
                tbd_matches = re.findall(r'TBD\d+', value_str)
                for tbd_name in tbd_matches:
                    if tbd_name not in self.preprocessed_tbds:  # Check if TBD is preprocessed
                        self.associations[attribute_name] = {'type': 'object', 'tbd_name': tbd_name}
            elif isinstance(target, ast.Name):
                value_str = ast.unparse(node.value).strip()
                tbd_matches = re.findall(r'TBD\d+', value_str)
                for tbd_name in tbd_matches:
                    # print("PREPROCESSED TBDS")
                    # print(self.preprocessed_tbds)
                    # print("TBD NAME")
                    # print(tbd_name)
                    if tbd_name not in self.preprocessed_tbds:  # Check if TBD is preprocessed
                        self.associations[target.id] = {'type': 'object', 'tbd_name': tbd_name}
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        for stmt in node.body:
            if isinstance(stmt, ast.Return) and stmt.value:
                return_str = ast.unparse(stmt.value).strip()
                tbd_matches = re.findall(r'TBD\d+', return_str)
                for tbd_name in tbd_matches:
                    if tbd_name not in self.preprocessed_tbds: 
                        self.associations[node.name] = {'type': 'callable', 'tbd_name': tbd_name}
        self.generic_visit(node)

def find_tbd_associations(code_snippet, preprocessed_tbds):
    tree = ast.parse(code_snippet)
    finder = TBDAssociationFinder(preprocessed_tbds=preprocessed_tbds)
    finder.visit(tree)
    return finder.associations

def update_incompleter_info(snippets_info, associations):
    """
    Updates the incompleter_predicted_type in snippets_info based on associations found.
    """
    for identifier, associated_type in associations.items():
        for snippet in snippets_info:
            if identifier in snippet['identifiers']:
                snippet['identifiers'][identifier]['incompleter_predicted_type'] = associated_type
            else:
                snippet['identifiers'][identifier] = {
                    "lexecutor_predicted_type": "did not implement",
                    "incompleter_predicted_type": associated_type
                }

def find_associations_types(current_snippet_info, associations, unroll_dict):
    """
    Updates the incompleter_predicted_type in current_snippet_info based on associations and unroll_dict.
    """
    for identifier, info in associations.items():
        tbd_name = info['tbd_name'].replace('()', '').strip()  # Remove parentheses for matching

        if tbd_name in unroll_dict:
            inferred_type = unroll_dict[tbd_name]['type']

            if info['type'] == 'callable':
                inferred_type = "callable"
            elif inferred_type == "object" and info['type'] == 'object':
                inferred_type = "object"

            if identifier in current_snippet_info['identifiers']:
                current_snippet_info['identifiers'][identifier]['incompleter_predicted_type'] = inferred_type
            else:
                current_snippet_info['identifiers'][identifier] = {
                    "lexecutor_predicted_type": "did not implement",
                    "incompleter_predicted_type": inferred_type
                }
        else:
            current_snippet_info['identifiers'][identifier]['incompleter_predicted_type'] = "does not deduce this"

def fuzz(snippet_obj, code_snippet, class_name, info, class_container_init, unroll_dict):
    original_type = info['type']
    if original_type == 'list':
        # Temporarily change to list for the fuzz attempt
        info['type'] = 'dict'
        updated_code_snippet = apply_single_replacement(code_snippet, class_name, info, class_container_init)
        success = test_snippet(snippet_obj, updated_code_snippet)
        if success:
            # Keep list type change
            unroll_dict[class_name] = info
            info['deductions'] = ['fuzzed from list to dict']
            return True, updated_code_snippet
        else:
            # Revert changes if unsuccessful
            info['type'] = original_type
            unroll_dict[class_name] = info
    return False, None


def unmock_code_snippet(snippet_obj, executability=True):
    """
    Analyzes the given code snippet, applies type deductions to replace class instantiations,
    and removes unused class definitions.

    Args:
        snippet_obj (Snippet): The Snippet object to analyze and update.

    Returns:
        str: The updated code snippet.
        dict: deduction tally of what deductions were successful
    """
    print('\nSTARTED UNMOCKING\n')
    code_snippet = snippet_obj.get_latest()
    unroll_dict, class_container_init = analyze_code_to_unroll_dict(code_snippet)
    tbd_associations = find_tbd_associations(code_snippet, snippet_obj.preprocessed_tbds)

    print("ASSOCIATIONS")
    print(tbd_associations)

    # Initialize tally for deductions
    deductions_tally = {'list': 0, 'dict': 0, 'set': 0, 'int': 0, 'str': 0, 'object': 0, 'total': 0}

    snippets_info_path = "../data/type_inference/snippets_info_chunk100.json"
    snippets_info_incompleter_path = "../data/type_inference/snippets_info_chunk100_incompleter.json"
    current_snippet_info = None
    
    if os.path.exists(snippets_info_path):
        with open(snippets_info_path, 'r') as file:
            snippets_info = json.load(file)
        
        # Extract the snippet number from the snippet name (e.g., "snippet_748-3.py" -> "748")
        snippet_no = snippet_obj.snippet_name.split('_')[-1].split('.')[0]
        
        # Find the dictionary for the current snippet
        for snippet_info in snippets_info:
            if snippet_info["snippet_no"] == snippet_no:
                current_snippet_info = snippet_info
                break

    # if current_snippet_info is not None:
    #     print(f"Current snippet info retrieved: {current_snippet_info}")
    # else:
    #     print("Current snippet info not found or the JSON file does not exist.")
    final_code_snippet = code_snippet

    if(executability):
        for class_name, info in unroll_dict.items():
            # Backup the current state before applying the change
            original_code_snippet = code_snippet

            is_preprocessed_tbd = class_name in snippet_obj.preprocessed_tbds
            
            if info['type'] in ['list', 'dict', 'set', 'int', 'str']:
                # Apply one change at a time
                updated_code_snippet = apply_single_replacement(code_snippet, class_name, info, class_container_init)

                success = test_snippet(snippet_obj, updated_code_snippet)
                
                if success:
                    # If the change is successful, update the code_snippet
                    # print('\nUNMOCKER: SUCCESSFUL SNIPPET:\n{}\n'.format(code_snippet))
                    code_snippet = updated_code_snippet

                    if not is_preprocessed_tbd:
                        deductions_tally[info['type']] += 1
                        deductions_tally['total'] += 1
                else:
                    # If not successful, fuzz it!
                    fuzz_success, fuzzed_snippet = fuzz(snippet_obj, code_snippet, class_name, info, class_container_init, unroll_dict)
                    if fuzz_success:
                        code_snippet = fuzzed_snippet
                        if not is_preprocessed_tbd:
                            deductions_tally[info['type']] += 1
                            deductions_tally['total'] += 1
                    else:
                        # If not successful, revert to original
                        code_snippet = original_code_snippet
                        if not is_preprocessed_tbd:
                            deductions_tally['total'] += 1
                    
            else:
                if not is_preprocessed_tbd:
                    deductions_tally['object'] += 1
                continue  

        final_code_snippet = remove_unused_classes(code_snippet)

    if os.path.exists(snippets_info_incompleter_path) and current_snippet_info is not None:
        # tbd_associations = find_tbd_associations(final_code_snippet, snippet_obj.preprocessed_tbds)

        # print("ASSOCIATIONS AGAIN")
        # print(tbd_associations)
        with open(snippets_info_incompleter_path, 'r') as file:
            existing_snippets_info = json.load(file)

        find_associations_types(current_snippet_info, tbd_associations, unroll_dict)
        existing_snippets_info.append(current_snippet_info)
        
        with open(snippets_info_incompleter_path, 'w') as file:
            json.dump(existing_snippets_info, file, indent=4)
    
    # print(deductions_tally)
    for var, info in unroll_dict.items():
        print(f"{var}: {info}")
    
    return final_code_snippet, deductions_tally


# To run directly for testing
if __name__ == "__main__":
    code_snippet = """ 
    """
    unroll_dict, class_container_init = analyze_code_to_unroll_dict(code_snippet)
    # updated_code_snippet = apply_replacements_and_remove_classes(code_snippet, unroll_dict, class_container_init)
    for var, info in unroll_dict.items():
        print(f"{var}: {info}")
    # print(updated_code_snippet)