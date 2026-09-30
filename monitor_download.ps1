$logPath = "C:\Users\Daniel Yepez Garces\.gemini\antigravity-cli\brain\0b81f3a6-4813-418b-aec7-129f8916ed94\.system_generated\tasks\task-166.log"
$fso = New-Object -ComObject Scripting.FileSystemObject
$target = "C:\src\chromium"
$startTime = Get-Date

Clear-Host
$host.UI.RawUI.WindowTitle = "Monitor en Vivo - Descarga de Chromium (Git + Disco)"

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "            MONITOR EN TIEMPO REAL: DESCARGA DE CHROMIUM" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "Destino: $target" -ForegroundColor Gray
Write-Host "Presiona Ctrl+C en cualquier momento para salir." -ForegroundColor DarkGray
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    $now = Get-Date
    $elapsed = $now - $startTime
    $elapsedStr = "{0:d2}:{1:d2}:{2:d2}" -f [int]$elapsed.TotalHours, $elapsed.Minutes, $elapsed.Seconds
    
    # Tamaño en disco
    $sizeGB = 0
    if (Test-Path $target) {
        try {
            $folder = $fso.GetFolder($target)
            $sizeGB = [math]::Round($folder.Size / 1GB, 3)
        } catch {}
    }
    
    # Última línea de progreso de Git
    $gitLine = "Conectando..."
    if (Test-Path $logPath) {
        try {
            $lines = Get-Content $logPath -Tail 5 -ErrorAction SilentlyContinue
            foreach ($l in $lines) {
                if ($l -match "Receiving objects|Resolving deltas|Updating files|Counting objects|Finding sources") {
                    $gitLine = $l.Trim()
                }
            }
        } catch {}
    }
    
    Write-Host "`r[$elapsedStr] Disco: $sizeGB GB | Git: $gitLine                       " -NoNewline -ForegroundColor Yellow
    
    Start-Sleep -Seconds 1
}
