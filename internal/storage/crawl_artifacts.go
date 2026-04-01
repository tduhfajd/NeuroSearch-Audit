package storage

import (
	"fmt"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/crawl"
)

const crawlSchemaVersion = "1.0.0"

type VisitedURLsArtifact struct {
	SchemaVersion  string               `json:"schema_version"`
	AuditID        string               `json:"audit_id"`
	VisitedURLs    []string             `json:"visited_urls"`
	SkippedURLs    []string             `json:"skipped_urls"`
	FilteredURLs   []string             `json:"filtered_urls"`
	FailureCount   int                  `json:"failure_count"`
	ThrottlePolicy crawl.ThrottlePolicy `json:"throttle_policy"`
}

type FetchLogArtifact struct {
	SchemaVersion string          `json:"schema_version"`
	AuditID       string          `json:"audit_id"`
	Entries       []FetchLogEntry `json:"entries"`
}

type FetchLogEntry struct {
	URL                     string              `json:"url"`
	NormalizedURL           string              `json:"normalized_url"`
	Depth                   int                 `json:"depth"`
	Source                  string              `json:"source,omitempty"`
	Status                  crawl.OutcomeStatus `json:"status"`
	StatusCode              int                 `json:"status_code,omitempty"`
	ContentType             string              `json:"content_type,omitempty"`
	StrictTransportSecurity string              `json:"strict_transport_security,omitempty"`
	Error                   string              `json:"error,omitempty"`
	FetchedAt               string              `json:"fetched_at,omitempty"`
}

type RawPageArtifact struct {
	SchemaVersion           string `json:"schema_version"`
	AuditID                 string `json:"audit_id"`
	URL                     string `json:"url"`
	NormalizedURL           string `json:"normalized_url"`
	StatusCode              int    `json:"status_code"`
	ContentType             string `json:"content_type,omitempty"`
	StrictTransportSecurity string `json:"strict_transport_security,omitempty"`
	FetchedAt               string `json:"fetched_at,omitempty"`
	HTML                    string `json:"html"`
}

type LinkGraphArtifact struct {
	SchemaVersion string          `json:"schema_version"`
	AuditID       string          `json:"audit_id"`
	Edges         []LinkGraphEdge `json:"edges"`
}

type LinkGraphEdge struct {
	Source string `json:"source"`
	Target string `json:"target"`
}

func crawlArtifacts(report crawl.Report) (VisitedURLsArtifact, FetchLogArtifact, LinkGraphArtifact, error) {
	var auditID string
	entries := make([]FetchLogEntry, 0, len(report.Outcomes))
	edges := make([]LinkGraphEdge, 0)

	for _, outcome := range report.Outcomes {
		if outcome.AuditID == "" {
			return VisitedURLsArtifact{}, FetchLogArtifact{}, LinkGraphArtifact{}, fmt.Errorf("crawl outcome audit id is required")
		}
		if auditID == "" {
			auditID = outcome.AuditID
		}
		if outcome.AuditID != auditID {
			return VisitedURLsArtifact{}, FetchLogArtifact{}, LinkGraphArtifact{}, fmt.Errorf("mixed audit ids in report")
		}

		fetchedAt := ""
		if !outcome.FetchedAt.IsZero() {
			fetchedAt = outcome.FetchedAt.UTC().Format("2006-01-02T15:04:05Z")
		}

		entries = append(entries, FetchLogEntry{
			URL:                     outcome.URL,
			NormalizedURL:           outcome.NormalizedURL,
			Depth:                   outcome.Depth,
			Source:                  outcome.Source,
			Status:                  outcome.Status,
			StatusCode:              outcome.StatusCode,
			ContentType:             outcome.ContentType,
			StrictTransportSecurity: outcome.StrictTransportSecurity,
			Error:                   outcome.Error,
			FetchedAt:               fetchedAt,
		})

		for _, link := range outcome.Links {
			edges = append(edges, LinkGraphEdge{
				Source: outcome.NormalizedURL,
				Target: link,
			})
		}
	}

	visited := VisitedURLsArtifact{
		SchemaVersion:  crawlSchemaVersion,
		AuditID:        auditID,
		VisitedURLs:    sliceOrEmpty(report.State.VisitedURLs),
		SkippedURLs:    sliceOrEmpty(report.State.SkippedURLs),
		FilteredURLs:   sliceOrEmpty(report.State.FilteredURLs),
		FailureCount:   report.State.FailureCount,
		ThrottlePolicy: report.State.ThrottlePolicy,
	}
	fetchLog := FetchLogArtifact{
		SchemaVersion: crawlSchemaVersion,
		AuditID:       auditID,
		Entries:       entries,
	}
	linkGraph := LinkGraphArtifact{
		SchemaVersion: crawlSchemaVersion,
		AuditID:       auditID,
		Edges:         edges,
	}

	return visited, fetchLog, linkGraph, nil
}

func sliceOrEmpty(values []string) []string {
	if len(values) == 0 {
		return []string{}
	}
	return values
}
