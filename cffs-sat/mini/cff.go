package main

func isSubset(block1, block2 []int) bool {
	set := make(map[int]bool)
	for _, elem := range block2 {
		set[elem] = true
	}
	for _, elem := range block1 {
		if !set[elem] {
			return false
		}
	}
	return true
}

func union(blocks [][]int) []int {
	set := make(map[int]bool)
	for _, block := range blocks {
		for _, elem := range block {
			set[elem] = true
		}
	}
	unionBlock := []int{}
	for elem := range set {
		unionBlock = append(unionBlock, elem)
	}
	return unionBlock
}

func isCff(blocks [][]int, d int) bool {
	n := len(blocks)
	for i := 0; i < n; i++ {
		for j := 0; j < (1 << n); j++ {
			selectedBlocks := [][]int{}
			for k := 0; k < n; k++ {
				if j&(1<<k) != 0 && k != i {
					selectedBlocks = append(selectedBlocks, blocks[k])
				}
			}
			if len(selectedBlocks) == d {
				if isSubset(blocks[i], union(selectedBlocks)) {
					return false
				}
			}
		}
	}
	return true
}
