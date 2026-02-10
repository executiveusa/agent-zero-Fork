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
        # Try vault first, then env (support both NOTION_API_TOKEN and NOTION_API_KEY)
        self.api_key = ""
        try:
            from python.helpers.vault import vault_get
            self.api_key = vault_get("NOTION_API_TOKEN") or ""
        except Exception:
            pass
        if not self.api_key:
            self.api_key = os.getenv("NOTION_API_TOKEN", os.getenv("NOTION_API_KEY", ""))
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

    # ══════════════════════════════════════════════════════════
    # Moltbook — Notion as Agent Hangout / Meeting Hub
    # ══════════════════════════════════════════════════════════

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Dict],
        icon: str = "📋",
    ) -> Dict[str, Any]:
        """
        Create a new Notion database under a parent page.
        
        Args:
            parent_page_id: UUID of the parent page
            title: Database title
            properties: Property schema dict (Notion format)
            icon: Emoji icon for the database
        
        Returns:
            Created database metadata or error
        """
        if not requests or not self.api_key:
            return {"error": "Notion API key not configured", "success": False}

        try:
            payload = {
                "parent": {"type": "page_id", "page_id": parent_page_id},
                "icon": {"type": "emoji", "emoji": icon},
                "title": [{"type": "text", "text": {"content": title}}],
                "properties": properties,
            }

            response = requests.post(
                f"{self.base_url}/databases",
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "database_id": data.get("id"),
                "url": data.get("url"),
                "title": title,
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def create_meeting_db(self, parent_page_id: str) -> Dict[str, Any]:
        """
        Create the Meeting DB in Notion — stores all agent meeting records.
        
        Schema:
        - Name (title)
        - Type (select: daily_standup, weekly_strategy, ad_hoc)
        - Date (date)
        - Chair (select: agent names)
        - Attendees (multi_select: agent names)
        - Status (select: scheduled, in_progress, completed, cancelled)
        - Decisions (number)
        - Action Items (number)
        - Summary (rich_text)
        """
        properties = {
            "Name": {"title": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "daily_standup", "color": "blue"},
                        {"name": "weekly_strategy", "color": "purple"},
                        {"name": "ad_hoc", "color": "gray"},
                    ]
                }
            },
            "Date": {"date": {}},
            "Chair": {
                "select": {
                    "options": [
                        {"name": "Agent Zero", "color": "red"},
                        {"name": "SYNTHIA", "color": "green"},
                        {"name": "Security Officer", "color": "orange"},
                        {"name": "Dev Lead", "color": "blue"},
                        {"name": "Growth Hacker", "color": "purple"},
                    ]
                }
            },
            "Attendees": {
                "multi_select": {
                    "options": [
                        {"name": "Agent Zero", "color": "red"},
                        {"name": "SYNTHIA", "color": "green"},
                        {"name": "Security Officer", "color": "orange"},
                        {"name": "Dev Lead", "color": "blue"},
                        {"name": "Growth Hacker", "color": "purple"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "scheduled", "color": "yellow"},
                        {"name": "in_progress", "color": "blue"},
                        {"name": "completed", "color": "green"},
                        {"name": "cancelled", "color": "red"},
                    ]
                }
            },
            "Decisions": {"number": {"format": "number"}},
            "Action Items": {"number": {"format": "number"}},
            "Summary": {"rich_text": {}},
        }

        return self.create_database(parent_page_id, "Agent Meetings", properties, icon="🤝")

    def create_goal_tracker_db(self, parent_page_id: str) -> Dict[str, Any]:
        """
        Create the Goal Tracker DB — revenue milestones and task ownership.
        
        Schema:
        - Goal (title)
        - Target Revenue (number, dollar)
        - Target Date (date)
        - Owner (select: agent names)
        - Status (select: not_started, in_progress, at_risk, completed)
        - Priority (select: P0-P4)
        - Beads ID (rich_text)
        - Progress (number, percent)
        - Notes (rich_text)
        """
        properties = {
            "Goal": {"title": {}},
            "Target Revenue": {"number": {"format": "dollar"}},
            "Target Date": {"date": {}},
            "Owner": {
                "select": {
                    "options": [
                        {"name": "Agent Zero", "color": "red"},
                        {"name": "SYNTHIA", "color": "green"},
                        {"name": "Security Officer", "color": "orange"},
                        {"name": "Dev Lead", "color": "blue"},
                        {"name": "Growth Hacker", "color": "purple"},
                        {"name": "All", "color": "default"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "not_started", "color": "default"},
                        {"name": "in_progress", "color": "blue"},
                        {"name": "at_risk", "color": "orange"},
                        {"name": "completed", "color": "green"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "P0", "color": "red"},
                        {"name": "P1", "color": "orange"},
                        {"name": "P2", "color": "yellow"},
                        {"name": "P3", "color": "blue"},
                        {"name": "P4", "color": "gray"},
                    ]
                }
            },
            "Beads ID": {"rich_text": {}},
            "Progress": {"number": {"format": "percent"}},
            "Notes": {"rich_text": {}},
        }

        return self.create_database(parent_page_id, "Goal Tracker", properties, icon="🎯")

    def create_watercooler_db(self, parent_page_id: str) -> Dict[str, Any]:
        """
        Create the Watercooler DB — informal notes, ideas, cross-agent observations.
        
        Schema:
        - Topic (title)
        - Author (select: agent names)
        - Category (select: idea, observation, question, note)
        - Timestamp (date)
        - Content (rich_text)
        - Tags (multi_select)
        - Upvotes (number)
        """
        properties = {
            "Topic": {"title": {}},
            "Author": {
                "select": {
                    "options": [
                        {"name": "Agent Zero", "color": "red"},
                        {"name": "SYNTHIA", "color": "green"},
                        {"name": "Security Officer", "color": "orange"},
                        {"name": "Dev Lead", "color": "blue"},
                        {"name": "Growth Hacker", "color": "purple"},
                    ]
                }
            },
            "Category": {
                "select": {
                    "options": [
                        {"name": "idea", "color": "yellow"},
                        {"name": "observation", "color": "blue"},
                        {"name": "question", "color": "purple"},
                        {"name": "note", "color": "gray"},
                    ]
                }
            },
            "Timestamp": {"date": {}},
            "Content": {"rich_text": {}},
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "revenue", "color": "green"},
                        {"name": "security", "color": "red"},
                        {"name": "engineering", "color": "blue"},
                        {"name": "growth", "color": "purple"},
                        {"name": "strategy", "color": "orange"},
                    ]
                }
            },
            "Upvotes": {"number": {"format": "number"}},
        }

        return self.create_database(parent_page_id, "Watercooler", properties, icon="💬")

    def setup_moltbook(self, parent_page_id: str) -> Dict[str, Any]:
        """
        Create the full Moltbook workspace: Meeting DB + Goal Tracker + Watercooler.
        
        Args:
            parent_page_id: UUID of the Notion page to create databases under
        
        Returns:
            Dict with database IDs for all three databases
        """
        results = {}
        
        meeting_result = self.create_meeting_db(parent_page_id)
        results["meeting_db"] = meeting_result
        
        goal_result = self.create_goal_tracker_db(parent_page_id)
        results["goal_tracker_db"] = goal_result
        
        watercooler_result = self.create_watercooler_db(parent_page_id)
        results["watercooler_db"] = watercooler_result
        
        results["success"] = all(
            r.get("success") for r in [meeting_result, goal_result, watercooler_result]
        )
        
        return results

    def add_watercooler_note(
        self,
        database_id: str,
        topic: str,
        content: str,
        author: str = "Agent Zero",
        category: str = "note",
        tags: List[str] = None,
    ) -> Dict[str, Any]:
        """Post a note to the Watercooler."""
        if not requests or not self.api_key:
            return {"error": "Notion API key not configured", "success": False}

        try:
            page_data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Topic": {"title": [{"text": {"content": topic[:100]}}]},
                    "Author": {"select": {"name": author}},
                    "Category": {"select": {"name": category}},
                    "Timestamp": {"date": {"start": datetime.now().isoformat()}},
                    "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},
                    "Tags": {"multi_select": [{"name": t} for t in (tags or [])[:5]]},
                    "Upvotes": {"number": 0},
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
                "url": response.json().get("url"),
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
    elif action == "setup_moltbook":
        return integration.setup_moltbook(
            parent_page_id=tool_input.get("parent_page_id", ""),
        )
    elif action == "create_meeting_db":
        return integration.create_meeting_db(
            parent_page_id=tool_input.get("parent_page_id", ""),
        )
    elif action == "create_goal_tracker":
        return integration.create_goal_tracker_db(
            parent_page_id=tool_input.get("parent_page_id", ""),
        )
    elif action == "create_watercooler":
        return integration.create_watercooler_db(
            parent_page_id=tool_input.get("parent_page_id", ""),
        )
    elif action == "watercooler_note":
        return integration.add_watercooler_note(
            database_id=database_id,
            topic=tool_input.get("topic", ""),
            content=tool_input.get("content", ""),
            author=tool_input.get("author", "Agent Zero"),
            category=tool_input.get("category", "note"),
            tags=tool_input.get("tags", []),
        )
    else:
        return {"error": f"Unknown action: {action}"}
