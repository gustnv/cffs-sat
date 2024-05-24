import itertools
from pysat.solvers import *

class PHPSatSolver:
    def __init__(self, nof_holes):
        self.nof_holes = nof_holes
        self.nof_pigeons = self.nof_holes + 1
        self.clauses = self.CreateClauses()

    def CreateClauses(self):
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

        return clauses

    def Solve(self, solver_name="lingeling", with_proof=True):
        print("Checking satisfiability...")
        solver = Solver(name=solver_name, bootstrap_with=self.clauses, with_proof=with_proof)

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
