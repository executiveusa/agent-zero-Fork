"""
GitHub Repository Scanner & PRD Generator — Enhanced with Bi-directional Operations

Capabilities:
  - Scan repositories (issues, PRs, code structure, incomplete features)
  - Generate PRDs from scan data
  - Create issues, comments, and labels
  - Create/merge pull requests
  - Read and update file contents
  - Trigger workflow dispatches
  - Multi-repo batch scanning

Integrates with GitHub API v3. Token from GITHUB_TOKEN env var.
"""

import json
import re
import base64
from datetime import datetime
from typing import Optional
import os

try:
    import requests
except ImportError:
    requests = None


class GitHubRepoScanner:
    """Scan GitHub repos, generate PRDs, and perform write operations."""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.github_token else {}

    # ─── READ OPERATIONS ────────────────────────────────────────

    def scan_repository(self, owner: str, repo: str) -> dict:
        """Scan a GitHub repository for incomplete features and issues"""
        try:
            repo_data = {
                "owner": owner,
                "repo": repo,
                "timestamp": datetime.now().isoformat(),
                "issues": self._get_issues(owner, repo),
                "pull_requests": self._get_pull_requests(owner, repo),
                "repo_info": self._get_repo_info(owner, repo),
                "code_structure": self._analyze_code_structure(owner, repo),
                "incomplete_features": self._identify_incomplete_features(owner, repo),
            }
            return repo_data
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _get_issues(self, owner: str, repo: str) -> list:
        """Fetch open issues from repository"""
        if not requests:
            return []
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues"
            params = {"state": "open", "per_page": 30}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            issues = response.json()
            return [
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "body": issue["body"][:500] if issue["body"] else "",
                    "labels": [l["name"] for l in issue.get("labels", [])],
                    "created_at": issue["created_at"],
                    "state": issue["state"],
                }
                for issue in issues[:20]
            ]
        except Exception:
            return []

    def _get_pull_requests(self, owner: str, repo: str) -> list:
        """Fetch open pull requests"""
        if not requests:
            return []
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            params = {"state": "open", "per_page": 20}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            prs = response.json()
            return [
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "body": pr["body"][:300] if pr["body"] else "",
                    "created_at": pr["created_at"],
                    "updated_at": pr["updated_at"],
                }
                for pr in prs[:15]
            ]
        except Exception:
            return []

    def _get_repo_info(self, owner: str, repo: str) -> dict:
        """Get repository metadata"""
        if not requests:
            return {}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "name": data["name"],
                "full_name": data["full_name"],
                "description": data["description"],
                "language": data["language"],
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "open_issues": data["open_issues_count"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "homepage": data["homepage"],
                "topics": data.get("topics", []),
            }
        except Exception:
            return {}

    def _analyze_code_structure(self, owner: str, repo: str) -> dict:
        """Analyze repository code structure"""
        if not requests:
            return {}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            contents = response.json()

            structure = {
                "files": [],
                "directories": [],
                "languages_detected": [],
            }

            for item in contents[:30]:
                if item["type"] == "file":
                    structure["files"].append(item["name"])
                elif item["type"] == "dir":
                    structure["directories"].append(item["name"])

            return structure
        except Exception:
            return {}

    def _identify_incomplete_features(self, owner: str, repo: str) -> dict:
        """Identify incomplete features from code and issues"""
        issues = self._get_issues(owner, repo)
        patterns = {
            "todo": r"TODO|FIXME|WIP|In Progress",
            "bugs": r"bug|issue|error|crash|broken",
            "features": r"feature|enhancement|improvement",
            "documentation": r"docs|documentation|readme",
        }

        incomplete = {}
        for category, pattern in patterns.items():
            incomplete[category] = [
                issue["title"] for issue in issues
                if re.search(pattern, issue["title"], re.IGNORECASE)
            ]

        return incomplete

    def generate_prd(self, scan_data: dict) -> str:
        """Generate a PRD from scanned repository data"""
        prd = f"""# Product Requirements Document (PRD)

## Repository: {scan_data.get('owner')}/{scan_data.get('repo')}
Generated: {scan_data.get('timestamp')}

### Executive Summary
Repository analysis identified {len(scan_data.get('issues', []))} open issues and opportunities for enhancement.

### Current Status
- **Stars**: {scan_data.get('repo_info', {}).get('stars', 0)}
- **Forks**: {scan_data.get('repo_info', {}).get('forks', 0)}
- **Open Issues**: {scan_data.get('repo_info', {}).get('open_issues', 0)}
- **Language**: {scan_data.get('repo_info', {}).get('language', 'Unknown')}
- **Last Updated**: {scan_data.get('repo_info', {}).get('updated_at', 'Unknown')}

### Incomplete Features Identified

#### TODO Items
{self._format_list(scan_data.get('incomplete_features', {}).get('todo', []))}

#### Known Bugs
{self._format_list(scan_data.get('incomplete_features', {}).get('bugs', []))}

#### Feature Requests
{self._format_list(scan_data.get('incomplete_features', {}).get('features', []))}

### Open Issues ({len(scan_data.get('issues', []))})
{self._format_issues(scan_data.get('issues', []))}

### Code Structure
- **Main Directories**: {', '.join(scan_data.get('code_structure', {}).get('directories', [])[:5])}
- **Key Files**: {', '.join(scan_data.get('code_structure', {}).get('files', [])[:5])}

### Recommendations
1. Prioritize bug fixes from the identified issues
2. Implement requested features in order of community engagement
3. Update documentation for clearer project status
4. Consider adopting automated testing for better code quality

### Next Steps
- Review and prioritize open issues
- Plan sprint for top 3 items
- Engage community for feedback
- Set clear milestones
"""
        return prd

    def _format_list(self, items: list) -> str:
        """Format list items for PRD"""
        if not items:
            return "- No items identified"
        return "\n".join([f"- {item}" for item in items[:10]])

    def _format_issues(self, issues: list) -> str:
        """Format issues for PRD"""
        if not issues:
            return "- No open issues"
        return "\n".join([
            f"- **#{issue['number']}**: {issue['title']}"
            for issue in issues[:10]
        ])

    # ─── WRITE OPERATIONS ───────────────────────────────────────

    def create_issue(self, owner: str, repo: str, title: str, body: str = "",
                     labels: list = None, assignees: list = None) -> dict:
        """Create a new issue"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues"
            data = {"title": title, "body": body}
            if labels:
                data["labels"] = labels
            if assignees:
                data["assignees"] = assignees
            resp = requests.post(url, headers=self.headers, json=data, timeout=15)
            resp.raise_for_status()
            issue = resp.json()
            return {"number": issue["number"], "url": issue["html_url"], "title": issue["title"]}
        except Exception as e:
            return {"error": str(e)}

    def add_comment(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        """Add a comment to an issue or PR"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
            resp = requests.post(url, headers=self.headers, json={"body": body}, timeout=15)
            resp.raise_for_status()
            return {"id": resp.json()["id"], "url": resp.json()["html_url"]}
        except Exception as e:
            return {"error": str(e)}

    def create_pull_request(self, owner: str, repo: str, title: str, head: str,
                            base: str = "main", body: str = "", draft: bool = False) -> dict:
        """Create a pull request"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            data = {"title": title, "head": head, "base": base, "body": body, "draft": draft}
            resp = requests.post(url, headers=self.headers, json=data, timeout=15)
            resp.raise_for_status()
            pr = resp.json()
            return {"number": pr["number"], "url": pr["html_url"], "title": pr["title"]}
        except Exception as e:
            return {"error": str(e)}

    def merge_pull_request(self, owner: str, repo: str, pr_number: int,
                           merge_method: str = "squash", commit_message: str = "") -> dict:
        """Merge a pull request"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
            data = {"merge_method": merge_method}
            if commit_message:
                data["commit_message"] = commit_message
            resp = requests.put(url, headers=self.headers, json=data, timeout=15)
            resp.raise_for_status()
            return {"merged": True, "message": resp.json().get("message", "Merged")}
        except Exception as e:
            return {"error": str(e)}

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> dict:
        """Read a file from the repository"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            resp = requests.get(url, headers=self.headers, params={"ref": ref}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return {"path": path, "sha": data["sha"], "content": content, "size": data["size"]}
        except Exception as e:
            return {"error": str(e)}

    def update_file(self, owner: str, repo: str, path: str, content: str,
                    message: str, sha: str = "", branch: str = "main") -> dict:
        """Create or update a file in the repository"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            data = {"message": message, "content": encoded, "branch": branch}
            if sha:
                data["sha"] = sha
            resp = requests.put(url, headers=self.headers, json=data, timeout=15)
            resp.raise_for_status()
            return {"path": path, "sha": resp.json()["content"]["sha"], "committed": True}
        except Exception as e:
            return {"error": str(e)}

    def add_labels(self, owner: str, repo: str, issue_number: int, labels: list) -> dict:
        """Add labels to an issue or PR"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/labels"
            resp = requests.post(url, headers=self.headers, json={"labels": labels}, timeout=15)
            resp.raise_for_status()
            return {"labels": [l["name"] for l in resp.json()]}
        except Exception as e:
            return {"error": str(e)}

    def close_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        """Close an issue"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
            resp = requests.patch(url, headers=self.headers, json={"state": "closed"}, timeout=15)
            resp.raise_for_status()
            return {"number": issue_number, "state": "closed"}
        except Exception as e:
            return {"error": str(e)}

    def dispatch_workflow(self, owner: str, repo: str, workflow_id: str,
                          ref: str = "main", inputs: dict = None) -> dict:
        """Trigger a workflow dispatch event"""
        if not requests:
            return {"error": "requests not installed"}
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
            data = {"ref": ref}
            if inputs:
                data["inputs"] = inputs
            resp = requests.post(url, headers=self.headers, json=data, timeout=15)
            resp.raise_for_status()
            return {"dispatched": True, "workflow": workflow_id}
        except Exception as e:
            return {"error": str(e)}

    def batch_scan(self, repos: list) -> dict:
        """Scan multiple repositories. repos = list of 'owner/repo' strings"""
        results = {}
        for repo_str in repos:
            parts = repo_str.split("/")
            if len(parts) == 2:
                results[repo_str] = self.scan_repository(parts[0], parts[1])
            else:
                results[repo_str] = {"error": f"Invalid format: {repo_str}. Use 'owner/repo'"}
        return results


