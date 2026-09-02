[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [string]$CodexHome
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolkitVersion = '0.1.0'
$SkillNames = @(
    'orchestrator',
    'continuous-learning',
    'eval-harness',
    'verification-loop',
    'software-architecture',
    'concurrency-performance'
)

function Resolve-CodexHome {
    param([string]$ExplicitPath)
    if ($ExplicitPath) { return [System.IO.Path]::GetFullPath($ExplicitPath) }
    if ($env:CODEX_HOME) { return [System.IO.Path]::GetFullPath($env:CODEX_HOME) }
    return [System.IO.Path]::GetFullPath((Join-Path $HOME '.codex'))
}

function Get-DirectoryTreeHash {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return $null }

    $Root = [System.IO.Path]::GetFullPath($Path).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $Lines = foreach ($File in Get-ChildItem -LiteralPath $Root -File -Recurse | Sort-Object FullName) {
        $Relative = $File.FullName.Substring($Root.Length).TrimStart('\', '/').Replace('\', '/')
        $Hash = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$Relative`n$Hash"
    }

    $Payload = [string]::Join("`n", $Lines)
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Payload)
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($Hasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $Hasher.Dispose()
    }
}

function Read-Manifest {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-ManifestSkill {
    param($Manifest, [string]$Name)
    if ($null -eq $Manifest -or $null -eq $Manifest.skills) { return $null }
    return $Manifest.skills | Where-Object { $_.name -eq $Name } | Select-Object -First 1
}

function Backup-Target {
    param([string]$Target, [string]$Name, [string]$Home)
    if (-not (Test-Path -LiteralPath $Target)) { return $null }
    $Stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $BackupRoot = Join-Path $Home "backups/codex-engineering-kit/$Stamp/skills"
    $BackupPath = Join-Path $BackupRoot $Name
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    Copy-Item -LiteralPath $Target -Destination $BackupPath -Recurse -Force
    return $BackupPath
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SourceSkills = Join-Path $RepoRoot 'skills'
$CodexHome = Resolve-CodexHome $CodexHome
$ManifestPath = Join-Path $CodexHome 'codex-engineering-kit.manifest.json'
$ExistingManifest = Read-Manifest $ManifestPath

$Planned = [System.Collections.Generic.List[string]]::new()
$ManifestSkills = [System.Collections.Generic.List[object]]::new()

foreach ($Name in $SkillNames) {
    $Source = Join-Path $SourceSkills $Name
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        throw "Toolkit source skill is missing: $Source"
    }

    $RelativeTarget = "skills/$Name"
    $Target = Join-Path $CodexHome $RelativeTarget
    $SourceHash = Get-DirectoryTreeHash $Source
    $ExistingEntry = Get-ManifestSkill $ExistingManifest $Name
    $TargetExists = Test-Path -LiteralPath $Target -PathType Container
    $TargetHash = if ($TargetExists) { Get-DirectoryTreeHash $Target } else { $null }

    if ($TargetExists -and $TargetHash -eq $SourceHash) {
        $Planned.Add("UNCHANGED $RelativeTarget")
    }
    elseif ($TargetExists) {
        $OwnedAndUnmodified = $null -ne $ExistingEntry -and $TargetHash -eq [string]$ExistingEntry.tree_hash
        if (-not $OwnedAndUnmodified -and -not $Force) {
            throw "Refusing to overwrite user-modified or unowned target: $Target. Re-run with -Force to back it up and replace it."
        }

        if ($DryRun) {
            $Action = if ($OwnedAndUnmodified) { 'UPDATE' } else { 'BACKUP+REPLACE' }
            $Planned.Add("$Action $RelativeTarget")
        }
        else {
            if (-not $OwnedAndUnmodified) {
                $Backup = Backup-Target -Target $Target -Name $Name -Home $CodexHome
                Write-Host "Backed up $RelativeTarget to $Backup"
            }
            Remove-Item -LiteralPath $Target -Recurse -Force
            New-Item -ItemType Directory -Path (Split-Path -Parent $Target) -Force | Out-Null
            Copy-Item -LiteralPath $Source -Destination $Target -Recurse -Force
            $Planned.Add("INSTALLED $RelativeTarget")
        }
    }
    else {
        if ($DryRun) {
            $Planned.Add("INSTALL $RelativeTarget")
        }
        else {
            New-Item -ItemType Directory -Path (Split-Path -Parent $Target) -Force | Out-Null
            Copy-Item -LiteralPath $Source -Destination $Target -Recurse -Force
            $Planned.Add("INSTALLED $RelativeTarget")
        }
    }

    $ManifestSkills.Add([ordered]@{
        name = $Name
        path = $RelativeTarget
        tree_hash = $SourceHash
    })
}

$Manifest = [ordered]@{
    schema_version = 1
    toolkit = 'codex-engineering-kit'
    toolkit_version = $ToolkitVersion
    skills = $ManifestSkills
}
$ManifestJson = $Manifest | ConvertTo-Json -Depth 6

if ($DryRun) {
    Write-Host "DRY RUN: no files changed in $CodexHome"
    $Planned | ForEach-Object { Write-Host $_ }
    return
}

New-Item -ItemType Directory -Path $CodexHome -Force | Out-Null
$CurrentManifest = if (Test-Path -LiteralPath $ManifestPath) { Get-Content -LiteralPath $ManifestPath -Raw } else { $null }
if ($CurrentManifest -ne $ManifestJson) {
    Set-Content -LiteralPath $ManifestPath -Value $ManifestJson -NoNewline -Encoding utf8
}

$Planned | ForEach-Object { Write-Host $_ }
Write-Host "Codex Engineering Kit $ToolkitVersion installed in $CodexHome"
