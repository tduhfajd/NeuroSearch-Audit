package storage

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/extract"
)

func (s *FileStore) WriteTechnicalPage(ctx context.Context, features extract.TechnicalFeatures) error {
	if features.AuditID == "" {
		return fmt.Errorf("audit id is required")
	}
	if features.URL == "" {
		return fmt.Errorf("url is required")
	}

	filename := TechnicalFilename(features.URL)
	relative := filepath.Join("audit_package", features.AuditID, "pages", "technical", filename)
	return s.WriteJSON(ctx, relative, features)
}

func TechnicalFilename(url string) string {
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
