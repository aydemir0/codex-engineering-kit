# Product verification, recovery and native failures

These changes are local product engineering controls, not a CEK-vs-ECC model
benchmark and not historical M4 campaign recovery. No production receipt or
historical result is issued or amended by these APIs.

## Candidate-bound verification

`verification.runner.verify_project` captures a deterministic SHA-256 manifest
before test discovery/execution and compares it after verification. Each entry
binds its relative path, exact bytes, size and filesystem permission mode.
Tracked, staged, unstaged and relevant nonignored untracked working files are
measured without staging files or modifying the Git index. Git-ignored nested
standalone projects fall back to filesystem enumeration rather than an empty
Git listing. HEAD is not the candidate identity.

Use `verification.candidate.assert_report_current(project, report)` before
reusing a report. Publishing a passed report with `report_record` or
`write_report` also checks the live candidate. Missing, changed or added inputs,
a wrong digest and a candidate mutated during verification are rejected.
Legacy unbound PASS reports cannot be published as verified.

Input scope excludes `.git` and `.codex-kit/verification` report output. For Git
projects, ignored untracked files are not inputs; generated untracked cache,
dependency and build directories are also excluded. Without Git, the explicit
exclusions are `.git`, `__pycache__`, `.pytest_cache`, `node_modules`, `dist`,
`build`, and `coverage`. Ignored/build outputs are not attested artifacts.
Symlink/reparse inputs, hardlinked files and known credential paths fail closed.
No file content is exported in the manifest.

A digest is content-integrity evidence, not a signature or authorization grant.
The manifest is a checked snapshot, not an OS filesystem lock; files can change
after any check. Recheck before consuming evidence. This does not certify an
adversarial concurrently writable filesystem or atomic test isolation.

## Recovery boundaries

`WorkflowCoordinator.load` retains direct FAIL/BLOCKED terminal events instead
of resurrecting the previous accepted checkpoint. `resume` validates candidate
and worktree identity and does not replay stage side effects. Duplicate attempt
identifiers are rejected, including rework. Verified/closed execution cannot be
resumed or retried; cleanup transitions remain separate. Explicit retry of a
failed attempt requires a new attempt identity and preserves original evidence.
Atomic ledger replacement preserves the old checkpoint if publication fails;
truncated JSON and altered hash-chain evidence are rejected.

These controls do not promise transactional exactly-once execution of arbitrary
external services or multiple unsynchronized writers. This mainline port includes no M4 benchmark or production authority code.

## Native failures

`runtime.diagnostics.native_failure` supplies stable error classes and bounded
operator guidance for discovery, host availability, tool failures, permissions,
PowerShell CLM, protocol responses, timeouts and artifact verification.
`NativeHostError` and `NativeWorkflowError` expose `diagnostic.to_dict()`;
raw failure text is not exported by this representation.

The native workflow rejects terminal error events, malformed/incomplete JSONL
and missing turn completion, even with process exit zero. An intermediate failed
command followed by completed recovery is not itself a terminal failure; this
preserves legitimate RED-to-GREEN testing. Final workflow verification still
requires the existing ledger gates, not merely a completed CLI turn.

The diagnostics do not disable CLM. Operator guidance uses permitted cmdlets instead of static
System.IO calls and never recommends automatic permission escalation. Text-based
failure classification is diagnostic categorization, not independent proof of a
root cause. Unknown failures remain blocked.

The optional `scripts.acceptance.native_host_probe` command uses a pinned host, real JavaScript and a bounded
local delegate/artifact. It performs no authentication or model call and does
not establish product task performance. Focused tests also use controlled local
Python subprocesses and synthetic authority fixtures.

## Reproduce the local demo (PowerShell 5.1 or 7)

Requires Python 3.11+ and Git. No Codex installation, model access, login,
subscription, signing key, third-party Python package or network service is
required for the demo itself. Run these commands from a candidate checkout that
contains `scripts/demo_product_integrity.py`:

```powershell
$Candidate = git rev-parse HEAD
$Source = (Get-Location).Path
$Clean = Join-Path $env:TEMP 'cek-product-demo-clean'
if (Test-Path -LiteralPath $Clean) { throw 'Choose a new empty checkout path; preserve existing files.' }
git clone --no-local --no-checkout -- $Source $Clean
if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
git -C $Clean checkout --detach $Candidate
if ($LASTEXITCODE -ne 0) { throw 'Checkout failed' }
Push-Location $Clean
try {
    py -3 -B -m scripts.demo_product_integrity --output product-demo-new.json
    if ($LASTEXITCODE -ne 0) { throw 'Demo failed' }
    Get-Content -LiteralPath product-demo-new.json
} finally {
    Pop-Location
}
```

Use `python` instead of `py -3` if the Windows Python launcher is unavailable.
The output path must not already exist; the command never overwrites it. Fixtures
are created in a fresh temporary directory and cleaned up by the demo. The clean
checkout and JSON output are retained for inspection. No reset or deletion of
an existing checkout is required.

Expected output (other fields include explanations and corrective actions):

```json
{
  "status": "PASS",
  "verification": {"initialTests": "PASS", "staleGreen": "REJECTED", "foreignSentinel": "PRESERVED"},
  "recovery": {"scope": "SYNTHETIC_LOCAL_WORKFLOW", "checkpoint": "GREEN_CONFIRMED", "sideEffects": 1, "duplicateLedgerWrites": 0, "terminalState": "FAILED", "terminalResume": "WORKFLOW_EXECUTION_TERMINAL"},
  "nativeFailure": {"scope": "CONTROLLED_LOCAL_PROCESS_NOT_CODEX", "code": "PERMISSION_DENIED", "status": "BLOCKED"},
  "modelCalls": 0,
  "authentications": 0,
  "countedAttempts": 0
}
```

`PASS` means all expected positive and negative demo checks succeeded. The
recovery checkpoint is synthetic local state, not a recovered production session.
The failure is emitted by a controlled local Python subprocess and interpreted
by the production native-result validator, not by a real Codex/model process.
The demonstrated no-replay property covers coordinator resume; it is not a claim
of transactional exactly-once behavior for arbitrary external services.

Focused reproduction tests:

```powershell
py -3 -B -m unittest tests.test_product_integrity_demo tests.test_candidate_integrity tests.test_workflow_recovery_integrity tests.test_native_failure_diagnostics -q
```

Some filesystem regressions require Windows permission to create temporary
hardlinks. If policy denies those operations, report that limitation; do not
bypass managed policy or label an unexecuted test as passed.

## Mainline scope

The workflow state/model/ledger/profile and reviewer-lifecycle helpers are product
runtime foundations. Only the existing capability-name enum is retained from the
runtime-assurance model; no M2A probe/policy engine or production grant authority
is installed. `run_workflow` remains a Python API requiring an explicit caller-
supplied authorization provider for both orchestration and managed worktrees.
Missing, malformed or denied authorization fails before profile creation or
native execution. This port does not provide an automatic authorization provider
or a CLI command for starting live native workflows.

Local status, evidence and reviewer correlation are available through
`python -B -m scripts.cek_workflow workflow status --workflow-root <owned-root> --workflow-id <id>`.
The existing plugin install/uninstall CLI is unchanged. Neither this command nor
the credentials-free demo authenticates profiles or launches a benchmark.
