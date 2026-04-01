package render

import (
	"html"
	"regexp"
	"strings"
	"time"
)

type Planner struct{}

func NewPlanner() Planner {
	return Planner{}
}

func (Planner) ShouldRender(url string, contentType string) bool {
	return Planner{}.Assess(url, contentType, "").RequiresRender
}

func (Planner) Assess(url string, contentType string, htmlPayload string) Assessment {
	lowerURL := strings.ToLower(url)
	lowerType := strings.ToLower(contentType)
	signals := RequirementSignals{
		ContentType:      contentType,
		HTMLBytes:        len(htmlPayload),
		VisibleTextChars: visibleTextChars(htmlPayload),
		ScriptTagCount:   strings.Count(strings.ToLower(htmlPayload), "<script"),
		NoScriptHint:     strings.Contains(strings.ToLower(htmlPayload), "<noscript"),
		URLHint:          strings.Contains(lowerURL, "/app") || strings.Contains(lowerURL, "/spa"),
	}

	if strings.Contains(lowerType, "javascript") {
		return Assessment{RequiresRender: true, Reason: "javascript-content-type", Signals: signals}
	}
	if signals.URLHint {
		return Assessment{RequiresRender: true, Reason: "spa-url-pattern", Signals: signals}
	}
	if signals.ScriptTagCount >= 5 && signals.VisibleTextChars < 250 {
		return Assessment{RequiresRender: true, Reason: "script-heavy-thin-html", Signals: signals}
	}
	if signals.NoScriptHint && signals.VisibleTextChars < 200 {
		return Assessment{RequiresRender: true, Reason: "noscript-placeholder", Signals: signals}
	}
	if signals.HTMLBytes > 0 && signals.HTMLBytes < 600 && signals.VisibleTextChars < 80 {
		return Assessment{RequiresRender: true, Reason: "thin-html", Signals: signals}
	}
	return Assessment{RequiresRender: false, Signals: signals}
}

func (Planner) BuildJob(auditID, url, reason string) Job {
	return Job{
		AuditID:       auditID,
		URL:           url,
		Reason:        reason,
		WaitSelectors: []string{"body"},
	}
}

func (p Planner) BuildPlan(auditID string, pages []PageSnapshot, generatedAt time.Time) Plan {
	plan := Plan{
		SchemaVersion: schemaVersion,
		AuditID:       auditID,
		GeneratedAt:   generatedAt,
		Summary: PlanSummary{
			TotalPages: len(pages),
		},
		Candidates: make([]Candidate, 0),
	}
	for _, page := range pages {
		assessment := p.Assess(page.URL, page.ContentType, page.HTML)
		if assessment.RequiresRender {
			job := p.BuildJob(auditID, page.URL, assessment.Reason)
			plan.Candidates = append(plan.Candidates, Candidate{
				URL:           job.URL,
				Reason:        job.Reason,
				WaitSelectors: job.WaitSelectors,
				Signals:       assessment.Signals,
			})
		}
	}
	plan.Summary.RenderRequiredCount = len(plan.Candidates)
	plan.Summary.PlainFetchCount = plan.Summary.TotalPages - plan.Summary.RenderRequiredCount
	return plan
}

var (
	scriptStylePattern = regexp.MustCompile(`(?is)<(script|style)[^>]*>.*?</(script|style)>`)
	tagPattern         = regexp.MustCompile(`(?is)<[^>]+>`)
)

func visibleTextChars(rawHTML string) int {
	if rawHTML == "" {
		return 0
	}
	withoutScripts := scriptStylePattern.ReplaceAllString(rawHTML, " ")
	withoutTags := tagPattern.ReplaceAllString(withoutScripts, " ")
	decoded := html.UnescapeString(withoutTags)
	collapsed := strings.Join(strings.Fields(decoded), " ")
	return len(collapsed)
}
