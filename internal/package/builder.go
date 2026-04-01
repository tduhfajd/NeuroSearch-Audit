package pkg

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

const manifestSchemaVersion = "1.0.0"
const manifestSelfChecksum = "self"

type Builder struct {
	now func() time.Time
}

func NewBuilder() *Builder {
	return &Builder{
		now: time.Now().UTC,
	}
}

func (b *Builder) Build(packageRoot string, auditID string) (Manifest, error) {
	return b.BuildWithStageOverrides(packageRoot, auditID, nil)
}

func (b *Builder) BuildWithStageOverrides(packageRoot string, auditID string, overrides map[string]StageStatus) (Manifest, error) {
	if auditID == "" {
		return Manifest{}, fmt.Errorf("audit id is required")
	}

	files, err := collectFiles(packageRoot, auditID)
	if err != nil {
		return Manifest{}, err
	}

	manifest := Manifest{
		SchemaVersion: manifestSchemaVersion,
		AuditID:       auditID,
		CreatedAt:     b.now(),
		RulesetVersions: map[string]string{
			"analysis": "mvp-1",
		},
		SchemaVersions: map[string]string{
			"manifest": manifestSchemaVersion,
			"audit":    "1.0.0",
		},
		StageStatus: computeStageStatus(files, overrides),
		Files:       files,
	}

	for _, file := range files {
		if file.Schema != "" && manifest.SchemaVersions[file.Schema] == "" {
			manifest.SchemaVersions[file.Schema] = "1.0.0"
		}
	}

	return manifest, nil
}

func (b *Builder) WriteManifest(packageRoot string, manifest Manifest) error {
	path := filepath.Join(packageRoot, manifest.AuditID, "manifest.json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("create manifest dir: %w", err)
	}
	payload, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal manifest: %w", err)
	}
	payload = append(payload, '\n')
	if err := os.WriteFile(path, payload, 0o644); err != nil {
		return fmt.Errorf("write manifest: %w", err)
	}
	return nil
}

