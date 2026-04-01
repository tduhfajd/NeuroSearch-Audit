package audit

import (
	"context"
	"crypto/rand"
	"encoding/base32"
	"fmt"
	"net/url"
	"strings"
	"time"
)

type Clock func() time.Time

type IDGenerator func(time.Time) (string, error)

type Service struct {
	rulesetVersion string
	schemaVersion  string
	clock          Clock
	idGenerator    IDGenerator
}

func NewService(rulesetVersion, schemaVersion string) *Service {
	return &Service{
		rulesetVersion: rulesetVersion,
		schemaVersion:  schemaVersion,
		clock:          time.Now().UTC,
		idGenerator:    GenerateAuditID,
	}
}

func (s *Service) WithClock(clock Clock) {
	if clock != nil {
		s.clock = clock
	}
}

func (s *Service) WithIDGenerator(generator IDGenerator) {
	if generator != nil {
		s.idGenerator = generator
	}
}

func (s *Service) Create(_ context.Context, req IntakeRequest) (Record, error) {
	submittedURL, normalizedHost, err := NormalizeSubmittedURL(req.URL)
	if err != nil {
		return Record{}, err
	}

	now := s.clock().UTC()
	auditID, err := s.idGenerator(now)
	if err != nil {
		return Record{}, err
	}

	record := Record{
		SchemaVersion:  s.schemaVersion,
		AuditID:        auditID,
		SubmittedURL:   submittedURL,
		NormalizedHost: normalizedHost,
		Status:         StatusAccepted,
		RulesetVersion: s.rulesetVersion,
		CreatedAt:      now,
		UpdatedAt:      now,
		StageRuns: []StageRun{
			{
				Stage:      StageAccepted,
				Status:     StageRunCompleted,
				Attempt:    1,
				StartedAt:  now,
				FinishedAt: &now,
				Inputs:     []string{submittedURL},
				Outputs:    []string{fmt.Sprintf("audit/%s", auditID)},
			},
		},
		PackageStatus: PackageStatusNotReady,
	}

	return record, ValidateRecord(record)
}

func NormalizeSubmittedURL(raw string) (submittedURL string, normalizedHost string, err error) {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return "", "", fmt.Errorf("url is required")
	}

	if !strings.Contains(trimmed, "://") {
		trimmed = "https://" + trimmed
	}

	parsed, err := url.Parse(trimmed)
	if err != nil {
		return "", "", fmt.Errorf("parse url: %w", err)
	}
	if parsed.Scheme == "" || parsed.Host == "" {
		return "", "", fmt.Errorf("url must include scheme and host")
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return "", "", fmt.Errorf("unsupported scheme %q", parsed.Scheme)
	}

	host := strings.ToLower(parsed.Hostname())
	if host == "" {
		return "", "", fmt.Errorf("url host is empty")
	}

	port := parsed.Port()
	normalizedHost = host
	if port != "" {
		normalizedHost = host + ":" + port
	}

	path := parsed.EscapedPath()
	if path == "" {
		path = "/"
	}

	normalized := url.URL{
		Scheme:   strings.ToLower(parsed.Scheme),
		Host:     normalizedHost,
		Path:     path,
		RawQuery: parsed.RawQuery,
	}

	return normalized.String(), normalizedHost, nil
}

func GenerateAuditID(at time.Time) (string, error) {
	var entropy [4]byte
	if _, err := rand.Read(entropy[:]); err != nil {
		return "", fmt.Errorf("read entropy: %w", err)
	}

	suffix := strings.ToLower(base32.StdEncoding.WithPadding(base32.NoPadding).EncodeToString(entropy[:]))
	return fmt.Sprintf("aud_%s_%s", at.UTC().Format("20060102T150405Z"), suffix), nil
}
