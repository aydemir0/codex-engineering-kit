$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
}

function Get-Step {
    param($Report, [string]$Name)
    return @($Report.steps | Where-Object { $_.name -eq $Name })[0]
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
  "packageManager": "npm@10.0.0",
  "scripts": {
    "build": "node -e \"process.exit(0)\"",
    "typecheck": "node -e \"process.exit(0)\"",
    "test": "node -e \"process.exit(0)\""
  }
}
'@ | Set-Content -LiteralPath (Join-Path $Good 'package.json')

    $GoodJson = & $Verify -ProjectPath $Good -Json
    $GoodExit = $LASTEXITCODE
    $GoodResult = $GoodJson | ConvertFrom-Json
    $GoodBuild = Get-Step $GoodResult 'build'
    $GoodTypecheck = Get-Step $GoodResult 'typecheck'
    $GoodTests = Get-Step $GoodResult 'tests'
    $GoodLint = Get-Step $GoodResult 'lint'

    Assert-True ($GoodExit -eq 0) 'passing verification wrapper must preserve CLI exit code 0'
    Assert-True ($GoodBuild.status -eq 'passed') 'build must pass with lowercase status'
    Assert-True ($GoodTypecheck.status -eq 'passed') 'typecheck must pass with lowercase status'
    Assert-True ($GoodTests.status -eq 'passed') 'tests must pass with lowercase status'
    Assert-True ($GoodLint.status -eq 'skipped') 'missing lint command must remain explicitly skipped'
    Assert-True ($null -eq $GoodLint.command) 'skipped lint must not invent a command'
    Assert-True ($GoodResult.status -eq 'passed') 'passing discovered gates must produce passed overall status'

    $GoodArtifactPath = Join-Path $Good '.codex-kit/verification/latest.json'
    Assert-True (Test-Path -LiteralPath $GoodArtifactPath -PathType Leaf) 'default versioned verification artifact must exist'
    $GoodArtifact = Get-Content -LiteralPath $GoodArtifactPath -Raw | ConvertFrom-Json
    Assert-True ($GoodArtifact.schemaVersion -eq 1) 'artifact schemaVersion must be 1'
    Assert-True ($GoodArtifact.kind -eq 'verification-report') 'artifact kind must be verification-report'
    Assert-True ($GoodArtifact.status -eq 'passed') 'artifact must preserve report status'

    $Bad = Join-Path $TempRoot 'bad'
    New-Item -ItemType Directory -Path $Bad -Force | Out-Null
    @'
{
  "name": "verify-bad",
  "private": true,
  "packageManager": "npm@10.0.0",
  "scripts": {
    "build": "node -e \"process.exit(0)\"",
    "test": "node -e \"process.exit(7)\""
  }
}
'@ | Set-Content -LiteralPath (Join-Path $Bad 'package.json')

    $BadJson = & $Verify -ProjectPath $Bad -Json
    $BadExit = $LASTEXITCODE
    $BadResult = $BadJson | ConvertFrom-Json
    $BadTests = Get-Step $BadResult 'tests'
    $BadLint = Get-Step $BadResult 'lint'

    Assert-True ($BadExit -eq 1) 'failed verification wrapper must preserve CLI exit code 1'
    Assert-True ($BadTests.status -eq 'failed') 'failing test command must be failed'
    Assert-True ($BadTests.exitCode -eq 7) 'real exit code 7 must be preserved'
    Assert-True ($BadLint.status -eq 'skipped') 'missing lint must remain skipped in failed report'
    Assert-True ($BadResult.status -eq 'failed') 'failed required gate must fail overall report'

    $BadArtifactPath = Join-Path $Bad '.codex-kit/verification/latest.json'
    $BadArtifact = Get-Content -LiteralPath $BadArtifactPath -Raw | ConvertFrom-Json
    Assert-True ($BadArtifact.schemaVersion -eq 1) 'failed artifact schemaVersion must be 1'
    Assert-True ($BadArtifact.kind -eq 'verification-report') 'failed artifact kind must be verification-report'
    Assert-True ($BadArtifact.status -eq 'failed') 'failed artifact must preserve failed status'

    $global:LASTEXITCODE = 0
    Write-Host 'PASS: verification compatibility wrapper contract satisfied'
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
