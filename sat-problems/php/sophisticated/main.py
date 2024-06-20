import itertools
from pysat.solvers import *


class PHPSatSolver:
    """
    Demonstration of the Pigeonhole Principle problem using SAT solvers.

    The Pigeonhole Principle states that if n pigeons are placed into m holes
    with n > m, then at least one hole must contain more than one pigeon.

    The problem can be formulated as a SAT problem by creating a set of
    variables and clauses that represent the problem and then can be solved
    by checking the satisfiability of the clauses using a SAT solver.
    """

    def __init__(self, nof_holes):
        """Initializes the number of holes and pigeons, the second one is always greater
        by one than the number of holes that is given, and then creates the clauses.
        """

        self.nof_holes = nof_holes
        self.nof_pigeons = self.nof_holes + 1
        self.clauses = self.CreateClauses()

    def CreateClauses(self):
        """Creates the clauses that represent the pigeonhole principle problem.

        The clauses are created using variables xij, where i represents the 
        pigeon and j represents the hole. These variables are integers 
        calculated as i * n + j, where n is the number of pigeons and m is the 
        number of holes. The variables range from 1 to n * m. If a pigeon i is
        placed in hole j, Xij equals 1; otherwise, it equals 0.

        The first set of clauses ensures that each pigeon is placed in at least 
        one hole, it is build with a basic loop.
        And the second set of clauses ensures that each hole contains at most 
        one pigeon.
        """
        clauses = []
        variables = (list(range(1, self.nof_holes*self.nof_pigeons + 1)))

        for i in range(self.nof_pigeons):
            clause = []
            for j in range(self.nof_holes):
                clause.append(variables[i*self.nof_holes + j])
            clauses.append(clause)

        for j in range(self.nof_holes):
            pigeons = []
            for i in range(self.nof_pigeons):
                pigeons.append(-variables[i*self.nof_holes + j])
            for combination in itertools.combinations(pigeons, 2):
                clauses.append(list(combination))
        print(clauses)

        return clauses

    def Solve(self, solver_name="lingeling", with_proof=True):
        print("Checking satisfiability...")
        solver = Solver(name=solver_name,
                        bootstrap_with=self.clauses, with_proof=with_proof)

        if solver.solve():
            print("[SAT] ", end=" ")
            print("Model:", solver.get_model())
        else:
            print("[UNSAT]", end=" ")
            if with_proof:
                print("Proof:", solver.get_proof())
            print()

        solver.delete()


if __name__ == "__main__":
    solver = PHPSatSolver(2)
    solver.Solve()
