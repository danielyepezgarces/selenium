// Copyright 2011 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/installer/util/logging_installer.h"

#include <windows.h>
#include <io.h>

#include <shlobj.h>
#include <stdint.h>

#include <cstdio>
#include <iostream>
#include <optional>
#include <tuple>

#include "base/command_line.h"
#include "base/containers/heap_array.h"
#include "base/files/file.h"
#include "base/files/file_path.h"
#include "base/files/file_util.h"
#include "base/logging.h"
#include "base/logging/logging_settings.h"
#include "base/logging_win.h"
#include "base/path_service.h"
#include "base/strings/string_util.h"
#include "base/strings/utf_string_conversions.h"
#include "base/win/scoped_handle.h"
#include "build/branding_buildflags.h"
#include "chrome/installer/util/initial_preferences.h"
#include "chrome/installer/util/initial_preferences_constants.h"
#include "chrome/installer/util/util_constants.h"

// {93BCE0BF-3FAF-43b1-9E28-BEB6FAB5ECE7}
static const GUID kSetupTraceProvider = {
    0x93bce0bf,
    0x3faf,
    0x43b1,
    {0x9e, 0x28, 0xbe, 0xb6, 0xfa, 0xb5, 0xec, 0xe7}};

namespace installer {

namespace {

// This should be true for the period between the end of
// InitInstallerLogging() and the beginning of EndInstallerLogging().
bool installer_logging_ = false;

}  // namespace

TruncateResult TruncateLogFileIfNeeded(const base::FilePath& log_file) {
  TruncateResult result = LOGFILE_UNTOUCHED;

  std::optional<int64_t> log_size = base::GetFileSize(log_file);
  if (log_size.has_value() && log_size.value() > kMaxInstallerLogFileSize) {
    // Cause the old log file to be deleted when we are done with it.
    uint32_t file_flags = base::File::FLAG_OPEN | base::File::FLAG_READ |
                          base::File::FLAG_WIN_SHARE_DELETE |
                          base::File::FLAG_DELETE_ON_CLOSE;
    base::File old_log_file(log_file, file_flags);

    if (old_log_file.IsValid()) {
      result = LOGFILE_DELETED;
      base::FilePath tmp_log(log_file.value() + FILE_PATH_LITERAL(".tmp"));
      // Note that base::Move will attempt to replace existing files.
      if (base::Move(log_file, tmp_log)) {
        int64_t offset = log_size.value() - kTruncatedInstallerLogFileSize;
        auto old_log_data =
            base::HeapArray<uint8_t>::Uninit(kTruncatedInstallerLogFileSize);
        std::optional<size_t> bytes_read =
            old_log_file.Read(offset, old_log_data);
        if (bytes_read.value_or(0) > 0 &&
            (base::WriteFile(log_file, old_log_data.subspan(0, *bytes_read)) ||
             base::PathExists(log_file))) {
          result = LOGFILE_TRUNCATED;
        }
      }
    } else if (base::DeleteFile(log_file)) {
      // Couldn't get sufficient access to the log file, optimistically try to
      // delete it.
      result = LOGFILE_DELETED;
    }
  }

  return result;
}

namespace {

void RouteStdioToConsole() {
  // Don't change anything if stdout or stderr already point to a
  // valid stream.
  //
  // If we are running under Buildbot or under Cygwin's default
  // terminal (mintty), stdout and stderr will be pipe handles. In
  // that case, we don't want to open CONOUT$, because its output
  // likely does not go anywhere.
  //
  // We don't use GetStdHandle() to check stdout/stderr here because
  // it can return dangling IDs of handles that were never inherited
  // by this process.  These IDs could have been reused by the time
  // this function is called.  The CRT checks the validity of
  // stdout/stderr on startup (before the handle IDs can be reused).
  // _fileno(stdout) will return -2 (_NO_CONSOLE_FILENO) if stdout was
  // invalid.
  if (_fileno(stdout) >= 0 || _fileno(stderr) >= 0) {
    // _fileno was broken for SUBSYSTEM:WINDOWS from VS2010 to VS2012/2013.
    // http://crbug.com/358267. Confirm that the underlying HANDLE is valid
    // before aborting.

    intptr_t stdout_handle = _get_osfhandle(_fileno(stdout));
    intptr_t stderr_handle = _get_osfhandle(_fileno(stderr));
    if (stdout_handle >= 0 || stderr_handle >= 0) {
      return;
    }
  }

  if (!AttachConsole(ATTACH_PARENT_PROCESS)) {
    unsigned int result = GetLastError();
    // Was probably already attached.
    if (result == ERROR_ACCESS_DENIED) {
      return;
    }
    // Don't bother creating a new console for each child process if the
    // parent process is invalid (eg: crashed).
    if (result == ERROR_GEN_FAILURE) {
      return;
    }
    // Make a new console if attaching to parent fails with any other error.
    // It should be ERROR_INVALID_HANDLE at this point, which means the browser
    // was likely not started from a console.
    if (!AllocConsole()) {
      return;
    }
  }

  // Arbitrary byte count to use when buffering output lines.  More
  // means potential waste, less means more risk of interleaved
  // log-lines in output.
  enum { kOutputBufferSize = 64 * 1024 };

  if (freopen("CONOUT$", "w", stdout)) {
    setvbuf(stdout, nullptr, _IOLBF, kOutputBufferSize);
    // Overwrite FD 1 for the benefit of any code that uses this FD
    // directly.  This is safe because the CRT allocates FDs 0, 1 and
    // 2 at startup even if they don't have valid underlying Windows
    // handles.  This means we won't be overwriting an FD created by
    // _open() after startup.
    _dup2(_fileno(stdout), 1);
  }
  if (freopen("CONOUT$", "w", stderr)) {
    setvbuf(stderr, nullptr, _IOLBF, kOutputBufferSize);
    _dup2(_fileno(stderr), 2);
  }

  // Fix all cout, wcout, cin, wcin, cerr, wcerr, clog and wclog.
  std::ios::sync_with_stdio();
}

}  // namespace

void InitInstallerLogging(const installer::InitialPreferences& prefs) {
  if (installer_logging_)
    return;

  bool value = false;
  bool debug_enabled = false;
  bool verbose_enabled = false;
  if (prefs.GetBool(installer::initial_preferences::kDisableLogging, &value) &&
      value) {
    return;
  }
  installer_logging_ = true;
  if (prefs.GetBool(installer::initial_preferences::kDebugMode, &value) &&
      value) {
    debug_enabled = true;
  }
  if (prefs.GetBool(installer::initial_preferences::kVerboseLogging, &value) &&
      value) {
    verbose_enabled = true;
  }

  if (debug_enabled)
    RouteStdioToConsole();

  base::FilePath log_file_path(GetLogFilePath(prefs));
  TruncateLogFileIfNeeded(log_file_path);

  logging::LoggingSettings settings;
  settings.logging_dest = logging::LOG_TO_FILE;
  if (debug_enabled) {
    settings.logging_dest |= logging::LOG_TO_STDERR;
  }
  settings.log_file_path = log_file_path.value().c_str();
  logging::InitLogging(settings);

  if (verbose_enabled || debug_enabled) {
    logging::SetMinLogLevel(logging::LOGGING_VERBOSE);
  } else {
    logging::SetMinLogLevel(logging::LOGGING_ERROR);
  }

  // Enable ETW logging.
  logging::LogEventProvider::Initialize(kSetupTraceProvider);
}

void EndInstallerLogging() {
  if (!installer_logging_)
    return;

  logging::CloseLogFile();

  installer_logging_ = false;
}

base::FilePath GetLogFilePath(const installer::InitialPreferences& prefs) {
  std::string path;
  prefs.GetString(installer::initial_preferences::kLogFile, &path);
  if (!path.empty())
    return base::FilePath(base::UTF8ToWide(path));

  static const base::FilePath::CharType kLogFilename[] =
#if BUILDFLAG(GOOGLE_CHROME_BRANDING)
      FILE_PATH_LITERAL("chrome_installer.log");
#else  // BUILDFLAG(CHROMIUM_BRANDING)
      FILE_PATH_LITERAL("selenium_installer.log");
#endif

  // Fall back to the current directory if the secure or user temp directory
  // cannot be resolved.
  base::FilePath tmp_path;
  std::ignore = ::IsUserAnAdmin()
                    ? base::PathService::Get(base::DIR_SYSTEM_TEMP, &tmp_path)
                    : base::PathService::Get(base::DIR_TEMP, &tmp_path);

  return tmp_path.Append(kLogFilename);
}

}  // namespace installer
