$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Templates = Join-Path $RepoRoot 'mcp/templates'
$Configure = Join-Path $RepoRoot 'mcp/configure.ps1'
Assert-True (Test-Path -LiteralPath $Configure) 'mcp/configure.ps1 must exist'

$Providers = @('github', 'supabase', 'vercel', 'railway', 'cloudflare')
foreach ($Provider in $Providers) {
    $Path = Join-Path $Templates "$Provider.json"
    Assert-True (Test-Path -LiteralPath $Path) "missing MCP template: $Provider"
    $Raw = Get-Content -LiteralPath $Path -Raw
    Assert-True ($Raw -notmatch 'ghp_[A-Za-z0-9]{16,}') "$Provider template contains token-like value"
    Assert-True ($Raw -notmatch 'sk-[A-Za-z0-9]{16,}') "$Provider template contains secret-like value"
    $Template = $Raw | ConvertFrom-Json
    Assert-True ($Template.provider -eq $Provider) "$Provider template provider mismatch"
    $HasEnv = $null -ne $Template.required_environment -and $Template.required_environment.Count -gt 0
    $HasLogin = $Template.login_required -eq $true
    Assert-True ($HasEnv -or $HasLogin) "$Provider template must declare environment requirements or login flow"
}

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-kit-mcp-test-" + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null
    $Output = Join-Path $TempRoot 'github.local.json'
    & $Configure -Provider github -OutputPath $Output -DryRun | Out-Null
    Assert-True (-not (Test-Path -LiteralPath $Output)) 'MCP dry-run must not write local config'

    & $Configure -Provider github -OutputPath $Output | Out-Null
    Assert-True (Test-Path -LiteralPath $Output) 'MCP configurator must write selected local config'
    $Generated = Get-Content -LiteralPath $Output -Raw | ConvertFrom-Json
    Assert-True ($Generated.provider -eq 'github') 'generated provider must match selection'

    Write-Host 'PASS: MCP configuration contracts satisfied'
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
