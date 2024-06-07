from pysat.solvers import Lingeling
from pysat.examples.genhard import PHP

cnf = PHP(2)

with Lingeling(bootstrap_with=cnf.clauses, with_proof=True) as l:
    if l.solve():
        print("[SAT]", l.get_model())
    else:
        print("UNSAT", l.get_proof())