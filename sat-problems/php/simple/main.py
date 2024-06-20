from pysat.examples.genhard import PHP
from pysat.solvers import Lingeling

# Generate a Pigeonhole Principle (PHP) problem with 3 pigeons and 2 holes
cnf = PHP(2)

print("CNF Clauses:", cnf.clauses)
# When number of holes equals 2: (1 V 2) ^ (3 V 4) ^ (5 V 6) ^ (-1 V -3)
# ^ (-1 V -5) ^ (-3 V -5) ^ (-2 V -4) ^ (-2 V -6) ^ (-4 V -6)

# Create a Lingeling solver object and initialize it with the generated CNF clauses
with Lingeling(bootstrap_with=cnf.clauses, with_proof=True) as solver:
    # Solve the PHP problem
    if solver.solve():
        # If SAT, print the satisfying model
        print("[SAT] Model found:", solver.get_model())
    else:
        # If UNSAT, print the proof of unsatisfiability
        print("UNSAT. Proof:", solver.get_proof())
