from pycosat import solve

# Define the list of clauses
clauses = [
    [-1, -2, -3],  # Clause 1: ~1 OR ~2 OR ~3
    [1, -2],       # Clause 2: 1 OR ~2
    [2, -3],       # Clause 3: 2 OR ~3
    [3, -1],       # Clause 4: 3 OR ~1
    [1, 2, 3]      # Clause 5: 1 OR 2 OR 3
]

# Solve the SAT problem with all clauses
print(solve(clauses))

# Solve the SAT problem with clauses except the first one
print(solve(clauses[1:]))
