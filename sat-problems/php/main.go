package main

import (
	"fmt"
	"log"

	"github.com/gustnv/gosat"
)

// PHPSatSolver represents a SAT solver demonstration of the Pigeonhole Principle problem.
type PHPSatSolver struct {
	nofHoles   int
	nofPigeons int
	clauses    [][]int
}

// NewPHPSatSolver initializes the solver with the number of holes and creates the necessary clauses.
func NewPHPSatSolver(nofHoles int) *PHPSatSolver {
	nofPigeons := nofHoles + 1
	return &PHPSatSolver{
		nofHoles:   nofHoles,
		nofPigeons: nofPigeons,
		clauses:    createClauses(nofHoles, nofPigeons),
	}
}

// createClauses creates the clauses representing the pigeonhole principle problem.
func createClauses(nofHoles, nofPigeons int) [][]int {
	var clauses [][]int
	variables := make([]int, nofHoles*nofPigeons)

	for i := range variables {
		variables[i] = i + 1
	}

	// First set of clauses: Each pigeon is placed in at least one hole.
	for i := 0; i < nofPigeons; i++ {
		clause := make([]int, nofHoles)
		for j := 0; j < nofHoles; j++ {
			clause[j] = variables[i*nofHoles+j]
		}
		clauses = append(clauses, clause)
	}

	// Second set of clauses: No two pigeons are placed in the same hole.
	for j := 0; j < nofHoles; j++ {
		var pigeons []int
		for i := 0; i < nofPigeons; i++ {
			pigeons = append(pigeons, -variables[i*nofHoles+j])
		}

		// Generate combinations of two pigeons in the same hole
		for x := 0; x < len(pigeons); x++ {
			for y := x + 1; y < len(pigeons); y++ {
				clauses = append(clauses, []int{pigeons[x], pigeons[y]})
			}
		}
	}

	fmt.Println(clauses)
	return clauses
}

// Solve solves the pigeonhole principle problem using a SAT solver.
func (p *PHPSatSolver) Solve() {
	fmt.Println("Checking satisfiability...")

	// Create a new solver instance
	s, err := solver.NewSolver(p.clauses)
	if err != nil {
		log.Fatalf("Failed to create solver: %v", err)
	}
	defer s.Delete()

	// Solve the problem
	satisfiable, err := s.Solve()
	if err != nil {
		log.Fatalf("Error solving the problem: %v", err)
	}

	if satisfiable {
		m, err := s.GetModel()
		if err != nil {
			log.Fatalf("Error getting model: %v", err)
		}
		fmt.Println("[SAT] Model:", m)
	} else {
		fmt.Println("[UNSAT]")
	}
}

func main() {
	solver := NewPHPSatSolver(2)
	solver.Solve()
}
