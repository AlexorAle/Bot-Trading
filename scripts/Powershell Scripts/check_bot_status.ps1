chcp 65001 > $null
Write-Host "`n🔍 Verificando Estado del Bot`n" -ForegroundColor Cyan

function Show-Status($label, $ok) {
    if ($ok) {
        Write-Host "$label:`t✓ OK" -ForegroundColor Green
    } else {
        Write-Host "$label:`t✗ ERROR" -ForegroundColor Red
    }
}

$botRunning = Get-Process | Where-Object { $_.Path -like '*paper_trading_main.py*' }
Show-Status "Bot" ($botRunning -ne $null)

$ports = @{8080 = "Métricas"; 9090 = "Prometheus"; 3000 = "Grafana"}
foreach ($port in $ports.Keys) {
    $status = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    Show-Status $ports[$port] ($status -ne $null)
}

try {
    $metrics = Invoke-WebRequest http://localhost:8080/metrics -UseBasicParsing
    Write-Host "`n📊 Métricas relevantes:" -ForegroundColor Yellow
    $metrics.Content -split "`n" | Where-Object { $_ -like "paper_*" } | ForEach-Object { Write-Host $_ }
} catch {
    Write-Host "❌ No se pudo obtener métricas." -ForegroundColor Red
}
