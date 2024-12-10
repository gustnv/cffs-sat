from pysat.solvers import Solver

# Define the conjunctive normal form (CNF) expression
# (-1 v -2 v -3) ^ (1 v -2) ^ (2 v -3) ^ (3 v -1) ^ (1 v 2 v 3)
cnf = [[-1, -2, -3], [1, -2], [2, -3], [3, -1], [1, 2, 3]]

# Create a solver object and initialize it with some clauses (bootstrap_with)
s = Solver(bootstrap_with=cnf[1:])

# Solve the problem
if s.solve():
    # Print a message indicating a satisfying model is found
    print("SAT: Model found")
    print(s.get_model())  # Print the satisfying model
else:
    # Print a message indicating no satisfying model is found
    print("UNSAT: No model found")

# Clear the solver to prepare for adding new clauses
s.clear_interrupt()

# Add new clauses to the solver
s.append_formula(cnf)

# Solve the problem again after adding new clauses
if s.solve():
    # Print a message indicating a satisfying model is found
    print("SAT: Model found")
    print(s.get_model())  # Print the satisfying model
else:
    # Print a message indicating no satisfying model is found
    print("UNSAT: No model found")

# Delete the solver object to release resources
s.delete()
