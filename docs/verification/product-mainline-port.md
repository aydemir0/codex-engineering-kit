# Product-only mainline port

Base: `7b257e580c9636932e998aa4467a008fd1118ca0`.
Product source: `87046c177e13ed8ba368211f732682234fbf9758` and
`931182ce06aff135a8a9dc3fc7d2305950be104f`.
This is a file-level port, not a merge of the development branch or its ancestry.

## Dependency audit

The three workflow modules modified by the product implementation but absent
from main were `runtime/workflow/command.py`, `coordinator.py`, and `native.py`.
Their necessary transitive dependencies are:

```text
workflow.command -> coordinator, ledger, model, native, profile
coordinator      -> assurance.model.Permission, ledger, model
ledger, profile  -> runtime.state (already on main)
native          -> model, assurance.native_host, diagnostics.native_failure
native_host     -> diagnostics.native_failure
workflow.lifecycle -> runtime.state
workflow.candidate -> model, Git, Python standard library
verification.runner -> verification.candidate, existing verification modules
```

All other Python imports in these modules are standard-library imports. There
are no new package dependencies. Git remains an external prerequisite for Git
candidate snapshots. The optional live host probe additionally requires the
explicitly pinned official runtime; the standalone demo does not.

| Classification | Included scope |
| --- | --- |
| Necessary production foundation | Workflow model, coordinator, command, ledger, profile, native, candidate, lifecycle; existing state module reused unchanged; capability-name enum only |
| Product feature | Candidate-bound verification, native host probe, structured native failure diagnostics, recovery corrections |
| Necessary regressions | Candidate, recovery, diagnostics, workflow orchestration/CLI/reviewer lifecycle, and mainline boundary tests |
| Optional documentation/demo | Standalone integrity demo, its tests, these two documentation pages and README link |
| Experimental benchmark/authority code | None; no M4, production grants, completion receipts, frozen policy engine or release-contract changes |

The broad source `runtime.assurance` initializer is deliberately not ported:
it imported the M2A decision/policy/authority implementation. The mainline
initializer has no side effects; `assurance.model` retains only the original
`Permission` enum. No automatic authority provider is supplied. Both
orchestration and managed-worktree capabilities still require explicit Boolean
approval before native execution. Invalid/missing providers fail closed.

The existing install/uninstall CLI stays unchanged. A small
`scripts.cek_workflow` entry point provides only status, explain, resume, stage,
parent and lifecycle evidence commands. Its parser cannot start a native run.
Reviewer prompts refer to this entry point rather than the experimental source
lifecycle CLI. Native execution remains an explicitly authorized Python API.

During port validation, focused RED regressions exposed acceptance of `.`/`..`
workflow identifiers and an owned profile reopened through a junction after
path resolution. The port rejects these identifiers and inspects original path
components before resolving them. Static indirection is rejected; this is not
an atomic filesystem lock or certification of hostile concurrent writers.

## Reproduce focused validation

Run from a clean checkout using Python 3.11+ and Git (PowerShell 5.1 or 7):

```powershell
python -B -m unittest tests.test_product_integrity_demo tests.test_candidate_integrity tests.test_workflow_recovery_integrity tests.test_native_failure_diagnostics tests.test_verification_engine tests.test_m2b_orchestration tests.test_m2b_workflow_cli tests.test_m2b_native_lifecycle tests.test_state_contract tests.test_clean_install_lifecycle tests.test_product_port_boundaries -q
if ($LASTEXITCODE -ne 0) { throw 'Product regressions failed' }
python -B -m scripts.demo_product_integrity --output product-demo-new.json
if ($LASTEXITCODE -ne 0) { throw 'Product demo failed' }
```

The `m2b` test names refer to product workflow foundations, not an M4 counted
campaign. Filesystem tests create temporary local hardlinks and junctions; do
not weaken policy when a host prohibits them. The CLI-rejection tests emit
expected argparse errors while asserting failure-closed behavior.

See [product-integrity.md](product-integrity.md) for precise integrity scope,
expected demo output and clean-checkout commands. Results establish local
engineering controls, not real model task quality or superiority over ECC.
