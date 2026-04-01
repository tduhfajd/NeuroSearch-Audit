package audit

import (
	"context"
	"testing"
	"time"
)

func TestNormalizeSubmittedURL(t *testing.T) {
	t.Parallel()

	url, host, err := NormalizeSubmittedURL("Example.com/catalog?q=1")
	if err != nil {
		t.Fatalf("NormalizeSubmittedURL returned error: %v", err)
	}

	if url != "https://example.com/catalog?q=1" {
		t.Fatalf("unexpected normalized url: %s", url)
	}
	if host != "example.com" {
		t.Fatalf("unexpected host: %s", host)
	}
}

func TestNormalizeSubmittedURLRejectsUnsupportedScheme(t *testing.T) {
	t.Parallel()

	_, _, err := NormalizeSubmittedURL("ftp://example.com")
	if err == nil {
		t.Fatal("expected unsupported scheme error")
	}
}

func TestCreateAuditRecord(t *testing.T) {
	t.Parallel()

	service := NewService("ruleset-1", "1.0.0")
	fixedTime := time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC)
	service.WithClock(func() time.Time { return fixedTime })
	service.WithIDGenerator(func(time.Time) (string, error) {
		return "aud_20260311T120000Z_abc1234", nil
	})

	record, err := service.Create(context.Background(), IntakeRequest{URL: "example.com"})
	if err != nil {
		t.Fatalf("Create returned error: %v", err)
	}

	if record.Status != StatusAccepted {
		t.Fatalf("unexpected status: %s", record.Status)
	}
	if record.PackageStatus != PackageStatusNotReady {
		t.Fatalf("unexpected package status: %s", record.PackageStatus)
	}
	if len(record.StageRuns) != 1 {
		t.Fatalf("unexpected stage run count: %d", len(record.StageRuns))
	}
	if record.SubmittedURL != "https://example.com/" {
		t.Fatalf("unexpected submitted url: %s", record.SubmittedURL)
	}
	if record.NormalizedHost != "example.com" {
		t.Fatalf("unexpected normalized host: %s", record.NormalizedHost)
	}
}
