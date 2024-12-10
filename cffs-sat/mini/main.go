package main

import (
	"context"
	"fmt"
	"github.com/gustnv/gosat/minisat"
	"time"
)

type Solution struct {
	t, n, d  int
	solution bool
	blocks   [][]int
	err      error
	status   string
}

func find(d, t, n int, timeout time.Duration) (string, [][]int) {
	fmt.Printf("Finding Solution for d=%d, t=%d, n=%d\n", d, t, n)

	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Recovered from panic, likely due to memory exhaustion or timeout")
		}
	}()

	solver, err := minisat.NewSolver()
	if err != nil || solver == nil {
		fmt.Println("Error initializing solver")
		return "ERROR", nil
	}
	defer solver.Delete()

	solver.AddClauses(CreateClauses(t, n, d))

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	solution, err := solver.Solve()
	if err != nil {
		fmt.Printf("Error during solving: %v\n", err)
		return "ERROR", nil
	}

	select {
	case <-ctx.Done():
		fmt.Println("Solver timed out")
		return "TIMEOUT", nil
	default:
		if solution {
			model, err := solver.GetModel()
			if err != nil {
				fmt.Println("Error retrieving model")
				return "ERROR", nil
			}
			blocks := getBlocks(model[0:n*t], n, t)
			return "SAT", blocks
		}
		return "UNSAT", nil
	}
}

func findAll(d, t, n int) {
	for {
		solExists, _ := SolutionExists(d, t, n)
		if !solExists {
			info, blocks := find(d, t, n, 10*time.Second)
			UpdateSolution(Cff{D: d, T: t, N: n, Status: info, Solution: blocks})
			if info != "SAT" {
				t++
				n = t
			}
		}
		n++
	}
}

func findOne(d, t, n int) {
	solExists, _ := SolutionExists(d, t, n)
	if !solExists {
		info, blocks := find(d, t, n, 10*time.Second)
		fmt.Println("Solution found")

		// if isCff(blocks, d) {
		UpdateSolution(Cff{D: d, T: t, N: n, Status: info, Solution: blocks})
		fmt.Println(info, blocks)
		// }
	} else {
		fmt.Printf("Solution for d=%d, t=%d, n=%d already exists\n", d, t, n)
	}
}

func main() {
	// findAll(1, 5, 11)
	// b := [][]int{{1, 2, 6}, {1, 4, 5}, {1, 3, 7}, {2, 3, 8}, {2, 4, 7}, {3, 5, 6}, {2, 5, 9}, {3, 4, 9}, {1, 8, 9}, {4, 6, 8}, {5, 7, 8}, {6, 7, 9}}
	findOne(2, 13, 26)

}
