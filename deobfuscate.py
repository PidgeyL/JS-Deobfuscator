import re
from slimit import ast
from slimit.parser import Parser
from slimit.visitors import nodevisitor

def varReplace(js_file, variables):
  def myRep(match):
    match = match.group()
    prepend = match[0]
    return prepend + str(variables[match[1:]])

  for var in variables:
    js_file = re.sub(r"[(+[, ]"+var, myRep, js_file)
  return js_file

def stringConcat(js_file):
  def myRep(match):
    match = match.group()
    return repr(eval(match))
  js_file = re.sub(r"""(["'])[^'"]*\1[ ]*[+][ ]*(["'])[^'"]*\2""", myRep, js_file)
  js_file = re.sub(r"""(["'])[^'"]*\1[ ]*[+][ ]*(["'])[^'"]*\2""", myRep, js_file)
  return js_file

def removeDeclarations(js_file):
  parser = Parser()
  tree = parser.parse(js_file)
  output = ""
  for child in tree.children():
    if type(child) != ast.VarStatement:
      output += (child.to_ecma() + "\n")
    else:
      nodes = [x for x in nodevisitor.visit(child)]
      if type(nodes[0].initializer) not in [ast.String, ast.Number, ast.BinOp]:
        output += (child.to_ecma() + "\n")
  return output

def treeWalker(js_file):
  parser = Parser()
  tree = parser.parse(js_file)
  variables = {}
  for child in tree.children():
    if type(child) == ast.VarStatement:
      try:
        nodes = [x for x in nodevisitor.visit(child)]
        if   type(nodes[0].initializer) == ast.String:
          variables[nodes[0].identifier.value] = nodes[0].initializer.value
        elif type(nodes[0].initializer) == ast.Number:
          variables[nodes[0].identifier.value] = eval(nodes[0].initializer.to_ecma())
        elif type(nodes[0].initializer) == ast.BinOp:
          variables[nodes[0].identifier.value] = eval(nodes[0].initializer.to_ecma())
        else:
          print((nodes[0].identifier.value, nodes[0].initializer))
      except Exception as e:
        print (child.to_ecma())
  return variables

def emptyFunctionReplace(js_file):
  def myRep(match):
    match = match.group()
    result = match.split("(")[1]
    result = result.strip(")")
    return result

  matches = re.findall(r"function[ ]+([a-zA-Z0-9_]+)\([ ]*([a-zA-Z0-9_]+)[ ]*\)[ ]*{[^}]*return[ ]+\2[ ;(\n|\r)]*}", js_file)
  emptyFuncts = [x[0] for x in matches]
  js_file = re.sub(r"function[ ]+([a-zA-Z0-9_]+)\([ ]*([a-zA-Z0-9_]+)[ ]*\)[ ]*{[^}]*return[ ]+\2[ ;(\n|\r)]*}", "", js_file)
  for funct in emptyFuncts:
    js_file = re.sub(re.compile(funct+"\([^\)]*\)"), myRep, js_file)
    js_file = js_file.strip(";\n")
  return js_file

def fixedReturnFunctions(js_file):
  def myRep(match):
    match = match.group()
    result = match.split("return")[1]
    result = result.split("}")[0]
    result.strip(" ;\n")
    return result

  js_file = re.sub(r"""function[ ]+([a-zA-Z0-9_]+)\([ ]*([a-zA-Z0-9_]*)[ ]*\)[ ]*{([^}])*return[ ]+((["'])[^'"]*\5|[0-9]+)[ ;(\n|\r)]*}\([^\)]*\)""", myRep, js_file)
  return js_file

if __name__ == '__main__':
  import argparse
  argParser = argparse.ArgumentParser(description='Try to deobfuscate JavaScript files')
  argParser.add_argument('inp', metavar="file", type=str, help='File to analyse')
  argParser.add_argument('out', metavar="file", type=str, help='File to analyse')
  args = argParser.parse_args()

  js_file = open(args.inp, 'r').read()
  variables = treeWalker(js_file)
  js_file = removeDeclarations(js_file)
  js_file = varReplace(js_file, variables)
  js_file = emptyFunctionReplace(js_file)
  js_file = fixedReturnFunctions(js_file)
  js_file = stringConcat(js_file)
  js_file = stringConcat(js_file)
  if args.out:
    open(args.out, 'w').write(js_file)
  else:
    print(js_file)
