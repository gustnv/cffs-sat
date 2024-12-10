package main

import (
	"encoding/json"
	"fmt"
	"os"
)

const filePath = "data.json"

type Cff struct {
	D        int     `json:"d"`
	T        int     `json:"t"`
	N        int     `json:"n"`
	Status   string  `json:"status"`
	Solution [][]int `json:"solution"`
}

func SolutionExists(d, t, n int) (bool, error) {
	if _, fileDoesntExist := os.Stat(filePath); fileDoesntExist != nil {
		return false, nil
	}

	cffsByte, err := os.ReadFile(filePath)
	if err != nil {
		return false, err
	}

	var cffs []Cff
	err = json.Unmarshal(cffsByte, &cffs)
	if err != nil {
		return false, err
	}

	for _, cff := range cffs {
		if cff.D == d && cff.T == t && cff.N == n {
			if cff.Status != "TIMEOUT" {
				return true, nil
			}
		}
	}
	fmt.Println()

	return false, nil
}

func UpdateSolution(updatedCff Cff) error {
	var cffs []Cff

	if _, fileDoesntExist := os.Stat(filePath); fileDoesntExist == nil {
		cffsByte, err := os.ReadFile(filePath)
		if err != nil {
			return err
		}
		err = json.Unmarshal(cffsByte, &cffs)

		if err != nil {
			return err
		}
	}

	i := -1
	for index, cff := range cffs {
		if cff.D == updatedCff.D && cff.T == updatedCff.T && cff.N == updatedCff.N {
			i = index
			break
		}
	}

	if i == -1 {
		cffs = append(cffs, updatedCff)
	} else {
		if cffs[i].Status == "timeout" {
			cffs[i].Solution = updatedCff.Solution
		}
	}

	jsonData, err := json.MarshalIndent(cffs, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(filePath, jsonData, 0644)
}
