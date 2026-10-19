"""Synchronize before importing generation code; never update a running generator."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True, encoding="utf-8", timeout=120).stdout.strip()


def fingerprint(root):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / "scripts").glob("*.py"))}


def synchronize(root):
    if git(root, "status", "--porcelain"):
        raise RuntimeError("Working tree is not clean; preserve changes and stop")
    remote = git(root, "ls-remote", "--symref", "origin", "HEAD")
    ref = next((line.split()[1] for line in remote.splitlines()
                if line.startswith("ref: refs/heads/") and line.endswith("\tHEAD")), None)
    if not ref:
        raise RuntimeError("Cannot resolve origin default branch")
    branch = ref.removeprefix("refs/heads/")
    if git(root, "branch", "--show-current") != branch:
        raise RuntimeError("Publisher must run on origin default branch")
    git(root, "fetch", "origin", ref)
    target = git(root, "rev-parse", "FETCH_HEAD")
    git(root, "merge", "--ff-only", target)
    if git(root, "rev-parse", "HEAD") != target:
        raise RuntimeError("Local branch is ahead of remote; refusing unpublished code")
    return {"sha": target, "branch": branch, "files": fingerprint(root)}


def verify(root, manifest):
    if git(root, "rev-parse", "HEAD") != manifest["sha"] or fingerprint(root) != manifest["files"]:
        raise RuntimeError("Generator changed during execution; refuse publication")


def child_stdio():
    # pythonw has no console: a child started without explicit handles gets sys.stderr=None,
    # so unittest crashes on its first write and exits 1 with no message (2026-10-20).
    sys.stdout and sys.stdout.flush()
    sys.stderr and sys.stderr.flush()
    return {"stdout": sys.stdout or subprocess.DEVNULL, "stderr": sys.stderr or subprocess.DEVNULL}


def launch(root, check_only=False):
    lock = Path(git(root, "rev-parse", "--absolute-git-dir")) / "daily-runtime.lock"
    # Exclusive creation covers sync, tests and the entire child lifetime. Never steal a lock.
    with lock.open("x", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    try:
        manifest = synchronize(root)
        print("[DAILY_POST] runtime=" + json.dumps(manifest), flush=True)
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "scripts",
                        "-p", "test_*.py"], cwd=root, check=True, **child_stdio())
        verify(root, manifest)
        if check_only:
            return 0
        env = dict(os.environ, TECHBLOG_RUNTIME=json.dumps(manifest))
        return subprocess.run([sys.executable, str(root / "scripts/generate_daily_post.py")],
                              cwd=root, env=env, **child_stdio()).returncode
    finally:
        lock.unlink(missing_ok=True)
