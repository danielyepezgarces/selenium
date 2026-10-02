# ==============================================================================
# Registra la Tarea Programada de Actualizacion en Segundo Plano (Estilo Chrome)
# ==============================================================================
$TaskName = "SeleniumUpdateTaskUser"
$UpdaterScript = "C:\thorium\selenium_updater.ps1"

if (-not (Test-Path $UpdaterScript)) {
    Write-Error "No se encontro el script del actualizador en: $UpdaterScript"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$UpdaterScript`" -Silent"

# Disparadores: Al iniciar sesion y diariamente cada 24 horas
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn
$TriggerDaily = New-ScheduledTaskTrigger -Daily -At "12:00"

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

try {
    # Usar schtasks.exe para registrar la tarea a nivel de usuario sin requerir elevacion de Administrador
    $cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$UpdaterScript`" -Silent"
    & schtasks.exe /Create /TN $TaskName /TR "`"$cmd`"" /SC DAILY /ST 12:00 /F | Out-Null
    
    Write-Host "[EXITO] Tarea programada '$TaskName' registrada correctamente en Windows." -ForegroundColor Green
    Write-Host "Se ejecutara diariamente a las 12:00 PM para mantener Selenium siempre actualizado." -ForegroundColor Cyan
} catch {
    Write-Error "Error al registrar la tarea: $($_.Exception.Message)"
}
