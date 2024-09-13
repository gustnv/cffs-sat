package main

import (
	"fmt"
	"github.com/gustnv/gosat"
)

func main() {
	// Define the conjunctive normal form (CNF) expression
	// (-1 v -2 v -3) ^ (1 v -2) ^ (2 v -3) ^ (3 v -1) ^ (1 v 2 v 3)
	cnf := [][]int{
		{-1, -2, -3},
		{1, -2},
		{2, -3},
		{3, -1},
		{1, 2, 3},
	}

	// Create a new solver object and initialize it with some clauses (bootstrapWith)
	s, err := solver.NewSolver(cnf[1:])
	if err != nil {
		fmt.Println("Error creating solver:", err)
		return
	}

	// Solve the problem
	solved, err := s.Solve()
	if err != nil {
		fmt.Println("Error solving:", err)
		return
	}

	if solved {
		fmt.Println("SAT: Model found")
		model, err := s.GetModel()
		if err != nil {
			fmt.Println("Error getting model:", err)
		} else {
			fmt.Println("Model:", model)
		}
	} else {
		fmt.Println("UNSAT: No model found")
	}

	s.Delete() // Ensure solver resources are released

	s, err = solver.NewSolver(cnf[1:])
	if err != nil {
		fmt.Println("Error creating solver:", err)
		return
	}

	// Add new clauses to the solver
	err = s.AppendFormula(cnf)
	if err != nil {
		fmt.Println("Error appending formula:", err)
		return
	}

	// Solve the problem again after adding new clauses
	solved, err = s.Solve()
	if err != nil {
		fmt.Println("Error solving:", err)
		return
	}

	if solved {
		fmt.Println("SAT: Model found")
		model, err := s.GetModel()
		if err != nil {
			fmt.Println("Error getting model:", err)
		} else {
			fmt.Println("Model:", model)
		}
	} else {
		fmt.Println("UNSAT: No model found")
	}
}
