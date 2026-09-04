[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ProjectPath,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonCommand = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$LauncherArgs = @()

if ($null -eq $PythonCommand) {
    $PythonCommand = Get-Command py -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $PythonCommand) {
        throw 'Python 3 is required: neither python nor py launcher is available.'
    }
    $LauncherArgs = @('-3')
}

$CliArgs = @(
    '-m', 'verification.cli',
    '--project', ([System.IO.Path]::GetFullPath($ProjectPath))
)
if ($Json) {
    $CliArgs += '--json'
}

$AllArgs = @($LauncherArgs) + @($CliArgs)
$NativeExitCode = 1
Push-Location $RepoRoot
try {
    & $PythonCommand.Source @AllArgs
    $NativeExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

$global:LASTEXITCODE = $NativeExitCode
