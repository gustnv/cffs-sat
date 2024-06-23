# Coded by: Alexander Kulikov
# Advanced usage of the pysat library to solve the N-Queens problem.
# This serves as an inspiration for creating CNFs.
from itertools import *
from pysat.solvers import Solver
from pysat.card import *
from pysat.formula import IDPool, CNF

n = 8
pool, clauses = IDPool(), CNF()

for row in range(n):
    clauses.extend(CardEnc.equals(
        lits=[pool.id((row, column)) for column in range(n)], bound=1, vpool=pool))

for column in range(n):
    clauses.extend(CardEnc.equals(
        lits=[pool.id((row, column)) for row in range(n)], bound=1, vpool=pool))

for row, column in product(range(n), repeat=2):
    clauses.extend(CardEnc.atmost(
        lits=[pool.id((r, c)) for r, c in product(
            range(n), repeat=2) if r - c == row - column],
        bound=1,
        vpool=pool
    ))
    clauses.extend(CardEnc.atmost(
        lits=[pool.id((r, c)) for r, c in product(
            range(n), repeat=2) if r + c == row - column],
        bound=1,
        vpool=pool
    ))

solver = Solver(bootstrap_with=clauses)
solver.solve()
model = solver.get_model()

for row in range(n):
    for column in range(n):
        print("x" if pool.id((row, column)) in model else "*", end=" ")
    print()
