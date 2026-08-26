$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { throw 'python 을 찾을 수 없습니다.' }
$existing = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 8766 }
if ($existing) {
  Write-Host ('이미 8766 포트가 열려 있습니다. 브라우저만 엽니다. PID=' + ($existing.OwningProcess -join ','))
  Start-Process 'http://127.0.0.1:8766/'
  exit 0
}
Start-Process -FilePath $py.Source -ArgumentList @((Join-Path $root 'server.py'), '--port', '8766') -WorkingDirectory $root -WindowStyle Hidden
Start-Sleep -Seconds 1
Start-Process 'http://127.0.0.1:8766/'
Write-Host 'NEON BEAT: http://127.0.0.1:8766/'
