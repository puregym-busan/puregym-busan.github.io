#!/usr/bin/env python3
"""Validate the local package and push committed main; Actions deploys Pages."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
REMOTE = "https://github.com/puregym-busan/puregym-busan.github.io.git"


def git(*args):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def deploy():
    if Path(git("rev-parse", "--show-toplevel")).resolve() != ROOT:
        raise RuntimeError("Run this helper from the project source repository.")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("Deployment requires the main branch.")
    for args in (("remote", "get-url", "origin"), ("remote", "get-url", "--push", "origin")):
        if git(*args) != REMOTE:
            raise RuntimeError("origin must point to the PureGym organization repository.")
    if git("status", "--porcelain"):
        raise RuntimeError("Commit the source changes before deploying. No files were staged or committed.")
    subprocess.run([sys.executable, str(ROOT / "scripts/package.py")], check=True)
    git("push", "origin", "main")
    print(f"Pushed {git('rev-parse', 'HEAD')}\nPages: https://puregym-busan.github.io/\nCheck the Deploy GitHub Pages workflow before reporting deployment complete.")


if __name__ == "__main__":
    try:
        deploy()
    except subprocess.CalledProcessError as exc:
        print((exc.stderr or str(exc)).strip(), file=sys.stderr)
        sys.exit(1)
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
