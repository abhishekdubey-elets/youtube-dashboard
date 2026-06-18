# =============================================================================
# Install the elets Transcript Dashboard backend as auto-starting Windows
# services via NSSM:  Elets-Redis, Elets-Worker, Elets-API
# Must be run elevated (Administrator). Idempotent — safe to re-run.
# =============================================================================
$ErrorActionPreference = 'Stop'
$log = "C:\Users\User.DESKTOP-TARKBTO\Projects\exhibitor\tools\install-services.log"
function Note($m) { $line = "[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $m; Add-Content $log $line; Write-Output $line }
Set-Content $log "=== install-services $(Get-Date) ==="

$root    = "C:\Users\User.DESKTOP-TARKBTO\Projects\exhibitor"
$backend = Join-Path $root "backend"
$nssm    = "C:\Users\User.DESKTOP-TARKBTO\AppData\Local\Microsoft\WinGet\Packages\NSSM.NSSM_Microsoft.Winget.Source_8wekyb3d8bbwe\nssm-2.24-101-g897c7ad\win64\nssm.exe"
$redisExe = Join-Path $root "tools\redis\redis-server.exe"
$celery   = Join-Path $backend ".venv\Scripts\celery.exe"
$python   = Join-Path $backend ".venv\Scripts\python.exe"
$logDir   = Join-Path $root "tools\logs"
$hfCache  = Join-Path $root "tools\hf-cache"
New-Item -ItemType Directory -Force -Path $logDir, $hfCache | Out-Null

# ffmpeg bin (winget user-scope) so the LocalSystem worker can find it
$ffmpeg = (Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
           Select-Object -First 1)
$ffBin = if ($ffmpeg) { Split-Path $ffmpeg.FullName } else { "" }
$machinePath = [Environment]::GetEnvironmentVariable('Path','Machine')
$workerPath  = if ($ffBin) { "$ffBin;$machinePath" } else { $machinePath }
Note "nssm   : $nssm"
Note "ffmpeg : $ffBin"

function Remove-Svc($name) {
  if (Get-Service -Name $name -ErrorAction SilentlyContinue) {
    Note "removing existing $name"
    & $nssm stop $name confirm 2>$null | Out-Null
    & $nssm remove $name confirm 2>$null | Out-Null
    Start-Sleep -Seconds 2
  }
}

function Install-Svc($name, $app, $argline, $appDir, $deps, $env) {
  Remove-Svc $name
  Note "installing $name -> $app $argline"
  & $nssm install $name $app | Out-Null
  if ($argline) { & $nssm set $name AppParameters $argline | Out-Null }
  & $nssm set $name AppDirectory $appDir | Out-Null
  & $nssm set $name DisplayName "elets $name" | Out-Null
  & $nssm set $name Description "elets Transcript Dashboard - $name" | Out-Null
  & $nssm set $name Start SERVICE_AUTO_START | Out-Null
  & $nssm set $name AppStdout (Join-Path $logDir "$name.out.log") | Out-Null
  & $nssm set $name AppStderr (Join-Path $logDir "$name.err.log") | Out-Null
  & $nssm set $name AppRotateFiles 1 | Out-Null
  & $nssm set $name AppRotateBytes 10485760 | Out-Null
  & $nssm set $name AppExit Default Restart | Out-Null
  & $nssm set $name AppRestartDelay 5000 | Out-Null
  if ($deps) { & $nssm set $name DependOnService $deps | Out-Null }
  if ($env)  { & $nssm set $name AppEnvironmentExtra $env | Out-Null }
}

# 1) Redis ---------------------------------------------------------------------
Install-Svc "Elets-Redis" $redisExe "--port 6379" (Split-Path $redisExe) $null $null

# 2) Worker (needs Redis + Postgres; ffmpeg on PATH; shared HF cache) ----------
Install-Svc "Elets-Worker" $celery `
  "-A app.workers.celery_app.celery worker --loglevel=info --pool=solo --concurrency=1" `
  $backend @("Elets-Redis","postgresql-x64-16") @("PATH=$workerPath","HF_HOME=$hfCache")

# 3) API (needs Redis + Postgres) ---------------------------------------------
Install-Svc "Elets-API" $python `
  "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" `
  $backend @("Elets-Redis","postgresql-x64-16") @("PATH=$machinePath")

# Start everything -------------------------------------------------------------
foreach ($s in "Elets-Redis","Elets-Worker","Elets-API") {
  & $nssm start $s 2>$null | Out-Null
  Start-Sleep -Seconds 3
  $st = (Get-Service -Name $s -ErrorAction SilentlyContinue).Status
  Note "$s status = $st"
}
Note "DONE"
