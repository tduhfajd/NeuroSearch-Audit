package audit

import "time"

type Status string

const (
	StatusAccepted   Status = "accepted"
	StatusQueued     Status = "queued"
	StatusCrawling   Status = "crawling"
	StatusExtracting Status = "extracting"
	StatusAnalyzing  Status = "analyzing"
	StatusPackaging  Status = "packaging"
	StatusValidating Status = "validating"
	StatusCompleted  Status = "completed"
	StatusFailed     Status = "failed"
	StatusCancelled  Status = "cancelled"
)

type PackageStatus string

const (
	PackageStatusNotReady PackageStatus = "not_ready"
	PackageStatusBuilding PackageStatus = "building"
	PackageStatusRejected PackageStatus = "rejected"
	PackageStatusApproved PackageStatus = "approved"
)

type Stage string

const (
	StageAccepted   Stage = "accepted"
	StageQueued     Stage = "queued"
	StageCrawling   Stage = "crawling"
	StageExtracting Stage = "extracting"
	StageAnalyzing  Stage = "analyzing"
	StagePackaging  Stage = "packaging"
	StageValidating Stage = "validating"
)

type StageRunStatus string

const (
	StageRunPending   StageRunStatus = "pending"
	StageRunRunning   StageRunStatus = "running"
	StageRunCompleted StageRunStatus = "completed"
	StageRunFailed    StageRunStatus = "failed"
	StageRunCancelled StageRunStatus = "cancelled"
)

type StageRun struct {
	Stage        Stage          `json:"stage"`
	Status       StageRunStatus `json:"status"`
	Attempt      int            `json:"attempt"`
	WorkerID     string         `json:"worker_id,omitempty"`
	StartedAt    time.Time      `json:"started_at"`
	FinishedAt   *time.Time     `json:"finished_at,omitempty"`
	Inputs       []string       `json:"inputs"`
	Outputs      []string       `json:"outputs"`
	ErrorCode    string         `json:"error_code,omitempty"`
	ErrorMessage string         `json:"error_message,omitempty"`
}

type Record struct {
	SchemaVersion  string        `json:"schema_version"`
	AuditID        string        `json:"audit_id"`
	SubmittedURL   string        `json:"submitted_url"`
	NormalizedHost string        `json:"normalized_host"`
	Status         Status        `json:"status"`
	RulesetVersion string        `json:"ruleset_version"`
	CreatedAt      time.Time     `json:"created_at"`
	UpdatedAt      time.Time     `json:"updated_at"`
	StageRuns      []StageRun    `json:"stage_runs"`
	PackageStatus  PackageStatus `json:"package_status"`
}

type IntakeRequest struct {
	URL string `json:"url"`
}
