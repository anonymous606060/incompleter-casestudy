from path_config import DATA_DIR

from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from github import Auth, Github
from github.PaginatedList import PaginatedList
from github.ContentFile import ContentFile

from pathlib import Path
from typing import List, Tuple
import json
import os
import base64

import ast
import pickle

# Top PyPI Search
__top_pypi_path = os.path.join(DATA_DIR, 'package_meta', 'top_pypi.json')

def __create_cache(__top_pypi_path: str) -> None:
    top_pypi_file = Path(__top_pypi_path)
    top_pypi_file.parent.mkdir(parents=True, exist_ok=True)

    return None

def __top_pypi_read_cache() -> dict:
    try:
        if os.path.exists(__top_pypi_path):
            with open(__top_pypi_path, 'r') as __top_pypi_file:
                return json.loads(__top_pypi_file.read())
        else:
            __create_cache(__top_pypi_path)
            return None
    except FileNotFoundError as e:
        print('FileNotFoundError: when trying to read from top pypi package list cache')
        return None

def __top_pypi_validate_cache(cached_json: str = None, retrieved_json: str = None) -> bool:
    if cached_json == None or retrieved_json == None: return False
    return hash(json.dumps(cached_json)) == hash(json.dumps(retrieved_json))

def __get_top_pypi_json() -> dict:
    top_json_latest = None
    try:
        top_url = 'https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json'
        top_json_latest = json.loads(urlopen(top_url).read())
    except HTTPError as e:
        print('HTTPError: when trying to read the top pypi packages')
    except URLError as e:
        print('URLError: when trying to read the top pypi packages')

    top_json_cached = __top_pypi_read_cache()
    if top_json_latest != None:
        if not __top_pypi_validate_cache(top_json_latest, top_json_cached):
            with open(__top_pypi_path, 'w+') as __top_pypi_file:
                json.dump(top_json_latest, __top_pypi_file)
                return top_json_latest
        else:
            return top_json_cached
    
    return __top_pypi_read_cache()

# Github Search

def __new_github_object() -> Github:
    try:
        with open(os.path.join(DATA_DIR, 'package_meta', 'gh.key'), 'r') as gh_key:
            auth = Auth.Token(gh_key.read())
            return Github(auth=auth)
    except FileNotFoundError as e:
        print('FileNotFoundError: when trying to read secret gh.key in data/package_meta')

    return None

def __search_github_code_for_imports(project_name: str) -> str:
    query: str = 'import {} language:python ?page=1'.format(project_name)

    gh: Github = __new_github_object()
    search_results: PaginatedList[ContentFile] = gh.search_code(query=query)

    import_usages_set = set()
    for res in search_results:
        res_code = base64.b64decode(res.content).decode('utf-8', 'ignore')
        for line in res_code.split('\n'):
            if 'import' in line and project_name in line:
                if ',' in line:
                    for single_module in line.split(',')[1:]:
                        import_usages_set.add('import ' + single_module.strip())
                else:    
                    import_usages_set.add(line.strip())
    
    return '\n'.join(list(import_usages_set))

# Parse Github Search Results

def __parse_imports(github_references: List[str]) -> dict:
    import_dict = {}
    class ImportVisitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for _import_statement in node.names:
                if _import_statement.asname is not None:
                    import_dict[_import_statement.asname] = node
                else:
                    import_dict[_import_statement.name] = node

        def visit_ImportFrom(self, node):
            for _import_statement in node.names:
                if _import_statement.asname is not None:
                    import_dict[_import_statement.asname] = node
                else:
                    import_dict[_import_statement.name] = node

    for github_reference in github_references:
        try:
            tree = ast.parse(github_reference)
            ImportVisitor().visit(tree)
        except SyntaxError as e:
            pass

    return import_dict

def __save_import_dict(import_dict: dict) -> None:
    import_dict_path = os.path.join(DATA_DIR, 'package_meta/import_dict.pickle')
    with open(import_dict_path, 'wb') as import_dict_pickle:
        pickle.dump(import_dict, import_dict_pickle)

if __name__ == "__main__":
    top_pypi_json = __get_top_pypi_json()

    github_references: List[str] = []
    for project in top_pypi_json['rows']:
        github_references.append(__search_github_code_for_imports(project['project']))

    if github_references is not None:
        import_dict = __parse_imports(github_references)
        print(import_dict)
        __save_import_dict(import_dict)

    

    

