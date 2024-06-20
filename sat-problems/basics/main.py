# This is a simple example of how to use the PySAT library to solve a SAT problem.

from pysat.solvers import *

"""
 Create conjunctive normal form (CNF) from the following expression: 
 (-1 v -2 v -3) ^ (1 v -2) ^ (2 v -3) ^ (3 v -1) ^ (1 v 2 v 3)
"""
cnf = [[-1, -2, -3], [1, -2], [2, -3], [3, -1], [1, 2, 3]]

s = Solver(bootstrap_with=cnf[1:])

if s.solve():
    print(s.get_model())
else:
    print("UNSAT")

s.clear_interrupt()
s.append_formula(cnf)

if s.solve():
    print(s.get_model())
else:
    print("UNSAT")

s.delete()
