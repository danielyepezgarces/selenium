// Copyright 2011 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/win/app_icon.h"

#include "chrome/common/chrome_constants.h"
#include "chrome/install_static/install_details.h"
#include "third_party/skia/include/core/SkBitmap.h"
#include "ui/gfx/geometry/size.h"
#include "ui/gfx/image/image_family.h"
#include "ui/gfx/win/icon_util.h"

namespace {

// Returns the resource id of the application icon.
int GetAppIconResourceId() {
  return install_static::InstallDetails::Get().app_icon_resource_id();
}

}  // namespace

HICON GetAppIcon() {
  // TODO(mgiuca): Use GetAppIconImageFamily/CreateExact instead of LoadIcon, to
  // get correct scaling. (See http://crbug.com/40443246)
  const int icon_id = GetAppIconResourceId();
  // HICON returned from LoadIcon do not leak and do not have to be destroyed.
  HICON icon = LoadIcon(GetModuleHandle(nullptr), MAKEINTRESOURCE(icon_id));
  if (icon) {
    return icon;
  }
  return LoadIcon(GetModuleHandle(chrome::kBrowserResourcesDll),
                  MAKEINTRESOURCE(icon_id));
}

HICON GetSmallAppIcon() {
  // TODO(mgiuca): Use GetAppIconImageFamily/CreateExact instead of LoadIcon, to
  // get correct scaling. (See http://crbug.com/40443246)
  const int icon_id = GetAppIconResourceId();
  gfx::Size size = GetSmallAppIconSize();
  // HICON returned from LoadImage must be released using DestroyIcon.
  HICON icon = static_cast<HICON>(LoadImage(
      GetModuleHandle(nullptr), MAKEINTRESOURCE(icon_id),
      IMAGE_ICON, size.width(), size.height(), LR_DEFAULTCOLOR | LR_SHARED));
  if (icon) {
    return icon;
  }
  return static_cast<HICON>(LoadImage(
      GetModuleHandle(chrome::kBrowserResourcesDll), MAKEINTRESOURCE(icon_id),
      IMAGE_ICON, size.width(), size.height(), LR_DEFAULTCOLOR | LR_SHARED));
}

gfx::Size GetAppIconSize() {
  return gfx::Size(GetSystemMetrics(SM_CXICON), GetSystemMetrics(SM_CYICON));
}

gfx::Size GetSmallAppIconSize() {
  return gfx::Size(GetSystemMetrics(SM_CXSMICON),
                   GetSystemMetrics(SM_CYSMICON));
}

std::unique_ptr<gfx::ImageFamily> GetAppIconImageFamily() {
  const int icon_id = GetAppIconResourceId();
  HMODULE module = GetModuleHandle(nullptr);
  if (module) {
    auto family = IconUtil::CreateImageFamilyFromIconResource(module, icon_id);
    if (family) {
      return family;
    }
  }
  module = GetModuleHandle(chrome::kBrowserResourcesDll);
  if (!module)
    module = GetModuleHandle(nullptr);
  DCHECK(module);

  return IconUtil::CreateImageFamilyFromIconResource(module, icon_id);
}
