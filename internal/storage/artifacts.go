package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/crawl"
)

type ArtifactStore interface {
	WriteJSON(context.Context, string, any) error
}

type FileStore struct {
	root string
}

func NewFileStore(root string) *FileStore {
	return &FileStore{root: root}
}

func (s *FileStore) WriteJSON(_ context.Context, relativePath string, value any) error {
	fullPath := filepath.Join(s.root, relativePath)
	if err := os.MkdirAll(filepath.Dir(fullPath), 0o755); err != nil {
		return fmt.Errorf("create artifact directory: %w", err)
	}

	payload, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal json: %w", err)
	}
	payload = append(payload, '\n')

	if err := os.WriteFile(fullPath, payload, 0o644); err != nil {
		return fmt.Errorf("write artifact: %w", err)
	}
	return nil
}

func PersistCrawlReport(ctx context.Context, store ArtifactStore, report crawl.Report) error {
	if store == nil {
		return fmt.Errorf("artifact store is required")
	}

	visited, fetchLog, linkGraph, err := crawlArtifacts(report)
	if err != nil {
		return err
	}

	auditID := visited.AuditID
	if auditID == "" {
		return fmt.Errorf("audit id is required for crawl artifacts")
	}

	base := filepath.Join("audit_package", auditID, "crawl")
	if err := store.WriteJSON(ctx, filepath.Join(base, "visited_urls.json"), visited); err != nil {
		return err
	}
	if err := store.WriteJSON(ctx, filepath.Join(base, "fetch_log.json"), fetchLog); err != nil {
		return err
	}
	if err := store.WriteJSON(ctx, filepath.Join(base, "link_graph.json"), linkGraph); err != nil {
		return err
	}
	for _, outcome := range report.Outcomes {
		if outcome.Status != crawl.OutcomeFetched || outcome.Body == "" || !crawl.IsHTMLContentType(outcome.ContentType) {
			continue
		}
		if outcome.StatusCode < 200 || outcome.StatusCode >= 300 {
			continue
		}
		rawPage := RawPageArtifact{
			SchemaVersion:           crawlSchemaVersion,
			AuditID:                 outcome.AuditID,
			URL:                     outcome.URL,
			NormalizedURL:           outcome.NormalizedURL,
			StatusCode:              outcome.StatusCode,
			ContentType:             outcome.ContentType,
			StrictTransportSecurity: outcome.StrictTransportSecurity,
			FetchedAt:               outcome.FetchedAt.UTC().Format("2006-01-02T15:04:05Z"),
			HTML:                    outcome.Body,
		}
		if err := store.WriteJSON(ctx, filepath.Join("audit_package", auditID, "pages", "raw", TechnicalFilename(outcome.NormalizedURL)), rawPage); err != nil {
			return err
		}
	}

	return nil
}
