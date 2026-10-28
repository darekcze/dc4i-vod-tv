#!/usr/bin/env python3
"""Run the pinned 56-test VOD TV offline suite without touching a real TV or key.

Requires a fixture created by the existing committed-tree offline builder.
Never packages, installs, publishes, contacts providers or changes source files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
APP_ID = "com.dc4i.vodtv.offlinefixture"
KNOWN_QA_ONLY_FILES = {
    "scripts/run_fullstack_offline_qa.py",
    "scripts/test_fullstack_offline_qa.py",
    "docs/releases/2026-10-28-offline-qa.md",
    "docs/pl/releases/2026-10-28-offline-qa.md",
}
NODE_TESTS = """
test_archive_capabilities
test_archive_integration
test_backup_recovery_ui
test_backup_transaction
test_backup_ui
test_chart_integration
test_chart_links
test_chart_ui
test_dvr_integration
test_dvr_scheduler
test_epg_fixture
test_epg_identity
test_epg_integration
test_epg_metadata
test_epg_metadata_ui
test_epg_provider_fallback
test_epg_timeline
test_guide_bridge
test_guide_epg
test_guide_model
test_guide_runtime
test_guide_ui
test_handoff
test_hardening_integration
test_hardening_limits
test_home_integration
test_home_rails
test_home_ui
test_import_privacy_integration
test_metadata_backup
test_navigation_xtream
test_offline_guard
test_personalization_integration
test_personalization_ui_runtime
test_playback_integration
test_playback_learning
test_playback_ui
test_player_handoff
test_quick_panel
test_recommender
test_reminder_integration
test_reminder_ui
test_reminders
test_rich_epg
test_search_views
test_source_index
test_title_mapping
test_unified_provider_search
test_version_check
test_xtream_details
""".strip().splitlines()


class QAError(RuntimeError):
    """Fail closed without making changes to the release workspace."""


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise QAError("Required Git provenance check failed")
    return result.stdout.strip()


def verify_fixture(fixture: Path) -> tuple[str, str]:
    fixture = fixture.resolve(strict=True)
    marker = fixture / "OFFLINE_FIXTURE_ONLY.txt"
    meta_file = fixture / "fixture-provenance.json"
    app = fixture / "build" / "dc4i-vodtv"
    if not marker.is_file() or not meta_file.is_file():
        raise QAError("Missing explicitly marked offline QA fixture")
    private = fixture / "private"
    if (fixture / ".git").exists() or private.is_symlink() or (
        private.exists() and (not private.is_dir() or any(private.iterdir()))
    ):
        raise QAError("Fixture cannot contain private credentials or a repository")
    try:
        metadata = json.loads(meta_file.read_text(encoding="utf-8"))
        appinfo = json.loads((app / "appinfo.json").read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise QAError("Invalid offline fixture metadata") from exc
    if appinfo.get("id") != APP_ID:
        raise QAError("Refusing production application identity in offline QA")
    source_sha = metadata.get("projectCommit")
    if not isinstance(source_sha, str) or not re.fullmatch(r"[a-f0-9]{40}", source_sha):
        raise QAError("Offline fixture lacks a pinned Git source SHA")
    if metadata.get("workingTreeDirty") is not False:
        raise QAError("Offline fixture was not built from a clean committed tree")
    if metadata.get("inputPolicy") != "committed-tree-only":
        raise QAError("Offline fixture source policy is not reproducible")
    candidate_sha = git("rev-parse", "HEAD")
    # The fixture may predate this QA-only runner, but not any application changes.
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_sha, candidate_sha],
        cwd=ROOT, capture_output=True, check=False
    )
    if ancestor.returncode:
        raise QAError("Fixture revision is not an ancestor of candidate HEAD")
    changed = git("diff", "--name-only", source_sha, candidate_sha).splitlines()
    if any(path not in KNOWN_QA_ONLY_FILES for path in changed):
        raise QAError("Application changed after offline fixture creation; rebuild fixture")
    dirty = (
        git("diff", "--name-only").splitlines()
        + git("diff", "--cached", "--name-only").splitlines()
        + git("ls-files", "--others", "--exclude-standard").splitlines()
    )
    if any(path not in KNOWN_QA_ONLY_FILES for path in dirty):
        raise QAError("Uncommitted application changes; rebuild fixture from reviewed source")
    for tracked in git("ls-files").splitlines():
        if (ROOT / tracked).is_symlink():
            raise QAError("Tracked source symlinks need independent review")
    # Never follow an attacker-controlled fixture symlink into a private tree.
    if any(p.is_symlink() for p in (fixture / "build").rglob("*")):
        raise QAError("Offline fixture includes unsupported symlinks")
    required = ("app.js", "index.html", "vod-xtream.js", "config.js")
    if not all((app / name).is_file() for name in required):
        raise QAError("Fixture is missing required compiled application files")
    return source_sha, candidate_sha


def test_cases(fixture: Path) -> list[tuple[list[str], dict[str, str]]]:
    node = [["node", f"scripts/{name}.mjs"] for name in NODE_TESTS]
    python = [
        [sys.executable, "scripts/test_xmltv_metadata.py"],
        [sys.executable, "scripts/test_offline_provenance.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "integrations/kodi/service.dc4i.handoff/tests"],
        [sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_release_tooling.py"],
        [sys.executable, "scripts/test_offline_build.py", str(fixture)],
    ]
    return [(cmd, {}) for cmd in node + python] + [
        (["node", "scripts/test_reminders.mjs"], {"TZ": "Europe/Warsaw"})
    ]


def ignore_private(_dir: str, names: list[str]) -> set[str]:
    private = {".git", "build", "private", "dist", "node_modules", "__pycache__", ".venv", "tools"}
    return {name for name in names if name in private or name == "keys.js" or name.startswith(".env") or name in {".npmrc", ".pypirc"} or name.endswith((".ipk", ".pem", ".key", ".p12", ".pfx"))}


def run(fixture: Path, scratch: Path, receipt: Path, timeout: float) -> int:
    if len(NODE_TESTS) != 50 or len(set(NODE_TESTS)) != 50:
        raise QAError("Expected 50 pinned Node suites")
    fixture = fixture.resolve(strict=True)
    scratch = scratch.resolve(strict=True)
    receipt = receipt.absolute()
    if not scratch.is_dir() or not receipt.parent.is_dir():
        raise QAError("Scratch and receipt parent directories must exist")
    if receipt.exists():
        raise QAError("Receipt exists; refusing to overwrite prior evidence")
    source_sha, candidate_sha = verify_fixture(fixture)
    cases = test_cases(fixture)
    if len(cases) != 56:
        raise QAError("Expected exactly 56 offline checks")
    environment = {k: v for k, v in os.environ.items()
                   if k in {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT", "WINDIR"}}
    environment.update({
        "CI": "1", "DC4I_OFFLINE_QA": "1",
        "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
        "NO_PROXY": "", "no_proxy": ""
    })
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="dc4i-vodtv-offline-qa-", dir=scratch) as temp:
        workspace = Path(temp) / "source"
        shutil.copytree(ROOT, workspace, ignore=ignore_private, symlinks=False)
        shutil.copytree(fixture / "build", workspace / "build", symlinks=False)
        for index, (argv, overrides) in enumerate(cases, 1):
            if not (workspace / argv[1]).exists() and not (
                argv[1] == "-m" or argv[1] == "scripts/test_offline_build.py"
            ):
                raise QAError("Pinned test entrypoint missing from prepared checkout")
            env = {**environment, **overrides, "TMPDIR": str(Path(temp))}
            started = time.monotonic()
            try:
                proc = subprocess.run(
                    argv, cwd=workspace, env=env, text=True,
                    capture_output=True, timeout=timeout, check=False
                )
                code = proc.returncode
                combined = (proc.stdout + "\n" + proc.stderr).encode("utf-8", errors="replace")
                digest = hashlib.sha256(combined).hexdigest()
                state = "PASS" if code == 0 else "FAIL"
            except subprocess.TimeoutExpired:
                code, digest, state = None, None, "TIMEOUT"
            rows.append({
                "number": index, "command": argv, "environment": overrides,
                "status": state, "exit_code": code,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "output_sha256": digest,
            })
            if state != "PASS":
                print(f"{index}/56 {state}: {' '.join(argv)}", flush=True)
    result = {
        "schema": "dc4i.vodtv.offline-qa.v1",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_sha": source_sha, "candidate_sha": candidate_sha,
        "fixture_id": APP_ID, "offline_only": True,
        "tv_contacted": False, "production_package_created": False,
        "passed": sum(r["status"] == "PASS" for r in rows),
        "failed": sum(r["status"] != "PASS" for r in rows),
        "checks": rows,
    }
    descriptor = os.open(receipt, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(f"OFFLINE_QA {result['passed']}/56 PASS, {result['failed']} FAIL; receipt={receipt}")
    return 0 if result["failed"] == 0 else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture", type=Path, required=True, help="marked offline fixture directory")
    p.add_argument("--scratch-root", type=Path, required=True, help="preexisting AI-Hot scratch directory")
    p.add_argument("--receipt", type=Path, required=True, help="new machine-readable JSON evidence path")
    p.add_argument("--timeout", type=float, default=45)
    p.add_argument("--preflight-only", action="store_true")
    args = p.parse_args()
    try:
        if not 1 <= args.timeout <= 120:
            raise QAError("Per-test timeout must be between 1 and 120 seconds")
        if args.preflight_only:
            source, candidate = verify_fixture(args.fixture)
            print(f"QA_PREFLIGHT_OK source={source[:12]} candidate={candidate[:12]}")
            return 0
        return run(args.fixture, args.scratch_root, args.receipt, args.timeout)
    except (QAError, OSError) as exc:
        print(f"OFFLINE_QA_BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
