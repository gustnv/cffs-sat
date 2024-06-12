from pysat.solvers import Solver


class SudokuSolver:
    def __init__(self, sudoku):
        self.solver = Solver()
        self.sudoku = sudoku
        self._update_particular_clauses()

    def _rank(self, i, j, d):
        return i * 81 + j * 9 + d

    def _unrank(self, x):
        return (x - 1) // 81, ((x - 1) % 81) // 9, ((x - 1) % 9) + 1

    def _create_commom_clauses(self):
        self.clauses = []

        # Ensures that a given set of cells(tuple list) contains distinct values
        def rule(cells):
            for i, c1 in enumerate(cells):
                for j, c2 in enumerate(cells):
                    if i < j:
                        for d in range(1, 10):
                            self.clauses.append(
                                [-self._rank(c1[0], c1[1], d), -self._rank(c2[0], c2[1], d)])

        # Ensure rows have distinct values
        for i in range(9):
            rule([(i, j) for j in range(9)])

        # Ensure columns have distinct values
        for j in range(9):
            rule([(i, j) for i in range(9)])

        # Ensure 3x3 sub-grids have distinct values
        for i in 0, 3, 6:
            for j in 0, 3, 6:
                rule([(i + k % 3, j + k // 3)
                     for k in range(9)])  # Subgrades 3x3

        # Each cell:
        for i in range(9):
            for j in range(9):
                # Contains at least one digit
                self.clauses.append([self._rank(i, j, d)
                                     for d in range(1, 10)])

                # Contains at most one digit
                for d1 in range(1, 10):
                    for d2 in range(d1 + 1, 10):
                        self.clauses.append(
                            [-self._rank(i, j, d1), -self._rank(i, j, d2)])

        assert len(self.clauses) == 81 * (1 + 36) + 27 * 324

    def _update_particular_clauses(self):
        self._create_commom_clauses()

        # Initial condition
        for i in range(9):
            for j in range(9):
                d = self.sudoku[i][j]
                if d:
                    self.clauses.append([self._rank(i, j, d)])

    def solve(self):
        self.solver.clear_interrupt()
        self.solver.append_formula(self.clauses)

        if self.solver.solve():
            print("[SAT]")

            for e in self.solver.get_model():
                if e > 0:
                    i, j, d = self._unrank(e)
                    self.sudoku[i][j] = d

            self.print_sudoku()
        else:
            print("[UNSAT]")

    def print_sudoku(self):
        for row in self.sudoku:
            print(" ".join(map(str, row)))


if __name__ == "__main__":
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

    solver = SudokuSolver(sudoku)
    solver.solve()
