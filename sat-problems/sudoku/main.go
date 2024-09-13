package main

import (
	"fmt"
	"log"

	"github.com/gustnv/gosat" // Assuming a similar SAT solver library in Go is available
)

type SudokuSolver struct {
	sudoku  [9][9]int
	solver  *solver.Solver
	clauses [][]int
}

func NewSudokuSolver(sudoku [9][9]int) *SudokuSolver {
	solverInstance, err := solver.NewSolver()
	if err != nil {
		log.Fatalf("Failed to create a new solver: %v", err)
	}

	s := &SudokuSolver{
		sudoku: sudoku,
		solver: solverInstance,
	}
	s.updateParticularClauses()
	return s
}

func (s *SudokuSolver) ranking(i, j, d int) int {
	// Computes the unique rank for a given position (i, j) and value d in a 9x9 Sudoku grid
	return i*81 + j*9 + d
}

func (s *SudokuSolver) unranking(x int) (int, int, int) {
	// Computes the position (i, j) and value d in a 9x9 Sudoku grid from a given rank x
	i := (x - 1) / 81
	j := ((x - 1) % 81) / 9
	d := ((x - 1) % 9) + 1
	return i, j, d
}

func (s *SudokuSolver) createCommonClauses() {
	// Creates the common clauses for the Sudoku puzzle
	s.clauses = [][]int{}

	// For each cell: Contains at least one digit and at most one digit
	for i := 0; i < 9; i++ {
		for j := 0; j < 9; j++ {
			// Clause to ensure each cell has at least one digit
			atLeastOneDigit := []int{}
			for d := 1; d <= 9; d++ {
				atLeastOneDigit = append(atLeastOneDigit, s.ranking(i, j, d))
			}
			s.clauses = append(s.clauses, atLeastOneDigit)

			// Clauses to ensure each cell has at most one digit
			for d1 := 1; d1 <= 9; d1++ {
				for d2 := d1 + 1; d2 <= 9; d2++ {
					s.clauses = append(s.clauses, []int{-s.ranking(i, j, d1), -s.ranking(i, j, d2)})
				}
			}
		}
	}

	// Function to enforce distinct values within lists of cells (rows, columns, sub-grids)
	rule := func(cells [][2]int) {
		for i := 0; i < len(cells); i++ {
			for j := i + 1; j < len(cells); j++ {
				for d := 1; d <= 9; d++ {
					s.clauses = append(s.clauses, []int{-s.ranking(cells[i][0], cells[i][1], d), -s.ranking(cells[j][0], cells[j][1], d)})
				}
			}
		}
	}

	// Ensure rows have distinct values
	for i := 0; i < 9; i++ {
		cells := [][2]int{}
		for j := 0; j < 9; j++ {
			cells = append(cells, [2]int{i, j})
		}
		rule(cells)
	}

	// Ensure columns have distinct values
	for j := 0; j < 9; j++ {
		cells := [][2]int{}
		for i := 0; i < 9; i++ {
			cells = append(cells, [2]int{i, j})
		}
		rule(cells)
	}

	// Ensure 3x3 sub-grids have distinct values
	for i := 0; i <= 6; i += 3 {
		for j := 0; j <= 6; j += 3 {
			cells := [][2]int{}
			for k := 0; k < 9; k++ {
				cells = append(cells, [2]int{i + k%3, j + k/3})
			}
			rule(cells)
		}
	}
}

func (s *SudokuSolver) updateParticularClauses() {
	// Updates the common clauses with the particular clauses for the initial condition of the Sudoku puzzle
	s.createCommonClauses()
	for i := 0; i < 9; i++ {
		for j := 0; j < 9; j++ {
			if d := s.sudoku[i][j]; d != 0 {
				s.clauses = append(s.clauses, []int{s.ranking(i, j, d)})
			}
		}
	}
}

func (s *SudokuSolver) solve() {
	// Solves the sudoku SAT by solving the generated clauses
	s.solver.AppendFormula(s.clauses)
	result, err := s.solver.Solve()
	if err != nil {
		log.Fatalf("Failed to solve the Sudoku: %v", err)
	}

	if result {
		fmt.Println("[SAT]")
		model, _ := s.solver.GetModel()
		for _, e := range model {
			if e > 0 {
				i, j, d := s.unranking(e)
				s.sudoku[i][j] = d
			}
		}
		s.printSudoku()
	} else {
		fmt.Println("[UNSAT]")
	}
}

func (s *SudokuSolver) printSudoku() {
	// Prints the Sudoku puzzle
	for _, row := range s.sudoku {
		for _, num := range row {
			fmt.Printf("%d ", num)
		}
		fmt.Println()
	}
}

func main() {
	sudoku := [9][9]int{
		{0, 2, 0, 0, 0, 0, 0, 3, 0},
		{0, 0, 0, 6, 0, 1, 0, 0, 0},
		{0, 6, 8, 2, 0, 0, 0, 0, 5},
		{0, 0, 9, 0, 0, 8, 3, 0, 0},
		{0, 4, 6, 0, 0, 0, 7, 5, 0},
		{0, 0, 1, 3, 0, 0, 4, 0, 0},
		{9, 0, 0, 0, 0, 7, 5, 1, 0},
		{0, 0, 0, 1, 0, 4, 0, 0, 0},
		{0, 1, 0, 0, 0, 0, 0, 9, 0},
	}

	solver := NewSudokuSolver(sudoku)
	solver.solve()
}
