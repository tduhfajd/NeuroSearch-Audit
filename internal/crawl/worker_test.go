package crawl

import (
	"context"
	"errors"
	"testing"
	"time"
)

type stubFetcher struct {
	results map[string]Result
	errors  map[string]error
}

type stubReporter struct {
	called bool
	report Report
	err    error
}

func (s *stubReporter) Persist(_ context.Context, report Report) error {
	s.called = true
	s.report = report
	return s.err
}

func (s stubFetcher) Fetch(_ context.Context, url string) (Result, error) {
	if err := s.errors[url]; err != nil {
		return Result{FetchedAt: time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC)}, err
	}
	result, ok := s.results[url]
	if !ok {
		return Result{FetchedAt: time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC)}, nil
	}
	return result, nil
}

func TestWorkerRunProcessesDiscoveredURLs(t *testing.T) {
	t.Parallel()

	queue := NewMemoryQueue()
	if err := queue.Enqueue(Job{
		AuditID: "aud_20260311T120000Z_abc1234",
		URL:     "https://example.com",
		Depth:   0,
		Source:  "submitted",
	}); err != nil {
		t.Fatalf("enqueue seed job: %v", err)
	}

	fetcher := stubFetcher{
		results: map[string]Result{
			"https://example.com/": {
				StatusCode: 200,
				Links: []string{
					"https://example.com/about",
					"https://example.com/about",
				},
				FetchedAt: time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC),
			},
			"https://example.com/about": {
				StatusCode: 200,
				FetchedAt:  time.Date(2026, 3, 11, 12, 1, 0, 0, time.UTC),
			},
		},
		errors: map[string]error{},
	}

	reporter := &stubReporter{}
	worker := NewWorker(queue, fetcher, reporter, 1)
	report, err := worker.Run(context.Background())
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}

	if len(report.Outcomes) != 2 {
		t.Fatalf("unexpected outcome count: %d", len(report.Outcomes))
	}
	if report.Outcomes[0].Source != "submitted" {
		t.Fatalf("unexpected first outcome source: %s", report.Outcomes[0].Source)
	}
	if report.Outcomes[1].Source != "discovered" {
		t.Fatalf("unexpected second outcome source: %s", report.Outcomes[1].Source)
	}
	if len(report.State.VisitedURLs) != 2 {
		t.Fatalf("unexpected visited count: %d", len(report.State.VisitedURLs))
	}
	if report.State.FailureCount != 0 {
		t.Fatalf("unexpected failure count: %d", report.State.FailureCount)
	}
	if !reporter.called {
		t.Fatal("expected reporter to be called")
	}
}

func TestWorkerRunRecordsFailures(t *testing.T) {
	t.Parallel()

	queue := NewMemoryQueue()
	if err := queue.Enqueue(Job{
		AuditID: "aud_20260311T120000Z_abc1234",
		URL:     "https://example.com",
		Depth:   0,
		Source:  "submitted",
	}); err != nil {
		t.Fatalf("enqueue seed job: %v", err)
	}

	worker := NewWorker(queue, stubFetcher{
		results: map[string]Result{},
		errors: map[string]error{
			"https://example.com/": errors.New("boom"),
		},
	}, nil, 1)

	report, err := worker.Run(context.Background())
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}

	if report.State.FailureCount != 1 {
		t.Fatalf("unexpected failure count: %d", report.State.FailureCount)
	}
	if report.Outcomes[0].Status != OutcomeFailed {
		t.Fatalf("unexpected outcome status: %s", report.Outcomes[0].Status)
	}
}

func TestWorkerRunDeduplicatesFilteredURLs(t *testing.T) {
	t.Parallel()

	queue := NewMemoryQueue()
	if err := queue.Enqueue(Job{
		AuditID: "aud_20260311T120000Z_abc1234",
		URL:     "https://example.com",
		Depth:   0,
		Source:  "submitted",
	}); err != nil {
		t.Fatalf("enqueue seed job: %v", err)
	}

	fetcher := stubFetcher{
		results: map[string]Result{
			"https://example.com/": {
				StatusCode: 200,
				Links: []string{
					"https://example.com/site.css",
					"https://example.com/site.css",
					"https://example.com/login/",
					"https://example.com/login/",
				},
				FetchedAt: time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC),
			},
		},
	}

	report, err := NewWorker(queue, fetcher, nil, 1).Run(context.Background())
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}

	if len(report.State.FilteredURLs) != 2 {
		t.Fatalf("unexpected filtered url count: %d", len(report.State.FilteredURLs))
	}
}

func TestWorkerRunAppliesThrottleBetweenSameHostRequests(t *testing.T) {
	t.Parallel()

	queue := NewMemoryQueue()
	if err := queue.Enqueue(Job{
		AuditID: "aud_20260311T120000Z_abc1234",
		URL:     "https://example.com",
		Depth:   0,
		Source:  "submitted",
	}); err != nil {
		t.Fatalf("enqueue seed job: %v", err)
	}

	fetcher := stubFetcher{
		results: map[string]Result{
			"https://example.com/": {
				StatusCode: 200,
				Links:      []string{"https://example.com/about"},
				FetchedAt:  time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC),
			},
			"https://example.com/about": {
				StatusCode: 200,
				FetchedAt:  time.Date(2026, 3, 11, 12, 0, 1, 0, time.UTC),
			},
		},
	}

	worker := NewWorkerWithThrottle(queue, fetcher, nil, 1, ThrottlePolicy{
		MinRequestIntervalMillis: 250,
		MaxInFlightPerHost:       1,
	})
	now := time.Date(2026, 3, 11, 12, 0, 0, 0, time.UTC)
	worker.now = func() time.Time { return now }
	sleepCalls := 0
	worker.sleep = func(_ context.Context, d time.Duration) error {
		sleepCalls++
		if d != 250*time.Millisecond {
			t.Fatalf("unexpected sleep duration: %s", d)
		}
		now = now.Add(d)
		return nil
	}

	report, err := worker.Run(context.Background())
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}
	if len(report.Outcomes) != 2 {
		t.Fatalf("unexpected outcome count: %d", len(report.Outcomes))
	}
	if sleepCalls != 1 {
		t.Fatalf("unexpected sleep call count: %d", sleepCalls)
	}
	if report.State.ThrottlePolicy.MinRequestIntervalMillis != 250 {
		t.Fatalf("unexpected throttle interval: %d", report.State.ThrottlePolicy.MinRequestIntervalMillis)
	}
	if report.State.ThrottlePolicy.MaxInFlightPerHost != 1 {
		t.Fatalf("unexpected max inflight per host: %d", report.State.ThrottlePolicy.MaxInFlightPerHost)
	}
}
