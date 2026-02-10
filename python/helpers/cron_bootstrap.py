"""
Cron Bootstrap — Auto-register recurring tasks at Agent Zero startup.

Registers the following cron jobs into the existing TaskScheduler:
1. Morning Briefing    — 7:00 AM daily
2. Memory Compaction   — 3:00 AM daily
3. Health Check        — Every 15 minutes
4. Channel Sync        — Every 30 minutes
5. Backup Snapshot     — 2:00 AM daily

Uses the existing TaskScheduler from python/helpers/task_scheduler.py.
Called from initialize.py during startup.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def bootstrap_crons(timezone: str = "America/Los_Angeles") -> int:
    """
    Register default cron jobs if they don't already exist.

    Args:
        timezone: Default timezone for scheduled tasks

    Returns:
        Number of newly registered cron jobs
    """
    try:
        from python.helpers.task_scheduler import (
            TaskScheduler,
            ScheduledTask,
            TaskSchedule,
        )
    except ImportError as e:
        logger.error(f"Cannot import TaskScheduler: {e}")
        return 0

    scheduler = TaskScheduler.get()
    registered = 0

    cron_definitions = [
        # ── Security cron jobs ────────────────────────────────
        {
            "name": "security_vault_audit",
            "system_prompt": (
                "You are the Agent Claw security officer. Run a vault "
                "health audit and report any issues found."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="*/6",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Run security_agent:vault with action audit. "
                "Check for env leaks, unvaulted secrets, and master key status. "
                "Log any issues and alert if security score drops below 80."
            ),
        },
        {
            "name": "security_secret_scan",
            "system_prompt": (
                "You are the Agent Claw security officer. Scan the codebase "
                "for accidentally committed secrets and credentials."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="4",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Run security_agent:scan on the project root. "
                "Report any leaked API keys, passwords, tokens, or "
                "hardcoded credentials found in source files."
            ),
        },
        {
            "name": "security_full_report",
            "system_prompt": (
                "You are the Agent Claw security officer. Generate a full "
                "security audit report covering all security domains."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="6",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Run security_agent:report to generate a comprehensive "
                "security report. Include vault status, secret scan results, "
                ".gitignore coverage, and dependency check. Save results to memory."
            ),
        },
        {
            "name": "security_rotation_check",
            "system_prompt": (
                "You are the Agent Claw security officer. Check if any "
                "vault secrets are past their rotation window."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="5",
                day="*",
                month="*",
                weekday="0",
                timezone=timezone,
            ),
            "prompt": (
                "Run security_agent:rotate with max_age_days 90. "
                "Report any secrets older than 90 days that need rotation. "
                "Alert the user if critical keys (API keys, tokens) are stale."
            ),
        },
        # ── Original cron jobs ────────────────────────────────
        {
            "name": "morning_briefing",
            "system_prompt": (
                "Generate a morning briefing for the user. Include: "
                "pending tasks, unread messages across platforms, "
                "calendar events, and weather. Keep it concise."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="7",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Run the morning briefing: check all messaging channels, "
                "summarize unread messages, list today's tasks, and "
                "deliver via voice notification if available."
            ),
        },
        {
            "name": "memory_compaction",
            "system_prompt": (
                "Perform memory maintenance. Compress old conversation "
                "fragments, deduplicate knowledge entries, and archive "
                "stale data beyond 30 days."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="3",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Run memory compaction: deduplicate embeddings, "
                "archive conversations older than 30 days, "
                "and generate a compaction report."
            ),
        },
        {
            "name": "health_check",
            "system_prompt": (
                "Check system health: Docker container status, "
                "API connectivity (Venice, ElevenLabs, OpenClaw), "
                "memory usage, and disk space."
            ),
            "schedule": TaskSchedule(
                minute="*/15",
                hour="*",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Run health check: verify all services are responsive, "
                "check Docker containers, API endpoints, and resource usage. "
                "Log results and alert on failures."
            ),
        },
        {
            "name": "channel_sync",
            "system_prompt": (
                "Sync messaging channels via OpenClaw. Pull unread messages "
                "from all connected platforms and update conversation state."
            ),
            "schedule": TaskSchedule(
                minute="*/30",
                hour="*",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Sync all OpenClaw messaging channels. Pull unread messages "
                "from WhatsApp, Telegram, Discord, Slack. Update internal "
                "conversation state and flag items needing attention."
            ),
        },
        {
            "name": "backup_snapshot",
            "system_prompt": (
                "Create a backup snapshot of critical data: memory DB, "
                "task scheduler state, conversation history, and configs."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="2",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Create backup snapshot: export memory database, "
                "scheduler state, conversation logs, and config files "
                "to the backup directory. Rotate old backups (keep 7 days)."
            ),
        },
        # ── Agent Meeting cron jobs ───────────────────────────
        {
            "name": "daily_standup",
            "system_prompt": (
                "You are Agent Zero, the CEO. Convene the daily standup meeting. "
                "Use agent_meeting:convene with type=daily_standup. Then have each "
                "core team member (SYNTHIA, Security Officer, Dev Lead, Growth Hacker) "
                "report their status via agent_meeting:discuss. Record any decisions "
                "via agent_meeting:decide. Finally, generate minutes with agent_meeting:minutes."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="9",
                day="*",
                month="*",
                weekday="1-5",
                timezone=timezone,
            ),
            "prompt": (
                "Run the daily standup meeting:\n"
                "1. Use agent_meeting:convene with type='daily_standup', topic='Daily Standup'\n"
                "2. For each agent (synthia, security_officer, dev_lead, growth_hacker), "
                "use call_subordinate to ask for their status update, then log it with "
                "agent_meeting:discuss\n"
                "3. Record any decisions with agent_meeting:decide\n"
                "4. Generate and store minutes with agent_meeting:minutes\n"
                "5. Check beads_tool:ready for outstanding tasks and assign as needed"
            ),
        },
        {
            "name": "weekly_strategy_meeting",
            "system_prompt": (
                "You are Agent Zero, the CEO. Convene the weekly strategy meeting. "
                "Review revenue metrics, security posture, sprint progress, and growth. "
                "Make strategic decisions aligned with the $100M goal."
            ),
            "schedule": TaskSchedule(
                minute="0",
                hour="10",
                day="*",
                month="*",
                weekday="1",
                timezone=timezone,
            ),
            "prompt": (
                "Run the weekly strategy meeting:\n"
                "1. Use agent_meeting:convene with type='weekly_strategy', "
                "topic='Weekly Strategy Review'\n"
                "2. SYNTHIA: Revenue dashboard review and pipeline update\n"
                "3. Security Officer: Security posture report and vault audit results\n"
                "4. Dev Lead: Sprint progress, tech debt, and deployment status\n"
                "5. Growth Hacker: Growth metrics, experiments, and content performance\n"
                "6. Agent Zero: Strategic decisions and resource allocation\n"
                "7. Create beads tasks for all action items\n"
                "8. Generate minutes and sync to Notion via agent_meeting:minutes"
            ),
        },
        {
            "name": "notion_meeting_sync",
            "system_prompt": (
                "Sync recent meeting data to Notion workspace. Check for any "
                "unsynced meetings and push them to the Meeting DB."
            ),
            "schedule": TaskSchedule(
                minute="*/30",
                hour="*",
                day="*",
                month="*",
                weekday="*",
                timezone=timezone,
            ),
            "prompt": (
                "Check tmp/meetings/ for any meetings not yet synced to Notion. "
                "For each unsynced meeting, use notion_integration to create a page "
                "in the Meeting DB. Update the meeting JSON with the Notion page_id "
                "once synced. Also check MCP Agent Mail inbox for any unread messages "
                "that need attention."
            ),
        },
    ]

    for cron_def in cron_definitions:
        name = cron_def["name"]

        # Check if task already exists
        existing = scheduler.find_task_by_name(name)
        if existing:
            logger.debug(f"Cron '{name}' already registered, skipping")
            continue

        try:
            task = ScheduledTask(
                name=name,
                system_prompt=cron_def["system_prompt"],
                prompt=cron_def["prompt"],
                schedule=cron_def["schedule"],
            )
            await scheduler.add_task(task)
            registered += 1
            logger.info(f"Registered cron: {name}")
        except Exception as e:
            logger.error(f"Failed to register cron '{name}': {e}")

    if registered > 0:
        await scheduler.save()
        logger.info(f"Bootstrap complete: {registered} new cron jobs registered")
    else:
        logger.debug("Bootstrap complete: no new cron jobs needed")

    return registered
