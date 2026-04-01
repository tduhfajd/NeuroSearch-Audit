package crawl

import (
	"fmt"
	"net/url"
	"strings"
)

func NormalizeURL(raw string) (string, error) {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return "", fmt.Errorf("url is required")
	}

	parsed, err := url.Parse(trimmed)
	if err != nil {
		return "", fmt.Errorf("parse url: %w", err)
	}
	if parsed.Scheme == "" || parsed.Host == "" {
		return "", fmt.Errorf("url must include scheme and host")
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return "", fmt.Errorf("unsupported scheme %q", parsed.Scheme)
	}

	host := strings.ToLower(parsed.Hostname())
	if host == "" {
		return "", fmt.Errorf("url host is empty")
	}
	port := parsed.Port()
	if port != "" {
		host += ":" + port
	}

	path := parsed.EscapedPath()
	if path == "" {
		path = "/"
	}

	normalized := url.URL{
		Scheme:   strings.ToLower(parsed.Scheme),
		Host:     host,
		Path:     path,
		RawQuery: parsed.RawQuery,
	}

	return normalized.String(), nil
}
