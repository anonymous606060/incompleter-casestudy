from typing import Tuple

from path_config import DATA_DIR
from main.utils.snippet import Snippet
from main.errors.error_base_class import ErrorBaseClass
from main.actions.action_base_class import ActionBaseClass
from main.actions.files.create_file import CreateFile
from main.actions.files.create_dir import CreateDir

import re
import os

class _FileNotFoundError(ErrorBaseClass):
    sample_exts = ['json', 'xml', 'html', 'csv', 'xlsx', 'xls', 'ppt', 'pdf', 'txt', 'rtf', 'doc', 'docx', 'odt', 'ods', 'odp', 'zip', 'tar', 'gz', 'png', 'jpg', 'gif', 'tiff', 'svg', 'webp', 'bmp', 'ico', 'hdf', 'h4', 'hdf4', 'he2', 'h5', 'hdf5', 'he5', 'mp3', 'wav', 'ogg', 'mp4', 'avi', 'mov', 'wmv', 'webm']

    mappings = {
        r'\'?([^\']+)\'? not found.*?': [ CreateFile ],
        r'\[Errno 2\] No such file or directory: \'?([^\']+)\'?': [ CreateFile, CreateDir ],
        r'File \'?([^\']+)\'? does not exist': [ CreateFile]
    }

    def __init__(self, path: str, snippet: Snippet, stack_trace: str) -> None:
        super().__init__(path=path, snippet=snippet, stack_trace=stack_trace)

    def find_action(self) -> ActionBaseClass:
        for err_msg_pattern, action_class_list in _FileNotFoundError.mappings.items():
            if m := re.search(err_msg_pattern, self.err_msg):
                for ActionClass in action_class_list:
                    kwargs = {}
                    if ActionClass == CreateFile:
                        file_name = m.groups()[0]
                        file_ext = file_name.split('.')[-1]
                        file_content = b''

                        if file_ext in _FileNotFoundError.sample_exts:
                            sample_file = open(os.path.join(DATA_DIR, 'sample_files', 'sample.{}'.format(file_ext)), 'rb')
                            file_content = sample_file.read()
                        else:
                            sample_file = open(os.path.join(DATA_DIR, 'sample_files', 'sample.txt'), 'rb')
                            file_content = sample_file.read()

                        kwargs['file_name'] = file_name
                        kwargs['file_content'] = file_content
                    
                    elif ActionClass == CreateDir:
                        dir_name = m.groups()[0]
                        kwargs['dir_name'] = dir_name

                    if (action := ActionClass(snippet=self.snippet, lineno=self.lineno, **kwargs)).check_criteria():
                        return action
        
        return None