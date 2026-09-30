// Copyright 2026 The Chromium Authors and Alex313031
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/thorium_url_utils.h"

#include "base/feature_list.h"
#include "base/strings/string_util.h"
#include "chrome/common/chrome_features.h"
#include "content/public/common/url_constants.h"
#include "url/gurl.h"

namespace thorium {

GURL CanonicalizeInternalURL(const GURL& url) {
  if (!url.SchemeIs(content::kThoriumUIScheme) &&
      !url.SchemeIs("thorium")) {
    return url;
  }

  GURL::Replacements replacements;
  replacements.SetSchemeStr(content::kChromeUIScheme);
  return url.ReplaceComponents(replacements);
}

void RewriteInternalURLAlias(GURL* url, content::BrowserContext*) {
  *url = CanonicalizeInternalURL(*url);
}

GURL GetInternalURLForDisplay(const GURL& url) {
  const GURL canonical_url = CanonicalizeInternalURL(url);
  if (!IsInternalURLSchemeBrandingEnabled() ||
      !canonical_url.SchemeIs(content::kChromeUIScheme)) {
    return canonical_url;
  }

  GURL::Replacements replacements;
  replacements.SetSchemeStr(content::kThoriumUIScheme);
  return canonical_url.ReplaceComponents(replacements);
}

std::u16string GetInternalURLTextForDisplay(const GURL& url,
                                            std::u16string_view formatted_url) {
  constexpr std::u16string_view kChromeScheme = u"chrome:";
  constexpr std::u16string_view kSeleniumScheme = u"selenium:";
  constexpr std::u16string_view kLegacyThoriumScheme = u"thorium:";
  if (!url.SchemeIs(content::kChromeUIScheme) &&
      !url.SchemeIs(content::kThoriumUIScheme) &&
      !url.SchemeIs("thorium")) {
    return std::u16string(formatted_url);
  }

  std::u16string_view source_scheme;
  if (base::StartsWith(formatted_url, kChromeScheme,
                       base::CompareCase::INSENSITIVE_ASCII)) {
    source_scheme = kChromeScheme;
  } else if (base::StartsWith(formatted_url, kSeleniumScheme,
                              base::CompareCase::INSENSITIVE_ASCII)) {
    source_scheme = kSeleniumScheme;
  } else if (base::StartsWith(formatted_url, kLegacyThoriumScheme,
                              base::CompareCase::INSENSITIVE_ASCII)) {
    source_scheme = kLegacyThoriumScheme;
  } else {
    return std::u16string(formatted_url);
  }

  std::u16string result =
      IsInternalURLSchemeBrandingEnabled() ? u"selenium" : u"chrome";
  result.append(formatted_url.substr(source_scheme.size() - 1));
  return result;
}

bool IsInternalURLSchemeBrandingEnabled() {
  return base::FeatureList::IsEnabled(
      features::kThoriumInternalUrlSchemeBranding);
}

}  // namespace thorium
