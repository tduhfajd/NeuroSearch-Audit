package main

import (
	"log"
	"net/http"

	"github.com/vadimevgrafov/neurosearch-analyzer/internal/audit"
	"github.com/vadimevgrafov/neurosearch-analyzer/internal/platform"
)

func main() {
	cfg := platform.LoadConfig()
	if err := cfg.Validate(); err != nil {
		log.Fatalf("load config: %v", err)
	}

	logger := platform.NewLogger()
	service := audit.NewService(cfg.DefaultRuleset, cfg.SchemaVersion)
	handler := audit.NewHandler(service)

	mux := http.NewServeMux()
	handler.Register(mux)

	logger.Info("starting api server", "addr", cfg.ListenAddr)
	if err := http.ListenAndServe(cfg.ListenAddr, mux); err != nil {
		log.Fatalf("listen and serve: %v", err)
	}
}
