package main

import (
	"context"
	"encoding/json"
	"flag"
	"log"
	"os"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/runtime"
)

func main() {
	var (
		root    string
		auditID string
		attempt int
	)
	flag.StringVar(&root, "root", ".", "output root containing runtime state")
	flag.StringVar(&auditID, "audit-id", "", "audit identifier")
	flag.IntVar(&attempt, "attempt", 1, "run attempt number")
	flag.Parse()

	if auditID == "" {
		log.Fatal("audit-id is required")
	}

	store := runtime.NewFileStateStore(root)
	inspection, err := runtime.NewInspector(store, root).Inspect(context.Background(), auditID, attempt)
	if err != nil {
		log.Fatalf("inspect runtime state: %v", err)
	}

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetEscapeHTML(false)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(inspection); err != nil {
		log.Fatalf("encode inspection: %v", err)
	}
}
