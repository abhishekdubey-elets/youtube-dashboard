# Clean reconcile of the elets services. Run elevated. Idempotent.
$ErrorActionPreference = 'Continue'
$log = "C:\Users\User.DESKTOP-TARKBTO\Projects\exhibitor\tools\restart-services.log"
function Note($m){ $l="[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'),$m; Add-Content $log $l }
Set-Content $log "=== restart $(Get-Date) ==="
$nssm = "C:\Users\User.DESKTOP-TARKBTO\AppData\Local\Microsoft\WinGet\Packages\NSSM.NSSM_Microsoft.Winget.Source_8wekyb3d8bbwe\nssm-2.24-101-g897c7ad\win64\nssm.exe"
$svcs = "Elets-API","Elets-Worker","Elets-Redis"

# Stop all services
foreach ($s in $svcs) { & $nssm stop $s confirm 2>$null | Out-Null; Note "stopped $s" }
Start-Sleep -Seconds 3

# Kill any strays still holding the ports
foreach ($port in 8000,6379) {
  $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if ($c) { $c | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Note "killed stray PID $($_.OwningProcess) on $port" } }
}
Start-Sleep -Seconds 2

# Start in dependency order
foreach ($s in "Elets-Redis","Elets-Worker","Elets-API") {
  & $nssm start $s 2>$null | Out-Null
  Start-Sleep -Seconds 5
  Note ("{0} = {1}" -f $s, (Get-Service $s -ErrorAction SilentlyContinue).Status)
}
Note "DONE"
