package extract

import "time"

type Input struct {
	AuditID                 string `json:"audit_id"`
	URL                     string `json:"url"`
	HTML                    string `json:"html"`
	Source                  string `json:"source"`
	ContentType             string `json:"content_type,omitempty"`
	StrictTransportSecurity string `json:"strict_transport_security,omitempty"`
}

type TechnicalFeatures struct {
	SchemaVersion     string            `json:"schema_version"`
	AuditID           string            `json:"audit_id"`
	URL               string            `json:"url"`
	Source            string            `json:"source"`
	ExtractedAt       time.Time         `json:"extracted_at"`
	Title             string            `json:"title,omitempty"`
	Meta              Meta              `json:"meta"`
	Headings          HeadingSummary    `json:"headings"`
	CanonicalURL      string            `json:"canonical_url,omitempty"`
	Robots            string            `json:"robots,omitempty"`
	SchemaHints       []string          `json:"schema_hints"`
	RunetSignals      RunetSignals      `json:"runet_signals"`
	CommercialSignals CommercialSignals `json:"commercial_signals"`
	TransportSignals  TransportSignals  `json:"transport_signals"`
}

type Meta struct {
	Description string `json:"description,omitempty"`
}

type HeadingSummary struct {
	H1 []string `json:"h1"`
	H2 []string `json:"h2"`
}

type RunetSignals struct {
	Phones         []string `json:"phones"`
	Emails         []string `json:"emails"`
	MessengerHints []string `json:"messenger_hints"`
	PaymentHints   []string `json:"payment_hints"`
	LegalHints     []string `json:"legal_hints"`
}

type CommercialSignals struct {
	PriceHints    []string `json:"price_hints"`
	TimelineHints []string `json:"timeline_hints"`
	GeoHints      []string `json:"geo_hints"`
	OfferTerms    []string `json:"offer_terms"`
}

type TransportSignals struct {
	StrictTransportSecurity string   `json:"strict_transport_security"`
	MixedContentURLs        []string `json:"mixed_content_urls"`
}
