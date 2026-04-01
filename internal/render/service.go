package render

import (
	"context"
	"fmt"
	"time"
)

type Renderer interface {
	Render(context.Context, Job) (Result, error)
}

type ArtifactWriter interface {
	WriteRenderedPage(context.Context, Result) error
}

type Service struct {
	renderer Renderer
	writer   ArtifactWriter
	now      func() time.Time
}

func NewService(renderer Renderer, writer ArtifactWriter) *Service {
	return &Service{
		renderer: renderer,
		writer:   writer,
		now:      time.Now().UTC,
	}
}

func (s *Service) Render(ctx context.Context, job Job) (Result, error) {
	if s.renderer == nil {
		return Result{}, fmt.Errorf("renderer is required")
	}
	if job.AuditID == "" {
		return Result{}, fmt.Errorf("audit id is required")
	}
	if job.URL == "" {
		return Result{}, fmt.Errorf("url is required")
	}

	result, err := s.renderer.Render(ctx, job)
	if err != nil {
		return Result{}, err
	}
	if result.SchemaVersion == "" {
		result.SchemaVersion = schemaVersion
	}
	if result.AuditID == "" {
		result.AuditID = job.AuditID
	}
	if result.URL == "" {
		result.URL = job.URL
	}
	if result.RenderedAt.IsZero() {
		result.RenderedAt = s.now()
	}
	if result.FinalURL == "" {
		result.FinalURL = result.URL
	}

	if s.writer != nil {
		if err := s.writer.WriteRenderedPage(ctx, result); err != nil {
			return Result{}, err
		}
	}
	return result, nil
}
