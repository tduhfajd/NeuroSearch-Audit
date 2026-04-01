package storage

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/render"
)

func TestWriteRenderedPage(t *testing.T) {
	t.Parallel()

	root := t.TempDir()
	store := NewFileStore(root)

	err := store.WriteRenderedPage(context.Background(), render.Result{
		SchemaVersion: "1.0.0",
		AuditID:       "aud_20260311T120000Z_abc1234",
		URL:           "https://example.com/app",
		RenderMode:    "browser",
		FinalURL:      "https://example.com/app",
		HTML:          "<html></html>",
		RenderedAt:    time.Date(2026, 3, 11, 13, 0, 0, 0, time.UTC),
	})
	if err != nil {
		t.Fatalf("WriteRenderedPage returned error: %v", err)
	}

	path := filepath.Join(root, "audit_package", "aud_20260311T120000Z_abc1234", "pages", "rendered", "example.com_app.json")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected rendered artifact to exist: %v", err)
	}
}
