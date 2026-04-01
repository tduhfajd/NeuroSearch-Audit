package render

import (
	"testing"
	"time"
)

func TestPlannerShouldRender(t *testing.T) {
	t.Parallel()

	planner := NewPlanner()
	if !planner.ShouldRender("https://example.com/app", "text/html") {
		t.Fatal("expected app url to require rendering")
	}
	if planner.ShouldRender("https://example.com/about", "text/html") {
		t.Fatal("did not expect static html page to require rendering")
	}
	if !planner.ShouldRender("https://example.com/about", "application/javascript") {
		t.Fatal("expected javascript content type to require rendering")
	}
}

func TestPlannerAssessScriptHeavyThinHTML(t *testing.T) {
	t.Parallel()

	planner := NewPlanner()
	assessment := planner.Assess(
		"https://example.com/product",
		"text/html",
		`<html><head><script></script><script></script><script></script><script></script><script></script></head><body><div id="app"></div></body></html>`,
	)
	if !assessment.RequiresRender {
		t.Fatal("expected script-heavy thin html to require rendering")
	}
	if assessment.Reason != "script-heavy-thin-html" {
		t.Fatalf("unexpected reason: %s", assessment.Reason)
	}
}

func TestPlannerBuildPlan(t *testing.T) {
	t.Parallel()

	planner := NewPlanner()
	plan := planner.BuildPlan("aud_20260312T080000Z_abc1234", []PageSnapshot{
		{
			URL:  "https://example.com/app",
			HTML: `<html><body><div id="app"></div></body></html>`,
		},
		{
			URL:  "https://example.com/about",
			HTML: `<html><body><h1>About</h1><p>Useful static content with enough text to stay in plain fetch mode and describe the company, services, delivery terms, contact options, and customer support expectations in ordinary HTML.</p></body></html>`,
		},
	}, time.Date(2026, 3, 12, 8, 0, 0, 0, time.UTC))
	if plan.Summary.TotalPages != 2 {
		t.Fatalf("unexpected total pages: %d", plan.Summary.TotalPages)
	}
	if plan.Summary.RenderRequiredCount != 1 {
		t.Fatalf("unexpected render-required count: %d", plan.Summary.RenderRequiredCount)
	}
	if len(plan.Candidates) != 1 || plan.Candidates[0].URL != "https://example.com/app" {
		t.Fatalf("unexpected candidates: %#v", plan.Candidates)
	}
}
