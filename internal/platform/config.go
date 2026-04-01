package platform

import (
	"fmt"
	"os"
)

const (
	defaultListenAddr  = ":8080"
	defaultRuleset     = "mvp-1"
	defaultSchema      = "1.0.0"
	defaultWorkerLabel = "worker-1"
)

// Config holds minimal runtime configuration for the first execution slice.
type Config struct {
	ListenAddr     string
	DefaultRuleset string
	SchemaVersion  string
	WorkerID       string
}

// LoadConfig reads environment-backed runtime settings and applies sane MVP defaults.
func LoadConfig() Config {
	return Config{
		ListenAddr:     valueOrDefault("NEUROSEARCH_LISTEN_ADDR", defaultListenAddr),
		DefaultRuleset: valueOrDefault("NEUROSEARCH_RULESET_VERSION", defaultRuleset),
		SchemaVersion:  valueOrDefault("NEUROSEARCH_SCHEMA_VERSION", defaultSchema),
		WorkerID:       valueOrDefault("NEUROSEARCH_WORKER_ID", defaultWorkerLabel),
	}
}

func (c Config) Validate() error {
	if c.ListenAddr == "" {
		return fmt.Errorf("listen address is required")
	}
	if c.DefaultRuleset == "" {
		return fmt.Errorf("default ruleset version is required")
	}
	if c.SchemaVersion == "" {
		return fmt.Errorf("schema version is required")
	}
	if c.WorkerID == "" {
		return fmt.Errorf("worker id is required")
	}
	return nil
}

func valueOrDefault(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
