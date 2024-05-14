from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_func import DefineFunc
from main.actions.defines.define_int import DefineInteger
from main.actions.defines.define_str import DefineString
from typing import Any
import ast

class DefineOperator(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.operator = kwargs['operator']
        self.class1 = kwargs['class1']
        self.class2 = kwargs['class2']

        self.operator_to_func_name = {
            '+': '__add__', '-': '__sub__', '*': '__mul__', '/': '__truediv__', '//': '__floordiv__',
            '%': '__mod__', '**': '__pow__', '>>': '__rshift__', '<<': '__lshift__', '~': '__invert__', '&': '__and__',
            '|': '__or__', '^': '__xor__', '<': '__lt__', '>': '__gt__', '<=': '__le__', '>=': '__ge__',
            '==': '__eq__', '!=': '__ne__', '-=': '__isub__', '+=': '__iadd__', '*=': '__imul__', '/=': '__idiv__',
            '//=': '__ifloordiv__', '%=': '__imod__', '**=': '__ipow__', '>>=': '__irshift__', '<<=': '__ilshift__',
            '&=': '__iand__', '|=': '__ior__', '^=': '__ixor__'
        }

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'Operator: {}\nClass 1: {}\nClass 2: {}'.format(self.operator, self.class1, self.class2)

        return desc

    def check_criteria(self) -> bool:
        if self.operator in self.operator_to_func_name.keys():
            return True
        return False

    def apply_pattern(self) -> str:
        if self.class1 is not None and 'TBD' in self.class1:
            func_name = self.operator_to_func_name[self.operator]
            class_scope = self.class1
            func_args = [ast.arg(arg='self'), ast.arg(arg='other')]

            # Subclassing one class based on type of the other
            if self.class2 in [ 'int', 'float' ]:
                DefineInteger(snippet=self.snippet, lineno=self.lineno, class_name=self.class1).apply_pattern()
            elif self.class2 in [ 'str' ]:
                DefineString(snippet=self.snippet, lineno=self.lineno, class_name=self.class1).apply_pattern()
            
            def_func = DefineFunc(snippet=self.snippet, lineno=self.lineno, func_name=func_name, class_scope=class_scope, func_args=func_args, override_criteria=True)
            def_func.check_criteria()
            def_func.apply_pattern()
        if self.class2 is not None and 'TBD' in self.class2:
            func_name = self.operator_to_func_name[self.operator]
            class_scope = self.class2
            func_args = [ast.arg(arg='self'), ast.arg(arg='other')]

            # Subclassing one class based on type of the other
            if self.class1 in [ 'int', 'float' ]:
                DefineInteger(snippet=self.snippet, lineno=self.lineno, class_name=self.class2).apply_pattern()
            elif self.class1 in [ 'str' ]:
                DefineString(snippet=self.snippet, lineno=self.lineno, class_name=self.class2).apply_pattern()
            
            def_func = DefineFunc(snippet=self.snippet, lineno=self.lineno, func_name=func_name, class_scope=class_scope, func_args=func_args, override_criteria=True)
            def_func.check_criteria()
            def_func.apply_pattern()
        
        return