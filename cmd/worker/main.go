package main

import (
	"context"
	"log"
	"time"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/crawl"
	"github.com/vadimevgrafov/neurosearch-analyzer/internal/platform"
	"github.com/vadimevgrafov/neurosearch-analyzer/internal/storage"
)

func main() {
	cfg := platform.LoadConfig()
	if err := cfg.Validate(); err != nil {
		log.Fatalf("load config: %v", err)
	}

	logger := platform.NewLogger()
	queue := crawl.NewMemoryQueue()
	reporter := storage.CrawlReportWriter{Store: storage.NewFileStore(".")}
	worker := crawl.NewWorker(queue, noopFetcher{}, reporter, 1)

	report, err := worker.Run(context.Background())
	if err != nil {
		log.Fatalf("run worker: %v", err)
	}

	logger.Info("worker runtime initialized", "worker_id", cfg.WorkerID, "outcomes", len(report.Outcomes))
}

type noopFetcher struct{}

func (noopFetcher) Fetch(context.Context, string) (crawl.Result, error) {
	return crawl.Result{
		StatusCode: 204,
		FetchedAt:  time.Now().UTC(),
	}, nil
}
