// Copyright 2026 The Chromium Authors and Alex313031
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_THORIUM_URL_UTILS_H_
#define CHROME_BROWSER_THORIUM_URL_UTILS_H_

#include <string>
#include <string_view>

class GURL;

namespace content {
class BrowserContext;
}  // namespace content

namespace thorium {

// Converts the user-facing `thorium://` or `selenium://` alias to the canonical `chrome://`
// scheme. All URL components other than the scheme are preserved.
GURL CanonicalizeInternalURL(const GURL& url);

// Canonicalizes the internal URL alias before Chromium's normal browser URL
// handlers run. This preserves all existing platform and policy rewrites.
void RewriteInternalURLAlias(GURL* url, content::BrowserContext*);

// Returns the user-facing representation of a canonical internal URL. The
// returned URL is intended for display or copying only, never for storage or
// security decisions.
GURL GetInternalURLForDisplay(const GURL& url);

// Replaces the leading internal scheme in already-formatted text according to
// the branding feature. Other formatting is preserved.
std::u16string GetInternalURLTextForDisplay(const GURL& url,
                                            std::u16string_view formatted_url);

// Returns whether user-facing internal URL branding is enabled on this
// platform. Input support remains enabled independently of this feature.
bool IsInternalURLSchemeBrandingEnabled();

}  // namespace thorium

#endif  // CHROME_BROWSER_THORIUM_URL_UTILS_H_
