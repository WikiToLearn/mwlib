#! /usr/bin/env python

# Copyright (c) 2007-2008 PediaPress GmbH
# See README.txt for additional licensing information.
# based on pyparsing example code (SimpleCalc.py)

"""Implementation of mediawiki's #expr template. 
http://meta.wikimedia.org/wiki/ParserFunctions#.23expr:
"""

from __future__ import division

import re
import inspect

class ExprError(Exception):
    pass

def _myround(a,b):
    r=round(a, int(b))
    if int(r)==r:
        return int(r)
    return r


pattern = """
(?:\s+)
|((?:\d+)(?:\.\d+)?
 |(?:\.\d+))
|(\+|-|\*|/|>=|<=|<>|!=|[a-zA-Z]+|.)
"""

rxpattern = re.compile(pattern, re.VERBOSE | re.DOTALL | re.IGNORECASE)
def tokenize(s):
    return [(v1,v2.lower()) for (v1,v2) in rxpattern.findall(s) if v1 or v2]

class uminus: pass
class uplus: pass

precedence = {"(":-1, ")":-1}
functions = {}

def addop(op, prec, fun):
    precedence[op] = prec
    numargs = len(inspect.getargspec(fun)[0])
    
    
    def wrap(stack):
        assert len(stack)>=numargs
        
        args = tuple(stack[-numargs:])
        del stack[-numargs:]

        stack.append(fun(*args))

    functions[op] = wrap
        
a=addop
a(uminus, 10, lambda x: -x)
a(uplus, 10, lambda x: x)

a("not", 9, lambda x:int(not(bool(x))))

a("*", 8, lambda x,y: x*y)
a("/", 8, lambda x,y: x/y)
a("div", 8, lambda x,y: x/y)
a("mod", 8, lambda x,y: int(x)%int(y))


a("+", 6, lambda x,y: x+y)
a("-", 6, lambda x,y: x-y)

a("round", 5, _myround)

a("<", 4, lambda x,y: int(x<y))
a(">", 4, lambda x,y: int(x>y))
a("<=", 4, lambda x,y: int(x<=y))
a(">=", 4, lambda x,y: int(x>=y))
a("!=", 4, lambda x,y: int(x!=y))
a("<>", 4, lambda x,y: int(x!=y))
a("=", 4, lambda x,y: int(x==y))

a("and", 3, lambda x,y: int(bool(x) and bool(y)))
a("or", 2, lambda x,y: int(bool(x) or bool(y)))
del a

class Expr(object):
    
    def as_float_or_int(self, s):
        if "." in s or "e" in s.lower():
            return float(s)
        return long(s)
    
    def output_operator(self, op):
        return functions[op](self.operand_stack)
    
    def output_operand(self, operand):
        self.operand_stack.append(operand)
            
    def parse_expr(self, s):
        tokens = tokenize(s)

        self.operand_stack = []
        operator_stack = []

        seen_operand=False
        
        last_operand, last_operator = False, True
        
        for operand, operator in tokens:
            if operand:
                if last_operand:
                    raise ExprError("expected operator")
                self.output_operand(self.as_float_or_int(operand))
            elif operator=="(":
                operator_stack.append("(")
            elif operator==")":
                while 1:
                    if not operator_stack:
                        raise ExprError("unbalanced parenthesis")
                    t = operator_stack.pop()
                    if t=="(":
                        break
                    self.output_operator(t)
            elif operator in precedence:
                if last_operator and last_operator!=")":
                    if operator=='-':
                        operator = uminus
                    elif operator=='+':
                        operator = uplus

                prec = precedence[operator]
                while operator_stack and prec<=precedence[operator_stack[-1]]:
                    p = operator_stack.pop()
                    self.output_operator(p)
                operator_stack.append(operator)
            else:
                raise ExprError("unknown operator: %r" % (operator,))

            last_operand, last_operator = operand, operator
            
            
        while operator_stack:
            p=operator_stack.pop()
            if p=="(":
                raise ExprError("unbalanced parenthesis")
            self.output_operator(p)
            
        if len(self.operand_stack)!=1:
            raise ExprError("bad stack: %s" % (self.operand_stack,))

        return self.operand_stack[-1]
    
def expr(s):
    return Expr().parse_expr(s)

def main():
    ParseException = ExprError
    import time
    try:
        import readline  # do not remove. makes raw_input use readline
        readline
    except ImportError:
        pass

    ep = expr
  
    while 1:
        input_string = raw_input("> ")
        if not input_string:
            continue
    
        stime = time.time()
        try:
            res=expr(input_string)
        except ParseException, err:
            print "ERROR:", err
            continue
        print res
        print time.time()-stime, "s"

if __name__=='__main__':
    main()
    
