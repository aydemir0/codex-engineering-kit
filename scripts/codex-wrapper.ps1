[CmdletBinding()]
param(
    [string]$CheckpointPath,
    [string]$LearningInput,
    [string]$LearningOutput,
    [string[]]$CodexArgs = @()
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Codex = Get-Command codex -ErrorAction SilentlyContinue
if ($null -eq $Codex) {
    throw 'Codex CLI was not found on PATH.'
}

Write-Host "Codex preflight: $($Codex.Source)"
if ($CheckpointPath) {
    $ResolvedCheckpoint = [System.IO.Path]::GetFullPath($CheckpointPath)
    if (Test-Path -LiteralPath $ResolvedCheckpoint -PathType Leaf) {
        Write-Host "Checkpoint available: $ResolvedCheckpoint"
    }
    else {
        Write-Warning "Checkpoint was requested but not found: $ResolvedCheckpoint"
    }
}

& $Codex.Source @CodexArgs
$CodexExit = $LASTEXITCODE

if ($LearningInput) {
    if (-not $LearningOutput) {
        throw '-LearningOutput is required when -LearningInput is provided.'
    }
    $Learner = Join-Path $PSScriptRoot 'learn-session.ps1'
    & $Learner -InputPath $LearningInput -OutputPath $LearningOutput
}

if ($CodexExit -ne 0) {
    exit $CodexExit
}
