from pysat.solvers import Solver


class NQueensSatSolver:
    """
    Solves the N-Queens problem using SAT solvers.

    The N-Queens problem is a classic combinatorial problem that requires
    placing N queens on an NxN chessboard so that no two queens attack each
    other.
    """

    def __init__(self, n):
        """Initializes the board and the SAT solver."""

        self.n = n
        self.board = self._create_board()
        self.solver = Solver()

    def _create_board(self):
        """Creates an NxN board with unique variables for each cell.

        A variable is calculated as i * n + j + 1, where i and j are the row
        and column indexes of the cell, respectively. The variables range from
        1 to n^2.

        For example, for a 4x4 board, the variables are as follows:
        1  2   3  4
        5  6   7  8
        9  10 11 12
        13 14 15 16

        Returns: A 2D list representing the board.
        """

        board = [[0 for j in range(self.n)] for i in range(self.n)]
        for i in range(self.n):
            for j in range(self.n):
                board[i][j] = i*self.n + j + 1
        return board

    def _queens_in_row(self, i):
        """Returns the variables representing the queens in the ith row."""

        return self.board[i]

    def _queens_in_column(self, j):
        """Returns the variables representing the queens in the jth column."""

        return [self.board[i][j] for i in range(self.n)]

    def _queens_in_diag(self, x, y):
        """Returns the variables representing the queens in the diagonal
        containing the cell (x, y).
        """

        diag_vars = [self.board[x][y]]
        for i in range(self.n):
            if x+i in range(self.n) and y+i in range(self.n):
                diag_vars.append(self.board[x+i][y+i])
            if x-i in range(self.n) and y-i in range(self.n):
                diag_vars.append(self.board[x-i][y-i])
        return diag_vars

    def _queens_in_anti_diag(self, x, y):
        """Returns the variables representing the queens in the anti-diagonal
        containing the cell (x, y).
        """

        anti_diag_vars = [self.board[x][y]]
        for i in range(self.n):
            if x+i in range(self.n) and y-i in range(self.n):
                anti_diag_vars.append(self.board[x+i][y-i])
            if x-i in range(self.n) and y+i in range(self.n):
                anti_diag_vars.append(self.board[x-i][y+i])
        return anti_diag_vars

    def _attacked_vars(self, x, y):
        """Returns the set of variables attacked by the queen in cell (x, y).
        This set is the union of the variables in the same row, column,
        diagonal, and anti-diagonal as the queen, excluding the queen's
        variable.
        """

        s = set()
        s.update(self._queens_in_row(x))
        s.update(self._queens_in_column(y))
        s.update(self._queens_in_diag(x, y))
        s.update(self._queens_in_anti_diag(x, y))
        s.remove(self.board[x][y])
        return s

    def create_clauses(self):
        """Creates the clauses that represent the N-Queens problem.

        The first set of clauses ensures that there is a queen in each row.

        The second set of clauses ensures that there is a queen in each column.

        The third set of clauses ensures that no two queens can attack each
        other. For each posible position of a queen, represented by the
        variable x, from 1 to n^2, we create a clause with the negations of the
        queen and all the variables attacked by the queen. The negation comes
        from transforming "x implies not y" into "not x or not y", in other
        words, if the queen is in position x, then none of the attacked
        variables can be true.
        """

        # First set of clauses: There must be a queen in each row.
        for i in range(self.n):
            self.solver.add_clause(self._queens_in_row(i))

        # Second set of clauses: There must be a queen in each column.
        for i in range(self.n):
            self.solver.add_clause(self._queens_in_column(i))

        # Third set of clauses: No two queens can attack each other.
        for i in range(self.n):
            for j in range(self.n):
                for attacked in self._attacked_vars(i, j):
                    self.solver.add_clause([-self.board[i][j], -attacked])

    def solve(self, with_proof=True):
        """Solves the N-Queens problem using a SAT solver."""

        self.create_clauses()
        if self.solver.solve():
            print("[SAT] ")
            self.print_model()
        else:
            print("[UNSAT]", end=" ")
            if with_proof:
                print("Proof:", solver.get_proof())

    def print_model(self):
        """Prints the solution to the N-Queens problem."""

        print("Solution:")
        for i in range(self.n):
            s = ""
            for j in range(self.n):
                if self.solver.get_model()[self.board[i][j]-1] > 0:
                    s += "👑"
                else:
                    s += "⬜" if (i + j) % 2 == 0 else "⬛"
            print(s)


if __name__ == "__main__":
    solver = NQueensSatSolver(12)
    solver.solve()
