#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import time
import argparse
import hashlib

# Define a base directory for caching clones.
CACHE_BASE = os.path.expanduser("~/.cache/git_clone_cache")

def get_cache_path(repo_url, branch):
    """
    Create a unique cache directory name from the repo URL and branch.
    """
    key = f"{repo_url}_{branch}"
    hash_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_BASE, hash_key)

def perform_git_clone(repo_url, branch, target_dir):
    """
    Clone the repo into the target directory using --depth=1 (and branch if provided).
    """
    cmd = ["git", "clone"]
    if branch:
        cmd.extend(["-b", branch])
    cmd.extend(["--depth=1", repo_url, target_dir])
    print("Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)

def is_recent(path, seconds=86400):
    """
    Check if the given directory was modified within the past `seconds` seconds.
    Default: 86400 seconds = 24 hours.
    """
    mtime = os.path.getmtime(path)
    return (time.time() - mtime) < seconds

def main():
    parser = argparse.ArgumentParser(description="Cache git clones to avoid re-cloning within 24 hours.")
    parser.add_argument("repo_url", help="Git repository URL to clone.")
    parser.add_argument("destination", nargs="?", help="Destination directory (defaults to the repo name).")
    parser.add_argument("--branch", help="Branch to clone.", default=None)
    args = parser.parse_args()

    repo_url = args.repo_url
    branch = args.branch

    # Determine the destination directory if not provided.
    destination = args.destination
    if destination is None:
        # Derive the directory name from the repo URL.
        base = os.path.basename(repo_url)
        if base.endswith(".git"):
            base = base[:-4]
        destination = base

    # Ensure the cache base directory exists.
    os.makedirs(CACHE_BASE, exist_ok=True)

    # Determine the cache path for this repo/branch.
    cache_repo_dir = get_cache_path(repo_url, branch)

    # If a cached clone exists and is fresh (< 24 hours old), we can use it.
    if os.path.isdir(cache_repo_dir) and is_recent(cache_repo_dir):
        print("Using cached repository.")
    else:
        if os.path.isdir(cache_repo_dir):
            print("Cached repository is older than 24 hours. Refreshing...")
            shutil.rmtree(cache_repo_dir)
        else:
            print("Repository not found in cache. Cloning...")
        # Clone the repository into the cache.
        perform_git_clone(repo_url, branch, cache_repo_dir)
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=cache_repo_dir, check=True)

    # If the destination directory already exists, remove it.
    if os.path.exists(destination):
        print(f"Destination directory '{destination}' already exists. Removing it.")
        shutil.rmtree(destination)

    # Copy the cached repository to the destination.
    # Note: copytree will copy the entire directory, preserving symlinks.
    shutil.copytree(cache_repo_dir, destination, symlinks=True)
    print(f"Repository cloned to '{destination}' using cache.")

if __name__ == "__main__":
    main()

