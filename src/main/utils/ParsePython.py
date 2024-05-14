import ast
from pprint import pprint

##
class MyVisitor(ast.NodeVisitor):

  def visit_Constant(self, node):
    print(node)

  def visit_BinOp(self, node):
    self.visit(node.left)
    print(node.op)
    self.visit(node.right)


tree = ast.parse("""
def add(a, b):
  return a + 2
""")


# pprint(ast.dump(tree))

MyVisitor().visit(tree)


# Found this by parsing one example input 
# Import(names=[alias(name='os')])
# the following visitor modifies the ast to add an import statement
class RewriteName(ast.NodeTransformer):

  def visit_Body(self, node):      
      node.body.insert(0, ast.Import(names=[ast.alias(name='os')]))
      return node


RewriteName().visit_Body(tree)
print(ast.unparse(tree))