package storage

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/render"
)

func (s *FileStore) WriteRenderedPage(ctx context.Context, result render.Result) error {
	if result.AuditID == "" {
		return fmt.Errorf("audit id is required")
	}
	if result.URL == "" {
		return fmt.Errorf("url is required")
	}

	filename := renderFilename(result.URL)
	relative := filepath.Join("audit_package", result.AuditID, "pages", "rendered", filename)
	return s.WriteJSON(ctx, relative, result)
}

func renderFilename(url string) string {
	replacer := strings.NewReplacer(
		"https://", "",
		"http://", "",
		"/", "_",
		"?", "_",
		"&", "_",
		"=", "_",
		":", "_",
	)
	name := replacer.Replace(url)
	if name == "" {
		name = "page"
	}
	return name + ".json"
}
