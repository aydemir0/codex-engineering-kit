[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputPath,
    [Parameter(Mandatory)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$AllowedCategories = @(
    'error_resolution',
    'user_correction',
    'workaround',
    'debugging_technique',
    'project_specific'
)
$SecretPatterns = @(
    'ghp_[A-Za-z0-9]{16,}',
    'sk-[A-Za-z0-9]{16,}',
    'BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY'
)

if (-not (Test-Path -LiteralPath $InputPath -PathType Leaf)) {
    throw "Learning input not found: $InputPath"
}

$Observations = @(Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json)
$Candidates = [System.Collections.Generic.List[object]]::new()
$Rejected = [System.Collections.Generic.List[object]]::new()
$SeenTitles = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$Redactions = 0

foreach ($Observation in $Observations) {
    $Title = [string]$Observation.title
    $Category = [string]$Observation.category
    $Evidence = @($Observation.evidence | ForEach-Object { [string]$_ })
    $Scope = if ([string]$Observation.scope -eq 'general') { 'general' } else { 'project' }

    if ($AllowedCategories -notcontains $Category) {
        $Rejected.Add([ordered]@{ title = $Title; reason = "unsupported category: $Category" })
        continue
    }

    if ([string]::IsNullOrWhiteSpace($Title) -or $Evidence.Count -eq 0) {
        $Rejected.Add([ordered]@{ title = $Title; reason = 'insufficient evidence' })
        continue
    }

    $Combined = "$Title`n$($Evidence -join "`n")"
    $ContainsSensitive = $false
    foreach ($Pattern in $SecretPatterns) {
        if ($Combined -match $Pattern) {
            $ContainsSensitive = $true
            break
        }
    }
    if ($ContainsSensitive) {
        $Rejected.Add([ordered]@{ title = $Title; reason = 'sensitive data detected; candidate rejected' })
        $Redactions += 1
        continue
    }

    $NormalizedTitle = ($Title -replace '\s+', ' ').Trim()
    if (-not $SeenTitles.Add($NormalizedTitle)) {
        $Rejected.Add([ordered]@{ title = $Title; reason = 'duplicate candidate' })
        continue
    }

    $Confidence = if ($Evidence.Count -ge 3) { 'high' } elseif ($Evidence.Count -ge 2) { 'medium' } else { 'low' }
    $Candidates.Add([ordered]@{
        title = $NormalizedTitle
        category = $Category
        evidence = $Evidence
        confidence = $Confidence
        scope = $Scope
        contains_sensitive_data = $false
        promotion_status = 'pending_review'
    })
}

$Result = [ordered]@{
    candidates = $Candidates
    rejected = $Rejected
    redactions = $Redactions
}

$Parent = Split-Path -Parent ([System.IO.Path]::GetFullPath($OutputPath))
if ($Parent -and -not (Test-Path -LiteralPath $Parent)) {
    New-Item -ItemType Directory -Path $Parent -Force | Out-Null
}
$Result | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $OutputPath -NoNewline -Encoding utf8

Write-Host "Learning candidates: $($Candidates.Count); rejected: $($Rejected.Count); awaiting human review."
