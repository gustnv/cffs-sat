from itertools import *
from pysat.solvers import Solver
from pysat.card import *
from pysat.formula import IDPool, CNF

n = 8
pool, clauses = IDPool(), CNF()

for row in range(n):
    clauses.extend(CardEnc.equals(lits=[pool.id((row, column)) for column in range(n)], bound=1, vpool=pool))

for column in range(n):
    clauses.extend(CardEnc.equals(lits=[pool.id((row, column)) for row in range(n)], bound=1, vpool=pool))

for row, column in product(range(n), repeat=2):
    