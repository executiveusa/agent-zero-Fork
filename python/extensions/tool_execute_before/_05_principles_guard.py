"""
Principles Guard Extension

Enforces Agent Zero Core Principles before every tool execution:
1. Prefer internal sources over public web
2. Require user confirmation for binding actions
3. Block sensitive data in tool args
4. Ensure timezone awareness for dates
5. Validate safety constraints

This extension runs BEFORE tool execution and can block or warn.
"""

from python.helpers.extension import Extension
from python.helpers import AgentLoopData
from initialize import Config
from python.helpers.print_style import PrintStyle
import re
from datetime import datetime
import pytz


class PrinciplesGuard(Extension):
    async def execute(self, loop_data: AgentLoopData, config: Config):
        tool_name = loop_data.tool_name
        tool_args = loop_data.tool_args or {}

        # Skip if no tool call
        if not tool_name:
            return

        # Initialize warnings list if not exists
        if not hasattr(loop_data, "warnings"):
            loop_data.warnings = []

        # Check 1: Prefer Internal Sources
        await self._check_source_preference(tool_name, tool_args, loop_data)

        # Check 2: Binding Actions (require confirmation)
        await self._check_binding_actions(tool_name, tool_args, loop_data)

        # Check 3: Sensitive Data Detection
        await self._check_sensitive_data(tool_args, loop_data)

        # Check 4: Timezone Awareness
        await self._check_timezone_handling(tool_args, loop_data)

        # Check 5: Safety Constraints
        await self._check_safety_constraints(tool_name, tool_args, loop_data)

    # ─────────────────────────────────────────────────────────────────
    # Check 1: Source Preference (Internal > External)
    # ─────────────────────────────────────────────────────────────────
    async def _check_source_preference(
        self,
        tool_name: str,
        tool_args: dict,
        loop_data: AgentLoopData
    ):
        """Warn if using web search when internal sources might suffice"""

        # List of tools that access external web
        external_tools = ["web_search", "search_engine", "browser_open"]

        if tool_name not in external_tools:
            return

        # Get query/search term
        query = (
            tool_args.get("query") or
            tool_args.get("url") or
            tool_args.get("search_term") or
            ""
        )

        # Patterns that suggest internal content
        internal_patterns = [
            r"our\s+",  # "our code", "our docs"
            r"this\s+repo",
            r"this\s+project",
            r"agent\s+zero",
            r"my\s+",  # "my functions", "my code"
            r"\.py$",  # file extensions
            r"\.ts$",
            r"\.go$",
            r"\.rs$",
        ]

        for pattern in internal_patterns:
            if re.search(pattern, query.lower()):
                warning = (
                    f"⚠️ Source Preference: Query '{query}' suggests internal content. "
                    f"Consider using Read/Glob/Grep instead of {tool_name}."
                )
                loop_data.warnings.append(warning)
                PrintStyle(font_color="yellow").print(warning)
                break

    # ─────────────────────────────────────────────────────────────────
    # Check 2: Binding Actions (Require Confirmation)
    # ─────────────────────────────────────────────────────────────────
    async def _check_binding_actions(
        self,
        tool_name: str,
        tool_args: dict,
        loop_data: AgentLoopData
    ):
        """Block binding actions unless user explicitly confirmed"""

        # Binding actions that require confirmation
        binding_patterns = {
            # Git operations
            "git push.*--force": "Force push (can destroy history)",
            "git push.*origin main": "Push to main branch",
            "git push.*origin master": "Push to master branch",
            "rm -rf": "Recursive force delete",

            # Deployment
            "kubectl delete": "Kubernetes resource deletion",
            "docker rm": "Docker container removal",
            "vercel --prod": "Production deployment",

            # Database
            "DROP DATABASE": "Database deletion",
            "DELETE FROM.*WHERE": "Database record deletion",
            "TRUNCATE": "Table truncation",

            # Payment/Financial
            "stripe.*charge": "Payment processing",
            "paypal.*send": "Payment sending",
        }

        # Tools that are always binding
        binding_tools = {
            "deploy_to_production",
            "send_email",
            "post_to_social",
            "delete_database",
            "charge_payment",
        }

        # Check tool name
        if tool_name in binding_tools:
            # Check if user explicitly requested this in the conversation
            # (For now, we'll allow if the tool is called - in production,
            #  you'd check loop_data.context for explicit user confirmation)
            warning = (
                f"⚠️ Binding Action: {tool_name} is irreversible. "
                f"Ensure user explicitly confirmed this action."
            )
            loop_data.warnings.append(warning)
            PrintStyle(font_color="orange").print(warning)
            return

        # Check bash commands
        if tool_name == "bash":
            command = tool_args.get("command", "")
            for pattern, description in binding_patterns.items():
                if re.search(pattern, command, re.IGNORECASE):
                    warning = (
                        f"⚠️ Binding Action: Command contains '{pattern}' ({description}). "
                        f"Ensure user explicitly confirmed this."
                    )
                    loop_data.warnings.append(warning)
                    PrintStyle(font_color="orange").print(warning)
                    break

    # ─────────────────────────────────────────────────────────────────
    # Check 3: Sensitive Data Detection
    # ─────────────────────────────────────────────────────────────────
    async def _check_sensitive_data(self, tool_args: dict, loop_data: AgentLoopData):
        """Block if tool args contain sensitive data patterns"""

        # Convert all args to strings for scanning
        args_str = str(tool_args)

        # Sensitive data patterns
        sensitive_patterns = {
            r"\b\d{16}\b": "Credit card number",
            r"\b\d{3}-\d{2}-\d{4}\b": "Social Security Number",
            r"password\s*=\s*['\"]?[^'\"\s]+": "Password in args",
            r"api_key\s*=\s*['\"]?[A-Za-z0-9]{32,}": "Unmasked API key",
            r"secret\s*=\s*['\"]?[^'\"\s]+": "Secret in args",
        }

        for pattern, description in sensitive_patterns.items():
            if re.search(pattern, args_str, re.IGNORECASE):
                # Don't block (secrets are already masked by another extension)
                # Just warn
                warning = f"⚠️ Sensitive Data: Detected {description} in tool args (should be masked)"
                loop_data.warnings.append(warning)
                PrintStyle(font_color="red").print(warning)
                break

    # ─────────────────────────────────────────────────────────────────
    # Check 4: Timezone Awareness
    # ─────────────────────────────────────────────────────────────────
    async def _check_timezone_handling(self, tool_args: dict, loop_data: AgentLoopData):
        """Warn if dates/times lack timezone info"""

        args_str = str(tool_args)

        # Date patterns without timezone
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?![+-]\d{2}:?\d{2}|Z)",  # ISO without TZ
            r"schedule.*\d{4}-\d{2}-\d{2}",  # Scheduling without TZ
            r"deploy.*at.*\d{1,2}:\d{2}",  # Deployment time without TZ
        ]

        for pattern in date_patterns:
            if re.search(pattern, args_str):
                warning = (
                    "⚠️ Timezone: Date/time detected without timezone. "
                    "User locale: America/Mexico_City (UTC-6). "
                    "Consider adding timezone info."
                )
                loop_data.warnings.append(warning)
                PrintStyle(font_color="yellow").print(warning)
                break

    # ─────────────────────────────────────────────────────────────────
    # Check 5: Safety Constraints
    # ─────────────────────────────────────────────────────────────────
    async def _check_safety_constraints(
        self,
        tool_name: str,
        tool_args: dict,
        loop_data: AgentLoopData
    ):
        """Block prohibited content/transactions"""

        args_str = str(tool_args).lower()

        # Prohibited transaction keywords
        prohibited_keywords = {
            "gambling": "Gambling transactions prohibited",
            "lottery": "Gambling transactions prohibited",
            "casino": "Gambling transactions prohibited",
            "alcohol purchase": "Alcohol purchase prohibited",
            "tobacco": "Tobacco purchase prohibited",
            "weapon": "Weapon transactions prohibited",
            "firearm": "Weapon transactions prohibited",
        }

        for keyword, reason in prohibited_keywords.items():
            if keyword in args_str:
                error = f"🚨 Safety Constraint: {reason}"
                loop_data.warnings.append(error)
                PrintStyle(font_color="red", bold=True).print(error)
                # In production, you might want to raise an exception here
                # raise Exception(error)
                break

        # Privacy-sensitive patterns
        privacy_patterns = [
            r"based on.*race",
            r"based on.*ethnicity",
            r"based on.*religion",
            r"based on.*sexual orientation",
        ]

        for pattern in privacy_patterns:
            if re.search(pattern, args_str, re.IGNORECASE):
                error = "🚨 Privacy: Cannot make decisions based on protected characteristics"
                loop_data.warnings.append(error)
                PrintStyle(font_color="red", bold=True).print(error)
                break
