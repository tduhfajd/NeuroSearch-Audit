package extract

import (
	"context"
	"fmt"
)

type ArtifactWriter interface {
	WriteTechnicalPage(context.Context, TechnicalFeatures) error
}

type Service struct {
	parser *Parser
	writer ArtifactWriter
}

func NewService(parser *Parser, writer ArtifactWriter) *Service {
	return &Service{
		parser: parser,
		writer: writer,
	}
}

func (s *Service) Extract(ctx context.Context, input Input) (TechnicalFeatures, error) {
	if s.parser == nil {
		return TechnicalFeatures{}, fmt.Errorf("parser is required")
	}
	features, err := s.parser.Parse(input)
	if err != nil {
		return TechnicalFeatures{}, err
	}
	if s.writer != nil {
		if err := s.writer.WriteTechnicalPage(ctx, features); err != nil {
			return TechnicalFeatures{}, err
		}
	}
	return features, nil
}
