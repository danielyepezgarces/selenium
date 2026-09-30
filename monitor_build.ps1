# Real-Time Build Monitor - Selenium AVX2
param(
    [int]$EstimatedTotal = 0
)

$outDir = "C:\src\chromium\src\out\thorium"
$ninjaLog = Join-Path $outDir ".ninja_log"
$startTime = Get-Date

Clear-Host
try { $host.UI.RawUI.WindowTitle = "⚡ Build Monitor - Selenium x64 AVX2" } catch {}

function Get-DoneActions {
    param([string]$path)
    if (-not (Test-Path $path)) { return 0 }
    try {
        $count = 0
        $fileStream = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $reader = New-Object System.IO.StreamReader($fileStream)
        while ($reader.ReadLine() -ne $null) { $count++ }
        $reader.Close()
        $fileStream.Close()
        return $count
    } catch {
        return 0
    }
}

function Get-ObjCount {
    param([string]$dir)
    if (-not (Test-Path $dir)) { return 0 }
    try {
        return (Get-ChildItem -Path $dir -Filter "*.obj" -Recurse -ErrorAction SilentlyContinue).Count
    } catch {
        return 0
    }
}

while ($true) {
    $now = Get-Date
    $elapsed = $now - $startTime
    $elapsedStr = "{0:d2}:{1:d2}:{2:d2}" -f [int]$elapsed.TotalHours, $elapsed.Minutes, $elapsed.Seconds
    
    # 1. Action and object count
    $ninjaActions = Get-DoneActions $ninjaLog
    $objDir = Join-Path $outDir "obj"
    $objCount = Get-ObjCount $objDir
    $doneActions = [math]::Max($ninjaActions, $objCount)
    
    # Target total for full browser (chrome -> selenium.exe)
    $targetTotal = 36412
    $remaining = [math]::Max(0, $targetTotal - $doneActions)
    $percent = [math]::Min(100.0, [math]::Round(($doneActions / $targetTotal) * 100, 1))
    
    # 2. Visual progress bar
    $barWidth = 28
    $filled = [int](($percent / 100) * $barWidth)
    $empty = $barWidth - $filled
    $bar = ("#" * $filled) + ("-" * $empty)
    
    # 3. Compiler processes
    $clangProcs = Get-Process -Name "clang-cl" -ErrorAction SilentlyContinue
    $rustProcs = Get-Process -Name "rustc" -ErrorAction SilentlyContinue
    $lldProcs = Get-Process -Name "lld-link" -ErrorAction SilentlyContinue
    $sisoProcs = Get-Process -Name "siso" -ErrorAction SilentlyContinue
    
    $compilersCount = 0
    $compilersRamMB = 0
    
    $allProcs = @()
    if ($clangProcs) { $allProcs += $clangProcs }
    if ($rustProcs) { $allProcs += $rustProcs }
    if ($lldProcs) { $allProcs += $lldProcs }
    
    if ($allProcs.Count -gt 0) {
        $compilersCount = $allProcs.Count
        $totalBytes = ($allProcs | Measure-Object -Property WorkingSet64 -Sum).Sum
        $compilersRamMB = [math]::Round($totalBytes / 1MB, 0)
    }
    
    # 4. Total System Memory
    $os = Get-CimInstance Win32_OperatingSystem
    $sysTotalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
    $sysFreeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
    $sysUsedGB = [math]::Round($sysTotalGB - $sysFreeGB, 1)
    
    # 5. Phase
    $phase = "Compiling C++/C with Clang"
    if ($lldProcs) {
        $phase = "Linking binaries (ThinLTO LLD)"
    } elseif ($rustProcs) {
        $phase = "Compiling Rust modules"
    } elseif ($clangProcs) {
        $phase = "Compiling with Clang AVX2"
    } elseif ($sisoProcs) {
        $phase = "Siso: Scheduling dependencies"
    } else {
        $phase = "Idle / Completing stage"
    }

    try { [Console]::SetCursorPosition(0, 0) } catch { Clear-Host }
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "             REAL-TIME BUILD MONITOR: SELENIUM BROWSER                    " -ForegroundColor Green
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ("  Elapsed time       : {0}   |  Phase: {1}" -f $elapsedStr, $phase) -ForegroundColor White
    Write-Host "--------------------------------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host ("  Progress           : [{0}] {1,5:N1}%" -f $bar, $percent) -ForegroundColor Yellow
    Write-Host ("  Completed actions  : {0,6}  |  Remaining: {1,6}  |  .obj files: {2,5}" -f $doneActions, $remaining, $objCount) -ForegroundColor White
    Write-Host "--------------------------------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host ("  Compiler threads   : {0,2}/12 active  (Clang / Rust / LLD)" -f $compilersCount) -ForegroundColor Green
    Write-Host ("  Compiler RAM       : {0,5} MB ({1:N1} GB)" -f $compilersRamMB, ($compilersRamMB / 1024)) -ForegroundColor White
    Write-Host ("  System Total RAM   : {0:N1} GB used  /  {1:N1} GB total" -f $sysUsedGB, $sysTotalGB) -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  Note: Clang dynamically allocates RAM. When compiling Blink, V8 and ThinLTO," -ForegroundColor Gray
    Write-Host "  RAM usage will automatically scale up to 12-16+ GB as needed." -ForegroundColor Gray
    Write-Host "  Press Ctrl+C at any time to close this monitor." -ForegroundColor DarkGray
    Write-Host "==========================================================================" -ForegroundColor Cyan

    Start-Sleep -Seconds 2
}