func collectFiles(packageRoot, auditID string) ([]FileEntry, error) {
	base := filepath.Join(packageRoot, auditID)
	required := requiredFiles()
	fileMap := make(map[string]FileEntry, len(required))
	for _, entry := range required {
		fileMap[entry.Path] = entry
	}

	var files []FileEntry
	err := filepath.WalkDir(base, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(base, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		entry, ok := fileMap[rel]
		if !ok {
			entry = FileEntry{
				Path:     rel,
				Category: detectCategory(rel),
				Required: false,
				Schema:   detectSchema(rel),
			}
		}
		if rel == "manifest.json" {
			entry.Checksum = manifestSelfChecksum
		} else {
			checksum, checksumErr := checksumFile(path)
			if checksumErr != nil {
				return checksumErr
			}
			entry.Checksum = checksum
		}
		files = append(files, entry)
		delete(fileMap, rel)
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("walk package: %w", err)
	}

	for _, missing := range fileMap {
		files = append(files, missing)
	}

	sort.Slice(files, func(i, j int) bool {
		return files[i].Path < files[j].Path
	})
	return files, nil
}

func computeStageStatus(files []FileEntry, overrides map[string]StageStatus) map[string]StageStatus {
	lookup := make(map[string]FileEntry, len(files))
	for _, file := range files {
		lookup[file.Path] = file
	}

	hasAll := func(paths ...string) bool {
		for _, path := range paths {
			entry, ok := lookup[path]
			if !ok || entry.Checksum == "" {
				return false
			}
		}
		return true
	}

	status := map[string]StageStatus{
		"crawl":    statusFor(hasAll("crawl/visited_urls.json", "crawl/fetch_log.json", "crawl/link_graph.json")),
		"extract":  statusFor(hasAll("pages/technical/example.com_service.json") || anyWithPrefix(files, "pages/technical/")),
		"analyze":  statusFor(hasAll("analysis/entities.json", "analysis/normalized_facts.json", "analysis/coverage_report.json", "analysis/contradictions.json", "analysis/ai_readiness_scores.json", "analysis/recommendations.json")),
		"package":  statusFor(anyWithPrefix(files, "prompts/")),
		"validate": StagePending,
	}
	for stage, value := range overrides {
		status[stage] = value
	}
	return status
}

func statusFor(ok bool) StageStatus {
	if ok {
		return StageCompleted
	}
	return StagePending
}

func anyWithPrefix(files []FileEntry, prefix string) bool {
	for _, file := range files {
		if strings.HasPrefix(file.Path, prefix) && file.Checksum != "" {
			return true
		}
	}
	return false
}

func requiredFiles() []FileEntry {
	return []FileEntry{
		{Path: "manifest.json", Category: "audit", Required: true, Schema: "manifest"},
		{Path: "crawl/visited_urls.json", Category: "crawl", Required: true, Schema: "crawl/visited_urls"},
		{Path: "crawl/fetch_log.json", Category: "crawl", Required: true, Schema: "crawl/fetch_log"},
		{Path: "crawl/link_graph.json", Category: "crawl", Required: true, Schema: "crawl/link_graph"},
		{Path: "analysis/entities.json", Category: "analysis", Required: true, Schema: "entities"},
		{Path: "analysis/normalized_facts.json", Category: "analysis", Required: true, Schema: "normalized_facts"},
		{Path: "analysis/coverage_report.json", Category: "analysis", Required: true, Schema: "coverage_report"},
		{Path: "analysis/contradictions.json", Category: "analysis", Required: true, Schema: "contradictions"},
		{Path: "analysis/ai_readiness_scores.json", Category: "analysis", Required: true, Schema: "ai_readiness_scores"},
		{Path: "analysis/recommendations.json", Category: "analysis", Required: true, Schema: "recommendations"},
	}
}

func detectCategory(path string) string {
	switch {
	case strings.HasPrefix(path, "crawl/"):
		return "crawl"
	case strings.HasPrefix(path, "pages/"):
		return "page"
	case strings.HasPrefix(path, "analysis/"):
		return "analysis"
	case strings.HasPrefix(path, "exports/"):
		return "export"
	case strings.HasPrefix(path, "prompts/"):
		return "prompt"
	default:
		return "audit"
	}
}

func detectSchema(path string) string {
	switch path {
	case "manifest.json":
		return "manifest"
	case "analysis/entities.json":
		return "entities"
	case "analysis/normalized_facts.json":
		return "normalized_facts"
	case "analysis/coverage_report.json":
		return "coverage_report"
	case "analysis/contradictions.json":
		return "contradictions"
	case "analysis/ai_readiness_scores.json":
		return "ai_readiness_scores"
	case "analysis/recommendations.json":
		return "recommendations"
	case "analysis/legacy_factor_assessments.json":
		return "legacy_factor_assessments"
	case "analysis/legacy_index_scores.json":
		return "legacy_index_scores"
	case "exports/client_report_input.json":
		return "client_report_input"
	case "exports/client_report.json":
		return "client_report"
	case "exports/scoring_parity_snapshot.json":
		return "scoring_parity_snapshot"
	case "exports/expert_report.json":
		return "expert_report"
	case "exports/technical_client_report.json":
		return "technical_client_report"
	case "exports/commercial_offer.json":
		return "commercial_offer"
	case "exports/technical_action_plan.json":
		return "technical_action_plan"
	case "exports/review_brief.json":
		return "review_brief"
	case "exports/summary.json":
		return "export_summary"
	case "exports/backlog.json":
		return "export_backlog"
	case "crawl/visited_urls.json":
		return "crawl/visited_urls"
	case "crawl/fetch_log.json":
		return "crawl/fetch_log"
	case "crawl/link_graph.json":
		return "crawl/link_graph"
	case "audit.json":
		return "audit"
	default:
		return ""
	}
}

func checksumFile(path string) (string, error) {
	payload, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("read file for checksum: %w", err)
	}
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:]), nil
}
