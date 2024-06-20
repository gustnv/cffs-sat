from pysat.solvers import *

# Define the list of clauses
cnf = [
    [-1, -2, -3],  # Clause 1: ~1 OR ~2 OR ~3
    [1, -2],       # Clause 2: 1 OR ~2
    [2, -3],       # Clause 3: 2 OR ~3
    [3, -1],       # Clause 4: 3 OR ~1
    [1, 2, 3]      # Clause 5: 1 OR 2 OR 3
]

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
