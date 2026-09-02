$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Verify = Join-Path $RepoRoot 'scripts/verify.ps1'
Assert-True (Test-Path -LiteralPath $Verify) 'verify.ps1 must exist'

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-kit-verify-test-" + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null

    $Good = Join-Path $TempRoot 'good'
    New-Item -ItemType Directory -Path $Good -Force | Out-Null
    @'
{
  "name": "verify-good",
  "private": true,
  "scripts": {
    "build": "node -e \"process.exit(0)\"",
    "typecheck": "node -e \"process.exit(0)\"",
    "test": "node -e \"process.exit(0)\""
  }
}
'@ | Set-Content -LiteralPath (Join-Path $Good 'package.json')

    $GoodJson = & $Verify -ProjectPath $Good -Json
    $GoodResult = $GoodJson | ConvertFrom-Json
    Assert-True ($GoodResult.build.status -eq 'PASS') 'build must pass'
    Assert-True ($GoodResult.typecheck.status -eq 'PASS') 'typecheck must pass'
    Assert-True ($GoodResult.tests.status -eq 'PASS') 'tests must pass'
    Assert-True ($GoodResult.lint.status -eq 'SKIPPED') 'missing lint command must be explicitly skipped'
    Assert-True ($GoodResult.readiness -eq 'READY') 'passing discovered required gates must be READY'
    Assert-True ($GoodResult.commands.Count -eq 3) 'report must contain the three commands actually executed'

    $Bad = Join-Path $TempRoot 'bad'
    New-Item -ItemType Directory -Path $Bad -Force | Out-Null
    @'
{
  "name": "verify-bad",
  "private": true,
  "scripts": {
    "build": "node -e \"process.exit(0)\"",
    "test": "node -e \"process.exit(7)\""
  }
}
'@ | Set-Content -LiteralPath (Join-Path $Bad 'package.json')

    $BadJson = & $Verify -ProjectPath $Bad -Json
    $BadResult = $BadJson | ConvertFrom-Json
    Assert-True ($BadResult.tests.status -eq 'FAIL') 'failing test command must be FAIL'
    Assert-True ($BadResult.tests.exit_code -eq 7) 'real exit code must be preserved'
    Assert-True ($BadResult.readiness -eq 'NOT_READY') 'failed required gate must block readiness'

    Write-Host 'PASS: verification contracts satisfied'
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
