package main

import (
	"context"
	"flag"
	"log"
	"os"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/platform"
	"github.com/vadimevgrafov/neurosearch-analyzer/internal/runtime"
)

func main() {
	cfg := platform.LoadConfig()
	if err := cfg.Validate(); err != nil {
		log.Fatalf("load config: %v", err)
	}

	var (
		manifestPath string
		outputRoot   string
		pythonBin    string
	)
	flag.StringVar(&manifestPath, "manifest", "", "path to batch manifest json")
	flag.StringVar(&outputRoot, "root", ".", "output root for runtime artifacts")
	flag.StringVar(&pythonBin, "python-bin", "python3", "python interpreter used for analysis and validation stages")
	flag.Parse()

	if manifestPath == "" {
		log.Fatal("manifest is required")
	}

	workspaceRoot, err := os.Getwd()
	if err != nil {
		log.Fatalf("resolve workspace root: %v", err)
	}

	manifest, err := runtime.LoadBatchManifest(manifestPath)
	if err != nil {
		log.Fatalf("load batch manifest: %v", err)
	}

	report, err := runtime.BatchRunner{}.Run(context.Background(), manifest, manifestPath, runtime.RunConfig{
		OutputRoot:    outputRoot,
		PythonBin:     pythonBin,
		WorkspaceRoot: workspaceRoot,
		WorkerID:      cfg.WorkerID,
		Ruleset:       cfg.DefaultRuleset,
		SchemaVersion: cfg.SchemaVersion,
	})
	if err != nil {
		log.Fatalf("run batch manifest: %v", err)
	}

	log.Printf("batch run completed: batch_id=%s status=%s items=%d", report.BatchID, report.Status, len(report.Items))
}
