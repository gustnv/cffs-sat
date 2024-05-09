from pysat.solvers import Minisat22

# Define the list of clauses
clauses = [
    [-1, -2, -3],  # Clause 1: ~1 OR ~2 OR ~3
    [1, -2],       # Clause 2: 1 OR ~2
    [2, -3],       # Clause 3: 2 OR ~3
    [3, -1],       # Clause 4: 3 OR ~1
    [1, 2, 3]      # Clause 5: 1 OR 2 OR 3
]

# Create a Minisat22 solver instance
solver_0 = Minisat22()

# Add all clauses to the solver
solver_0.append_formula(clauses)

# Solve the SAT problem
if solver_0.solve():
    model = solver_0.get_model()  # Get the satisfying assignment
    print(model)
else:
    print("UNSAT")  # Print if the problem is unsatisfiable

# Create a new Minisat22 solver instance
solver_1 = Minisat22()

# Add clauses except the first one to the solver
solver_1.append_formula(clauses[1:])

# Solve the modified SAT problem
if solver_1.solve():
    model = solver_1.get_model()  # Get the satisfying assignment
    print(model)
else:
    print("UNSAT")  # Print if the problem is unsatisfiable
