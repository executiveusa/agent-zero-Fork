"""
GitHub Repository Scanner & PRD Generator

Scans GitHub repositories to analyze incomplete features and generate PRDs.
Integrates with GitHub API to extract issues, PRs, code structure, and documentation.
"""

import json
import re
from datetime import datetime
from typing import Optional
import os

try:
    import requests
except ImportError:
    requests = None


class GitHubRepoScanner:
    """Scan GitHub repos and generate Product Requirements Documents (PRDs)"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.github_token else {}

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


def process_tool(tool_input: dict) -> dict:
    """Process GitHub repository scanning request"""
    scanner = GitHubRepoScanner()

    action = tool_input.get("action", "scan")
    owner = tool_input.get("owner")
    repo = tool_input.get("repo")

    if not owner or not repo:
        return {"error": "owner and repo parameters required"}

    if action == "scan":
        result = scanner.scan_repository(owner, repo)
        return result
    elif action == "prd":
        scan_data = scanner.scan_repository(owner, repo)
        if "error" not in scan_data:
            prd = scanner.generate_prd(scan_data)
            return {"prd": prd, "scan_data": scan_data}
        return scan_data
    else:
        return {"error": f"Unknown action: {action}"}
