from pysat.solvers import Solver


class SudokuSolver:
    """
    Solves a Sudoku puzzle using SAT solvers.

    The Sudoku puzzle is a classic combinatorial problem that requires filling
    a 9x9 grid with digits so that each column, each row, and each of the nine
    3x3 subgrids that compose the grid contain all of the digits from 1 to 9.
    """

    def __init__(self, sudoku):
        """Initializes the Sudoku puzzle and the SAT solver."""

        self.solver = Solver()
        self.sudoku = sudoku
        self._update_particular_clauses()

    def _ranking(self, i, j, d):
        """Computes the unique rank for a given position (i, j) and value d
        in a 9x9 Sudoku grid. This ranking function determines the position
        of the combinatorial object (i.e., a specific digit in a specific cell)
        among all possible objects in the Sudoku puzzle.

        The ranking ensures a unique mapping by combining the row index (i),
        column index (j), and the digit (d) to produce a single integer.

        Parameters:
        i (int): The row index (0-8).
        j (int): The column index (0-8).
        d (int): The digit value (1-9).

        Returns:
        int: The unique rank for the given combinatorial object (position and
        digit). Rank represents the variable of the problem and can range from
        1 to 729.
        """

        return i * 81 + j * 9 + d

    def _unranking(self, x):
        """Computes the position (i, j) and value d in a 9x9 Sudoku grid
        from a given rank x. This unranking function finds the combinatorial
        object (i.e., the specific digit in a specific cell) corresponding
        to the given rank, effectively reversing the ranking process.

        The unranking function decomposes the rank into the row index (i),
        column index (j), and the digit (d).

        Parameters:
        x (int): The rank to be converted into position and digit.

        Returns:
        tuple: A tuple (i, j, d) where
            i (int): The row index (0-8).
            j (int): The column index (0-8).
            d (int): The digit value (1-9).
        """

        return (x - 1) // 81, ((x - 1) % 81) // 9, ((x - 1) % 9) + 1

    def _create_commom_clauses(self):
        """Creates the common clauses for the Sudoku puzzle.

        The first set of clauses ensures each cell contains at least one and at
        most one digit. For each cell, the function generates:
        1. A clause with all possible digits (1-9) to ensure at least one digit
        is present. For example, for cell (0, 0), the clause would be:
        [self._ranking(0, 0, 1), self._ranking(0, 0, 2), ...,
        self._ranking(0, 0, 9)]. This results in 1 clause per cell.
        2. For each pair of digits, a clause with the negation of both to
        ensure at most one digit is present. This results in 36 clauses per
        cell. The negation is achieved by transforming "x implies not y"
        into "not x or not y".

        The rule function ensures a given list of cells contains distinct
        values by generating the necessary clauses. It takes all possible pairs
        of cells and for each digit from 1 to 10, it appends the negation of
        the ranking function for each pair and digit. The negation is achieved
        by transforming "x implies not y" into "not x or not y". This ensures
        if a digit is in a position, it cannot be in another. For a list of
        length n, the number of clauses generated is n(n-1)/2 * 9. For a list
        of length 9, 324 clauses are generated.

        The subsequent sets of clauses ensure distinct values within rows,
        columns,and 3x3 sub-grids. For each context (row, column, or sub-grid),
        the function gathers the relevant cells and passes them to the rule
        function, which generates the necessary clauses to enforce distinct
        values.
        """

        self.clauses = []

        # For each cell:
        for i in range(9):
            for j in range(9):
                # Contains at least one digit.
                self.clauses.append([self._ranking(i, j, d)
                                    for d in range(1, 10)])

                # Contains at most one digit.
                for d1 in range(1, 10):
                    for d2 in range(d1 + 1, 10):
                        self.clauses.append(
                            [-self._ranking(i, j, d1),
                             -self._ranking(i, j, d2)])

        def rule(cells):
            for i, c1 in enumerate(cells):
                for j, c2 in enumerate(cells):
                    if i < j:
                        for d in range(1, 10):
                            self.clauses.append(
                                [-self._ranking(c1[0], c1[1], d),
                                 -self._ranking(c2[0], c2[1], d)])

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

        assert len(self.clauses) == 81 * (1 + 36) + (9 + 9 + 9) * 324

    def _update_particular_clauses(self):
        """Updates the common clauses with the particular clauses for the
        initial condition of the Sudoku puzzle.
        """

        self._create_commom_clauses()
        for i in range(9):
            for j in range(9):
                d = self.sudoku[i][j]
                if d:
                    self.clauses.append([self._ranking(i, j, d)])

    def solve(self):
        """Solves the sudoku SAT solving the clauses generated """

        self.solver.clear_interrupt()
        self.solver.append_formula(self.clauses)

        if self.solver.solve():
            print("[SAT]")

            for e in self.solver.get_model():
                if e > 0:
                    i, j, d = self._unranking(e)
                    self.sudoku[i][j] = d

            self.print_sudoku()
        else:
            print("[UNSAT]")

    def print_sudoku(self):
        """Prints the Sudoku puzzle."""

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
