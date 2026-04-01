package crawl

import "testing"

func TestShouldFollowURL(t *testing.T) {
	t.Parallel()

	cases := []struct {
		url  string
		want bool
	}{
		{url: "https://example.com/catalog/item", want: true},
		{url: "https://example.com/assets/site.css", want: false},
		{url: "https://example.com/favicon.ico", want: false},
		{url: "https://example.com/site.webmanifest", want: false},
		{url: "https://example.com/login/", want: false},
		{url: "https://example.com/cart/", want: false},
		{url: "https://example.com/product/123?quickview=1", want: false},
		{url: "https://example.com/category/dolls?page=2", want: true},
	}

	for _, tc := range cases {
		if got := ShouldFollowURL(tc.url); got != tc.want {
			t.Fatalf("ShouldFollowURL(%q) = %v, want %v", tc.url, got, tc.want)
		}
	}
}

func TestIsHTMLContentType(t *testing.T) {
	t.Parallel()

	if !IsHTMLContentType("text/html; charset=utf-8") {
		t.Fatal("expected text/html to be accepted")
	}
	if IsHTMLContentType("text/css") {
		t.Fatal("expected text/css to be rejected")
	}
	if !IsHTMLContentType("") {
		t.Fatal("expected empty content type to be treated as html-compatible")
	}
}
