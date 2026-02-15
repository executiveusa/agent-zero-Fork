"""
A2A Protocol Integration for Agent Zero
Enables agent-to-agent communication without human relay
"""

import os
import json
import uuid
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum


class AgentRole(Enum):
    """Role of the agent in communication"""
    INITIATOR = "initiator"
    RESPONDER = "responder"
    COORDINATOR = "coordinator"
    OBSERVER = "observer"


class MessageStatus(Enum):
    """Status of a message"""
    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    RESPONDED = "responded"


@dataclass
class AgentCard:
    """Agent discovery card - describes an agent's capabilities"""
    agent_id: str
    name: str
    description: str
    role: AgentRole
    capabilities: List[str]
    endpoints: Dict[str, str]
    status: str = "active"
    last_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "role": self.role.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        data["role"] = AgentRole(data["role"])
        return cls(**data)


@dataclass
class A2AMessage:
    """A message between agents"""
    message_id: str
    conversation_id: str
    from_agent: str
    to_agent: str
    content: str
    status: MessageStatus
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "status": self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        data["status"] = MessageStatus(data["status"])
        return cls(**data)


@dataclass
class Conversation:
    """A conversation between agents"""
    conversation_id: str
    participants: List[str]
    messages: List[A2AMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    topic: str = ""
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "participants": self.participants,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "topic": self.topic,
            "status": self.status
        }


class A2AServer:
    """
    A2A Server for Agent Zero
    Allows other agents to discover and communicate with this agent
    """
    
    def __init__(self, agent_card: AgentCard, port: int = 8080):
        self.agent_card = agent_card
        self.port = port
        self.conversations: Dict[str, Conversation] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler
        
    async def handle_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Handle an incoming message"""
        # Add to conversation
        if message.conversation_id not in self.conversations:
            self.conversations[message.conversation_id] = Conversation(
                conversation_id=message.conversation_id,
                participants=[message.from_agent, message.to_agent]
            )
        
        self.conversations[message.conversation_id].messages.append(message)
        
        # Update status
        message.status = MessageStatus.DELIVERED
        
        # Call handler if exists
        message_type = message.metadata.get("type", "default")
        if message_type in self.message_handlers:
            response = await self.message_handlers[message_type](message)
            if response:
                return response
                
        return None
    
    async def send_response(
        self,
        conversation_id: str,
        to_agent: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> A2AMessage:
        """Send a response message"""
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            from_agent=self.agent_card.agent_id,
            to_agent=to_agent,
            content=content,
            status=MessageStatus.PENDING,
            metadata=metadata or {}
        )
        
        if conversation_id in self.conversations:
            self.conversations[conversation_id].messages.append(message)
            
        return message
    
    def get_agent_card(self) -> Dict[str, Any]:
        """Return the agent card for discovery"""
        return self.agent_card.to_dict()
    
    def get_conversation_history(self, conversation_id: str) -> List[A2AMessage]:
        """Get the message history for a conversation"""
        if conversation_id in self.conversations:
            return self.conversations[conversation_id].messages
        return []


class A2AClient:
    """
    A2A Client for Agent Zero
    Allows this agent to discover and communicate with other agents
    """
    
    def __init__(self, agent_card: AgentCard):
        self.agent_card = agent_card
        self.discovered_agents: Dict[str, AgentCard] = {}
        self.conversations: Dict[str, Conversation] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def discover_agent(self, agent_url: str) -> Optional[AgentCard]:
        """Discover an agent via its Agent Card endpoint"""
        try:
            async with self.session.get(f"{agent_url}/.well-known/agent.json") as response:
                if response.status == 200:
                    data = await response.json()
                    agent_card = AgentCard.from_dict(data)
                    self.discovered_agents[agent_card.agent_id] = agent_card
                    return agent_card
        except Exception as e:
            print(f"Discovery failed: {e}")
        return None
    
    async def send_message(
        self,
        to_agent_id: str,
        content: str,
        conversation_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> A2AMessage:
        """Send a message to another agent"""
        
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            from_agent=self.agent_card.agent_id,
            to_agent=to_agent_id,
            content=content,
            status=MessageStatus.PENDING,
            metadata=metadata or {}
        )
        
        # Store in conversation
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(
                conversation_id=conversation_id,
                participants=[self.agent_card.agent_id, to_agent_id]
            )
        self.conversations[conversation_id].messages.append(message)
        
        # Send via JSON-RPC 2.0
        if to_agent_id in self.discovered_agents:
            agent = self.discovered_agents[to_agent_id]
            endpoint = agent.endpoints.get("a2a", "")
            
            if endpoint and self.session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "params": message.to_dict(),
                    "id": str(uuid.uuid4())
                }
                
                try:
                    async with self.session.post(
                        endpoint,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            message.status = MessageStatus.DELIVERED
                except Exception as e:
                    print(f"Send failed: {e}")
                    
        return message
    
    async def start_conversation(
        self,
        to_agent_id: str,
        topic: str,
        initial_message: str
    ) -> Conversation:
        """Start a new conversation with another agent"""
        conversation_id = str(uuid.uuid4())
        
        conversation = Conversation(
            conversation_id=conversation_id,
            participants=[self.agent_card.agent_id, to_agent_id],
            topic=topic
        )
        
        self.conversations[conversation_id] = conversation
        
        # Send initial message
        message = await self.send_message(
            to_agent_id=to_agent_id,
            content=initial_message,
            conversation_id=conversation_id,
            metadata={"type": "conversation_start", "topic": topic}
        )
        
        conversation.messages.append(message)
        
        return conversation


# Pre-defined agent cards for BambuVerse
def get_bambu_agent_card() -> AgentCard:
    """Get Bambu's agent card"""
    return AgentCard(
        agent_id="bambu-executiveusa",
        name="Bambu",
        description="CEO & Founder of BambuVerse. GitHub Agent Secretary.",
        role=AgentRole.COORDINATOR,
        capabilities=[
            "repo_analysis",
            "prd_generation",
            "deployment_management",
            "agent_coordination"
        ],
        endpoints={
            "a2a": "https://bambu.example.com/a2a",
            "agent_card": "https://bambu.example.com/.well-known/agent.json"
        }
    )


