package crawl

import (
	"context"
	"time"
)

type Result struct {
	StatusCode              int
	Links                   []string
	Body                    string
	ContentType             string
	StrictTransportSecurity string
	FetchedAt               time.Time
}

type Fetcher interface {
	Fetch(context.Context, string) (Result, error)
}
