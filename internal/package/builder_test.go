package pkg

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestBuilderBuildAndWriteManifest(t *testing.T) {
	t.Parallel()

	root := t.TempDir()
	auditID := "aud_20260311T120000Z_abc1234"
	base := filepath.Join(root, auditID)

	files := map[string]string{
		"crawl/visited_urls.json":                  "{}\n",
		"crawl/fetch_log.json":                     "{}\n",
		"crawl/link_graph.json":                    "{}\n",
		"pages/technical/example.com_service.json": "{}\n",
		"analysis/entities.json":                   "{}\n",
		"analysis/normalized_facts.json":           "{}\n",
		"analysis/coverage_report.json":            "{}\n",
		"analysis/contradictions.json":             "{}\n",
		"analysis/ai_readiness_scores.json":        "{}\n",
		"analysis/recommendations.json":            "{}\n",
		"exports/client_report_input.json":         "{}\n",
		"exports/client_report.json":               "{}\n",
		"exports/expert_report.json":               "{}\n",
		"exports/commercial_offer.json":            "{}\n",
		"exports/technical_action_plan.json":       "{}\n",
		"exports/review_brief.json":                "{}\n",
		"exports/summary.json":                     "{}\n",
		"exports/backlog.json":                     "{}\n",
		"prompts/client-report.md":                 "# prompt\n",
	}

	for relative, content := range files {
		path := filepath.Join(base, relative)
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			t.Fatalf("mkdir %s: %v", relative, err)
		}
		if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
			t.Fatalf("write %s: %v", relative, err)
		}
	}

	builder := NewBuilder()
	builder.now = func() time.Time {
		return time.Date(2026, 3, 11, 18, 0, 0, 0, time.UTC)
	}

	manifest, err := builder.Build(root, auditID)
	if err != nil {
		t.Fatalf("Build returned error: %v", err)
	}
	if manifest.StageStatus["crawl"] != StageCompleted {
		t.Fatalf("unexpected crawl status: %s", manifest.StageStatus["crawl"])
	}
	if manifest.StageStatus["analyze"] != StageCompleted {
		t.Fatalf("unexpected analyze status: %s", manifest.StageStatus["analyze"])
	}
	if err := builder.WriteManifest(root, manifest); err != nil {
		t.Fatalf("WriteManifest returned error: %v", err)
	}

	path := filepath.Join(base, "manifest.json")
	payload, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read manifest: %v", err)
	}

	var decoded Manifest
	if err := json.Unmarshal(payload, &decoded); err != nil {
		t.Fatalf("unmarshal manifest: %v", err)
	}
	if decoded.AuditID != auditID {
		t.Fatalf("unexpected audit id: %s", decoded.AuditID)
	}
	foundReviewBrief := false
	foundClientReportInput := false
	foundClientReport := false
	foundExpertReport := false
	foundCommercialOffer := false
	foundTechnicalPlan := false
	foundSummary := false
	foundBacklog := false
	for _, entry := range decoded.Files {
		if entry.Path == "exports/client_report_input.json" {
			foundClientReportInput = true
			if entry.Category != "export" {
				t.Fatalf("expected client_report_input category export, got %s", entry.Category)
			}
			if entry.Schema != "client_report_input" {
				t.Fatalf("expected client_report_input schema, got %s", entry.Schema)
			}
		}
		if entry.Path == "exports/client_report.json" {
			foundClientReport = true
			if entry.Category != "export" {
				t.Fatalf("expected client_report category export, got %s", entry.Category)
			}
			if entry.Schema != "client_report" {
				t.Fatalf("expected client_report schema, got %s", entry.Schema)
			}
		}
		if entry.Path == "exports/expert_report.json" {
			foundExpertReport = true
			if entry.Category != "export" {
				t.Fatalf("expected expert_report category export, got %s", entry.Category)
			}
			if entry.Schema != "expert_report" {
				t.Fatalf("expected expert_report schema, got %s", entry.Schema)
			}
		}
		if entry.Path == "exports/commercial_offer.json" {
			foundCommercialOffer = true
			if entry.Category != "export" {
				t.Fatalf("expected commercial_offer category export, got %s", entry.Category)
			}
			if entry.Schema != "commercial_offer" {
				t.Fatalf("expected commercial_offer schema, got %s", entry.Schema)
			}
		}
		if entry.Path == "exports/technical_action_plan.json" {
			foundTechnicalPlan = true
			if entry.Category != "export" {
				t.Fatalf("expected technical_action_plan category export, got %s", entry.Category)
			}
			if entry.Schema != "technical_action_plan" {
				t.Fatalf("expected technical_action_plan schema, got %s", entry.Schema)
			}
		}
		if entry.Path == "exports/review_brief.json" {
			foundReviewBrief = true
			if entry.Required {
				t.Fatal("expected review_brief to remain optional in manifest inventory")
			}
			if entry.Category != "export" {
				t.Fatalf("expected review_brief category export, got %s", entry.Category)
			}
			if entry.Schema != "review_brief" {
				t.Fatalf("expected review_brief schema, got %s", entry.Schema)
			}
		}
		if entry.Path == "exports/summary.json" {
			foundSummary = true
			if entry.Category != "export" {
				t.Fatalf("expected summary category export, got %s", entry.Category)
			}
			if entry.Schema != "export_summary" {
				t.Fatalf("expected export_summary schema, got %s", entry.Schema)
			}
		}
		if entry.Path == "exports/backlog.json" {
			foundBacklog = true
			if entry.Category != "export" {
				t.Fatalf("expected backlog category export, got %s", entry.Category)
			}
			if entry.Schema != "export_backlog" {
				t.Fatalf("expected export_backlog schema, got %s", entry.Schema)
			}
		}
	}
	if !foundReviewBrief {
		t.Fatal("expected review_brief entry in manifest inventory")
	}
	if !foundClientReportInput {
		t.Fatal("expected client_report_input entry in manifest inventory")
	}
	if !foundClientReport {
		t.Fatal("expected client_report entry in manifest inventory")
	}
	if !foundExpertReport {
		t.Fatal("expected expert_report entry in manifest inventory")
	}
	if !foundCommercialOffer {
		t.Fatal("expected commercial_offer entry in manifest inventory")
	}
	if !foundTechnicalPlan {
		t.Fatal("expected technical_action_plan entry in manifest inventory")
	}
	if !foundSummary {
		t.Fatal("expected summary entry in manifest inventory")
	}
	if !foundBacklog {
		t.Fatal("expected backlog entry in manifest inventory")
	}
}

