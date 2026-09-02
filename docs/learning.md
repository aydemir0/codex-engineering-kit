# Continuous Learning Model

Codex Engineering Kit treats learned behavior as **untrusted candidates**, not automatic policy.

## Pipeline

```text
completed work
  -> evidence extraction
  -> candidate normalization
  -> sensitive-data rejection
  -> deduplication
  -> confidence + scope
  -> pending_review
  -> human approval
  -> trusted project rule or skill
```

The public toolkit never needs raw private transcripts. `scripts/learn-session.ps1` accepts a small observation JSON file containing only the evidence the user chooses to provide.

## Candidate schema

```json
{
  "title": "Node-only imports must stay behind the server runtime boundary",
  "category": "error_resolution",
  "evidence": [
    "server module evaluation failed on a browser-only global",
    "moving the import behind the runtime boundary fixed the build"
  ],
  "confidence": "medium",
  "scope": "general",
  "contains_sensitive_data": false,
  "promotion_status": "pending_review"
}
```

## Safety properties

- unsupported/noisy categories are rejected;
- secret-like material is rejected before candidate creation;
- candidates never execute shell content;
- candidates are not installed into the Codex skill directory;
- project-specific observations remain project-scoped unless explicitly generalized;
- confidence reflects evidence count, not model certainty.

## Manual extraction

```powershell
pwsh -File scripts/learn-session.ps1 `
  -InputPath .codex-kit/local/observations.json `
  -OutputPath .codex-kit/candidates/session.json
```

Both `.codex-kit/local/` and `.codex-kit/candidates/` are ignored by the repository template so private working state stays local.
