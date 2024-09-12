package main

import (
	"fmt"
	"github.com/gustnv/gosat"
)

func main() {
	s, err := solver.NewMinisatGH(nil, true, true)
	if err != nil {
		panic(err)
	}
	defer s.Delete()

	err = s.AddClause([]int{1, 2, 3, 4}, false)

	s.AddClause([]int{-1}, false)
	r, err := s.Solve()
	if err != nil {
		panic(err)
	}
	fmt.Println(r)
	fmt.Println(s.GetModel())
}
