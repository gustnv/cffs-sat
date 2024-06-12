from pysat.solvers import Solver


def x(i, j, d):
    return i * 81 + j * 9 + d


clauses = []

# For each cell
for i in range(9):
    for j in range(9):
        # Each cell contains at least one digit
        clauses.append([x(i, j, d) for d in range(1, 10)])

        # Each cell contains at most one digit
        for d1 in range(1, 10):
            for d2 in range(d1 + 1, 10):
                clauses.append([-x(i, j, d1), -x(i, j, d2)])

# Ensures that a given set of cells (which could represent a row, a column, or a 3x3 sub-grid) contains distinct values


def rule(cells):
    for i, c1 in enumerate(cells):
        for j, c2 in enumerate(cells):
            if i < j:
                for d in range(1, 10):
                    clauses.append([-x(c1[0], c1[1], d), -x(c2[0], c2[1], d)])


# Ensure rows have distinct values
for i in range(9):
    rule([(i, j) for j in range(9)])

# Ensure columns have distinct values
for j in range(9):
    rule([(i, j) for i in range(9)])

# Ensure 3x3 sub-grids have distinct values
for i in 0, 3, 6:
    for j in 0, 3, 6:
        rule([(i + k % 3, j + k // 3) for k in range(9)])

assert len(clauses) == 81 * (1 + 36) + 27 * 324

sudoku = [
    [0, 2, 0, 0, 0, 0, 0, 3, 0],
    [0, 0, 0, 6, 0, 1, 0, 0, 0],
    [0, 6, 8, 2, 0, 0, 0, 0, 5],
    [0, 0, 9, 0, 0, 8, 3, 0, 0],
    [0, 4, 6, 0, 0, 0, 7, 5, 0],
    [0, 0, 1, 3, 0, 0, 4, 0, 0],
    [9, 0, 0, 0, 0, 7, 5, 1, 0],
    [0, 0, 0, 1, 0, 4, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 9, 0]
]

# Initial condition
for i in range(9):
    for j in range(9):
        d = sudoku[i][j]
        if d:
            clauses.append([x(i, j, d)])


def print_model(model):
    def read_cell(i, j):
        # return the digit of cell i, j according to the solution
        for d in range(1, 10):
            if x(i, j, d) in model:
                return d

    for i in range(9):
        for j in range(9):
            sudoku[i][j] = read_cell(i, j)

    for i in range(9):
        for j in range(9):
            print(sudoku[i][j], end=" ")
        print()


solver = Solver(bootstrap_with=clauses)
if solver.solve():
    print("[SAT] ")
    print_model(solver.get_model())
else:
    print("[UNSAT]", end=" ")
