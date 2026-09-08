[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$CodexHome
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

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
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes([string]::Join("`n", $Lines))
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    try { return ([System.BitConverter]::ToString($Hasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $Hasher.Dispose() }
}

$CodexHome = Resolve-CodexHome $CodexHome
$ManifestPath = Join-Path $CodexHome 'codex-engineering-kit.manifest.json'
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Write-Host "Codex Engineering Kit manifest not found in $CodexHome; nothing to uninstall."
    return
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
if ($Manifest.schema_version -ne 1 -or $Manifest.toolkit -ne 'codex-engineering-kit') {
    throw 'Invalid Codex Engineering Kit manifest identity.'
}
$Preserved = [System.Collections.Generic.List[string]]::new()
$CodexHomePrefix = $CodexHome.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar

foreach ($Skill in $Manifest.skills) {
    $Name = [string]$Skill.name
    $RelativePath = ([string]$Skill.path).Replace('\', '/')
    if ($Name -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$' -or $RelativePath -ne "skills/$Name") {
        throw "Invalid toolkit-owned skill path in manifest: $RelativePath"
    }
    $Target = [System.IO.Path]::GetFullPath((Join-Path $CodexHome $RelativePath))
    if (-not $Target.StartsWith($CodexHomePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Toolkit-owned path escapes Codex home: $RelativePath"
    }
    if (-not (Test-Path -LiteralPath $Target -PathType Container)) { continue }

    $CurrentHash = Get-DirectoryTreeHash $Target
    if ($CurrentHash -ne [string]$Skill.tree_hash) {
        $Preserved.Add($RelativePath)
        Write-Warning "Preserving modified toolkit path: $Target"
        continue
    }

    if ($DryRun) {
        Write-Host "REMOVE $RelativePath"
    }
    else {
        Remove-Item -LiteralPath $Target -Recurse -Force
        Write-Host "REMOVED $RelativePath"
    }
}

if ($DryRun) {
    Write-Host "DRY RUN: manifest would be removed; no files changed."
    return
}

Remove-Item -LiteralPath $ManifestPath -Force
Write-Host 'Removed Codex Engineering Kit manifest.'
if ($Preserved.Count -gt 0) {
    Write-Warning ("Modified paths were preserved and are now user-owned: " + ($Preserved -join ', '))
}
