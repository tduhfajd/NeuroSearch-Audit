package crawl

import "testing"

func TestMemoryQueueDeduplicatesJobs(t *testing.T) {
	t.Parallel()

	queue := NewMemoryQueue()
	job := Job{AuditID: "aud_20260311T120000Z_abc1234", URL: "https://example.com"}

	if err := queue.Enqueue(job); err != nil {
		t.Fatalf("enqueue returned error: %v", err)
	}
	if err := queue.Enqueue(job); err != nil {
		t.Fatalf("enqueue duplicate returned error: %v", err)
	}

	if got := queue.Len(); got != 1 {
		t.Fatalf("unexpected queue length: %d", got)
	}
}

func TestNormalizeURL(t *testing.T) {
	t.Parallel()

	got, err := NormalizeURL("https://Example.com/catalog?q=1")
	if err != nil {
		t.Fatalf("NormalizeURL returned error: %v", err)
	}
	if got != "https://example.com/catalog?q=1" {
		t.Fatalf("unexpected normalized URL: %s", got)
	}
}
