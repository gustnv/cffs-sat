import itertools
from pysat.solvers import Solver

d = 2
t = 9
n = 12


clauses = []
m = []
x = 1
for row in range(t):
    v = []
    for column in range(n):
        v.append(x)
        x += 1
    m.append(v)

w = x

columns_combinations = itertools.combinations(range(n), d + 1)
for selected_columns in columns_combinations:
    w_m = [[0 for _ in range(n)] for _ in range(t)]
    for w_r in range(t):
        for w_c in selected_columns:
            w_m[w_r][w_c] = w
            w += 1

    for row_ind in range(t):
        for col_ind in selected_columns:
            for cursor in selected_columns:
                if cursor == col_ind:
                    clauses.append(
                        [-w_m[row_ind][col_ind], m[row_ind][cursor]])
                else:
                    clauses.append(
                        [-w_m[row_ind][col_ind], -m[row_ind][cursor]])

    for col_ind in selected_columns:
        ws = []
        for row_ind in range(t):
            ws.append(w_m[row_ind][col_ind])
        clauses.append(ws[:])


print(len(clauses), w)
s = Solver(name='g4')
s.append_formula(clauses)
s.solve()
blocks = [[] for _ in range(n)]

for x in list(s.get_model()[0:n*t]):
    if x > 0:
        blocks[(x-1) % n].append(((x-1) // n) + 1)

blocks = sorted(blocks, key=lambda x: sum(x))
print('blocks:')
for block in blocks:
    print(block, end=" ")
print()
