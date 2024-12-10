package main

import (
	"fmt"
	"sort"
)

func Combinations(arr []int, d int) [][]int {
	if d == 0 || len(arr) == 0 {
		return [][]int{}
	}
	if d == 1 {
		combinations := make([][]int, len(arr))
		for i, v := range arr {
			combinations[i] = []int{v}
		}
		return combinations
	}

	var combinations [][]int
	for i := 0; i < len(arr); i++ {
		remaining := Combinations(arr[i+1:], d-1)
		for _, comb := range remaining {
			combinations = append(combinations, append([]int{arr[i]}, comb...))
		}
	}
	return combinations
}

func CreateClauses(t, n, d int) [][]int {
	var clauses [][]int
	m := make([][]int, t)
	x := 1

	for row := 0; row < t; row++ {
		v := make([]int, n)
		for column := 0; column < n; column++ {
			v[column] = x
			x++
		}
		m[row] = v
	}

	y := x

	for column := 0; column < n; column++ {
		var otherColumns []int
		for i := 0; i < n; i++ {
			if i != column {
				otherColumns = append(otherColumns, i)
			}
		}

		combinations := Combinations(otherColumns, d)

		for _, coveringColumns := range combinations {
			var ys []int
			for row := 0; row < t; row++ {
				ys = append(ys, y)
				clauses = append(clauses, []int{m[row][column], -y})
				for _, coveringColumn := range coveringColumns {
					clauses = append(clauses, []int{-m[row][coveringColumn], -y})
				}
				y++
			}
			clauses = append(clauses, ys)
		}
	}

	return clauses
}

func getBlocks(solution []int, n, t int) [][]int {
	blocks := make([][]int, n)

	for i := 0; i < n*t; i++ {
		x := solution[i]
		if x > 0 {
			blocks[(x-1)%n] = append(blocks[(x-1)%n], (x-1)/n+1)
		}
	}

	sort.Slice(blocks, func(i, j int) bool {
		return sum(blocks[i]) < sum(blocks[j])
	})

	return blocks
}

func sum(slice []int) int {
	total := 0
	for _, v := range slice {
		total += v
	}
	return total
}

func printBlocks(blocks [][]int) {
	fmt.Println("blocks:")
	for _, block := range blocks {
		fmt.Print(block, " ")
	}
	fmt.Println()
}
