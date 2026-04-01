package audit

import (
	"fmt"
	"regexp"
)

var auditIDPattern = regexp.MustCompile(`^aud_[0-9]{8}T[0-9]{6}Z_[a-z0-9]{6,}$`)

func ValidateRecord(record Record) error {
	if record.SchemaVersion == "" {
		return fmt.Errorf("schema version is required")
	}
	if !auditIDPattern.MatchString(record.AuditID) {
		return fmt.Errorf("invalid audit id")
	}
	if record.SubmittedURL == "" {
		return fmt.Errorf("submitted url is required")
	}
	if record.NormalizedHost == "" {
		return fmt.Errorf("normalized host is required")
	}
	if !isValidStatus(record.Status) {
		return fmt.Errorf("invalid status %q", record.Status)
	}
	if record.RulesetVersion == "" {
		return fmt.Errorf("ruleset version is required")
	}
	if record.CreatedAt.IsZero() || record.UpdatedAt.IsZero() {
		return fmt.Errorf("timestamps are required")
	}
	if !isValidPackageStatus(record.PackageStatus) {
		return fmt.Errorf("invalid package status %q", record.PackageStatus)
	}
	for _, stageRun := range record.StageRuns {
		if err := ValidateStageRun(stageRun); err != nil {
			return err
		}
	}
	return nil
}

func ValidateStageRun(stageRun StageRun) error {
	if !isValidStage(stageRun.Stage) {
		return fmt.Errorf("invalid stage %q", stageRun.Stage)
	}
	if !isValidStageRunStatus(stageRun.Status) {
		return fmt.Errorf("invalid stage run status %q", stageRun.Status)
	}
	if stageRun.Attempt < 1 {
		return fmt.Errorf("attempt must be >= 1")
	}
	if stageRun.StartedAt.IsZero() {
		return fmt.Errorf("started_at is required")
	}
	if stageRun.Inputs == nil {
		return fmt.Errorf("inputs are required")
	}
	if stageRun.Outputs == nil {
		return fmt.Errorf("outputs are required")
	}
	return nil
}

func isValidStatus(status Status) bool {
	switch status {
	case StatusAccepted, StatusQueued, StatusCrawling, StatusExtracting, StatusAnalyzing, StatusPackaging, StatusValidating, StatusCompleted, StatusFailed, StatusCancelled:
		return true
	default:
		return false
	}
}

func isValidPackageStatus(status PackageStatus) bool {
	switch status {
	case PackageStatusNotReady, PackageStatusBuilding, PackageStatusRejected, PackageStatusApproved:
		return true
	default:
		return false
	}
}

func isValidStage(stage Stage) bool {
	switch stage {
	case StageAccepted, StageQueued, StageCrawling, StageExtracting, StageAnalyzing, StagePackaging, StageValidating:
		return true
	default:
		return false
	}
}

func isValidStageRunStatus(status StageRunStatus) bool {
	switch status {
	case StageRunPending, StageRunRunning, StageRunCompleted, StageRunFailed, StageRunCancelled:
		return true
	default:
		return false
	}
}
