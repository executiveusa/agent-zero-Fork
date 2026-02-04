"""
Notion API Integration

Bidirectional sync between Agent Zero and Notion for project management,
documentation, and knowledge base integration.
"""

import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


class NotionIntegration:
    """Integrate Agent Zero with Notion workspace"""

    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY", "")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2024-02-15",
            "Content-Type": "application/json",
        } if self.api_key else {}
        self.version = "1.0"

    def sync_project_to_notion(
        self,
        database_id: str,
        project_name: str,
        project_description: str,
        status: str = "In Progress",
        tasks: List[str] = None,
    ) -> Dict[str, Any]:
        """Sync an Agent Zero project to Notion database"""
        if not requests or not self.api_key:
            return {"error": "Notion API key not configured", "success": False}

        try:
            page_data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": project_name}}]
                    },
                    "Description": {
                        "rich_text": [{"text": {"content": project_description or ""}}]
                    },
                    "Status": {
                        "select": {"name": status}
                    },
                    "Last Synced": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    },
                    "Agent Zero": {
                        "checkbox": True
                    },
                },
                "children": self._build_task_blocks(tasks or []),
            }

            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data,
                timeout=15,
            )
            response.raise_for_status()

            return {
                "success": True,
                "page_id": response.json().get("id"),
                "url": response.json().get("url"),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def sync_knowledge_to_notion(
        self,
        database_id: str,
        title: str,
        content: str,
        tags: List[str] = None,
        source: str = None,
    ) -> Dict[str, Any]:
        """Sync Agent Zero knowledge/memory to Notion"""
        if not requests or not self.api_key:
            return {"error": "Notion API key not configured", "success": False}

        try:
            page_data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": title[:100]}}]
                    },
                    "Content": {
                        "rich_text": [{"text": {"content": content[:500]}}]
                    },
                    "Tags": {
                        "multi_select": [
                            {"name": tag} for tag in (tags or [])[:5]
                        ]
                    },
                    "Source": {
                        "select": {"name": source or "Agent Zero"}
                    },
                    "Created": {
                        "date": {"start": datetime.now().isoformat()}
                    },
                },
            }

            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data,
                timeout=15,
            )
            response.raise_for_status()

            return {
                "success": True,
                "page_id": response.json().get("id"),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def query_notion_database(
        self,
        database_id: str,
        filter_condition: Dict = None,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """Query Notion database and retrieve pages"""
        if not requests or not self.api_key:
            return {"error": "Notion API key not configured", "success": False}

        try:
            query_body = {
                "page_size": page_size,
            }
            if filter_condition:
                query_body["filter"] = filter_condition

            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=query_body,
                timeout=15,
            )
            response.raise_for_status()

            results = response.json().get("results", [])
            return {
                "success": True,
                "results": [self._extract_page_data(page) for page in results],
                "count": len(results),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def update_notion_page(
        self,
        page_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update properties of a Notion page"""
        if not requests or not self.api_key:
            return {"error": "Notion API key not configured", "success": False}

        try:
            response = requests.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                json={"properties": updates},
                timeout=15,
            )
            response.raise_for_status()

            return {
                "success": True,
                "page_id": response.json().get("id"),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def add_page_content(
        self,
        page_id: str,
        content_blocks: List[Dict],
    ) -> Dict[str, Any]:
        """Add content blocks to a Notion page"""
        if not requests or not self.api_key:
            return {"error": "Notion API key not configured", "success": False}

        try:
            for block in content_blocks:
                response = requests.patch(
                    f"{self.base_url}/blocks/{page_id}/children",
                    headers=self.headers,
                    json={"children": [block]},
                    timeout=15,
                )
                response.raise_for_status()

            return {
                "success": True,
                "blocks_added": len(content_blocks),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def _build_task_blocks(self, tasks: List[str]) -> List[Dict]:
        """Build Notion block objects for tasks"""
        blocks = []
        for task in tasks[:10]:
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": task}}],
                    "checked": False,
                }
            })
        return blocks

    def _extract_page_data(self, page: Dict) -> Dict[str, Any]:
        """Extract useful data from Notion page"""
        properties = page.get("properties", {})
        extracted = {
            "id": page.get("id"),
            "url": page.get("url"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "properties": {},
        }

        for prop_name, prop_value in properties.items():
            prop_type = prop_value.get("type")

            if prop_type == "title":
                extracted["properties"][prop_name] = (
                    prop_value.get("title", [{}])[0].get("plain_text", "")
                )
            elif prop_type == "rich_text":
                extracted["properties"][prop_name] = (
                    prop_value.get("rich_text", [{}])[0].get("plain_text", "")
                )
            elif prop_type == "select":
                extracted["properties"][prop_name] = (
                    prop_value.get("select", {}).get("name", "")
                )
            elif prop_type == "checkbox":
                extracted["properties"][prop_name] = (
                    prop_value.get("checkbox", False)
                )
            elif prop_type == "date":
                extracted["properties"][prop_name] = (
                    prop_value.get("date", {}).get("start", "")
                )

        return extracted

    def sync_tasks_from_notion(
        self,
        database_id: str,
    ) -> Dict[str, Any]:
        """Sync tasks from Notion to Agent Zero scheduler"""
        if not requests or not self.api_key:
            return {"error": "Notion API key not configured", "success": False}

        try:
            # Query Notion database for tasks
            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json={"page_size": 50},
                timeout=15,
            )
            response.raise_for_status()

            tasks = []
            for page in response.json().get("results", []):
                task_data = self._extract_page_data(page)
                tasks.append({
                    "notion_id": task_data["id"],
                    "title": task_data.get("properties", {}).get("Name", ""),
                    "completed": task_data.get("properties", {}).get("Done", False),
                    "due_date": task_data.get("properties", {}).get("Due Date", ""),
                })

            return {
                "success": True,
                "tasks": tasks,
                "count": len(tasks),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}


def process_tool(tool_input: dict) -> dict:
    """Process Notion integration request"""
    integration = NotionIntegration()

    action = tool_input.get("action", "sync_project")
    database_id = tool_input.get("database_id", "")

    if action == "sync_project":
        return integration.sync_project_to_notion(
            database_id=database_id,
            project_name=tool_input.get("project_name", ""),
            project_description=tool_input.get("project_description", ""),
            status=tool_input.get("status", "In Progress"),
            tasks=tool_input.get("tasks", []),
        )
    elif action == "sync_knowledge":
        return integration.sync_knowledge_to_notion(
            database_id=database_id,
            title=tool_input.get("title", ""),
            content=tool_input.get("content", ""),
            tags=tool_input.get("tags", []),
            source=tool_input.get("source", "Agent Zero"),
        )
    elif action == "query":
        return integration.query_notion_database(
            database_id=database_id,
            filter_condition=tool_input.get("filter"),
            page_size=tool_input.get("page_size", 10),
        )
    elif action == "update":
        return integration.update_notion_page(
            page_id=tool_input.get("page_id", ""),
            updates=tool_input.get("updates", {}),
        )
    elif action == "sync_tasks":
        return integration.sync_tasks_from_notion(
            database_id=database_id,
        )
    else:
        return {"error": f"Unknown action: {action}"}
