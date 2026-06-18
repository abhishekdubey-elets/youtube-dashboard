# Make Elets-API log unbuffered so tracebacks flush immediately, then restart it.
$ErrorActionPreference = 'Continue'
$nssm = "C:\Users\User.DESKTOP-TARKBTO\AppData\Local\Microsoft\WinGet\Packages\NSSM.NSSM_Microsoft.Winget.Source_8wekyb3d8bbwe\nssm-2.24-101-g897c7ad\win64\nssm.exe"
$machinePath = [Environment]::GetEnvironmentVariable('Path','Machine')
& $nssm set Elets-API AppEnvironmentExtra "PATH=$machinePath" "PYTHONUNBUFFERED=1" | Out-Null
& $nssm stop  Elets-API confirm 2>$null | Out-Null
Start-Sleep -Seconds 2
$c = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($c) { $c | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }
Start-Sleep -Seconds 2
& $nssm start Elets-API 2>$null | Out-Null
Start-Sleep -Seconds 5
Set-Content "C:\Users\User.DESKTOP-TARKBTO\Projects\exhibitor\tools\diag-api.log" ("Elets-API = " + (Get-Service Elets-API).Status + " DONE")
