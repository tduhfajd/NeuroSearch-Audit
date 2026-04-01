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
	var root string
	flag.StringVar(&root, "root", ".", "output root containing runtime and runtime_batches")
	flag.Parse()

	summary, err := runtime.NewAggregator(root).Build(context.Background())
	if err != nil {
		log.Fatalf("build runtime summary: %v", err)
	}

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetEscapeHTML(false)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(summary); err != nil {
		log.Fatalf("encode summary: %v", err)
	}
}
