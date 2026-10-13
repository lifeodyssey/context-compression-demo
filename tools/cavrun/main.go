// Based on /tmp/ctxlab/cavrun/main.go; CCR state is scoped to each invocation.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"unicode/utf8"

	"github.com/JuliusBrussee/caveman/engine"
	"github.com/JuliusBrussee/caveman/engine/ccr"
)

func dimensions(text string) map[string]int {
	lines := strings.Count(text, "\n")
	if text != "" && !strings.HasSuffix(text, "\n") {
		lines++
	}
	return map[string]int{"bytes": len(text), "characters": utf8.RuneCountInString(text), "lines": lines}
}

func keptLines(input, output, required string) (int, int) {
	before, kept := 0, 0
	for _, line := range strings.Split(input, "\n") {
		if strings.Contains(line, required) {
			before++
			if strings.Contains(output, line) {
				kept++
			}
		}
	}
	return before, kept
}

func run() error {
	if len(os.Args) < 2 || len(os.Args) > 3 {
		return fmt.Errorf("usage: cavrun <file> [query]")
	}
	input, err := os.ReadFile(os.Args[1])
	if err != nil {
		return err
	}
	query := ""
	if len(os.Args) == 3 {
		query = os.Args[2]
	}
	storeDir, err := os.MkdirTemp("", "context-demo-caveman-ccr-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(storeDir)
	store, err := ccr.Open(filepath.Join(storeDir, "ccr.db"))
	if err != nil {
		return err
	}
	defer store.Close()
	eng := engine.New(store, nil)
	res, err := eng.Compress(input, engine.Options{Mode: engine.ModeCompress, Query: query, Type: os.Getenv("CAV_TYPE")})
	if err != nil {
		return fmt.Errorf("compress: %w", err)
	}
	if _, err := os.Stdout.Write(res.Output); err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "type=%s tokens %d -> %d bytes %d -> %d passthrough=%v\n", res.ContentType, res.TokensBefore, res.TokensAfter, len(input), len(res.Output), res.PassedThrough())
	if path := os.Getenv("CAV_METADATA"); path != "" {
		encoded, err := json.Marshal(res)
		if err != nil {
			return err
		}
		metadata := map[string]any{}
		if err := json.Unmarshal(encoded, &metadata); err != nil {
			return err
		}
		before, after := string(input), string(res.Output)
		metadata["script"] = "scripts/run_caveman.sh"
		metadata["input"] = os.Args[1]
		metadata["query"] = query
		metadata["forced_type"] = os.Getenv("CAV_TYPE")
		metadata["input_dimensions"] = dimensions(before)
		metadata["output_dimensions"] = dimensions(after)
		metadata["passthrough"] = res.PassedThrough()
		metadata["unchanged"] = before == after
		metadata["freeship_lines_before"], metadata["freeship_lines_kept"] = keptLines(before, after, "coupon=FREESHIP")
		metadata["pricing_lines_before"], metadata["pricing_lines_kept"] = keptLines(before, after, "service=pricing")
		metadata["passed_test_lines_before"], metadata["passed_test_lines_kept"] = keptLines(before, after, " PASSED")
		elided := 0
		for _, match := range regexp.MustCompile(`(\d+) lines elided`).FindAllStringSubmatch(after, -1) {
			count, _ := strconv.Atoi(match[1])
			elided += count
		}
		metadata["lines_elided_in_markers"] = elided
		var issues []struct {
			Number int    `json:"number"`
			Title  string `json:"title"`
		}
		if json.Unmarshal(input, &issues) == nil && len(issues) > 0 {
			kept := []int{}
			issue42 := false
			for _, issue := range issues {
				if issue.Title != "" && strings.Contains(after, issue.Title) {
					kept = append(kept, issue.Number)
					issue42 = issue42 || issue.Number == 42
				}
			}
			metadata["issues_before"] = len(issues)
			metadata["issues_kept"] = len(kept)
			metadata["issues_elided"] = len(issues) - len(kept)
			metadata["kept_issue_numbers"] = kept
			metadata["issue_42_kept"] = issue42
		}
		encoded, err = json.MarshalIndent(metadata, "", "  ")
		if err != nil {
			return err
		}
		return os.WriteFile(path, append(encoded, '\n'), 0644)
	}
	return nil
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
