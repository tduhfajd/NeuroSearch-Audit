package audit

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestCreateAuditHandler(t *testing.T) {
	t.Parallel()

	service := NewService("ruleset-1", "1.0.0")
	service.WithClock(func() time.Time {
		return time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC)
	})
	service.WithIDGenerator(func(time.Time) (string, error) {
		return "aud_20260311T120000Z_abc1234", nil
	})

	handler := NewHandler(service)
	mux := http.NewServeMux()
	handler.Register(mux)

	req := httptest.NewRequest(http.MethodPost, "/api/audits", bytes.NewBufferString(`{"url":"example.com"}`))
	rec := httptest.NewRecorder()

	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusAccepted {
		t.Fatalf("unexpected status code: %d", rec.Code)
	}
	if got := rec.Header().Get("Content-Type"); got != "application/json" {
		t.Fatalf("unexpected content type: %s", got)
	}
}
