package main

import (
	"fmt"
	"log"

	"github.com/gustnv/gosat" // Assuming the Go version of the solver is correctly set up in this package
)

type NQueensSatSolver struct {
	n      int
	board  [][]int
	solver *solver.Solver
}

func NewNQueensSatSolver(n int) *NQueensSatSolver {
	board := createBoard(n)
	solverInstance, err := solver.NewSolver() // Handle the error from NewSolver
	if err != nil {
		log.Fatalf("Failed to create a new solver: %v", err)
	}

	return &NQueensSatSolver{
		n:      n,
		board:  board,
		solver: solverInstance,
	}
}

func createBoard(n int) [][]int {
	board := make([][]int, n)
	for i := range board {
		board[i] = make([]int, n)
		for j := range board[i] {
			board[i][j] = i*n + j + 1
		}
	}
	return board
}

func (s *NQueensSatSolver) queensInRow(i int) []int {
	return s.board[i]
}

func (s *NQueensSatSolver) queensInColumn(j int) []int {
	column := make([]int, s.n)
	for i := 0; i < s.n; i++ {
		column[i] = s.board[i][j]
	}
	return column
}

func (s *NQueensSatSolver) queensInDiag(x, y int) []int {
	diagVars := []int{s.board[x][y]}
	for i := 1; i < s.n; i++ {
		if x+i < s.n && y+i < s.n {
			diagVars = append(diagVars, s.board[x+i][y+i])
		}
		if x-i >= 0 && y-i >= 0 {
			diagVars = append(diagVars, s.board[x-i][y-i])
		}
	}
	return diagVars
}

func (s *NQueensSatSolver) queensInAntiDiag(x, y int) []int {
	antiDiagVars := []int{s.board[x][y]}
	for i := 1; i < s.n; i++ {
		if x+i < s.n && y-i >= 0 {
			antiDiagVars = append(antiDiagVars, s.board[x+i][y-i])
		}
		if x-i >= 0 && y+i < s.n {
			antiDiagVars = append(antiDiagVars, s.board[x-i][y+i])
		}
	}
	return antiDiagVars
}

func (s *NQueensSatSolver) attackedVars(x, y int) map[int]struct{} {
	attacked := make(map[int]struct{})
	for _, v := range s.queensInRow(x) {
		attacked[v] = struct{}{}
	}
	for _, v := range s.queensInColumn(y) {
		attacked[v] = struct{}{}
	}
	for _, v := range s.queensInDiag(x, y) {
		attacked[v] = struct{}{}
	}
	for _, v := range s.queensInAntiDiag(x, y) {
		attacked[v] = struct{}{}
	}
	delete(attacked, s.board[x][y])
	return attacked
}

func (s *NQueensSatSolver) createClauses() {
	// First set of clauses: There must be a queen in each row.
	for i := 0; i < s.n; i++ {
		s.solver.AddClause(s.queensInRow(i))
	}

	// Second set of clauses: There must be a queen in each column.
	for i := 0; i < s.n; i++ {
		s.solver.AddClause(s.queensInColumn(i))
	}

	// Third set of clauses: No two queens can attack each other.
	for i := 0; i < s.n; i++ {
		for j := 0; j < s.n; j++ {
			for attacked := range s.attackedVars(i, j) {
				s.solver.AddClause([]int{-s.board[i][j], -attacked})
			}
		}
	}
}

func (s *NQueensSatSolver) solve() {
	s.createClauses()
	result, err := s.solver.Solve()
	if err != nil {
		log.Fatalf("[Error] %v", err)
	}
	if result {
		fmt.Println("[SAT]")
		s.printModel()
	} else {
		fmt.Println("[UNSAT]")
	}
}

func (s *NQueensSatSolver) printModel() {
	model, err := s.solver.GetModel()
	if err != nil {
		log.Fatalf("[Error] %v", err)
	}
	fmt.Println("Solution:")
	for i := 0; i < s.n; i++ {
		line := ""
		for j := 0; j < s.n; j++ {
			if model[s.board[i][j]-1] > 0 {
				line += "👑"
			} else {
				if (i+j)%2 == 0 {
					line += "⬜"
				} else {
					line += "⬛"
				}
			}
		}
		fmt.Println(line)
	}
}

func main() {
	solver := NewNQueensSatSolver(12)
	solver.solve()
}
