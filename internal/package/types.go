package pkg

import "time"

type StageStatus string

const (
	StagePending   StageStatus = "pending"
	StageCompleted StageStatus = "completed"
	StageFailed    StageStatus = "failed"
	StageRejected  StageStatus = "rejected"
)

type FileEntry struct {
	Path     string `json:"path"`
	Category string `json:"category"`
	Required bool   `json:"required"`
	Schema   string `json:"schema"`
	Checksum string `json:"checksum,omitempty"`
}

type Manifest struct {
	SchemaVersion   string                 `json:"schema_version"`
	AuditID         string                 `json:"audit_id"`
	CreatedAt       time.Time              `json:"created_at"`
	RulesetVersions map[string]string      `json:"ruleset_versions"`
	SchemaVersions  map[string]string      `json:"schema_versions"`
	StageStatus     map[string]StageStatus `json:"stage_status"`
	Files           []FileEntry            `json:"files"`
}
