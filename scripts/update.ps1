[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [string]$CodexHome
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Install = Join-Path $PSScriptRoot 'install.ps1'
if (-not (Test-Path -LiteralPath $Install -PathType Leaf)) {
    throw "Installer not found: $Install"
}

$Args = @{}
if ($CodexHome) { $Args.CodexHome = $CodexHome }
if ($DryRun) { $Args.DryRun = $true }
if ($Force) { $Args.Force = $true }

& $Install @Args
