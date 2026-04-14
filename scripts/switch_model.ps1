<#
.SYNOPSIS
  Switch opencode config between cost-first and quality-first

USAGE
  .\switch_model.ps1 cost
  .\switch_model.ps1 quality
  .\switch_model.ps1 status
#>
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('cost','quality','status')]
  [string]$Mode
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir '..')
$CostFile = Join-Path $Root 'opencode.json'
$QualityFile = Join-Path $Root 'opencode.quality.json'

function Status {
  if (!(Test-Path $CostFile)) { Write-Host "opencode.json not found"; return }
  if (!(Test-Path $QualityFile)) { Write-Host "opencode.quality.json not found"; return }
  $costHash = Get-FileHash $CostFile -Algorithm MD5
  $qualityHash = Get-FileHash $QualityFile -Algorithm MD5
  if ($costHash.Hash -eq $qualityHash.Hash) {
    Write-Host "Both configs are identical."
    return
  }
  Write-Host "Current opencode.json differs from opencode.quality.json" -ForegroundColor Yellow
}

switch ($Mode) {
  'status' { Status; break }
  'quality' {
    if (Test-Path $QualityFile) {
      Copy-Item -Force $QualityFile $CostFile
      Write-Host "Activated quality-first (copied opencode.quality.json -> opencode.json)"
    } else { Write-Error "Quality config not found: $QualityFile" }
    break
  }
  'cost' {
    $backup = Join-Path $Root 'opencode.cost_backup.json'
    if (Test-Path $backup) {
      Copy-Item -Force $backup $CostFile
      Write-Host "Restored previous cost-first config (from opencode.cost_backup.json)."
    } else {
      Write-Error "No backup found; cannot restore."; exit 1
    }
    break
  }
}
