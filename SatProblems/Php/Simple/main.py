from pysat.solvers import Lingeling
from pysat.examples.genhard import PHP

cnf = PHP(3)
print(cnf.clauses)

with Lingeling(bootstrap_with=cnf.clauses, with_proof=True) as l:
    print(l.solve())
    print(l.get_proof())