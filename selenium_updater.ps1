# ==============================================================================
# Selenium Browser Auto-Updater (Chrome-Style Background Engine)
# ==============================================================================
param(
    [switch]$CheckOnly,
    [switch]$Force,
    [switch]$Silent,
    [string]$ServerUrl = "https://update.dyepezg.dev/dl/selenium/version.json"
)

$ErrorActionPreference = "SilentlyContinue"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMsg = "[$timestamp] [$Level] $Message"
    if (-not $Silent) {
        switch ($Level) {
            "ERROR" { Write-Host $logMsg -ForegroundColor Red }
            "WARN"  { Write-Host $logMsg -ForegroundColor Yellow }
            "SUCCESS" { Write-Host $logMsg -ForegroundColor Green }
            default { Write-Host $logMsg -ForegroundColor Cyan }
        }
    }
    # Log to file in %LOCALAPPDATA%\Selenium\updater.log
    $logDir = "$env:LOCALAPPDATA\Selenium"
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    Add-Content -Path "$logDir\updater.log" -Value $logMsg -ErrorAction SilentlyContinue
}

function Show-ToastNotification {
    param([string]$Title, [string]$Message)
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $textNodes = $template.GetElementsByTagName("text")
        $textNodes.Item(0).AppendChild($template.CreateTextNode($Title)) | Out-Null
        $textNodes.Item(1).AppendChild($template.CreateTextNode($Message)) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Selenium Browser").Show($toast)
    } catch {
        # Fallback if WinRT toast fails in older PS session
    }
}

function Get-LocalSeleniumPath {
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Selenium\Application\selenium.exe",
        "C:\Program Files\Selenium\Application\selenium.exe",
        "C:\src\chromium\src\out\thorium\selenium.exe"
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path $p) {
            return $p
        }
    }
    return $null
}

function Compare-Versions {
    param([string]$v1, [string]$v2)
    try {
        $ver1 = [System.Version]$v1
        $ver2 = [System.Version]$v2
        return $ver1.CompareTo($ver2)
    } catch {
        # Fallback split
        $parts1 = $v1.Split('.') | ForEach-Object { [int]$_ }
        $parts2 = $v2.Split('.') | ForEach-Object { [int]$_ }
        for ($i = 0; $i -lt [Math]::Max($parts1.Length, $parts2.Length); $i++) {
            $p1 = if ($i -lt $parts1.Length) { $parts1[$i] } else { 0 }
            $p2 = if ($i -lt $parts2.Length) { $parts2[$i] } else { 0 }
            if ($p1 -lt $p2) { return -1 }
            if ($p1 -gt $p2) { return 1 }
        }
        return 0
    }
}

# 1. Localizar binario local de Selenium
$seleniumExe = Get-LocalSeleniumPath
if (-not $seleniumExe) {
    Write-Log "No se encontro ninguna instalacion local de Selenium." "ERROR"
    exit 1
}

$localVersion = (Get-Item $seleniumExe).VersionInfo.ProductVersion
if (-not $localVersion) {
    $localVersion = (Get-Item $seleniumExe).VersionInfo.FileVersion
}
Write-Log "Selenium local detectado: $seleniumExe (v$localVersion)"

# 2. Consultar el servidor de actualizaciones
Write-Log "Comprobando actualizaciones en: $ServerUrl..."
try {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 -bor [System.Net.SecurityProtocolType]::Tls13
    $response = Invoke-RestMethod -Uri $ServerUrl -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
} catch {
    Write-Log "No se pudo conectar al servidor de actualizaciones: $($_.Exception.Message)" "WARN"
    exit 0
}

$remoteVersion = if ($response.latest -and $response.latest.version) { $response.latest.version } else { $response.version }
$downloadUrl = if ($response.latest -and $response.latest.download_url) { $response.latest.download_url } else { $response.download_url }
$expectedSha = if ($response.latest -and $response.latest.sha256) { $response.latest.sha256 } else { $response.sha256 }

if (-not $remoteVersion -or -not $downloadUrl) {
    Write-Log "Respuesta del servidor invalida o incompleta." "WARN"
    exit 0
}

Write-Log "Ultima version disponible en el servidor: v$remoteVersion"

# 3. Comparar versiones
$comparison = Compare-Versions $remoteVersion $localVersion
if ($comparison -le 0 -and -not $Force) {
    Write-Log "Selenium esta completamente actualizado (v$localVersion)." "SUCCESS"
    exit 0
}

Write-Log "¡Nueva version detectada! (Remota: v$remoteVersion > Local: v$localVersion)" "SUCCESS"

if ($CheckOnly) {
    Write-Log "Modo solo comprobacion activo. No se descargara nada."
    exit 0
}

# 4. Descargar instalador
$tempDir = "$env:TEMP\SeleniumUpdate"
if (-not (Test-Path $tempDir)) { New-Item -ItemType Directory -Path $tempDir -Force | Out-Null }
$installerDest = "$tempDir\selenium_installer.exe"

Write-Log "Descargando actualizacion desde: $downloadUrl..."
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerDest -TimeoutSec 180 -UseBasicParsing -ErrorAction Stop
} catch {
    Write-Log "Fallo al descargar el instalador: $($_.Exception.Message)" "ERROR"
    exit 1
}

# 5. Verificar Hash SHA-256 si esta presente
if ($expectedSha) {
    Write-Log "Verificando integridad SHA-256..."
    $actualSha = (Get-FileHash -Path $installerDest -Algorithm SHA256).Hash.ToLower()
    if ($actualSha -ne $expectedSha.ToLower()) {
        Write-Log "Error de integridad: el hash SHA-256 no coincide (Esperado: $expectedSha, Obtenido: $actualSha)" "ERROR"
        Remove-Item $installerDest -Force -ErrorAction SilentlyContinue
        exit 1
    }
    Write-Log "Verificacion SHA-256 correcta." "SUCCESS"
}

# 6. Ejecutar instalador silenciosamente (Chrome-style background install)
Write-Log "Instalando actualizacion en segundo plano..."
$installArgs = @("--silent", "--do-not-launch-chrome")
$proc = Start-Process -FilePath $installerDest -ArgumentList $installArgs -PassThru -Wait

if ($proc.ExitCode -eq 0) {
    Write-Log "Selenium se ha actualizado exitosamente a la version $remoteVersion." "SUCCESS"
    Show-ToastNotification "Selenium Browser Actualizado" "La version $remoteVersion se instalo correctamente. Reinicia el navegador para aplicar los cambios."
} else {
    Write-Log "El instalador finalizo con codigo de salida: $($proc.ExitCode)" "WARN"
}

# Limpiar instalador temporal
Remove-Item $installerDest -Force -ErrorAction SilentlyContinue
