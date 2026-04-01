package crawl

import (
	"net/url"
	"path"
	"strings"
)

var blockedExtensions = map[string]struct{}{
	".css":   {},
	".js":    {},
	".json":  {},
	".xml":   {},
	".rss":   {},
	".ico":   {},
	".png":   {},
	".jpg":   {},
	".jpeg":  {},
	".gif":   {},
	".svg":   {},
	".webp":  {},
	".avif":  {},
	".woff":  {},
	".woff2": {},
	".ttf":   {},
	".eot":   {},
	".otf":   {},
	".pdf":   {},
	".zip":   {},
	".gz":    {},
	".mp3":   {},
	".mp4":   {},
	".webm":  {},
	".webmanifest": {},
}

var blockedQueryKeys = map[string]struct{}{
	"quickview": {},
}

var blockedPathPrefixes = []string{
	"/cart",
	"/login",
	"/signup",
	"/order",
	"/search",
	"/forgotpassword",
}

func ShouldFollowURL(raw string) bool {
	parsed, err := url.Parse(raw)
	if err != nil {
		return false
	}

	ext := strings.ToLower(path.Ext(parsed.Path))
	if _, blocked := blockedExtensions[ext]; blocked {
		return false
	}

	lowerPath := strings.ToLower(parsed.Path)
	for _, prefix := range blockedPathPrefixes {
		if lowerPath == prefix || strings.HasPrefix(lowerPath, prefix+"/") {
			return false
		}
	}

	query := parsed.Query()
	for key := range query {
		if _, blocked := blockedQueryKeys[strings.ToLower(key)]; blocked {
			return false
		}
	}

	return true
}

func IsHTMLContentType(contentType string) bool {
	lower := strings.ToLower(contentType)
	if lower == "" {
		return true
	}
	return strings.Contains(lower, "text/html") || strings.Contains(lower, "application/xhtml+xml")
}
