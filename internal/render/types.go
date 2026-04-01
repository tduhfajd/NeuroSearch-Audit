package render

import "time"

const schemaVersion = "1.0.0"

type Job struct {
	AuditID       string   `json:"audit_id"`
	URL           string   `json:"url"`
	Reason        string   `json:"reason"`
	WaitSelectors []string `json:"wait_selectors,omitempty"`
}

type PageSnapshot struct {
	URL         string `json:"url"`
	ContentType string `json:"content_type,omitempty"`
	HTML        string `json:"html"`
}

type RequirementSignals struct {
	ContentType      string `json:"content_type,omitempty"`
	HTMLBytes        int    `json:"html_bytes"`
	VisibleTextChars int    `json:"visible_text_chars"`
	ScriptTagCount   int    `json:"script_tag_count"`
	NoScriptHint     bool   `json:"noscript_hint"`
	URLHint          bool   `json:"url_hint"`
}

type Assessment struct {
	RequiresRender bool               `json:"requires_render"`
	Reason         string             `json:"reason,omitempty"`
	Signals        RequirementSignals `json:"signals"`
}

type Plan struct {
	SchemaVersion string      `json:"schema_version"`
	AuditID       string      `json:"audit_id"`
	GeneratedAt   time.Time   `json:"generated_at"`
	Summary       PlanSummary `json:"summary"`
	Candidates    []Candidate `json:"candidates"`
}

type PlanSummary struct {
	TotalPages          int `json:"total_pages"`
	RenderRequiredCount int `json:"render_required_count"`
	PlainFetchCount     int `json:"plain_fetch_count"`
}

type Candidate struct {
	URL           string             `json:"url"`
	Reason        string             `json:"reason"`
	WaitSelectors []string           `json:"wait_selectors,omitempty"`
	Signals       RequirementSignals `json:"signals"`
}

type Result struct {
	SchemaVersion string    `json:"schema_version"`
	AuditID       string    `json:"audit_id"`
	URL           string    `json:"url"`
	RenderMode    string    `json:"render_mode"`
	FinalURL      string    `json:"final_url"`
	HTML          string    `json:"html"`
	RenderedAt    time.Time `json:"rendered_at"`
	Signals       Signals   `json:"signals"`
}

type Signals struct {
	NetworkRequests int      `json:"network_requests"`
	ScriptHints     []string `json:"script_hints,omitempty"`
}