def get_alex_agent_card() -> AgentCard:
    """Get Alex's agent card"""
    return AgentCard(
        agent_id="alex-metagpt",
        name="Alex",
        description="MetaGPT-powered developer agent for collaborative development.",
        role=AgentRole.RESPONDER,
        capabilities=[
            "code_writing",
            "architecture_design",
            "documentation",
            "testing"
        ],
        endpoints={
            "a2a": "https://alex.example.com/a2a",
            "agent_card": "https://alex.example.com/.well-known/agent.json"
        }
    )


def get_devika_agent_card() -> AgentCard:
    """Get Devika's agent card"""
    return AgentCard(
        agent_id="devika-agent",
        name="Devika",
        description="Agentic AI Software Engineer for autonomous development.",
        role=AgentRole.RESPONDER,
        capabilities=[
            "code_generation",
            "project_planning",
            "web_browsing",
            "code_execution"
        ],
        endpoints={
            "a2a": "https://devika.example.com/a2a",
            "agent_card": "https://devika.example.com/.well-known/agent.json"
        }
    )


def get_pauli_agent_card() -> AgentCard:
    """Get Pauli's agent card"""
    return AgentCard(
        agent_id="pauli-planner",
        name="Pauli",
        description="Planning and coordination agent for BambuVerse.",
        role=AgentRole.COORDINATOR,
        capabilities=[
            "task_planning",
            "resource_allocation",
            "agent_coordination",
            "monitoring"
        ],
        endpoints={
            "a2a": "https://pauli.example.com/a2a",
            "agent_card": "https://pauli.example.com/.well-known/agent.json"
        }
    )


def get_synthia_agent_card() -> AgentCard:
    """Get Synthia's agent card"""
    return AgentCard(
        agent_id="synthia-executor",
        name="Synthia",
        description="Execution and implementation agent for BambuVerse.",
        role=AgentRole.RESPONDER,
        capabilities=[
            "task_execution",
            "deployment",
            "api_integration",
            "monitoring"
        ],
        endpoints={
            "a2a": "https://synthia.example.com/a2a",
            "agent_card": "https://synthia.example.com/.well-known/agent.json"
        }
    )


# Convenience function for agent communication
async def connect_agents(agent_a: AgentCard, agent_b: AgentCard, topic: str, message: str) -> Conversation:
    """Connect two agents and start a conversation"""
    async with A2AClient(agent_a) as client:
        client.discovered_agents[agent_b.agent_id] = agent_b
        conversation = await client.start_conversation(
            to_agent_id=agent_b.agent_id,
            topic=topic,
            initial_message=message
        )
        return conversation


def main():
    """Test the A2A integration"""
    print("A2A Protocol Integration for Agent Zero")
    print("=" * 50)
    
    # Show agent cards
    agents = [
        get_bambu_agent_card(),
        get_alex_agent_card(),
        get_devika_agent_card(),
        get_pauli_agent_card(),
        get_synthia_agent_card()
    ]
    
    for agent in agents:
        print(f"\n{agent.name} ({agent.agent_id}):")
        print(f"  Role: {agent.role.value}")
        print(f"  Capabilities: {', '.join(agent.capabilities)}")
    
    print("\nA2A Protocol ready for agent-to-agent communication!")


if __name__ == "__main__":
    main()