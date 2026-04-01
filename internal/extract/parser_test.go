package extract

import (
	"testing"
	"time"
)

func TestParserParse(t *testing.T) {
	t.Parallel()

	parser := NewParser()
	parser.now = func() time.Time {
		return time.Date(2026, 3, 11, 14, 0, 0, 0, time.UTC)
	}

	features, err := parser.Parse(Input{
		AuditID:                 "aud_20260311T120000Z_abc1234",
		URL:                     "https://example.com/service",
		Source:                  "rendered",
		StrictTransportSecurity: "max-age=31536000; includeSubDomains",
		HTML: `
			<html>
				<head>
					<title>Service Page</title>
					<meta name="description" content="Technical description">
					<meta content="index,follow" name="robots">
					<link rel="canonical" href="https://example.com/service">
					<script type="application/ld+json">{"@type":"FAQPage"}</script>
				</head>
				<body>
					<h1>Main heading</h1>
					<h2>Step one</h2>
					<h2>Step two</h2>
					<p>Телефон: +7 (999) 123-45-67</p>
					<p>Email: hello@example.com</p>
					<p>Оплата картой и СБП. Гарантия и возврат товара.</p>
					<p>Стоимость услуги от 25 000 руб.</p>
					<p>Срок выполнения от 2 недель. Работаем по России и Москве по договору.</p>
					<a href="https://t.me/example">Telegram</a>
				</body>
			</html>
		`,
	})
	if err != nil {
		t.Fatalf("Parse returned error: %v", err)
	}

	if features.Title != "Service Page" {
		t.Fatalf("unexpected title: %s", features.Title)
	}
	if features.Meta.Description != "Technical description" {
		t.Fatalf("unexpected description: %s", features.Meta.Description)
	}
	if features.CanonicalURL != "https://example.com/service" {
		t.Fatalf("unexpected canonical: %s", features.CanonicalURL)
	}
	if len(features.Headings.H1) != 1 || features.Headings.H1[0] != "Main heading" {
		t.Fatalf("unexpected h1 headings: %#v", features.Headings.H1)
	}
	if len(features.SchemaHints) != 1 || features.SchemaHints[0] != "faqpage" {
		t.Fatalf("unexpected schema hints: %#v", features.SchemaHints)
	}
	if len(features.RunetSignals.Phones) != 1 || features.RunetSignals.Phones[0] != "79991234567" {
		t.Fatalf("unexpected phones: %#v", features.RunetSignals.Phones)
	}
	if len(features.RunetSignals.Emails) != 1 || features.RunetSignals.Emails[0] != "hello@example.com" {
		t.Fatalf("unexpected emails: %#v", features.RunetSignals.Emails)
	}
	if len(features.RunetSignals.MessengerHints) == 0 || features.RunetSignals.MessengerHints[0] != "telegram" {
		t.Fatalf("unexpected messenger hints: %#v", features.RunetSignals.MessengerHints)
	}
	if len(features.RunetSignals.PaymentHints) == 0 {
		t.Fatalf("unexpected payment hints: %#v", features.RunetSignals.PaymentHints)
	}
	if len(features.RunetSignals.LegalHints) == 0 {
		t.Fatalf("unexpected legal hints: %#v", features.RunetSignals.LegalHints)
	}
	if len(features.CommercialSignals.PriceHints) == 0 || features.CommercialSignals.PriceHints[0] != "от 25 000 руб." {
		t.Fatalf("unexpected price hints: %#v", features.CommercialSignals.PriceHints)
	}
	if len(features.CommercialSignals.TimelineHints) == 0 || features.CommercialSignals.TimelineHints[0] != "от 2 недель" {
		t.Fatalf("unexpected timeline hints: %#v", features.CommercialSignals.TimelineHints)
	}
	if len(features.CommercialSignals.GeoHints) == 0 {
		t.Fatalf("unexpected geo hints: %#v", features.CommercialSignals.GeoHints)
	}
	if len(features.CommercialSignals.OfferTerms) == 0 {
		t.Fatalf("unexpected offer terms: %#v", features.CommercialSignals.OfferTerms)
	}
	if features.TransportSignals.StrictTransportSecurity == "" {
		t.Fatal("expected strict transport security signal")
	}
	if len(features.TransportSignals.MixedContentURLs) != 0 {
		t.Fatalf("expected no mixed content urls, got %#v", features.TransportSignals.MixedContentURLs)
	}
}

func TestParserParseEmptyHTMLReturnsValidOutput(t *testing.T) {
	t.Parallel()

	parser := NewParser()
	features, err := parser.Parse(Input{
		AuditID: "aud_20260311T120000Z_abc1234",
		URL:     "https://example.com",
	})
	if err != nil {
		t.Fatalf("Parse returned error: %v", err)
	}
	if features.Title != "" {
		t.Fatalf("expected empty title, got %q", features.Title)
	}
	if features.Headings.H1 == nil || features.Headings.H2 == nil {
		t.Fatal("expected headings slices to be initialized")
	}
}

func TestParserParseDetectsMixedContent(t *testing.T) {
	t.Parallel()

	parser := NewParser()
	features, err := parser.Parse(Input{
		AuditID: "aud_20260311T120000Z_abc1234",
		URL:     "https://example.com/app",
		Source:  "rendered",
		HTML: `
			<html>
				<head>
					<script src="http://cdn.example.com/app.js"></script>
				</head>
				<body>
					<img src="http://cdn.example.com/image.png">
					<style>.hero { background-image: url(http://cdn.example.com/bg.jpg); }</style>
				</body>
			</html>
		`,
	})
	if err != nil {
		t.Fatalf("Parse returned error: %v", err)
	}

	if len(features.TransportSignals.MixedContentURLs) != 3 {
		t.Fatalf("unexpected mixed content urls: %#v", features.TransportSignals.MixedContentURLs)
	}
	if features.TransportSignals.MixedContentURLs[0] != "http://cdn.example.com/app.js" {
		t.Fatalf("unexpected first mixed content url: %q", features.TransportSignals.MixedContentURLs[0])
	}
}
