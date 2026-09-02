$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Learn = Join-Path $RepoRoot 'scripts/learn-session.ps1'
Assert-True (Test-Path -LiteralPath $Learn) 'learn-session.ps1 must exist'

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-kit-learning-test-" + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null
    $InputPath = Join-Path $TempRoot 'observations.json'
    $OutputPath = Join-Path $TempRoot 'candidates.json'

    @'
[
  {
    "title": "Node-only PDF import must stay out of browser module evaluation",
    "category": "error_resolution",
    "evidence": [
      "DOMMatrix failure reproduced during server module evaluation",
      "moving browser-only import behind the runtime boundary fixed the build"
    ],
    "scope": "general"
  },
  {
    "title": "Fixed a one-off spelling typo",
    "category": "simple_typo",
    "evidence": ["single typo correction"],
    "scope": "project"
  },
  {
    "title": "Secret-bearing workaround",
    "category": "workaround",
    "evidence": ["use ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456 directly in config"],
    "scope": "general"
  }
]
'@ | Set-Content -LiteralPath $InputPath

    & $Learn -InputPath $InputPath -OutputPath $OutputPath | Out-Null
    Assert-True (Test-Path -LiteralPath $OutputPath) 'candidate output must be created'

    $Result = Get-Content -LiteralPath $OutputPath -Raw | ConvertFrom-Json
    Assert-True ($Result.candidates.Count -eq 1) 'exactly one reusable candidate must survive'
    Assert-True ($Result.candidates[0].promotion_status -eq 'pending_review') 'candidate must require review'
    Assert-True ($Result.candidates[0].contains_sensitive_data -eq $false) 'accepted candidate must be sanitized'
    Assert-True ($Result.rejected.Count -eq 2) 'typo and secret-bearing observation must be rejected'
    Assert-True (($Result.rejected.reason -join ' ') -match 'unsupported category') 'simple typo must be rejected by category'
    Assert-True (($Result.rejected.reason -join ' ') -match 'sensitive') 'secret-bearing observation must be rejected'
    Assert-True (-not (Test-Path -LiteralPath (Join-Path $TempRoot 'skills'))) 'learning must not auto-install skills'

    Write-Host 'PASS: learning candidate contracts satisfied'
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
