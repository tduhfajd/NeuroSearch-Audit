package storage

import (
	"context"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/crawl"
)

type CrawlReportWriter struct {
	Store ArtifactStore
}

func (w CrawlReportWriter) Persist(ctx context.Context, report crawl.Report) error {
	return PersistCrawlReport(ctx, w.Store, report)
}
