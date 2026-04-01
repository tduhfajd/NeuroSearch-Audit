package extract

import (
	"fmt"
	"net/url"
	"regexp"
	"strings"
	"time"
)

const schemaVersion = "1.0.0"

type Parser struct {
	now func() time.Time
}

func NewParser() *Parser {
	return &Parser{
		now: time.Now().UTC,
	}
}

func (p *Parser) Parse(input Input) (TechnicalFeatures, error) {
	if input.AuditID == "" {
		return TechnicalFeatures{}, fmt.Errorf("audit id is required")
	}
	if input.URL == "" {
		return TechnicalFeatures{}, fmt.Errorf("url is required")
	}

	html := input.HTML
	features := TechnicalFeatures{
		SchemaVersion: schemaVersion,
		AuditID:       input.AuditID,
		URL:           input.URL,
		Source:        input.Source,
		ExtractedAt:   p.now(),
		Meta:          Meta{},
		Headings: HeadingSummary{
			H1: []string{},
			H2: []string{},
		},
		SchemaHints: []string{},
		RunetSignals: RunetSignals{
			Phones:         []string{},
			Emails:         []string{},
			MessengerHints: []string{},
			PaymentHints:   []string{},
			LegalHints:     []string{},
		},
		CommercialSignals: CommercialSignals{
			PriceHints:    []string{},
			TimelineHints: []string{},
			GeoHints:      []string{},
			OfferTerms:    []string{},
		},
		TransportSignals: TransportSignals{
			StrictTransportSecurity: input.StrictTransportSecurity,
			MixedContentURLs:        []string{},
		},
	}

	if html == "" {
		return features, nil
	}

	features.Title = firstMatch(html, `(?is)<title[^>]*>(.*?)</title>`)
	features.Meta.Description = metaContent(html, "description")
	features.CanonicalURL = linkHref(html, "canonical")
	features.Robots = metaContent(html, "robots")
	features.Headings.H1 = allMatches(html, `(?is)<h1[^>]*>(.*?)</h1>`)
	features.Headings.H2 = allMatches(html, `(?is)<h2[^>]*>(.*?)</h2>`)
	features.SchemaHints = schemaHints(html)
	features.RunetSignals = runetSignals(html)
	features.CommercialSignals = commercialSignals(html)
	features.TransportSignals = transportSignals(input.URL, input.StrictTransportSecurity, html)

	return features, nil
}

func transportSignals(pageURL string, strictTransportSecurity string, html string) TransportSignals {
	signals := TransportSignals{
		StrictTransportSecurity: strictTransportSecurity,
		MixedContentURLs:        []string{},
	}

	parsed, err := url.Parse(pageURL)
	if err != nil || !strings.EqualFold(parsed.Scheme, "https") {
		return signals
	}

	patterns := []string{
		`(?is)src=["'](http://[^"']+)["']`,
		`(?is)<link[^>]*rel=["'][^"']*(?:stylesheet|preload|icon)[^"']*["'][^>]*href=["'](http://[^"']+)["']`,
		`(?is)<link[^>]*href=["'](http://[^"']+)["'][^>]*rel=["'][^"']*(?:stylesheet|preload|icon)[^"']*["']`,
		`(?is)url\((http://[^)\s"']+)\)`,
	}
	values := []string{}
	for _, pattern := range patterns {
		re := regexp.MustCompile(pattern)
		matches := re.FindAllStringSubmatch(html, -1)
		for _, match := range matches {
			if len(match) < 2 {
				continue
			}
			values = append(values, strings.TrimSpace(match[1]))
		}
	}
	signals.MixedContentURLs = firstN(dedupe(values), 5)
	return signals
}

func firstMatch(input, pattern string) string {
	re := regexp.MustCompile(pattern)
	match := re.FindStringSubmatch(input)
	if len(match) < 2 {
		return ""
	}
	return cleanText(match[1])
}

func allMatches(input, pattern string) []string {
	re := regexp.MustCompile(pattern)
	matches := re.FindAllStringSubmatch(input, -1)
	values := make([]string, 0, len(matches))
	for _, match := range matches {
		if len(match) < 2 {
			continue
		}
		value := cleanText(match[1])
		if value != "" {
			values = append(values, value)
		}
	}
	return values
}

func metaContent(input, name string) string {
	patterns := []string{
		fmt.Sprintf(`(?is)<meta[^>]*name=["']%s["'][^>]*content=["'](.*?)["'][^>]*>`, regexp.QuoteMeta(name)),
		fmt.Sprintf(`(?is)<meta[^>]*content=["'](.*?)["'][^>]*name=["']%s["'][^>]*>`, regexp.QuoteMeta(name)),
	}
	for _, pattern := range patterns {
		if value := firstMatch(input, pattern); value != "" {
			return value
		}
	}
	return ""
}

func linkHref(input, rel string) string {
	patterns := []string{
		fmt.Sprintf(`(?is)<link[^>]*rel=["']%s["'][^>]*href=["'](.*?)["'][^>]*>`, regexp.QuoteMeta(rel)),
		fmt.Sprintf(`(?is)<link[^>]*href=["'](.*?)["'][^>]*rel=["']%s["'][^>]*>`, regexp.QuoteMeta(rel)),
	}
	for _, pattern := range patterns {
		if value := firstMatch(input, pattern); value != "" {
			return value
		}
	}
	return ""
}

