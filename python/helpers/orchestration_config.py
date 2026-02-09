"""
Orchestration Config Loader

Loads and validates conf/orchestration.yaml, providing typed dataclasses
for agent definitions, routing rules, recovery policies, and budget config.

Used by:
- Orchestrator agent profile extension
- Swarm dispatcher
- Dashboard APIs
- Cost tracker budget enforcement

Created: 2026-02-09
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional
from python.helpers.print_style import PrintStyle


# ─── Typed Dataclasses ───────────────────────────────────────

@dataclass
class AgentDef:
    id: str
    name: str
    role: str
    model: str
    fallback_model: str = ""
    port: int = 0
    profile: str = "default"
    execution_mode: str = "short_run"
    mail_address: str = ""


@dataclass
class RoutingRule:
    keywords: list[str] = field(default_factory=list)
    route_to: str = ""
    priority: int = 0


@dataclass 
class DurationRule:
    min_minutes: int = 0
    max_minutes: int = 0
    route_to: str = ""
    reason: str = ""


@dataclass
class BudgetConfig:
    monthly_cap_usd: float = 50.0
    per_agent_caps: dict[str, float] = field(default_factory=dict)
    free_tier_models: list[str] = field(default_factory=list)
    budget_exceeded_action: str = "downgrade"


@dataclass
class RecoveryPolicy:
    max_retries: int = 3
    backoff_ms: list[int] = field(default_factory=lambda: [1000, 2000, 4000])
    escalation_minutes: int = 5
    health_check_interval: int = 30


@dataclass
class LoopConfig:
    cycle_duration_seconds: int = 30
    perception_window_seconds: int = 10
    decision_window_seconds: int = 10
    action_window_seconds: int = 10
    max_concurrent_tasks: int = 5
    task_queue_path: str = "memory/agent_zero/task_queue.json"


@dataclass
class ChannelDef:
    name: str
    priority: int = 0  # 0=P0 mission critical, 1=P1 priority, 2=P2 personal, 3=P3 deferred
    voice_enabled: bool = False
    handler: str = ""


@dataclass
class OrchestrationConfig:
    agents: list[AgentDef] = field(default_factory=list)
    keyword_rules: list[RoutingRule] = field(default_factory=list)
    duration_rules: list[DurationRule] = field(default_factory=list)
    default_route: str = "MASTER"
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    recovery: RecoveryPolicy = field(default_factory=RecoveryPolicy)
    loop: LoopConfig = field(default_factory=LoopConfig)
    channels: list[ChannelDef] = field(default_factory=list)
    memory_domains: list[str] = field(default_factory=list)
    
    def get_agent(self, agent_id: str) -> Optional[AgentDef]:
        """Get agent definition by ID."""
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def get_agent_by_name(self, name: str) -> Optional[AgentDef]:
        """Get agent definition by name."""
        name_lower = name.lower()
        for agent in self.agents:
            if agent.name.lower() == name_lower:
                return agent
        return None
    
    def route_task(self, objective: str, estimated_minutes: int = 0) -> str:
        """
        Route a task to the appropriate agent using keyword + duration rules.
        Returns the agent ID.
        """
        objective_lower = objective.lower()
        
        # Check duration rules first (they override keywords)
        if estimated_minutes > 0:
            for rule in self.duration_rules:
                if rule.min_minutes and estimated_minutes >= rule.min_minutes:
                    return rule.route_to
                if rule.max_minutes and estimated_minutes <= rule.max_minutes:
                    return rule.route_to
        
        # Check keyword rules
        best_match = None
        best_priority = 999
        
        for rule in self.keyword_rules:
            for keyword in rule.keywords:
                if keyword in objective_lower:
                    if rule.priority < best_priority:
                        best_match = rule.route_to
                        best_priority = rule.priority
                    break
        
        return best_match or self.default_route


# ─── Config File Loader ──────────────────────────────────────

_cached_config: Optional[OrchestrationConfig] = None
CONFIG_PATH = os.path.join("conf", "orchestration.yaml")


def load_orchestration_config(force_reload: bool = False) -> OrchestrationConfig:
    """Load orchestration config from YAML file."""
    global _cached_config
    
    if _cached_config is not None and not force_reload:
        return _cached_config
    
    config = OrchestrationConfig()
    
    try:
        if not os.path.exists(CONFIG_PATH):
            PrintStyle.warning(f"Orchestration config not found at {CONFIG_PATH}, using defaults")
            _cached_config = config
            return config
        
        with open(CONFIG_PATH, 'r') as f:
            raw = yaml.safe_load(f)
        
        if not raw:
            _cached_config = config
            return config
        
        # Parse agents
        for agent_raw in raw.get("agents", []):
            config.agents.append(AgentDef(
                id=agent_raw.get("id", ""),
                name=agent_raw.get("name", ""),
                role=agent_raw.get("role", ""),
                model=agent_raw.get("model", ""),
                fallback_model=agent_raw.get("fallback_model", ""),
                port=agent_raw.get("port", 0),
                profile=agent_raw.get("profile", "default"),
                execution_mode=agent_raw.get("execution_mode", "short_run"),
                mail_address=agent_raw.get("mail_address", ""),
            ))
        
        # Parse routing
        routing = raw.get("routing", {})
        for rule_raw in routing.get("keyword_rules", []):
            config.keyword_rules.append(RoutingRule(
                keywords=rule_raw.get("keywords", []),
                route_to=rule_raw.get("route_to", ""),
                priority=rule_raw.get("priority", 0),
            ))
        
        for rule_raw in routing.get("duration_rules", []):
            config.duration_rules.append(DurationRule(
                min_minutes=rule_raw.get("min_minutes", 0),
                max_minutes=rule_raw.get("max_minutes", 0),
                route_to=rule_raw.get("route_to", ""),
                reason=rule_raw.get("reason", ""),
            ))
        
        config.default_route = routing.get("default_route", "MASTER")
        
        # Parse budget
        budget_raw = raw.get("budget", {})
        config.budget = BudgetConfig(
            monthly_cap_usd=budget_raw.get("monthly_cap_usd", 50.0),
            per_agent_caps=budget_raw.get("per_agent_caps", {}),
            free_tier_models=budget_raw.get("free_tier_models", []),
            budget_exceeded_action=budget_raw.get("budget_exceeded_action", "downgrade"),
        )
        
        # Parse recovery
        recovery_raw = raw.get("recovery", {})
        escalation = recovery_raw.get("escalation", {})
        config.recovery = RecoveryPolicy(
            max_retries=recovery_raw.get("max_retries", 3),
            backoff_ms=recovery_raw.get("backoff_ms", [1000, 2000, 4000]),
            escalation_minutes=escalation.get("degraded_to_critical_minutes", 5),
            health_check_interval=recovery_raw.get("health_check", {}).get("interval_seconds", 30),
        )
        
        # Parse loop
        loop_raw = raw.get("loop", {})
        config.loop = LoopConfig(
            cycle_duration_seconds=loop_raw.get("cycle_duration_seconds", 30),
            perception_window_seconds=loop_raw.get("perception_window_seconds", 10),
            decision_window_seconds=loop_raw.get("decision_window_seconds", 10),
            action_window_seconds=loop_raw.get("action_window_seconds", 10),
            max_concurrent_tasks=loop_raw.get("max_concurrent_tasks", 5),
            task_queue_path=loop_raw.get("task_queue_path", "memory/agent_zero/task_queue.json"),
        )
        
        # Parse channels
        channels_raw = raw.get("channels", {})
        for ch in channels_raw.get("mission_critical", []):
            config.channels.append(ChannelDef(
                name=ch.get("name", ""), priority=0,
                voice_enabled=ch.get("voice_enabled", False),
                handler=ch.get("handler", ""),
            ))
        for ch in channels_raw.get("priority", []):
            config.channels.append(ChannelDef(
                name=ch.get("name", ""), priority=1,
                voice_enabled=ch.get("voice_enabled", False),
            ))
        for ch in channels_raw.get("personal", []):
            config.channels.append(ChannelDef(
                name=ch.get("name", ""), priority=2,
                voice_enabled=ch.get("voice_enabled", False),
            ))
        for ch_name in channels_raw.get("deferred", []):
            if isinstance(ch_name, str):
                config.channels.append(ChannelDef(name=ch_name, priority=3))
        
        # Parse memory domains
        config.memory_domains = raw.get("memory_domains", [])
        
        _cached_config = config
        return config
        
    except Exception as e:
        PrintStyle.error(f"Failed to load orchestration config: {e}")
        _cached_config = config
        return config


def get_config() -> OrchestrationConfig:
    """Convenience shorthand."""
    return load_orchestration_config()
