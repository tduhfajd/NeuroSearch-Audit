package platform

import (
	"log/slog"
	"os"
)

// NewLogger returns the default structured logger used by starter services.
func NewLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(os.Stdout, nil))
}
