$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
}

function Assert-Throws {
    param([scriptblock]$Action, [string]$Message)
    $threw = $false
    try { & $Action } catch { $threw = $true }
    if (-not $threw) { throw "ASSERTION FAILED: $Message" }
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Install = Join-Path $RepoRoot 'scripts/install.ps1'
$Uninstall = Join-Path $RepoRoot 'scripts/uninstall.ps1'

Assert-True (Test-Path -LiteralPath $Install) 'install.ps1 must exist'
Assert-True (Test-Path -LiteralPath $Uninstall) 'uninstall.ps1 must exist'

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-kit-install-test-" + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null

    $DryHome = Join-Path $TempRoot 'dry-home'
    & $Install -CodexHome $DryHome -DryRun | Out-Null
    Assert-True (-not (Test-Path -LiteralPath $DryHome)) 'dry-run must not create Codex home'

    $InstallHome = Join-Path $TempRoot 'install-home'
    & $Install -CodexHome $InstallHome | Out-Null

    $ExpectedSkills = @(
        'orchestrator',
        'continuous-learning',
        'eval-harness',
        'verification-loop',
        'software-architecture',
        'concurrency-performance'
    )

    foreach ($Skill in $ExpectedSkills) {
        $SkillFile = Join-Path $InstallHome ("skills/$Skill/SKILL.md")
        Assert-True (Test-Path -LiteralPath $SkillFile) "installed skill missing: $Skill"
    }

    $ManifestPath = Join-Path $InstallHome 'codex-engineering-kit.manifest.json'
    Assert-True (Test-Path -LiteralPath $ManifestPath) 'manifest must be written'
    $ManifestBefore = Get-Content -LiteralPath $ManifestPath -Raw

    & $Install -CodexHome $InstallHome | Out-Null
    $ManifestAfter = Get-Content -LiteralPath $ManifestPath -Raw
    Assert-True ($ManifestBefore -eq $ManifestAfter) 'second install must be idempotent'

    $ConflictHome = Join-Path $TempRoot 'conflict-home'
    $ConflictTarget = Join-Path $ConflictHome 'skills/orchestrator'
    New-Item -ItemType Directory -Path $ConflictTarget -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $ConflictTarget 'SKILL.md') -Value 'user-owned content' -NoNewline
    Assert-Throws { & $Install -CodexHome $ConflictHome | Out-Null } 'installer must refuse unsafe overwrite without -Force'

    $UserSentinel = Join-Path $InstallHome 'user-owned.txt'
    Set-Content -LiteralPath $UserSentinel -Value 'keep me' -NoNewline
    & $Uninstall -CodexHome $InstallHome | Out-Null
    Assert-True (Test-Path -LiteralPath $UserSentinel) 'uninstall must preserve user-owned files'
    Assert-True (-not (Test-Path -LiteralPath $ManifestPath)) 'uninstall must remove toolkit manifest'
    foreach ($Skill in $ExpectedSkills) {
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $InstallHome "skills/$Skill"))) "uninstall must remove toolkit-owned skill: $Skill"
    }

    Write-Host 'PASS: installer lifecycle contracts satisfied'
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
