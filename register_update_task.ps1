# ==============================================================================
# Registra la Tarea Programada de Actualizacion en Segundo Plano (Estilo Chrome)
# Utiliza silent_updater.vbs para ejecutar PowerShell sin ningun parpadeo de CMD
# ==============================================================================
$TaskName = "SeleniumUpdateTaskUser"
$VbsScript = "C:\thorium\silent_updater.vbs"

if (-not (Test-Path $VbsScript)) {
    Write-Error "No se encontro el lanzador silencioso en: $VbsScript"
    exit 1
}

try {
    # Usar wscript.exe para invocar el VBS de forma 100% invisible (Subsystem GUI, SW_HIDE = 0)
    $taskRun = "wscript.exe `"$VbsScript`""
    & schtasks.exe /Create /TN $TaskName /TR $taskRun /SC DAILY /ST 12:00 /F | Out-Null
    
    Write-Host "[EXITO] Tarea programada '$TaskName' registrada correctamente con ejecucion 100% invisible." -ForegroundColor Green
    Write-Host "Se ejecutara diariamente a las 12:00 PM sin ningun parpadeo de consola CMD." -ForegroundColor Cyan
} catch {
    Write-Error "Error al registrar la tarea: $($_.Exception.Message)"
}
