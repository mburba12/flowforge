$ErrorActionPreference="Stop";Write-Host "Run after API startup: Phase 2A live acceptance" -ForegroundColor Cyan
$Status=Invoke-RestMethod -Uri "http://127.0.0.1:8000/phase2a/status";if($Status.status-ne "implemented"){throw "Phase 2A status failed"};Write-Host "PHASE 2A LIVE STATUS PASSED" -ForegroundColor Green
