[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('github','supabase','vercel','railway','cloudflare')]
    [string]$Provider,

    [Parameter(Mandatory)][string]$OutputPath,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$TemplatePath = Join-Path $PSScriptRoot "templates/$Provider.json"
if (-not (Test-Path -LiteralPath $TemplatePath -PathType Leaf)) {
    throw "MCP template not found: $TemplatePath"
}

$Raw = Get-Content -LiteralPath $TemplatePath -Raw
$Template = $Raw | ConvertFrom-Json
$Missing = [System.Collections.Generic.List[string]]::new()
foreach ($Name in @($Template.required_environment)) {
    $Value = [System.Environment]::GetEnvironmentVariable([string]$Name)
    if ([string]::IsNullOrWhiteSpace($Value)) { $Missing.Add([string]$Name) }
}

if ($Missing.Count -gt 0) {
    throw "Missing required local environment variables for $Provider: $($Missing -join ', ')"
}

$ResolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
if ($DryRun) {
    Write-Host "DRY RUN: would write secret-free $Provider MCP metadata to $ResolvedOutput"
    if ($Template.login_required -eq $true) {
        Write-Host "$Provider requires a supported local login flow."
    }
    return
}

$Parent = Split-Path -Parent $ResolvedOutput
if ($Parent -and -not (Test-Path -LiteralPath $Parent)) {
    New-Item -ItemType Directory -Path $Parent -Force | Out-Null
}
Set-Content -LiteralPath $ResolvedOutput -Value $Raw -NoNewline -Encoding utf8
Write-Host "Wrote secret-free MCP metadata: $ResolvedOutput"
if ($Template.login_required -eq $true) {
    Write-Warning "$Provider still requires its supported local login flow; no credential was written by this script."
}
