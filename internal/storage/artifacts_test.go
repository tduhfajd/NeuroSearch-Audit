package storage

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/crawl"
)

func TestPersistCrawlReport(t *testing.T) {
	t.Parallel()

	root := t.TempDir()
	store := NewFileStore(root)

	report := crawl.Report{
		Outcomes: []crawl.Outcome{
			{
				AuditID:       "aud_20260311T120000Z_abc1234",
				URL:           "https://example.com/",
				NormalizedURL: "https://example.com/",
				Depth:         0,
				Status:        crawl.OutcomeFetched,
				StatusCode:    200,
				Links:         []string{"https://example.com/about"},
				Body:          "<html><body>ok</body></html>",
				ContentType:   "text/html; charset=utf-8",
				FetchedAt:     time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC),
			},
			{
				AuditID:       "aud_20260311T120000Z_abc1234",
				URL:           "https://example.com/site.css",
				NormalizedURL: "https://example.com/site.css",
				Depth:         0,
				Status:        crawl.OutcomeFetched,
				StatusCode:    200,
				Body:          "body { color: red; }",
				ContentType:   "text/css",
				FetchedAt:     time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC),
			},
			{
				AuditID:       "aud_20260311T120000Z_abc1234",
				URL:           "https://example.com/missing",
				NormalizedURL: "https://example.com/missing",
				Depth:         0,
				Status:        crawl.OutcomeFetched,
				StatusCode:    404,
				Body:          "<html><body>missing</body></html>",
				ContentType:   "text/html; charset=utf-8",
				FetchedAt:     time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC),
			},
		},
		State: crawl.CrawlState{
			VisitedURLs:  []string{"https://example.com/"},
			SkippedURLs:  []string{},
			FilteredURLs: []string{"https://example.com/site.css"},
			FailureCount: 0,
		},
	}

	if err := PersistCrawlReport(context.Background(), store, report); err != nil {
		t.Fatalf("PersistCrawlReport returned error: %v", err)
	}

	paths := []string{
		"audit_package/aud_20260311T120000Z_abc1234/crawl/visited_urls.json",
		"audit_package/aud_20260311T120000Z_abc1234/crawl/fetch_log.json",
		"audit_package/aud_20260311T120000Z_abc1234/crawl/link_graph.json",
		"audit_package/aud_20260311T120000Z_abc1234/pages/raw/example.com_.json",
	}
	for _, relative := range paths {
		content, err := os.ReadFile(filepath.Join(root, relative))
		if err != nil {
			t.Fatalf("read %s: %v", relative, err)
		}
		if !strings.Contains(string(content), `"audit_id": "aud_20260311T120000Z_abc1234"`) {
			t.Fatalf("artifact %s does not contain audit id", relative)
		}
	}

	cssPath := filepath.Join(root, "audit_package", "aud_20260311T120000Z_abc1234", "pages", "raw", "example.com_site.css.json")
	if _, err := os.Stat(cssPath); !os.IsNotExist(err) {
		t.Fatalf("expected non-html raw page to be skipped, stat err=%v", err)
	}

	notFoundPath := filepath.Join(root, "audit_package", "aud_20260311T120000Z_abc1234", "pages", "raw", "example.com_missing.json")
	if _, err := os.Stat(notFoundPath); !os.IsNotExist(err) {
		t.Fatalf("expected non-2xx html page to be skipped, stat err=%v", err)
	}
}
