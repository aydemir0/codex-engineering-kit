[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ProjectPath,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function New-SkippedGate {
    param([string]$Reason)
    return [ordered]@{ status = 'SKIPPED'; exit_code = $null; evidence = $Reason }
}

function Invoke-PackageScript {
    param(
        [string]$PackageManager,
        [string]$ScriptName,
        [string]$WorkingDirectory
    )

    Push-Location $WorkingDirectory
    try {
        $Output = & $PackageManager run $ScriptName --silent 2>&1
        $ExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    $Evidence = (($Output | Select-Object -Last 20) -join [Environment]::NewLine).Trim()
    if (-not $Evidence) { $Evidence = 'Command completed without output.' }

    return [ordered]@{
        status = if ($ExitCode -eq 0) { 'PASS' } else { 'FAIL' }
        exit_code = $ExitCode
        evidence = $Evidence
        command = "$PackageManager run $ScriptName --silent"
    }
}

function Get-PackageManager {
    param([string]$Path)
    if (Test-Path -LiteralPath (Join-Path $Path 'pnpm-lock.yaml')) { return 'pnpm' }
    if (Test-Path -LiteralPath (Join-Path $Path 'yarn.lock')) { return 'yarn' }
    if ((Test-Path -LiteralPath (Join-Path $Path 'bun.lockb')) -or (Test-Path -LiteralPath (Join-Path $Path 'bun.lock'))) { return 'bun' }
    return 'npm'
}

function Test-SecretPatterns {
    param([string]$Path)

    $Patterns = @(
        'ghp_[A-Za-z0-9]{16,}',
        'sk-[A-Za-z0-9]{16,}',
        'BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY'
    )
    $Extensions = @('.js','.jsx','.ts','.tsx','.mjs','.cjs','.py','.json','.yaml','.yml','.toml','.env','.md','.txt','.ps1')
    $Findings = [System.Collections.Generic.List[string]]::new()

    foreach ($File in Get-ChildItem -LiteralPath $Path -File -Recurse -ErrorAction SilentlyContinue) {
        $Relative = $File.FullName.Substring([System.IO.Path]::GetFullPath($Path).TrimEnd('\','/').Length).TrimStart('\','/')
        if ($Relative -match '(^|[\\/])(node_modules|\.git|dist|build|coverage)([\\/]|$)') { continue }
        if ($Extensions -notcontains $File.Extension.ToLowerInvariant() -and -not $File.Name.StartsWith('.env')) { continue }
        $Raw = Get-Content -LiteralPath $File.FullName -Raw -ErrorAction SilentlyContinue
        if ($null -eq $Raw) { continue }
        foreach ($Pattern in $Patterns) {
            if ($Raw -match $Pattern) {
                $Findings.Add($Relative.Replace('\','/'))
                break
            }
        }
    }

    if ($Findings.Count -gt 0) {
        return [ordered]@{ status = 'FAIL'; exit_code = 1; evidence = "Secret-like material found in: $($Findings -join ', ')" }
    }
    return [ordered]@{ status = 'PASS'; exit_code = 0; evidence = 'No secret-like patterns found by the built-in scan.' }
}

$ProjectPath = [System.IO.Path]::GetFullPath($ProjectPath)
if (-not (Test-Path -LiteralPath $ProjectPath -PathType Container)) {
    throw "Project path not found: $ProjectPath"
}

$Commands = [System.Collections.Generic.List[object]]::new()
$Build = New-SkippedGate 'No build command discovered.'
$Typecheck = New-SkippedGate 'No typecheck command discovered.'
$Lint = New-SkippedGate 'No lint command discovered.'
$Tests = New-SkippedGate 'No test command discovered.'

$PackageJsonPath = Join-Path $ProjectPath 'package.json'
if (Test-Path -LiteralPath $PackageJsonPath -PathType Leaf) {
    $Package = Get-Content -LiteralPath $PackageJsonPath -Raw | ConvertFrom-Json
    $PackageManager = Get-PackageManager $ProjectPath
    $AvailableScripts = @()
    if ($null -ne $Package.scripts) { $AvailableScripts = @($Package.scripts.PSObject.Properties.Name) }

    $ScriptMap = [ordered]@{
        build = @('build')
        typecheck = @('typecheck', 'type-check', 'check-types')
        lint = @('lint')
        tests = @('test', 'tests')
    }

    foreach ($GateName in $ScriptMap.Keys) {
        $Selected = $ScriptMap[$GateName] | Where-Object { $AvailableScripts -contains $_ } | Select-Object -First 1
        if (-not $Selected) { continue }
        $Gate = Invoke-PackageScript -PackageManager $PackageManager -ScriptName $Selected -WorkingDirectory $ProjectPath
        $Commands.Add([ordered]@{ command = $Gate.command; exit_code = $Gate.exit_code; gate = $GateName })
        switch ($GateName) {
            'build' { $Build = $Gate }
            'typecheck' { $Typecheck = $Gate }
            'lint' { $Lint = $Gate }
            'tests' { $Tests = $Gate }
        }
    }
}

$Security = Test-SecretPatterns $ProjectPath
$Diff = New-SkippedGate 'Project is not a Git work tree.'
$GitProbe = & git -C $ProjectPath rev-parse --is-inside-work-tree 2>$null
$GitProbeExit = $LASTEXITCODE
if ($GitProbeExit -eq 0 -and ($GitProbe | Out-String).Trim() -eq 'true') {
    $DiffOutput = & git -C $ProjectPath diff --check 2>&1
    $DiffExit = $LASTEXITCODE
    $DiffEvidence = (($DiffOutput | Select-Object -Last 20) -join [Environment]::NewLine).Trim()
    if (-not $DiffEvidence) { $DiffEvidence = 'git diff --check found no whitespace errors.' }
    $Diff = [ordered]@{ status = if ($DiffExit -eq 0) { 'PASS' } else { 'FAIL' }; exit_code = $DiffExit; evidence = $DiffEvidence }
}

$RequiredGates = @($Build, $Typecheck, $Lint, $Tests) | Where-Object { $_.status -ne 'SKIPPED' }
$HasFailure = (@($RequiredGates | Where-Object { $_.status -eq 'FAIL' }).Count -gt 0) -or $Security.status -eq 'FAIL' -or $Diff.status -eq 'FAIL'
$Readiness = if ($HasFailure) { 'NOT_READY' } else { 'READY' }

$Result = [ordered]@{
    project_path = $ProjectPath
    commands = $Commands
    build = $Build
    typecheck = $Typecheck
    lint = $Lint
    tests = $Tests
    security = $Security
    diff = $Diff
    readiness = $Readiness
}

if ($Json) {
    $JsonOutput = $Result | ConvertTo-Json -Depth 7
    $global:LASTEXITCODE = 0
    Write-Output $JsonOutput
    return
}

Write-Host "Verification: $ProjectPath"
foreach ($Name in @('build','typecheck','lint','tests','security','diff')) {
    $Gate = $Result[$Name]
    Write-Host ("{0,-10} {1}" -f $Name.ToUpperInvariant(), $Gate.status)
}
Write-Host "READINESS  $Readiness"
$global:LASTEXITCODE = 0
