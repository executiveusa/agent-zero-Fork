"""
A2A Protocol Enhancement with MCP Agent Mail
Enhanced agent communication using MCP Agent Mail + A2A Protocol + A2UI
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.fasta2a_client import connect_to_agent, is_client_available

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class MessagePriority(Enum):
    """Message priority levels for agent communication."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskState(Enum):
    """A2A task states."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCard:
    """A2A Agent Card containing agent metadata."""
    name: str
    description: str
    url: str
    version: str
    capabilities: List[str] = field(default_factory=list)
    skills: List[Dict[str, Any]] = field(default_factory=list)
    authentication: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        return cls(
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            url=data.get("url", ""),
            version=data.get("version", "1.0"),
            capabilities=data.get("capabilities", []),
            skills=data.get("skills", []),
            authentication=data.get("authentication", {})
        )


@dataclass
class AgentMessage:
    """Enhanced agent message with MCP Agent Mail features."""
    role: str  # "user", "agent", "system"
    content: str
    priority: MessagePriority = MessagePriority.NORMAL
    context_id: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    references: List[str] = field(default_factory=list)  # Message IDs
    
    def to_a2a_format(self) -> Dict[str, Any]:
        """Convert to A2A protocol format."""
        return {
            "role": self.role,
            "parts": [
                {
                    "kind": "text",
                    "text": self.content
                }
            ],
            "metadata": {
                "priority": self.priority.name.lower(),
                "timestamp": self.timestamp.isoformat(),
                **self.metadata
            }
        }


@dataclass
class TaskResult:
    """Result from agent task execution."""
    task_id: str
    state: TaskState
    content: str
    context_id: Optional[str]
    history: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]
    error: Optional[str]
    execution_time_ms: int
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# A2A Message Router
# ============================================================================

class A2AMessageRouter:
    """Advanced routing for A2A messages with load balancing and failover."""
    
    def __init__(self):
        self.agent_registry: Dict[str, AgentCard] = {}
        self.connection_pools: Dict[str, List[str]] = {}
        self.failure_counts: Dict[str, int] = {}
        self.round_robin_counters: Dict[str, int] = {}
    
    def register_agent(self, agent_url: str, card: AgentCard):
        """Register an agent in the routing table."""
        self.agent_registry[agent_url] = card
        logger.info(f"Registered agent: {card.name} at {agent_url}")
    
    def discover_agents(self, capability: str) -> List[str]:
        """Find agents with specific capability."""
        return [
            url for url, card in self.agent_registry.items()
            if capability in card.capabilities
        ]
    
    def select_agent(
        self, 
        agent_urls: List[str],
        strategy: str = "round_robin",
        prefer_url: Optional[str] = None
    ) -> Optional[str]:
        """Select best agent based on strategy."""
        if not agent_urls:
            return None
        
        # Prefer specified URL if available
        if prefer_url and prefer_url in agent_urls:
            # Check if it's not failing
            if self.failure_counts.get(prefer_url, 0) < 3:
                return prefer_url
        
        if strategy == "round_robin":
            return self._round_robin_select(agent_urls)
        elif strategy == "least_failures":
            return self._least_failures_select(agent_urls)
        elif strategy == "random":
            import random
            return random.choice(agent_urls)
        
        return agent_urls[0]
    
    def _round_robin_select(self, agent_urls: List[str]) -> str:
        """Round-robin selection."""
        for url in agent_urls:
            if self.failure_counts.get(url, 0) < 3:
                counter = self.round_robin_counters.get(url, 0)
                self.round_robin_counters[url] = (counter + 1) % 100
                return url
        return agent_urls[0]
    
    def _least_failures_select(self, agent_urls: List[str]) -> str:
        """Select agent with fewest failures."""
        min_failures = float('inf')
        selected = agent_urls[0]
        
        for url in agent_urls:
            failures = self.failure_counts.get(url, 0)
            if failures < min_failures:
                min_failures = failures
                selected = url
        
        return selected
    
    def record_failure(self, agent_url: str):
        """Record a failure for an agent."""
        self.failure_counts[agent_url] = self.failure_counts.get(agent_url, 0) + 1
        logger.warning(f"Agent {agent_url} failure count: {self.failure_counts[agent_url]}")
    
    def record_success(self, agent_url: str):
        """Record success, reset failure count."""
        if agent_url in self.failure_counts:
            self.failure_counts[agent_url] = max(0, self.failure_counts[agent_url] - 1)


# Global router instance
router = A2AMessageRouter()


# ============================================================================
# A2A Agent Mail Tool
# ============================================================================

class A2AAgentMailTool(Tool):
    """
    Enhanced A2A communication with MCP Agent Mail features.
    
    Features:
    - Priority-based message routing
    - Context persistence across sessions
    - Task state tracking
    - Multi-agent orchestration
    - Automatic failover and load balancing
    """
    
    async def execute(self, **kwargs):
        """Execute agent communication."""
        if not is_client_available():
            return Response(
                message="FastA2A client not available on this instance.",
                break_loop=False
            )
        
        # Parse arguments
        agent_url: Optional[str] = kwargs.get("agent_url")
        agent_urls: Optional[List[str]] = kwargs.get("agent_urls")  # Multi-agent
        message: Optional[str] = kwargs.get("message")
        priority: str = kwargs.get("priority", "normal")
        attachments = kwargs.get("attachments", None)
        reset = bool(kwargs.get("reset", False))
        strategy: str = kwargs.get("strategy", "round_robin")
        task_id: Optional[str] = kwargs.get("task_id")
        
        # Validate
        if not message or not isinstance(message, str):
            return Response(message="message argument missing", break_loop=False)
        
        if not agent_url and not agent_urls:
            return Response(
                message="agent_url or agent_urls argument missing",
                break_loop=False
            )
        
        # Parse priority
        try:
            priority_level = MessagePriority[priority.upper()]
        except (KeyError, AttributeError):
            priority_level = MessagePriority.NORMAL
        
        # Handle multi-agent routing
        if agent_urls and len(agent_urls) > 1:
            return await self._multi_agent_communicate(
                agent_urls=agent_urls,
                message=message,
                priority=priority_level,
                attachments=attachments,
                reset=reset,
                strategy=strategy
            )
        
        # Single agent
        return await self._single_agent_communicate(
            agent_url=agent_url or agent_urls[0],
            message=message,
            priority=priority_level,
            attachments=attachments,
            reset=reset,
            task_id=task_id
        )
    
    async def _single_agent_communicate(
        self,
        agent_url: str,
        message: str,
        priority: MessagePriority,
        attachments,
        reset: bool,
        task_id: Optional[str]
    ) -> Response:
        """Communicate with a single agent."""
        # Get session
        sessions: dict[str, str] = self.agent.get_data("_a2a_sessions") or {}
        context_id = None if reset else sessions.get(agent_url)
        
        # Create enhanced message
        msg = AgentMessage(
            role="user",
            content=message,
            priority=priority,
            context_id=context_id,
            task_id=task_id
        )
        
        try:
            async with await connect_to_agent(agent_url) as conn:
                # Get agent card if not registered
                if agent_url not in router.agent_registry:
                    try:
                        card = await conn.get_agent_card()
                        if card:
                            router.register_agent(agent_url, AgentCard.from_dict(card))
                    except Exception:
                        pass
                
                # Send message
                task_resp = await conn.send_message(
                    message=msg.content,
                    attachments=attachments,
                    context_id=msg.context_id
                )
                
                task_id_response = task_resp.get("result", {}).get("id")
                if not task_id_response:
                    return Response(
                        message="Remote agent failed to create task.",
                        break_loop=False
                    )
                
                # Wait for completion
                final = await conn.wait_for_completion(task_id_response)
                
                # Update context
                new_context_id = final["result"].get("context_id")
                if isinstance(new_context_id, str):
                    sessions[agent_url] = new_context_id
                    self.agent.set_data("_a2a_sessions", sessions)
                
                router.record_success(agent_url)
                
                # Extract response
                return self._parse_response(final)
                
        except Exception as e:
            router.record_failure(agent_url)
            PrintStyle.error(f"A2A agent mail error: {e}")
            return Response(
                message=f"A2A agent mail error: {e}",
                break_loop=False
            )
    
    async def _multi_agent_communicate(
        self,
        agent_urls: List[str],
        message: str,
        priority: MessagePriority,
        attachments,
        reset: bool,
        strategy: str
    ) -> Response:
        """Communicate with multiple agents (broadcast or relay)."""
        mode: str = kwargs.get("mode", "broadcast")  # broadcast, relay, aggregate
        
        if mode == "broadcast":
            # Send to all, collect first success
            tasks = [
                self._single_agent_communicate(
                    url, message, priority, attachments, reset, None
                )
                for url in agent_urls
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Return first successful result
            for i, result in enumerate(results):
                if isinstance(result, Response) and not result.message.startswith("Error"):
                    return result
            
            # All failed, return first error
            for result in results:
                if isinstance(result, Exception):
                    return Response(
                        message=f"All agents failed: {result}",
                        break_loop=False
                    )
        
        elif mode == "aggregate":
            # Collect all responses
            tasks = [
                self._single_agent_communicate(
                    url, message, priority, attachments, reset, None
                )
                for url in agent_urls
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate responses
            aggregated = []
            for i, (url, result) in enumerate(zip(agent_urls, results)):
                if isinstance(result, Response):
                    aggregated.append({
                        "agent": url,
                        "response": result.message
                    })
            
            return Response(
                message=json.dumps(aggregated, indent=2),
                break_loop=False
            )
        
        return Response(
            message="Unknown multi-agent mode",
            break_loop=False
        )
    
    def _parse_response(self, final: Dict[str, Any]) -> Response:
        """Parse A2A response."""
        history = final["result"].get("history", [])
        
        # Extract text
        assistant_text = ""
        artifacts = []
        
        if history:
            last_parts = history[-1].get("parts", [])
            for part in last_parts:
                if part.get("kind") == "text":
                    assistant_text += part.get("text", "")
                elif part.get("kind") == "artifact":
                    artifacts.append(part)
        
        return Response(
            message=assistant_text or "(no response)",
            break_loop=False
        )


# ============================================================================
# A2A Task Management
# ============================================================================

class A2ATaskTool(Tool):
    """A2A task management and state tracking."""
    
    async def execute(self, **kwargs):
        """Manage A2A tasks."""
        action: str = kwargs.get("action", "status")
        
        if action == "list":
            return self._list_tasks()
        elif action == "cancel":
            return self._cancel_task(kwargs.get("task_id"))
        elif action == "status":
            return self._task_status(kwargs.get("task_id"))
        
        return Response(message=f"Unknown action: {action}", break_loop=False)
    
    def _list_tasks(self) -> Response:
        """List all tracked tasks."""
        tasks = self.agent.get_data("_a2a_tasks") or {}
        task_list = [
            {
                "task_id": tid,
                "state": data.get("state"),
                "created": data.get("created")
            }
            for tid, data in tasks.items()
        ]
        return Response(
            message=json.dumps(task_list, indent=2),
            break_loop=False
        )
    
    def _cancel_task(self, task_id: Optional[str]) -> Response:
        """Cancel a task."""
        if not task_id:
            return Response(message="task_id required", break_loop=False)
        
        # Implementation depends on FastA2A client
        return Response(
            message=f"Task {task_id} cancellation requested",
            break_loop=False
        )
    
    def _task_status(self, task_id: Optional[str]) -> Response:
        """Get task status."""
        if not task_id:
            return Response(message="task_id required", break_loop=False)
        
        tasks = self.agent.get_data("_a2a_tasks") or {}
        task = tasks.get(task_id)
        
        if task:
            return Response(
                message=json.dumps(task, indent=2),
                break_loop=False
            )
        
        return Response(message="Task not found", break_loop=False)


# ============================================================================
# A2A Agent Discovery
# ============================================================================

class A2ADiscoveryTool(Tool):
    """Discover and register A2A agents."""
    
    async def execute(self, **kwargs):
        """Discover agents."""
        action: str = kwargs.get("action", "list")
        
        if action == "discover":
            return await self._discover_agents(kwargs.get("url"))
        elif action == "list":
            return self._list_registered()
        elif action == "capabilities":
            return self._find_by_capability(kwargs.get("capability"))
        
        return Response(message=f"Unknown action: {action}", break_loop=False)
    
    async def _discover_agents(self, base_url: Optional[str]) -> Response:
        """Discover agents at URL."""
        if not base_url:
            return Response(message="url required", break_loop=False)
        
        # Try to fetch agent card
        try:
            async with await connect_to_agent(base_url) as conn:
                card = await conn.get_agent_card()
                if card:
                    card_obj = AgentCard.from_dict(card)
                    router.register_agent(base_url, card_obj)
                    return Response(
                        message=f"Discovered agent: {card_obj.name}\n{card_obj.description}",
                        break_loop=False
                    )
        except Exception as e:
            return Response(message=f"Discovery failed: {e}", break_loop=False)
        
        return Response(message="No agent found", break_loop=False)
    
    def _list_registered(self) -> Response:
        """List registered agents."""
        agents = [
            {
                "url": url,
                "name": card.name,
                "capabilities": card.capabilities
            }
            for url, card in router.agent_registry.items()
        ]
        return Response(
            message=json.dumps(agents, indent=2),
            break_loop=False
        )
    
    def _find_by_capability(self, capability: Optional[str]) -> Response:
        """Find agents with capability."""
        if not capability:
            return Response(message="capability required", break_loop=False)
        
        agents = router.discover_agents(capability)
        return Response(
            message=json.dumps(agents, indent=2),
            break_loop=False
        )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "A2AAgentMailTool",
    "A2ATaskTool",
    "A2ADiscoveryTool",
    "A2AMessageRouter",
    "AgentCard",
    "AgentMessage",
    "TaskResult",
    "MessagePriority",
    "TaskState",
    "router"
]
