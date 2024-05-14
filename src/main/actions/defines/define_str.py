from main.utils.snippet import Snippet
from main.actions.action_base_class import ActionBaseClass
from main.actions.defines.define_func import DefineFunc
from typing import Any
import ast

class DefineString(ActionBaseClass):
    def __init__(self, snippet: Snippet=None, lineno: int=0, **kwargs: dict) -> None:
        super().__init__(snippet, lineno)

        self.class_name = None
        if 'class_name' in kwargs: 
            self.class_name = kwargs['class_name']

    def __str__(self) -> str:
        desc = super().__str__()
        desc += 'String Class name: {}\n'.format(self.class_name)

        return desc

    def check_criteria(self) -> bool:
        return True

    @ActionBaseClass.add_to_history
    def apply_pattern(self) -> str:
        class RemoveExistingClass(ast.NodeTransformer):
            def __init__(self, **kwargs):
                self.snippet = kwargs['snippet']
                self.lineno = kwargs['lineno']
                self.class_name = kwargs['class_name']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node):
                for (idx, child) in enumerate(node.body):
                    node.body[idx] = self.visit(child)         
                if None in node.body:
                  node.body.remove(None)
                return node

            def visit_ClassDef(self, node):
                if node.name == self.class_name:
                    return None
                return node

        with open('main/templates/template_str.txt') as template_file:
            template = template_file.read()
            template = template.replace('<class_name>', self.class_name)

            tree = ast.parse(self.snippet.get_latest())
            RemoveExistingClass(snippet=self.snippet, lineno=self.lineno, class_name=self.class_name).visit_Body(tree)

            return ast.parse(template + '\n\n' + self.snippet.get_latest())
        
        # # subclass 'str' class
        # self.__subclass_str()

        # # define function __new__(self)
        # self.__create_new_method_ast()

        # # define function __repr__(self)
        # self.__define_repr()

        # # define function __str__(self)
        # self.__define_str()

        # # define function __add__(self, another_str)
        # self.__define_add

        # # define function __getitem__(self, key)
        # self.__define_getitem()

        # # define function __iter__(self)
        # self.__define_iter()

        # # define function __len__(self)
        # self.__define_len()

        # return

    def __subclass_str(self) -> None:
        class StringSubclasser(ast.NodeTransformer):
            def __init__(self, **kwargs):
              self.class_name = kwargs['class_name']
              self.snippet = kwargs['snippet']
              self.lineno = kwargs['lineno']

            @ActionBaseClass.add_to_history
            def visit_Body(self, node):
              for (idx, child) in enumerate(node.body):
                node.body[idx] = self.visit(child)
              return node

            def visit_ClassDef(self, node):
              if node.name == self.class_name:
                  node.bases.append(ast.Name(id='str', ctx=ast.Load()))
              return node
        
        tree = ast.parse(self.snippet.get_latest())
        tree = StringSubclasser(class_name=self.class_name, snippet=self.snippet, lineno=self.lineno).visit_Body(tree)

        return None

    def __create_new_method_ast(self):
        kwargs = {}
        kwargs['func_name'] = '__new__'
        kwargs['class_scope'] = self.class_name
        kwargs['func_args'] = [ast.arg(arg='self')]
        kwargs['func_body'] = [
            ast.Return(value=ast.Call(
              func=ast.Attribute(
                  value=ast.Call(
                      func=ast.Name(id='super', ctx=ast.Load()),
                      args=[],
                      keywords=[],
                  ),
                  attr='__new__',
                  ctx=ast.Load(),
              ),
              args=[
                ast.Name(id='self', ctx=ast.Load()),
                ast.Attribute(
                  value=ast.Name(id='self', ctx=ast.Load()),
                  attr='__name__',
                  ctx=ast.Load()
                  )
                ],
              keywords=[],
          ))
        ]
        DefineFunc(snippet=self.snippet, lineno=self.lineno, **kwargs).apply_pattern()

    def __define_str(self) -> None:
        kwargs = {}
        kwargs['func_name'] = '__str__'
        kwargs['class_scope'] = self.class_name
        kwargs['func_args'] = [ast.arg(arg='self')]
        kwargs['func_body'] = [
            ast.Return(
              value=ast.Attribute(
                value=ast.Call(
                  func=ast.Name(id='type', ctx=ast.Load()),
                  args=[
                    ast.Name(id='self', ctx=ast.Load())],
                  keywords=[]),
                attr='__name__',
                ctx=ast.Load()))
        ]
        DefineFunc(snippet=self.snippet, lineno=self.lineno, **kwargs).apply_pattern()

    def __define_repr(self) -> None:
        kwargs = {}
        kwargs['func_name'] = '__repr__'
        kwargs['class_scope'] = self.class_name
        kwargs['func_args'] = [ast.arg(arg='self')]
        kwargs['func_body'] = [
            ast.Return(
              value=ast.Attribute(
                value=ast.Call(
                  func=ast.Name(id='type', ctx=ast.Load()),
                  args=[
                    ast.Name(id='self', ctx=ast.Load())],
                  keywords=[]),
                attr='__name__',
                ctx=ast.Load()))
        ]
        DefineFunc(snippet=self.snippet, lineno=self.lineno, **kwargs).apply_pattern()

    def __define_add(self) -> None:
        kwargs = {}
        kwargs['func_name'] = '__add__'
        kwargs['class_scope'] = self.class_name
        kwargs['func_args'] = [ast.arg(arg='self'), ast.arg(arg='another_str')]
        kwargs['func_body'] = [
            ast.Return(
              value=ast.BinOp(
                left=ast.Call(
                  func=ast.Name(id='str', ctx=ast.Load()),
                  args=[
                    ast.Name(id='self', ctx=ast.Load())],
                  keywords=[]),
                op=ast.Add(),
                right=ast.Name(id='another_str', ctx=ast.Load())))
        ]
        DefineFunc(snippet=self.snippet, lineno=self.lineno, **kwargs).apply_pattern()

    def __define_getitem(self) -> None:
        kwargs = {}
        kwargs['func_name'] = '__getitem__'
        kwargs['class_scope'] = self.class_name
        kwargs['func_args'] = [ast.arg(arg='self'), ast.arg(arg='key')]
        kwargs['func_body'] = [
            ast.Return(
              value=ast.Subscript(
                value=ast.Call(
                  func=ast.Name(id='str', ctx=ast.Load()),
                  args=[
                    ast.Name(id='self', ctx=ast.Load())],
                  keywords=[]),
                slice=ast.Name(id='key', ctx=ast.Load()),
                ctx=ast.Load()))
        ]
        DefineFunc(snippet=self.snippet, lineno=self.lineno, **kwargs).apply_pattern()

        return

    def __define_iter(self) -> None:
        kwargs = {}
        kwargs['func_name'] = '__iter__'
        kwargs['class_scope'] = self.class_name
        kwargs['func_args'] = [ast.arg(arg='self')]
        kwargs['func_body'] = [
            ast.Return(
              value=ast.Call(
                func=ast.Name(id='iter', ctx=ast.Load()),
                args=[
                  ast.Call(
                    func=ast.Name(id='str', ctx=ast.Load()),
                    args=[
                      ast.Name(id='self', ctx=ast.Load())],
                    keywords=[])],
                keywords=[]))
        ]
        DefineFunc(snippet=self.snippet, lineno=self.lineno, **kwargs).apply_pattern()

        return None

    def __define_len(self) -> None:
        kwargs = {}
        kwargs['func_name'] = '__len__'
        kwargs['class_scope'] = self.class_name
        kwargs['func_args'] = [ast.arg(arg='self')]
        kwargs['func_body'] = [
            ast.Return(
              value=ast.Call(
                func=ast.Name(id='len', ctx=ast.Load()),
                args=[
                  ast.Call(
                    func=ast.Name(id='str', ctx=ast.Load()),
                    args=[
                      ast.Name(id='self', ctx=ast.Load())],
                    keywords=[])],
                keywords=[]))
        ]
        DefineFunc(snippet=self.snippet, lineno=self.lineno, **kwargs).apply_pattern()

        return