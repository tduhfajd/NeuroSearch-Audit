package extract

import (
	"context"
	"testing"
)

type stubWriter struct {
	called   bool
	features TechnicalFeatures
	err      error
}

func (s *stubWriter) WriteTechnicalPage(_ context.Context, features TechnicalFeatures) error {
	s.called = true
	s.features = features
	return s.err
}

func TestServiceExtractWritesArtifact(t *testing.T) {
	t.Parallel()

	writer := &stubWriter{}
	service := NewService(NewParser(), writer)

	features, err := service.Extract(context.Background(), Input{
		AuditID: "aud_20260311T120000Z_abc1234",
		URL:     "https://example.com",
		HTML:    "<html><head><title>Hello</title></head></html>",
		Source:  "crawl",
	})
	if err != nil {
		t.Fatalf("Extract returned error: %v", err)
	}
	if !writer.called {
		t.Fatal("expected writer to be called")
	}
	if features.Title != "Hello" {
		t.Fatalf("unexpected title: %s", features.Title)
	}
}
