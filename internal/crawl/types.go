package crawl

import "time"

type ThrottlePolicy struct {
	MinRequestIntervalMillis int `json:"min_request_interval_ms"`
	MaxInFlightPerHost       int `json:"max_inflight_per_host"`
}

type Job struct {
	AuditID string
	URL     string
	Depth   int
	Parent  string
	Source  string
}

type OutcomeStatus string

const (
	OutcomeFetched OutcomeStatus = "fetched"
	OutcomeFailed  OutcomeStatus = "failed"
	OutcomeSkipped OutcomeStatus = "skipped"
)

type Outcome struct {
	AuditID                 string        `json:"audit_id"`
	URL                     string        `json:"url"`
	NormalizedURL           string        `json:"normalized_url"`
	Depth                   int           `json:"depth"`
	Source                  string        `json:"source,omitempty"`
	Status                  OutcomeStatus `json:"status"`
	StatusCode              int           `json:"status_code,omitempty"`
	Links                   []string      `json:"links,omitempty"`
	Body                    string        `json:"-"`
	ContentType             string        `json:"content_type,omitempty"`
	StrictTransportSecurity string        `json:"strict_transport_security,omitempty"`
	Error                   string        `json:"error,omitempty"`
	FetchedAt               time.Time     `json:"fetched_at"`
}

type CrawlState struct {
	Visited        map[string]struct{} `json:"-"`
	VisitedURLs    []string            `json:"visited_urls"`
	SkippedURLs    []string            `json:"skipped_urls"`
	FilteredURLs   []string            `json:"filtered_urls"`
	FailureCount   int                 `json:"failure_count"`
	ThrottlePolicy ThrottlePolicy      `json:"throttle_policy"`
}

type Report struct {
	Outcomes []Outcome  `json:"outcomes"`
	State    CrawlState `json:"state"`
}
