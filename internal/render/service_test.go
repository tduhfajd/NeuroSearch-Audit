package render

import (
	"context"
	"testing"
	"time"
)

type stubRenderer struct {
	result Result
	err    error
}

func (s stubRenderer) Render(context.Context, Job) (Result, error) {
	return s.result, s.err
}

type stubWriter struct {
	called bool
	result Result
	err    error
}

func (s *stubWriter) WriteRenderedPage(_ context.Context, result Result) error {
	s.called = true
	s.result = result
	return s.err
}

func TestServiceRenderWritesArtifacts(t *testing.T) {
	t.Parallel()

	writer := &stubWriter{}
	service := NewService(stubRenderer{
		result: Result{
			RenderMode: "browser",
			HTML:       "<html></html>",
		},
	}, writer)
	service.now = func() time.Time {
		return time.Date(2026, 3, 11, 13, 0, 0, 0, time.UTC)
	}

	result, err := service.Render(context.Background(), Job{
		AuditID: "aud_20260311T120000Z_abc1234",
		URL:     "https://example.com/app",
		Reason:  "js-heavy",
	})
	if err != nil {
		t.Fatalf("Render returned error: %v", err)
	}
	if !writer.called {
		t.Fatal("expected writer to be called")
	}
	if result.SchemaVersion != "1.0.0" {
		t.Fatalf("unexpected schema version: %s", result.SchemaVersion)
	}
	if result.AuditID != "aud_20260311T120000Z_abc1234" {
		t.Fatalf("unexpected audit id: %s", result.AuditID)
	}
}
