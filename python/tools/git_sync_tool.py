"""Git Sync Tool - Make GitHub the Ultimate Source of Truth

Actions
-------
sync_repo      - Compare local vs GitHub, intelligently synchronize
analyze_diff   - Detailed analysis of local vs remote differences
resolve_conflict - Resolve merge conflicts with AI assistance
commit_all     - Stage all changes, create descriptive commit, push
pull_latest    - Pull latest from remote with auto-merge
status_check   - Complete git status + diff + log summary

Environment
-----------
GIT_DEFAULT_BRANCH  - Default branch to sync with (default: main)
GIT_AUTO_PUSH       - Auto-push after commits (default: true)
"""

import os
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class GitSyncTool:
    def __init__(self, repo_path: str = ".") -> None:
        self.repo_path = Path(repo_path).resolve()
        self.default_branch = os.getenv("GIT_DEFAULT_BRANCH", "main")
        self.auto_push = os.getenv("GIT_AUTO_PUSH", "true").lower() == "true"

    def _run_git(self, *args: str, check: bool = True) -> Tuple[int, str, str]:
        """Run git command and return (returncode, stdout, stderr)"""
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stderr}")
        return result.returncode, result.stdout, result.stderr

    def _get_current_branch(self) -> str:
        _, stdout, _ = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        return stdout.strip()

    def _get_remote_branch(self) -> str:
        """Get the tracking remote branch for current branch"""
        _, stdout, _ = self._run_git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
        if stdout.strip():
            return stdout.strip()
        return f"origin/{self._get_current_branch()}"

    # ------------------------------------------------------------------
    # Status Check
    # ------------------------------------------------------------------
    def status_check(self) -> dict:
        """Complete status: uncommitted changes, unpushed commits, remote changes"""
        try:
            # Fetch latest from remote
            self._run_git("fetch", "--quiet")

            current_branch = self._get_current_branch()
            remote_branch = self._get_remote_branch()

            # Get status
            _, status_output, _ = self._run_git("status", "--porcelain")
            uncommitted_files = [line[3:] for line in status_output.strip().split("\n") if line.strip()]

            # Get unpushed commits
            _, ahead_output, _ = self._run_git("log", f"{remote_branch}..HEAD", "--oneline", check=False)
            unpushed_commits = [line for line in ahead_output.strip().split("\n") if line.strip()]

            # Get unpulled commits
            _, behind_output, _ = self._run_git("log", f"HEAD..{remote_branch}", "--oneline", check=False)
            unpulled_commits = [line for line in behind_output.strip().split("\n") if line.strip()]

            # Get diff summary
            _, diff_output, _ = self._run_git("diff", "--stat", check=False)

            return {
                "success": True,
                "current_branch": current_branch,
                "remote_branch": remote_branch,
                "uncommitted_files": uncommitted_files,
                "uncommitted_count": len([f for f in uncommitted_files if f]),
                "unpushed_commits": unpushed_commits,
                "unpushed_count": len([c for c in unpushed_commits if c]),
                "unpulled_commits": unpulled_commits,
                "unpulled_count": len([c for c in unpulled_commits if c]),
                "diff_summary": diff_output.strip(),
                "is_clean": len([f for f in uncommitted_files if f]) == 0,
                "is_synced": len([c for c in unpushed_commits if c]) == 0 and len([c for c in unpulled_commits if c]) == 0,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Analyze Diff
    # ------------------------------------------------------------------
    def analyze_diff(self, target_branch: Optional[str] = None) -> dict:
        """Detailed diff analysis between local and remote"""
        try:
            self._run_git("fetch", "--quiet")

            target = target_branch or self._get_remote_branch()

            # Get diff stat
            _, stat_output, _ = self._run_git("diff", target, "--stat", check=False)

            # Get full diff
            _, diff_output, _ = self._run_git("diff", target, check=False)

            # Get file changes
            _, name_status, _ = self._run_git("diff", target, "--name-status", check=False)
            file_changes = []
            for line in name_status.strip().split("\n"):
                if line.strip():
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        file_changes.append({"status": parts[0], "file": parts[1]})

            return {
                "success": True,
                "target_branch": target,
                "stat_summary": stat_output.strip(),
                "file_changes": file_changes,
                "diff_lines": len(diff_output.split("\n")),
                "full_diff": diff_output[:5000],  # First 5000 chars
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Sync Repo (Main Function)
    # ------------------------------------------------------------------
    def sync_repo(self, strategy: str = "auto", commit_message: Optional[str] = None) -> dict:
        """
        Intelligent sync: local <-> GitHub source of truth

        Strategies:
        - auto: Automatically choose best strategy
        - commit_push: Commit local changes and push
        - pull_merge: Pull remote changes and merge
        - rebase: Rebase local commits on remote
        """
        try:
            self._run_git("fetch", "--quiet")

            status = self.status_check()
            if not status["success"]:
                return status

            # Determine sync strategy
            has_local_changes = status["uncommitted_count"] > 0 or status["unpushed_count"] > 0
            has_remote_changes = status["unpulled_count"] > 0

            if not has_local_changes and not has_remote_changes:
                return {"success": True, "action": "no_sync_needed", "message": "Already in sync with remote"}

            if strategy == "auto":
                if has_local_changes and not has_remote_changes:
                    strategy = "commit_push"
                elif not has_local_changes and has_remote_changes:
                    strategy = "pull_merge"
                elif has_local_changes and has_remote_changes:
                    strategy = "rebase"

            # Execute strategy
            if strategy == "commit_push":
                return self._commit_and_push(commit_message)
            elif strategy == "pull_merge":
                return self._pull_and_merge()
            elif strategy == "rebase":
                return self._rebase_sync(commit_message)
            else:
                return {"success": False, "error": f"Unknown strategy: {strategy}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _commit_and_push(self, commit_message: Optional[str]) -> dict:
        """Commit all changes and push to remote"""
        try:
            # Stage all changes
            self._run_git("add", "-A")

            # Generate commit message if not provided
            if not commit_message:
                _, diff_output, _ = self._run_git("diff", "--cached", "--stat")
                commit_message = f"sync: update from local workspace\n\n{diff_output.strip()}"

            # Commit
            self._run_git("commit", "-m", commit_message)

            # Push if auto-push enabled
            if self.auto_push:
                current_branch = self._get_current_branch()
                self._run_git("push", "-u", "origin", current_branch)
                return {"success": True, "action": "commit_push", "message": "Committed and pushed to GitHub"}
            else:
                return {"success": True, "action": "commit_only", "message": "Committed locally (auto-push disabled)"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _pull_and_merge(self) -> dict:
        """Pull remote changes and merge"""
        try:
            # Use rebase to avoid merge commits
            self._run_git("pull", "--rebase", "--autostash")
            return {"success": True, "action": "pull_merge", "message": "Pulled and merged remote changes"}
        except Exception as e:
            # If rebase fails, try regular pull
            try:
                self._run_git("rebase", "--abort", check=False)
                self._run_git("pull", "--no-rebase")
                return {
                    "success": True,
                    "action": "pull_merge",
                    "message": "Pulled remote changes (merge commit created)",
                }
            except Exception as e2:
                return {"success": False, "error": f"Pull failed: {e2}"}

    def _rebase_sync(self, commit_message: Optional[str]) -> dict:
        """Commit local, pull remote with rebase, push"""
        try:
            # First commit local changes
            result = self._commit_and_push(commit_message)
            if not result["success"]:
                return result

            # Then pull with rebase
            try:
                self._run_git("pull", "--rebase", "--autostash")
            except:
                # If rebase fails, abort and use merge
                self._run_git("rebase", "--abort", check=False)
                self._run_git("pull", "--no-rebase")

            # Finally push
            if self.auto_push:
                current_branch = self._get_current_branch()
                self._run_git("push", "-u", "origin", current_branch)

            return {"success": True, "action": "rebase_sync", "message": "Synced via commit + rebase + push"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Resolve Conflicts
    # ------------------------------------------------------------------
    def resolve_conflict(self, resolution: str = "ours") -> dict:
        """
        Resolve merge conflicts

        Resolutions:
        - ours: Keep local changes
        - theirs: Keep remote changes
        - manual: List conflicts for manual resolution
        """
        try:
            if resolution == "ours":
                self._run_git("checkout", "--ours", ".")
                self._run_git("add", "-A")
                return {"success": True, "resolution": "ours", "message": "Kept local changes"}
            elif resolution == "theirs":
                self._run_git("checkout", "--theirs", ".")
                self._run_git("add", "-A")
                return {"success": True, "resolution": "theirs", "message": "Kept remote changes"}
            elif resolution == "manual":
                _, conflicts, _ = self._run_git("diff", "--name-only", "--diff-filter=U")
                conflict_files = [f for f in conflicts.strip().split("\n") if f.strip()]
                return {
                    "success": True,
                    "resolution": "manual",
                    "conflict_files": conflict_files,
                    "message": f"Found {len(conflict_files)} files with conflicts",
                }
            else:
                return {"success": False, "error": f"Unknown resolution: {resolution}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Pull Latest
    # ------------------------------------------------------------------
    def pull_latest(self, branch: Optional[str] = None) -> dict:
        """Pull latest from remote branch"""
        try:
            target_branch = branch or self.default_branch
            self._run_git("fetch", "origin")
            self._run_git("pull", "origin", target_branch)
            return {"success": True, "branch": target_branch, "message": f"Pulled latest from {target_branch}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Commit All
    # ------------------------------------------------------------------
    def commit_all(self, message: str, push: bool = True) -> dict:
        """Stage all, commit with message, optionally push"""
        try:
            self._run_git("add", "-A")
            self._run_git("commit", "-m", message)

            if push and self.auto_push:
                current_branch = self._get_current_branch()
                self._run_git("push", "-u", "origin", current_branch)
                return {"success": True, "message": "Committed and pushed", "pushed": True}
            else:
                return {"success": True, "message": "Committed locally", "pushed": False}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ----------------------------------------------------------------------
# Tool entry-point (auto-discovered by Agent Zero)
# ----------------------------------------------------------------------
def process_tool(tool_input: dict) -> dict:
    """Process git sync tool actions"""
    repo_path = tool_input.get("repo_path", ".")
    git_tool = GitSyncTool(repo_path)

    action = tool_input.get("action", "")

    try:
        if action == "status_check":
            return git_tool.status_check()

        elif action == "analyze_diff":
            return git_tool.analyze_diff(target_branch=tool_input.get("target_branch"))

        elif action == "sync_repo":
            return git_tool.sync_repo(
                strategy=tool_input.get("strategy", "auto"),
                commit_message=tool_input.get("commit_message"),
            )

        elif action == "resolve_conflict":
            return git_tool.resolve_conflict(resolution=tool_input.get("resolution", "ours"))

        elif action == "pull_latest":
            return git_tool.pull_latest(branch=tool_input.get("branch"))

        elif action == "commit_all":
            return git_tool.commit_all(
                message=tool_input["message"],
                push=tool_input.get("push", True),
            )

        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "status_check",
                    "analyze_diff",
                    "sync_repo",
                    "resolve_conflict",
                    "pull_latest",
                    "commit_all",
                ],
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