func schemaHints(input string) []string {
	values := []string{}
	typeRe := regexp.MustCompile(`(?is)<script[^>]*type=["']application/ld\+json["'][^>]*>(.*?)</script>`)
	matches := typeRe.FindAllStringSubmatch(input, -1)
	for _, match := range matches {
		if len(match) < 2 {
			continue
		}
		block := strings.ToLower(match[1])
		for _, candidate := range []string{"organization", "service", "faqpage", "product"} {
			if strings.Contains(block, candidate) {
				values = append(values, candidate)
			}
		}
	}
	return dedupe(values)
}

func runetSignals(input string) RunetSignals {
	lower := strings.ToLower(input)
	text := strings.ToLower(cleanText(input))

	signals := RunetSignals{
		Phones:         firstN(dedupe(normalizePhones(phoneMatches(input))), 5),
		Emails:         firstN(dedupe(emailMatches(input)), 5),
		MessengerHints: []string{},
		PaymentHints:   []string{},
		LegalHints:     []string{},
	}

	for _, candidate := range []string{"whatsapp", "telegram", "viber", "vk", "вконтакте"} {
		if strings.Contains(lower, candidate) || strings.Contains(text, candidate) {
			signals.MessengerHints = append(signals.MessengerHints, candidate)
		}
	}
	for _, candidate := range []string{"оплата", "карт", "налич", "сбп", "sbp", "visa", "mastercard"} {
		if strings.Contains(text, candidate) {
			signals.PaymentHints = append(signals.PaymentHints, candidate)
		}
	}
	for _, candidate := range []string{"офер", "конфиден", "реквизит", "инн", "огрн", "гарант", "возврат", "обмен"} {
		if strings.Contains(text, candidate) {
			signals.LegalHints = append(signals.LegalHints, candidate)
		}
	}

	signals.MessengerHints = dedupe(signals.MessengerHints)
	signals.PaymentHints = dedupe(signals.PaymentHints)
	signals.LegalHints = dedupe(signals.LegalHints)
	return signals
}

func commercialSignals(input string) CommercialSignals {
	text := strings.ToLower(cleanText(input))
	signals := CommercialSignals{
		PriceHints:    firstN(dedupe(priceMatches(text)), 5),
		TimelineHints: firstN(dedupe(timelineMatches(text)), 5),
		GeoHints:      []string{},
		OfferTerms:    []string{},
	}

	for _, candidate := range []string{
		"москва", "москве", "санкт-петербург", "санкт петербург", "спб",
		"россия", "по россии", "рф", "снг", "онлайн", "удаленно", "remote",
	} {
		if strings.Contains(text, candidate) {
			signals.GeoHints = append(signals.GeoHints, candidate)
		}
	}
	for _, candidate := range []string{
		"договор", "по договору", "предоплата", "постоплата", "оплата после",
		"безнал", "гарантия", "возврат", "обмен", "сроки", "условия",
	} {
		if strings.Contains(text, candidate) {
			signals.OfferTerms = append(signals.OfferTerms, candidate)
		}
	}

	signals.GeoHints = dedupe(signals.GeoHints)
	signals.OfferTerms = dedupe(signals.OfferTerms)
	return signals
}

func priceMatches(input string) []string {
	re := regexp.MustCompile(`(?i)(?:от\s*)?\d[\d\s]{1,10}(?:[.,]\d+)?\s?(?:₽|руб(?:\.|ля|лей)?)`)
	return normalizeSignalMatches(re.FindAllString(input, -1))
}

func timelineMatches(input string) []string {
	re := regexp.MustCompile(`(?i)(?:от\s*)?\d[\d\s-]{0,12}\s?(?:дн(?:я|ей)?|день|час(?:а|ов)?|ч|недел(?:я|и|ь)?|месяц(?:а|ев)?|мес(?:\.|яц(?:а|ев)?)?)`)
	return normalizeSignalMatches(re.FindAllString(input, -1))
}

func normalizeSignalMatches(values []string) []string {
	out := make([]string, 0, len(values))
	for _, value := range values {
		normalized := strings.Join(strings.Fields(strings.TrimSpace(value)), " ")
		if normalized != "" {
			out = append(out, normalized)
		}
	}
	return out
}

func phoneMatches(input string) []string {
	re := regexp.MustCompile(`(?:\+7|8)[\s\-\(\)]*\d[\d\s\-\(\)]{8,}`)
	return re.FindAllString(input, -1)
}

func normalizePhones(values []string) []string {
	out := make([]string, 0, len(values))
	digitRe := regexp.MustCompile(`\D`)
	for _, value := range values {
		normalized := digitRe.ReplaceAllString(value, "")
		if len(normalized) >= 10 {
			out = append(out, normalized)
		}
	}
	return out
}

func emailMatches(input string) []string {
	re := regexp.MustCompile(`(?i)[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}`)
	return re.FindAllString(input, -1)
}

func firstN(values []string, limit int) []string {
	if len(values) <= limit {
		return values
	}
	return values[:limit]
}

func cleanText(value string) string {
	tagRe := regexp.MustCompile(`(?is)<[^>]+>`)
	value = tagRe.ReplaceAllString(value, " ")
	value = strings.TrimSpace(value)
	return strings.Join(strings.Fields(value), " ")
}

func dedupe(values []string) []string {
	seen := make(map[string]struct{}, len(values))
	out := make([]string, 0, len(values))
	for _, value := range values {
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
		out = append(out, value)
	}
	return out
}
