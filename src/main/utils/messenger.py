import re

from main.actions.defines.define_key import DefineKey

class Messenger:
    def __init__(self, snippet=None, lineno=-1):
        self.snippet = snippet
        self.lineno = lineno

        self.DISPATCH_PATTERNS = {
            r'\[FROM INNER-WORLD\], \[ADD STR-KEY\], \[TGT (\S+)\], \[ADDING \(KEY, VALUE\): \((\S+), (\S+)\)\]': self.dispatch_add_str_key,
            r'\[FROM INNER-WORLD\], \[ADD OBJ-KEY\], \[TGT (\S+)\], \[ADDING \(KEY, VALUE\): \((\S+), (\S+)\)\]': self.dispatch_add_obj_key
        }

    def dispatch(self, msg=''):
        for (pattern, dispatcher) in self.DISPATCH_PATTERNS.items():
            if m := re.search(pattern, msg):
                print(m.groups()[0], m.groups()[1], m.groups()[2])
                dispatcher(m)

    def dispatch_add_str_key(self, match):
        define_key_action = DefineKey(snippet=self.snippet, lineno=-1, class_name=match.groups()[0], key=match.groups()[1])
        define_key_action.check_criteria()
        define_key_action.apply_pattern()

    def dispatch_add_obj_key(self, match):
        define_key_action = DefineKey(snippet=self.snippet, lineno=-1, class_name=match.groups()[0], key=match.groups()[1], val_id=match.groups()[1])
        define_key_action.check_criteria()
        define_key_action.apply_pattern()