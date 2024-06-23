import itertools
from pysat.solvers import Solver


class PHPSatSolver:
    """
    Demonstration of the Pigeonhole Principle problem using SAT solvers.

    The Pigeonhole Principle states that if n pigeons are placed into m holes
    with n > m, then at least one hole must contain more than one pigeon.

    The problem can be formulated as a SAT problem by creating a set of
    variables and clauses that represent the problem and then can be solved
    by checking the satisfiability of the clauses using a SAT solver.

    If the problem is satisfiable, it means that the Pigeonhole Principle is
    violated, and if it is unsatisfiable, it means that the pigeonhole
    principle holds.
    """

    def __init__(self, nof_holes):
        """Initializes the number of holes and pigeons, with the number of
        pigeons always being one more than the number of holes, and then
        creates the clauses."""

        self.nof_holes = nof_holes
        self.nof_pigeons = self.nof_holes + 1
        self.clauses = self.CreateClauses()

    def CreateClauses(self):
        """Creates and returns the clauses that represent the pigeonhole
        principle problem.

        The clauses are created using variables xij, where i represents the
        ith pigeon and j represents the jth hole. These variables are integers
        calculated as i * m + j, where m is the number of holes. The variables
        range from 1 to n * m. If a pigeon i is placed in hole j, xij equals 1;
        otherwise, it equals 0.

        The first set of clauses ensures that, for each pigeon, there is a
        clause that contains all the variables representing the holes. This
        ensures that each pigeon is placed in at least one hole. For the ith
        pigeon, we perform a logical OR between all the variables from i*m+1
        to i*m+m.

        The second set of clauses ensures that no two pigeons are placed in the
        same hole. For each hole, we create a clause that contains all the
        variables representing the pigeons. We then create a combination of all
        the variables, two by two, in the clause and negate them to ensure that
        no two pigeons are placed in the same hole. The negation comes from
        transforming "x implies not y" into "not x or not y", in other words,
        if x pigeon is in that hole, then y pigeon can't be there.
        """

        clauses = []
        variables = (list(range(1, self.nof_holes*self.nof_pigeons + 1)))

        # First set of clauses: Each pigeon is placed in at least one hole.
        for i in range(self.nof_pigeons):
            clause = []
            for j in range(self.nof_holes):
                clause.append(variables[i*self.nof_holes + j])
            clauses.append(clause)

        # Second set of clauses: No two pigeons are placed in the same hole.
        for j in range(self.nof_holes):
            pigeons = []
            for i in range(self.nof_pigeons):
                pigeons.append(-variables[i*self.nof_holes + j])
            for combination in itertools.combinations(pigeons, 2):
                clauses.append(list(combination))
        print(clauses)

        return clauses

    def Solve(self, solver_name="lingeling", with_proof=True):
        """Solves the pigeonhole principle problem using a SAT solver."""

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

        solver.delete()


if __name__ == "__main__":
    solver = PHPSatSolver(2)
    solver.Solve()