func TestBuilderUsesStableManifestEntryAndOverrides(t *testing.T) {
	t.Parallel()

	root := t.TempDir()
	auditID := "aud_20260311T120000Z_abc1234"
	base := filepath.Join(root, auditID)

	files := map[string]string{
		"manifest.json":                            "{}\n",
		"crawl/visited_urls.json":                  "{}\n",
		"crawl/fetch_log.json":                     "{}\n",
		"crawl/link_graph.json":                    "{}\n",
		"pages/technical/example.com_service.json": "{}\n",
		"analysis/entities.json":                   "{}\n",
		"analysis/normalized_facts.json":           "{}\n",
		"analysis/coverage_report.json":            "{}\n",
		"analysis/contradictions.json":             "{}\n",
		"analysis/ai_readiness_scores.json":        "{}\n",
		"analysis/recommendations.json":            "{}\n",
		"exports/review_brief.json":                "{}\n",
		"prompts/client_report_prompt.md":          "# prompt\n",
	}

	for relative, content := range files {
		path := filepath.Join(base, relative)
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			t.Fatalf("mkdir %s: %v", relative, err)
		}
		if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
			t.Fatalf("write %s: %v", relative, err)
		}
	}

	builder := NewBuilder()
	manifest, err := builder.BuildWithStageOverrides(root, auditID, map[string]StageStatus{"validate": StageCompleted})
	if err != nil {
		t.Fatalf("BuildWithStageOverrides returned error: %v", err)
	}

	if manifest.StageStatus["validate"] != StageCompleted {
		t.Fatalf("unexpected validate status: %s", manifest.StageStatus["validate"])
	}

	for _, entry := range manifest.Files {
		if entry.Path == "manifest.json" && entry.Checksum != manifestSelfChecksum {
			t.Fatalf("unexpected manifest checksum: %s", entry.Checksum)
		}
	}
}