def process_tool(tool_input: dict) -> dict:
    """Process GitHub repository operations"""
    scanner = GitHubRepoScanner()

    action = tool_input.get("action", "scan")
    owner = tool_input.get("owner", "")
    repo = tool_input.get("repo", "")

    # Actions that don't need owner/repo
    if action == "batch_scan":
        repos = tool_input.get("repos", [])
        return scanner.batch_scan(repos)

    if not owner or not repo:
        return {"error": "owner and repo parameters required"}

    if action == "scan":
        return scanner.scan_repository(owner, repo)
    elif action == "prd":
        scan_data = scanner.scan_repository(owner, repo)
        if "error" not in scan_data:
            prd = scanner.generate_prd(scan_data)
            return {"prd": prd, "scan_data": scan_data}
        return scan_data
    elif action == "create_issue":
        return scanner.create_issue(
            owner, repo,
            title=tool_input.get("title", ""),
            body=tool_input.get("body", ""),
            labels=tool_input.get("labels"),
            assignees=tool_input.get("assignees"),
        )
    elif action == "comment":
        return scanner.add_comment(
            owner, repo,
            issue_number=int(tool_input.get("issue_number", 0)),
            body=tool_input.get("body", ""),
        )
    elif action == "create_pr":
        return scanner.create_pull_request(
            owner, repo,
            title=tool_input.get("title", ""),
            head=tool_input.get("head", ""),
            base=tool_input.get("base", "main"),
            body=tool_input.get("body", ""),
            draft=tool_input.get("draft", False),
        )
    elif action == "merge_pr":
        return scanner.merge_pull_request(
            owner, repo,
            pr_number=int(tool_input.get("pr_number", 0)),
            merge_method=tool_input.get("merge_method", "squash"),
            commit_message=tool_input.get("commit_message", ""),
        )
    elif action == "read_file":
        return scanner.get_file_content(
            owner, repo,
            path=tool_input.get("path", ""),
            ref=tool_input.get("ref", "main"),
        )
    elif action == "update_file":
        return scanner.update_file(
            owner, repo,
            path=tool_input.get("path", ""),
            content=tool_input.get("content", ""),
            message=tool_input.get("message", "Update via Agent Zero"),
            sha=tool_input.get("sha", ""),
            branch=tool_input.get("branch", "main"),
        )
    elif action == "add_labels":
        return scanner.add_labels(
            owner, repo,
            issue_number=int(tool_input.get("issue_number", 0)),
            labels=tool_input.get("labels", []),
        )
    elif action == "close_issue":
        return scanner.close_issue(
            owner, repo,
            issue_number=int(tool_input.get("issue_number", 0)),
        )
    elif action == "dispatch_workflow":
        return scanner.dispatch_workflow(
            owner, repo,
            workflow_id=tool_input.get("workflow_id", ""),
            ref=tool_input.get("ref", "main"),
            inputs=tool_input.get("inputs"),
        )
    else:
        return {"error": f"Unknown action: {action}. Available: scan, prd, create_issue, comment, create_pr, merge_pr, read_file, update_file, add_labels, close_issue, dispatch_workflow, batch_scan"}
