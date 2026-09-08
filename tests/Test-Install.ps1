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

function Get-TestDirectoryTreeHash {
    param([Parameter(Mandatory)][string]$Path)
    $Root = [System.IO.Path]::GetFullPath($Path).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $Lines = foreach ($File in Get-ChildItem -LiteralPath $Root -File -Recurse | Sort-Object FullName) {
        $Relative = $File.FullName.Substring($Root.Length).TrimStart('\', '/').Replace('\', '/')
        $Hash = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$Relative`n$Hash"
    }
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes([string]::Join("`n", $Lines))
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    try { return ([System.BitConverter]::ToString($Hasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $Hasher.Dispose() }
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
    & $Install -CodexHome $ConflictHome -Force | Out-Null
    $BackupSkill = Get-ChildItem -LiteralPath (Join-Path $ConflictHome 'backups') -Filter 'SKILL.md' -File -Recurse |
        Where-Object { $_.FullName -match '[\\/]orchestrator[\\/]SKILL\.md$' } |
        Select-Object -First 1
    Assert-True ($null -ne $BackupSkill) 'forced replacement must back up unowned content'
    Assert-True ((Get-Content -LiteralPath $BackupSkill.FullName -Raw) -eq 'user-owned content') 'backup must preserve original content'

    $TamperedHome = Join-Path $TempRoot 'tampered-manifest-home'
    $TamperedTarget = Join-Path $TamperedHome 'skills/orchestrator'
    New-Item -ItemType Directory -Path $TamperedTarget -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $TamperedTarget 'SKILL.md') -Value 'user-owned manifest target' -NoNewline
    [ordered]@{
        schema_version = 1
        toolkit = 'codex-engineering-kit'
        toolkit_version = 'fixture'
        skills = @([ordered]@{
            name = 'orchestrator'
            path = 'skills/different-target'
            tree_hash = Get-TestDirectoryTreeHash $TamperedTarget
        })
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (
        Join-Path $TamperedHome 'codex-engineering-kit.manifest.json'
    )
    Assert-Throws {
        & $Install -CodexHome $TamperedHome -DryRun | Out-Null
    } 'installer must reject a manifest whose declared name and path disagree'
    Assert-True ((Get-Content -LiteralPath (Join-Path $TamperedTarget 'SKILL.md') -Raw) -eq 'user-owned manifest target') 'tampered manifest must not authorize replacement'

    $TraversalHome = Join-Path $TempRoot 'traversal-home'
    $TraversalTarget = Join-Path $TempRoot 'outside-owned-path'
    New-Item -ItemType Directory -Path $TraversalHome -Force | Out-Null
    New-Item -ItemType Directory -Path $TraversalTarget -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $TraversalTarget 'SKILL.md') -Value 'outside content' -NoNewline
    $TreeHash = Get-TestDirectoryTreeHash $TraversalTarget
    [ordered]@{
        schema_version = 1
        toolkit = 'codex-engineering-kit'
        version = 'fixture'
        skills = @([ordered]@{
            name = 'outside-owned-path'
            path = '../outside-owned-path'
            tree_hash = $TreeHash
        })
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (
        Join-Path $TraversalHome 'codex-engineering-kit.manifest.json'
    )
    Assert-Throws {
        & $Uninstall -CodexHome $TraversalHome -DryRun | Out-Null
    } 'uninstall must reject manifest paths outside Codex home'
    Assert-True (Test-Path -LiteralPath $TraversalTarget) 'outside path must remain untouched'

    $DotHome = Join-Path $TempRoot 'dot-home'
    $DotSkills = Join-Path $DotHome 'skills'
    New-Item -ItemType Directory -Path (Join-Path $DotSkills 'visible-skill') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $DotSkills 'visible-skill/SKILL.md') -Value 'visible content' -NoNewline
    [ordered]@{
        schema_version = 1
        toolkit = 'codex-engineering-kit'
        version = 'fixture'
        skills = @([ordered]@{
            name = '.'
            path = 'skills/.'
            tree_hash = Get-TestDirectoryTreeHash $DotSkills
        })
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (
        Join-Path $DotHome 'codex-engineering-kit.manifest.json'
    )
    Assert-Throws {
        & $Uninstall -CodexHome $DotHome -DryRun | Out-Null
    } 'uninstall must reject dot-segment skill names that target the skills root'
    Assert-True (Test-Path -LiteralPath (Join-Path $DotSkills 'visible-skill/SKILL.md')) 'skills root must remain untouched'

    $UserSentinel = Join-Path $InstallHome 'user-owned.txt'
    Set-Content -LiteralPath $UserSentinel -Value 'keep me' -NoNewline
    $ModifiedSkill = Join-Path $InstallHome 'skills/orchestrator/USER_CHANGE.txt'
    Set-Content -LiteralPath $ModifiedSkill -Value 'preserve me' -NoNewline
    & $Uninstall -CodexHome $InstallHome | Out-Null
    Assert-True (Test-Path -LiteralPath $UserSentinel) 'uninstall must preserve user-owned files'
    Assert-True (-not (Test-Path -LiteralPath $ManifestPath)) 'uninstall must remove toolkit manifest'
    foreach ($Skill in $ExpectedSkills) {
        $SkillPath = Join-Path $InstallHome "skills/$Skill"
        if ($Skill -eq 'orchestrator') {
            Assert-True (Test-Path -LiteralPath $ModifiedSkill) 'uninstall must preserve modified installed skill'
        }
        else {
            Assert-True (-not (Test-Path -LiteralPath $SkillPath)) "uninstall must remove toolkit-owned skill: $Skill"
        }
    }

    Write-Host 'PASS: installer lifecycle contracts satisfied'
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
