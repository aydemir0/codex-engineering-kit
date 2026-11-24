# Verify a TypeScript client and Python service

This example uses Node 24, npm, and Python 3.11 or newer on the command path.
The client calls the Python service over standard input and output. No server,
package installation, or credentials are required.

From the CEK checkout root, copy the example to a disposable directory.
Both CEK and the client use the `python` command on the command path.

```powershell
$demo = Join-Path ([System.IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
Copy-Item -LiteralPath ./examples/typescript-python-contract -Destination $demo -Recurse
python -B -m verification.cli --project $demo --include-project client --include-project service --require-complete --json
```

Both project families should pass. The root report lists `client` and
`service` under `projectRoots` and identifies the candidate across both.

For a RED-to-GREEN exercise, change the discount threshold in the copy's
`service/quote.py` from `>= 3` to `>= 4`. Run verification again and expect
exit code `1` with both project families failed. Restore `>= 3` and rerun
for GREEN. To see a one-sided failure, instead change one Python test's
expected total without changing the service. The client passes and the
aggregate result fails.

A subsequent edit invalidates the old candidate report. Reverify the edited
copy before relying on a GREEN result.
