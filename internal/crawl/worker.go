package crawl

import (
	"context"
	"fmt"
	neturl "net/url"
	"sort"
	"time"
)

type Reporter interface {
	Persist(context.Context, Report) error
}

type Worker struct {
	queue    Queue
	fetcher  Fetcher
	reporter Reporter
	maxDepth int
	throttle ThrottlePolicy
	now      func() time.Time
	sleep    func(context.Context, time.Duration) error
}

func NewWorker(queue Queue, fetcher Fetcher, reporter Reporter, maxDepth int) *Worker {
	return NewWorkerWithThrottle(queue, fetcher, reporter, maxDepth, ThrottlePolicy{
		MinRequestIntervalMillis: 250,
		MaxInFlightPerHost:       1,
	})
}

func NewWorkerWithThrottle(queue Queue, fetcher Fetcher, reporter Reporter, maxDepth int, throttle ThrottlePolicy) *Worker {
	if throttle.MinRequestIntervalMillis < 0 {
		throttle.MinRequestIntervalMillis = 0
	}
	if throttle.MaxInFlightPerHost <= 0 {
		throttle.MaxInFlightPerHost = 1
	}
	return &Worker{
		queue:    queue,
		fetcher:  fetcher,
		reporter: reporter,
		maxDepth: maxDepth,
		throttle: throttle,
		now:      time.Now().UTC,
		sleep: func(ctx context.Context, d time.Duration) error {
			timer := time.NewTimer(d)
			defer timer.Stop()
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-timer.C:
				return nil
			}
		},
	}
}

func (w *Worker) Run(ctx context.Context) (Report, error) {
	if w.queue == nil {
		return Report{}, fmt.Errorf("queue is required")
	}
	if w.fetcher == nil {
		return Report{}, fmt.Errorf("fetcher is required")
	}

	state := CrawlState{
		Visited:        make(map[string]struct{}),
		ThrottlePolicy: w.throttle,
	}
	lastFetchAtByHost := make(map[string]time.Time)
	report := Report{}

	for {
		job, ok := w.queue.Dequeue()
		if !ok {
			break
		}

		normalizedURL, err := NormalizeURL(job.URL)
		if err != nil {
			report.Outcomes = append(report.Outcomes, Outcome{
				AuditID:       job.AuditID,
				URL:           job.URL,
				NormalizedURL: job.URL,
				Depth:         job.Depth,
				Source:        job.Source,
				Status:        OutcomeFailed,
				Error:         err.Error(),
			})
			state.FailureCount++
			continue
		}

		if _, seen := state.Visited[normalizedURL]; seen {
			state.SkippedURLs = append(state.SkippedURLs, normalizedURL)
			report.Outcomes = append(report.Outcomes, Outcome{
				AuditID:       job.AuditID,
				URL:           job.URL,
				NormalizedURL: normalizedURL,
				Depth:         job.Depth,
				Source:        job.Source,
				Status:        OutcomeSkipped,
			})
			continue
		}

		if err := w.waitForThrottle(ctx, normalizedURL, lastFetchAtByHost); err != nil {
			return Report{}, err
		}
		result, err := w.fetcher.Fetch(ctx, normalizedURL)
		if err != nil {
			report.Outcomes = append(report.Outcomes, Outcome{
				AuditID:       job.AuditID,
				URL:           job.URL,
				NormalizedURL: normalizedURL,
				Depth:         job.Depth,
				Source:        job.Source,
				Status:        OutcomeFailed,
				Error:         err.Error(),
				FetchedAt:     result.FetchedAt,
			})
			state.FailureCount++
			state.Visited[normalizedURL] = struct{}{}
			state.VisitedURLs = append(state.VisitedURLs, normalizedURL)
			continue
		}

		state.Visited[normalizedURL] = struct{}{}
		state.VisitedURLs = append(state.VisitedURLs, normalizedURL)
		if host := normalizedHostname(normalizedURL); host != "" {
			lastFetchAtByHost[host] = w.now()
		}

		normalizedLinks := make([]string, 0, len(result.Links))
		if job.Depth < w.maxDepth {
			for _, link := range result.Links {
				normalizedLink, normalizeErr := NormalizeURL(link)
				if normalizeErr != nil {
					continue
				}
				if !ShouldFollowURL(normalizedLink) {
					state.FilteredURLs = append(state.FilteredURLs, normalizedLink)
					continue
				}
				normalizedLinks = append(normalizedLinks, normalizedLink)
				_ = w.queue.Enqueue(Job{
					AuditID: job.AuditID,
					URL:     normalizedLink,
					Depth:   job.Depth + 1,
					Parent:  normalizedURL,
					Source:  "discovered",
				})
			}
		}

		sort.Strings(normalizedLinks)
		report.Outcomes = append(report.Outcomes, Outcome{
			AuditID:                 job.AuditID,
			URL:                     job.URL,
			NormalizedURL:           normalizedURL,
			Depth:                   job.Depth,
			Source:                  job.Source,
			Status:                  OutcomeFetched,
			StatusCode:              result.StatusCode,
			Links:                   normalizedLinks,
			Body:                    result.Body,
			ContentType:             result.ContentType,
			StrictTransportSecurity: result.StrictTransportSecurity,
			FetchedAt:               result.FetchedAt,
		})
	}

	sort.Strings(state.VisitedURLs)
	sort.Strings(state.SkippedURLs)
	sort.Strings(state.FilteredURLs)
	state.FilteredURLs = compactStrings(state.FilteredURLs)
	report.State = state
	if w.reporter != nil {
		if err := w.reporter.Persist(ctx, report); err != nil {
			return Report{}, err
		}
	}
	return report, nil
}

func (w *Worker) waitForThrottle(ctx context.Context, rawURL string, lastFetchAtByHost map[string]time.Time) error {
	if w.throttle.MinRequestIntervalMillis <= 0 {
		return nil
	}
	host := normalizedHostname(rawURL)
	if host == "" {
		return nil
	}
	lastFetchAt, ok := lastFetchAtByHost[host]
	if !ok {
		return nil
	}
	waitFor := time.Duration(w.throttle.MinRequestIntervalMillis)*time.Millisecond - w.now().Sub(lastFetchAt)
	if waitFor <= 0 {
		return nil
	}
	if w.sleep == nil {
		return nil
	}
	return w.sleep(ctx, waitFor)
}

func normalizedHostname(rawURL string) string {
	parsed, err := neturl.Parse(rawURL)
	if err != nil {
		return ""
	}
	return parsed.Hostname()
}

func compactStrings(values []string) []string {
	if len(values) == 0 {
		return nil
	}
	result := values[:1]
	for _, value := range values[1:] {
		if value == result[len(result)-1] {
			continue
		}
		result = append(result, value)
	}
	return result
}
