// Copyright 2026 The Chromium Authors and Daniel Yepez Garces
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/ui/webui/help/version_updater.h"

#include <windows.h>
#include <winhttp.h>

#include <memory>
#include <optional>
#include <string>

#pragma comment(lib, "winhttp.lib")

#include "base/functional/bind.h"
#include "base/json/json_reader.h"
#include "base/memory/weak_ptr.h"
#include "base/strings/utf_string_conversions.h"
#include "base/task/thread_pool.h"
#include "base/values.h"
#include "base/version.h"
#include "chrome/browser/first_run/upgrade_util.h"
#include "components/version_info/version_info.h"
#include "content/public/browser/browser_thread.h"
#include "content/public/browser/web_contents.h"
#include "ui/aura/window.h"
#include "ui/aura/window_tree_host.h"
#include "ui/gfx/native_ui_types.h"

namespace {

struct SeleniumCheckResult {
  VersionUpdater::Status status = VersionUpdater::UPDATED;
  int progress = 0;
  std::u16string message;
};

SeleniumCheckResult CheckSeleniumUpdateTask() {
  if (upgrade_util::IsUpdatePendingRestart()) {
    return {VersionUpdater::NEARLY_UPDATED, 0, std::u16string()};
  }

  // Smooth UI delay so the user clearly sees the checking spinner
  ::Sleep(700);

  HINTERNET hSession = WinHttpOpen(L"Selenium-Browser/1.0",
                                   WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                   WINHTTP_NO_PROXY_NAME,
                                   WINHTTP_NO_PROXY_BYPASS, 0);
  if (!hSession) {
    return {VersionUpdater::UPDATED, 0, std::u16string()};
  }

  // Fast timeout (3s) so UI remains snappy if offline
  WinHttpSetTimeouts(hSession, 3000, 3000, 3000, 3000);

  HINTERNET hConnect = WinHttpConnect(hSession, L"update.dyepezg.dev",
                                      INTERNET_DEFAULT_HTTPS_PORT, 0);
  if (!hConnect) {
    WinHttpCloseHandle(hSession);
    return {VersionUpdater::UPDATED, 0, std::u16string()};
  }

  HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"GET",
                                          L"/dl/selenium/version.json",
                                          nullptr, WINHTTP_NO_REFERER,
                                          WINHTTP_DEFAULT_ACCEPT_TYPES,
                                          WINHTTP_FLAG_SECURE);
  if (!hRequest) {
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
    return {VersionUpdater::UPDATED, 0, std::u16string()};
  }

  BOOL bSend = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                                  WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
  if (!bSend || !WinHttpReceiveResponse(hRequest, nullptr)) {
    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
    return {VersionUpdater::UPDATED, 0, std::u16string()};
  }

  std::string response_data;
  DWORD bytes_read = 0;
  char buffer[4096];
  while (WinHttpReadData(hRequest, buffer, sizeof(buffer), &bytes_read) && bytes_read > 0) {
    response_data.append(buffer, bytes_read);
  }

  WinHttpCloseHandle(hRequest);
  WinHttpCloseHandle(hConnect);
  WinHttpCloseHandle(hSession);

  std::optional<base::Value> val = base::JSONReader::Read(response_data);
  if (val && val->is_dict()) {
    const base::Value::Dict& dict = val->GetDict();
    const std::string* ver_str = dict.FindString("version");
    if (!ver_str) {
      const base::Value::Dict* latest_dict = dict.FindDict("latest");
      if (latest_dict) {
        ver_str = latest_dict->FindString("version");
      }
    }
    if (ver_str) {
      base::Version remote_ver(*ver_str);
      base::Version current_ver(version_info::GetVersionNumber());
      if (remote_ver.IsValid() && current_ver.IsValid() && remote_ver > current_ver) {
        return {VersionUpdater::NEARLY_UPDATED, 0, std::u16string()};
      }
    }
  }

  return {VersionUpdater::UPDATED, 0, std::u16string()};
}

class VersionUpdaterWin : public VersionUpdater {
 public:
  explicit VersionUpdaterWin(gfx::AcceleratedWidget owner_widget)
      : owner_widget_(owner_widget), weak_factory_(this) {}

  VersionUpdaterWin(const VersionUpdaterWin&) = delete;
  VersionUpdaterWin& operator=(const VersionUpdaterWin&) = delete;

  ~VersionUpdaterWin() override = default;

  void CheckForUpdate(StatusCallback callback, PromoteCallback) override {
    callback_ = std::move(callback);

    callback_.Run(CHECKING, 0, false, false, std::string(), 0,
                  std::u16string());

    base::ThreadPool::PostTaskAndReplyWithResult(
        FROM_HERE, {base::MayBlock(), base::TaskPriority::USER_VISIBLE},
        base::BindOnce(&CheckSeleniumUpdateTask),
        base::BindOnce(&VersionUpdaterWin::OnSeleniumUpdateCheckResult,
                       weak_factory_.GetWeakPtr()));
  }

 private:
  void OnSeleniumUpdateCheckResult(SeleniumCheckResult result) {
    DCHECK_CURRENTLY_ON(content::BrowserThread::UI);
    callback_.Run(result.status, result.progress, false, false, std::string(), 0,
                  result.message);
  }

  gfx::AcceleratedWidget owner_widget_;
  StatusCallback callback_;
  base::WeakPtrFactory<VersionUpdaterWin> weak_factory_;
};

}  // namespace

std::unique_ptr<VersionUpdater> VersionUpdater::Create(
    content::WebContents* web_contents) {
  gfx::NativeWindow window = web_contents->GetTopLevelNativeWindow();
  aura::WindowTreeHost* window_tree_host = window ? window->GetHost() : nullptr;
  return std::make_unique<VersionUpdaterWin>(
      window_tree_host ? window_tree_host->GetAcceleratedWidget() : nullptr);
}
