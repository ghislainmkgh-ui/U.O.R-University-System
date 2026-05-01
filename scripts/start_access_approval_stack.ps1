param(
    [int]$Port = 5002,
    [switch]$NoTunnel,
    [string]$Subdomain = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$apiScript = Join-Path $repoRoot "api\access_request_approval_api.py"
$envPath = Join-Path $repoRoot ".env"
$logDir = Join-Path $repoRoot "logs"

if (!(Test-Path $pythonExe)) {
    throw "Python virtual env introuvable: $pythonExe"
}
if (!(Test-Path $apiScript)) {
    throw "Script API introuvable: $apiScript"
}
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$apiOut = Join-Path $logDir "access_approval_api.out.log"
$apiErr = Join-Path $logDir "access_approval_api.err.log"
$tunnelOut = Join-Path $logDir "access_approval_tunnel.out.log"
$tunnelErr = Join-Path $logDir "access_approval_tunnel.err.log"
$localHealth = "http://127.0.0.1:$Port/health"

function Test-LocalHealth {
    param([string]$Url)
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return ($resp.StatusCode -eq 200)
    } catch {
        return $false
    }
}

# Export vars for API process
$env:ACCESS_APPROVAL_API_HOST = "0.0.0.0"
$env:ACCESS_APPROVAL_API_PORT = "$Port"
$env:ACCESS_APPROVAL_API_DEBUG = "False"

Write-Host "[1/5] Vérification API approbation locale..."
$apiProc = $null
$localOk = Test-LocalHealth -Url $localHealth

if (-not $localOk) {
    Write-Host "[2/5] Lancement API approbation sur le port $Port..."
    $apiArgs = "`"$apiScript`""
    $apiProc = Start-Process -FilePath $pythonExe -ArgumentList $apiArgs -WorkingDirectory $repoRoot -PassThru -RedirectStandardOutput $apiOut -RedirectStandardError $apiErr
    Start-Sleep -Milliseconds 900

    if ($apiProc.HasExited) {
        $errTail = ""
        if (Test-Path $apiErr) { $errTail = (Get-Content $apiErr -Tail 80) -join "`n" }
        throw "L'API s'est arrêtée immédiatement. Détails:`n$errTail"
    }
}

Write-Host "[3/5] Test santé locale..."
for ($i = 0; $i -lt 20; $i++) {
    $localOk = Test-LocalHealth -Url $localHealth
    if ($localOk) { break }
    Start-Sleep -Milliseconds 500
}
if (-not $localOk) {
    throw "L'API ne répond pas localement sur $localHealth"
}

$publicUrl = ""
$tunnelProc = $null
if (-not $NoTunnel) {
    Write-Host "[4/5] Lancement tunnel public (localtunnel)..."

    $ltCmd = "npx --yes localtunnel --port $Port"
    if ($Subdomain) {
        $ltCmd = "$ltCmd --subdomain $Subdomain"
    }

    $tunnelProc = Start-Process -FilePath "powershell" -ArgumentList "-NoProfile", "-Command", $ltCmd -WorkingDirectory $repoRoot -PassThru -RedirectStandardOutput $tunnelOut -RedirectStandardError $tunnelErr

    for ($i = 0; $i -lt 60; $i++) {
        if ($tunnelProc.HasExited) { break }
        if (Test-Path $tunnelOut) {
            $line = (Get-Content $tunnelOut | Select-String -Pattern "your url is:\s*(https?://\S+)" | Select-Object -Last 1)
            if ($line) {
                $publicUrl = [regex]::Match($line.ToString(), "https?://\S+").Value
                if ($publicUrl) { break }
            }
        }
        Start-Sleep -Seconds 1
    }

    if (-not $publicUrl) {
        throw "Impossible de récupérer l'URL publique localtunnel. Voir: $tunnelOut"
    }

    Write-Host "[5/5] Mise à jour de .env avec l'URL publique..."
    if (!(Test-Path $envPath)) {
        "ACCESS_APPROVAL_BASE_URL=$publicUrl`nACCESS_APPROVAL_API_PORT=$Port`nACCESS_APPROVAL_API_DEBUG=False`n" | Set-Content -Path $envPath -Encoding UTF8
    } else {
        $envContent = Get-Content $envPath -Raw

        if ($envContent -match "(?m)^ACCESS_APPROVAL_BASE_URL=") {
            $envContent = [regex]::Replace($envContent, "(?m)^ACCESS_APPROVAL_BASE_URL=.*$", "ACCESS_APPROVAL_BASE_URL=$publicUrl")
        } else {
            $envContent += "`r`nACCESS_APPROVAL_BASE_URL=$publicUrl"
        }

        if ($envContent -match "(?m)^ACCESS_APPROVAL_API_PORT=") {
            $envContent = [regex]::Replace($envContent, "(?m)^ACCESS_APPROVAL_API_PORT=.*$", "ACCESS_APPROVAL_API_PORT=$Port")
        } else {
            $envContent += "`r`nACCESS_APPROVAL_API_PORT=$Port"
        }

        if ($envContent -match "(?m)^ACCESS_APPROVAL_API_DEBUG=") {
            $envContent = [regex]::Replace($envContent, "(?m)^ACCESS_APPROVAL_API_DEBUG=.*$", "ACCESS_APPROVAL_API_DEBUG=False")
        } else {
            $envContent += "`r`nACCESS_APPROVAL_API_DEBUG=False"
        }

        Set-Content -Path $envPath -Value $envContent -Encoding UTF8
    }

    Write-Host "[5/5] Test santé publique..."
    $pubResp = Invoke-WebRequest -Uri "$publicUrl/health" -UseBasicParsing -TimeoutSec 15
    if ($pubResp.StatusCode -ne 200) {
        throw "Health public KO: $($pubResp.StatusCode)"
    }
}

Write-Host ""
Write-Host "===== STACK PRÊTE ====="
if ($apiProc) {
    Write-Host "API PID: $($apiProc.Id)"
} else {
    Write-Host "API PID: (réutilisé - déjà actif)"
}
Write-Host "API locale: $localHealth"
if ($publicUrl) {
    Write-Host "Tunnel PID: $($tunnelProc.Id)"
    Write-Host "URL publique: $publicUrl"
} else {
    Write-Host "Tunnel: désactivé (--NoTunnel)"
}
Write-Host "Logs API:    $apiOut"
if ($tunnelProc) {
    Write-Host "Logs tunnel: $tunnelOut"
}
