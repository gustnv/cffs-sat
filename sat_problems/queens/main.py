from pysat.solvers import Minisat22

# Initialize the solver
solver = Minisat22()

# Size of board
n = 8

# Q[i,j] will denote there is a queen on square (i,j) 
Q = [[0 for j in range(n)] for i in range(n)]

# Give each variable a unique label in {1,...,n^2}
c = 1
for i in range(n):
    for j in range(n):
        Q[i][j] = c
        c += 1

# varsInCol returns the set of variables in the same column as y
def varsInCol(y):
    return {Q[i][y] for i in range(n)}

# varsInRow returns the set of variables in the same row as x
def varsInRow(x):
    return {Q[x][i] for i in range(n)}

# varsInDiag returns the set of variables in the same diagonal as (x,y)
def varsInDiag(x, y):
    diagVars = {Q[x][y]}
    for i in range(n):
        if x+i in range(n) and y+i in range(n):
            diagVars.add(Q[x+i][y+i])
        if x-i in range(n) and y-i in range(n):
            diagVars.add(Q[x-i][y-i])
    return diagVars

# varsinAntiDiag returns the set of variables in the same anti-diagonal as (x,y)
def varsInAntiDiag(x, y):
    antiDiagVars = {Q[x][y]}
    for i in range(n):
        if x+i in range(n) and y-i in range(n):
            antiDiagVars.add(Q[x+i][y-i])
        if x-i in range(n) and y+i in range(n):
            antiDiagVars.add(Q[x-i][y+i])
    return antiDiagVars

# attackedVars returns the set of variables attacked by a queen at (x,y)
def attackedVars(x, y):
    s = varsInRow(x)
    s.update(varsInCol(y))
    s.update(varsInDiag(x, y))
    s.update(varsInAntiDiag(x, y))
    s.remove(Q[x][y])
    return s

# There must be a queen in each row and column
for i in range(n):
    solver.add_clause(varsInRow(i))
    solver.add_clause(varsInCol(i))

# No two queens can attack each other, if element is not a queen it will be negative
for i in range(n):
    for j in range(n):
        for attacked in attackedVars(i, j):
            solver.add_clause([-Q[i][j], -attacked])

# Solve the SAT problem
if solver.solve():
    model = solver.get_model()  # Get the satisfying assignment
    print(model)
    # Print model
    for i in range(n):
        s = ""
        for j in range(n):
            if model[j*n+i] > 0:
                s += "Q "
            else:
                s += "* "
        print(s)
else:
    print("UNSAT")  # Print if the problem is unsatisfiable


