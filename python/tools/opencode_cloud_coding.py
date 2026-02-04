"""
OpenCode Cloud Coding Integration

Enables Agent Zero to develop full applications in the cloud using OpenCode,
with automatic deployment and testing.
"""

import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


class OpenCodeCloudCoding:
    """Integrate with OpenCode for cloud-based development"""

    def __init__(self):
        self.api_key = os.getenv("OPENCODE_API_KEY", "")
        self.base_url = os.getenv("OPENCODE_API_URL", "https://api.opencode.app")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        } if self.api_key else {}

    def create_project(
        self,
        project_name: str,
        description: str,
        tech_stack: List[str],
        template: str = "react-typescript",
    ) -> Dict[str, Any]:
        """Create a new project on OpenCode"""
        if not requests or not self.api_key:
            return {"error": "OpenCode API key not configured", "success": False}

        try:
            payload = {
                "name": project_name,
                "description": description,
                "technologies": tech_stack,
                "template": template,
                "created_at": datetime.now().isoformat(),
            }

            response = requests.post(
                f"{self.base_url}/projects",
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "project_id": data.get("id"),
                "project_url": data.get("url"),
                "git_url": data.get("git_url"),
                "live_url": data.get("live_url"),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def code_feature(
        self,
        project_id: str,
        feature_description: str,
        file_paths: List[str] = None,
        requirements: str = None,
    ) -> Dict[str, Any]:
        """Generate code for a feature using AI"""
        if not requests or not self.api_key:
            return {"error": "OpenCode API key not configured", "success": False}

        try:
            payload = {
                "project_id": project_id,
                "feature_description": feature_description,
                "target_files": file_paths or [],
                "requirements": requirements,
                "ai_model": "gpt-4",
            }

            response = requests.post(
                f"{self.base_url}/projects/{project_id}/code-feature",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "generated_code": data.get("generated_code"),
                "files_modified": data.get("files_modified", []),
                "code_review": data.get("code_review"),
                "suggestions": data.get("suggestions", []),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def vibe_code(
        self,
        project_id: str,
        vibe_description: str,
        components: List[str] = None,
    ) -> Dict[str, Any]:
        """Creative 'vibe coding' - generate code based on vibes/feelings"""
        if not requests or not self.api_key:
            return {"error": "OpenCode API key not configured", "success": False}

        try:
            payload = {
                "project_id": project_id,
                "vibe": vibe_description,
                "components": components or [],
                "style": "creative",
                "ai_model": "claude-3-5-sonnet",
            }

            response = requests.post(
                f"{self.base_url}/projects/{project_id}/vibe-code",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "generated_components": data.get("generated_components", []),
                "styling": data.get("styling"),
                "animations": data.get("animations", []),
                "vibe_score": data.get("vibe_score", 0),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def run_tests(
        self,
        project_id: str,
        test_type: str = "unit",
    ) -> Dict[str, Any]:
        """Run tests on the OpenCode project"""
        if not requests or not self.api_key:
            return {"error": "OpenCode API key not configured", "success": False}

        try:
            response = requests.post(
                f"{self.base_url}/projects/{project_id}/tests/run",
                headers=self.headers,
                json={"test_type": test_type},
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "passed": data.get("passed", 0),
                "failed": data.get("failed", 0),
                "coverage": data.get("coverage", 0),
                "results": data.get("results", []),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def deploy_project(
        self,
        project_id: str,
        deployment_target: str = "cloud",
        environment: str = "production",
    ) -> Dict[str, Any]:
        """Deploy project to cloud"""
        if not requests or not self.api_key:
            return {"error": "OpenCode API key not configured", "success": False}

        try:
            payload = {
                "target": deployment_target,
                "environment": environment,
            }

            response = requests.post(
                f"{self.base_url}/projects/{project_id}/deploy",
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "deployment_id": data.get("deployment_id"),
                "live_url": data.get("live_url"),
                "status": data.get("status"),
                "deployment_logs": data.get("logs", []),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get current status of a project"""
        if not requests or not self.api_key:
            return {"error": "OpenCode API key not configured", "success": False}

        try:
            response = requests.get(
                f"{self.base_url}/projects/{project_id}",
                headers=self.headers,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "project_id": data.get("id"),
                "name": data.get("name"),
                "status": data.get("status"),
                "live_url": data.get("live_url"),
                "git_url": data.get("git_url"),
                "last_deploy": data.get("last_deploy"),
                "test_coverage": data.get("test_coverage", 0),
                "performance_score": data.get("performance_score", 0),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def list_projects(self, limit: int = 10) -> Dict[str, Any]:
        """List all OpenCode projects"""
        if not requests or not self.api_key:
            return {"error": "OpenCode API key not configured", "success": False}

        try:
            response = requests.get(
                f"{self.base_url}/projects",
                headers=self.headers,
                params={"limit": limit},
                timeout=15,
            )
            response.raise_for_status()

            projects = response.json().get("projects", [])
            return {
                "success": True,
                "projects": [
                    {
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "status": p.get("status"),
                        "live_url": p.get("live_url"),
                    }
                    for p in projects
                ],
                "count": len(projects),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def regenerate_code(
        self,
        project_id: str,
        file_path: str,
        feedback: str,
    ) -> Dict[str, Any]:
        """Regenerate code with feedback"""
        if not requests or not self.api_key:
            return {"error": "OpenCode API key not configured", "success": False}

        try:
            payload = {
                "file_path": file_path,
                "feedback": feedback,
            }

            response = requests.post(
                f"{self.base_url}/projects/{project_id}/regenerate",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "generated_code": data.get("generated_code"),
                "improvements": data.get("improvements", []),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}


def process_tool(tool_input: dict) -> dict:
    """Process OpenCode cloud coding request"""
    opencode = OpenCodeCloudCoding()

    action = tool_input.get("action", "create_project")

    if action == "create_project":
        return opencode.create_project(
            project_name=tool_input.get("project_name", ""),
            description=tool_input.get("description", ""),
            tech_stack=tool_input.get("tech_stack", ["react", "typescript"]),
            template=tool_input.get("template", "react-typescript"),
        )
    elif action == "code_feature":
        return opencode.code_feature(
            project_id=tool_input.get("project_id", ""),
            feature_description=tool_input.get("feature_description", ""),
            file_paths=tool_input.get("file_paths"),
            requirements=tool_input.get("requirements"),
        )
    elif action == "vibe_code":
        return opencode.vibe_code(
            project_id=tool_input.get("project_id", ""),
            vibe_description=tool_input.get("vibe_description", ""),
            components=tool_input.get("components"),
        )
    elif action == "run_tests":
        return opencode.run_tests(
            project_id=tool_input.get("project_id", ""),
            test_type=tool_input.get("test_type", "unit"),
        )
    elif action == "deploy":
        return opencode.deploy_project(
            project_id=tool_input.get("project_id", ""),
            deployment_target=tool_input.get("deployment_target", "cloud"),
            environment=tool_input.get("environment", "production"),
        )
    elif action == "status":
        return opencode.get_project_status(
            project_id=tool_input.get("project_id", ""),
        )
    elif action == "list":
        return opencode.list_projects(
            limit=tool_input.get("limit", 10),
        )
    elif action == "regenerate":
        return opencode.regenerate_code(
            project_id=tool_input.get("project_id", ""),
            file_path=tool_input.get("file_path", ""),
            feedback=tool_input.get("feedback", ""),
        )
    else:
        return {"error": f"Unknown action: {action}"}
