"""Content identity of verification inputs; never stages files; rejects known credential paths."""
from __future__ import annotations
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .model import VerificationReport

class CandidateIntegrityError(ValueError):
    pass
# Input scope: tracked files plus nonignored untracked inputs; generated report
# output is excluded to avoid self-reference. No-Git projects use this explicit
# generated-directory exclusion set. Ignored build outputs are not attested.
GENERATED = {'.git', '__pycache__', '.pytest_cache', 'node_modules', 'dist', 'build', 'coverage'}

def _report_path(parts: tuple[str, ...]) -> bool:
    return parts[:2] == ('.codex-kit', 'verification')

def manifest_digest(manifest: tuple[tuple[str, int, str, int], ...]) -> str:
    return hashlib.sha256(json.dumps(manifest, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()

def capture_manifest(project: Path) -> tuple[tuple[str, int, str, int], ...]:
    project = project.absolute()

    def safe(path: Path) -> None:
        for item in (*reversed(path.parents), path):
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                raise CandidateIntegrityError('CANDIDATE_UNSAFE_PATH')
    safe(project)
    env = dict(os.environ)
    env['GIT_OPTIONAL_LOCKS'] = '0'
    try:
        probe = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], cwd=project, env=env, capture_output=True)
    except FileNotFoundError:
        probe = None
    ignored = None
    if probe is not None and probe.returncode == 0:
        ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--no-index', '--', '.'], cwd=project, env=env, capture_output=True)
        if ignored.returncode not in {0, 1}:
            raise CandidateIntegrityError('CANDIDATE_SCOPE_UNAVAILABLE')
    if probe is not None and probe.returncode == 0 and ignored is not None and ignored.returncode == 1:
        listing = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=project, env=env, capture_output=True)
        if listing.returncode:
            raise CandidateIntegrityError('CANDIDATE_LIST_FAILED')
        tracked = subprocess.run(['git', 'ls-files', '-z', '--cached'], cwd=project, env=env, capture_output=True, check=True)
        tracked_names = set((os.fsdecode(x) for x in tracked.stdout.split(b'\x00') if x))
        names = set((os.fsdecode(x) for x in listing.stdout.split(b'\x00') if x))
    else:
        names = set()
        tracked_names = set()
        for folder, dirs, files in os.walk(project, followlinks=False):
            dirs[:] = [d for d in dirs if d not in GENERATED and (not _report_path((Path(folder) / d).relative_to(project).parts))]
            for d in dirs:
                safe(Path(folder) / d)
            names.update(((Path(folder) / f).relative_to(project).as_posix() for f in files))
    rows = []
    for name in sorted(names):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise CandidateIntegrityError('CANDIDATE_OUTSIDE_ROOT')
        if _report_path(relative.parts) or '.git' in relative.parts:
            continue
        if name not in tracked_names and any((p in GENERATED for p in relative.parts)):
            continue
        if relative.name.casefold() in {'auth.json', 'credentials', 'credentials.json'}:
            raise CandidateIntegrityError('CANDIDATE_CREDENTIAL_PATH')
        path = project / relative
        try:
            safe(path)
        except FileNotFoundError:
            continue
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise CandidateIntegrityError('CANDIDATE_UNSAFE_FILE')
        with path.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            after = os.fstat(stream.fileno())
        current = path.stat()
        identity = lambda m: (m.st_dev, m.st_ino, m.st_size, m.st_mode, m.st_nlink)
        safe(path)
        if not identity(before) == identity(opened) == identity(after) == identity(current) or (opened.st_mtime_ns, opened.st_ctime_ns) != (after.st_mtime_ns, after.st_ctime_ns):
            raise CandidateIntegrityError('CANDIDATE_CHANGED_DURING_READ')
        rows.append((relative.as_posix(), after.st_size, digest, stat.S_IMODE(after.st_mode)))
    return tuple(rows)

def assert_report_current(project: Path, report: VerificationReport) -> None:
    if not report.candidate_digest or manifest_digest(report.candidate_manifest) != report.candidate_digest:
        raise CandidateIntegrityError('CANDIDATE_IDENTITY_INVALID')
    if capture_manifest(project) != report.candidate_manifest:
        raise CandidateIntegrityError('VERIFICATION_STALE_OR_ARTIFACT_MISSING')
    if any((s.name == 'candidate-integrity' and s.status != 'passed' for s in report.steps)):
        raise CandidateIntegrityError('CANDIDATE_CHANGED_DURING_VERIFICATION')
