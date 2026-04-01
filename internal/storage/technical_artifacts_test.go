package storage

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/extract"
)

func TestWriteTechnicalPage(t *testing.T) {
	t.Parallel()

	root := t.TempDir()
	store := NewFileStore(root)

	err := store.WriteTechnicalPage(context.Background(), extract.TechnicalFeatures{
		SchemaVersion: "1.0.0",
		AuditID:       "aud_20260311T120000Z_abc1234",
		URL:           "https://example.com/service",
		Source:        "crawl",
		ExtractedAt:   time.Date(2026, 3, 11, 14, 0, 0, 0, time.UTC),
		Title:         "Service",
		Meta:          extract.Meta{Description: "Desc"},
		Headings:      extract.HeadingSummary{H1: []string{"Main"}, H2: []string{"Step"}},
		SchemaHints:   []string{"organization"},
	})
	if err != nil {
		t.Fatalf("WriteTechnicalPage returned error: %v", err)
	}

	path := filepath.Join(root, "audit_package", "aud_20260311T120000Z_abc1234", "pages", "technical", "example.com_service.json")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected technical artifact to exist: %v", err)
	}
}
