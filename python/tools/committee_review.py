"""Committee Code Review - Multi-Model Verification (Zenflow Pattern)

Implements Zenflow's "Committee Approach" where different models review
each other's code to eliminate blind spots and catch errors.

Actions
-------
review_code    - Review code using opposing model
review_spec    - Review specification using different model
review_design  - Review architecture using different model

Environment
-----------
COMMITTEE_REVIEW_ENABLED  - Enable multi-model review (default: true)
PRIMARY_MODEL             - Model used for generation
REVIEW_MODEL             - Model used for review (auto if not set)
"""

import os
from typing import Dict, Optional


class CommitteeReview:
    def __init__(self) -> None:
        self.enabled = os.getenv("COMMITTEE_REVIEW_ENABLED", "true").lower() == "true"
        self.primary_model = os.getenv("PRIMARY_MODEL", "claude-sonnet-4-5-20250929")
        self.review_model = os.getenv("REVIEW_MODEL", "auto")

        # Model opposition matrix (Zenflow pattern)
        self.opposition_map = {
            # Claude models → Use Gemini for review
            "claude-opus-4-5": "gemini-2.0-flash",
            "claude-sonnet-4-5": "gpt-4-turbo",
            "claude-sonnet-4-5-20250929": "gemini-2.0-flash",

            # GPT models → Use Claude for review
            "gpt-4-turbo": "claude-sonnet-4-5-20250929",
            "gpt-4o": "claude-sonnet-4-5-20250929",
            "gpt-4": "claude-opus-4-5",

            # Gemini models → Use Claude for review
            "gemini-2.0-flash": "claude-sonnet-4-5-20250929",
            "gemini-1.5-pro": "claude-opus-4-5",
            "gemini-exp-1206": "claude-opus-4-5",

            # Venice models → Use Claude for review
            "llama-3.3-70b": "claude-sonnet-4-5-20250929",
        }

    def get_opposing_model(self, primary_model: str) -> str:
        """Get the best opposing model for review"""
        if self.review_model != "auto":
            return self.review_model

        # Find exact match first
        if primary_model in self.opposition_map:
            return self.opposition_map[primary_model]

        # Fallback: Detect model family and return opposite
        if "claude" in primary_model.lower():
            return "gemini-2.0-flash"
        elif "gpt" in primary_model.lower() or "openai" in primary_model.lower():
            return "claude-sonnet-4-5-20250929"
        elif "gemini" in primary_model.lower():
            return "claude-sonnet-4-5-20250929"
        else:
            # Default opposition: Use Claude
            return "claude-sonnet-4-5-20250929"

    def review_code(
        self,
        code: str,
        language: str,
        primary_model: str,
        context: Optional[str] = None
    ) -> dict:
        """
        Review code using opposing model (Zenflow Committee pattern)

        Returns issues found, severity, and approval status
        """
        if not self.enabled:
            return {"success": True, "committee_review": "disabled", "approved": True}

        reviewer_model = self.get_opposing_model(primary_model)

        review_prompt = f"""You are a senior code reviewer conducting a COMMITTEE REVIEW.

The code below was written by {primary_model}. Your job is to find issues that model might have missed.

Code Language: {language}

{f"Context: {context}" if context else ""}

CODE TO REVIEW:
```{language}
{code}
```

Review for:
1. **Bugs** - Logic errors, edge cases, null handling
2. **Security** - SQL injection, XSS, exposed secrets, auth bypass
3. **Performance** - N+1 queries, memory leaks, inefficient algorithms
4. **Best Practices** - Code style, naming, error handling
5. **Blind Spots** - Issues {primary_model} typically misses

Output JSON:
{{
    "approved": true/false,
    "severity": "critical" | "major" | "minor" | "none",
    "issues": [
        {{"line": X, "type": "bug", "description": "...", "suggestion": "..."}}
    ],
    "summary": "Overall assessment"
}}
"""

        # This would normally call the agent's model interface
        # For now, return structure that Super Orchestrator can use
        return {
            "success": True,
            "primary_model": primary_model,
            "reviewer_model": reviewer_model,
            "review_prompt": review_prompt,
            "committee_review": "ready",
            "message": f"Code review by {reviewer_model} (opposing {primary_model}) is ready. Use this prompt with the reviewer model."
        }

    def review_spec(
        self,
        spec: str,
        primary_model: str,
        requirements: Optional[str] = None
    ) -> dict:
        """Review technical specification using opposing model"""
        if not self.enabled:
            return {"success": True, "committee_review": "disabled", "approved": True}

        reviewer_model = self.get_opposing_model(primary_model)

        review_prompt = f"""You are a senior architect conducting a SPEC REVIEW.

The specification below was written by {primary_model}. Your job is to find gaps that model might have missed.

{f"Original Requirements: {requirements}" if requirements else ""}

SPECIFICATION TO REVIEW:
{spec}

Review for:
1. **Completeness** - Missing requirements, edge cases, error scenarios
2. **Clarity** - Ambiguous descriptions, missing details
3. **Feasibility** - Unrealistic timelines, impossible requirements
4. **Security** - Missing auth, encryption, data protection
5. **Architecture** - Scalability, maintainability, testability

Output JSON:
{{
    "approved": true/false,
    "severity": "critical" | "major" | "minor" | "none",
    "gaps": [
        {{"section": "X", "issue": "...", "recommendation": "..."}}
    ],
    "summary": "Overall assessment"
}}
"""

        return {
            "success": True,
            "primary_model": primary_model,
            "reviewer_model": reviewer_model,
            "review_prompt": review_prompt,
            "committee_review": "ready"
        }

    def review_design(
        self,
        design: str,
        primary_model: str,
        requirements: Optional[str] = None
    ) -> dict:
        """Review architecture/design using opposing model"""
        if not self.enabled:
            return {"success": True, "committee_review": "disabled", "approved": True}

        reviewer_model = self.get_opposing_model(primary_model)

        review_prompt = f"""You are a principal engineer conducting an ARCHITECTURE REVIEW.

The design below was created by {primary_model}. Your job is to find architectural issues that model might have missed.

{f"Requirements: {requirements}" if requirements else ""}

DESIGN TO REVIEW:
{design}

Review for:
1. **Scalability** - Bottlenecks, single points of failure
2. **Security** - Attack surface, data flow vulnerabilities
3. **Maintainability** - Complexity, coupling, technical debt
4. **Performance** - Latency, throughput, resource usage
5. **Trade-offs** - Alternative approaches, pros/cons

Output JSON:
{{
    "approved": true/false,
    "risk_level": "high" | "medium" | "low",
    "concerns": [
        {{"area": "X", "risk": "...", "mitigation": "..."}}
    ],
    "recommendations": ["..."],
    "summary": "Overall assessment"
}}
"""

        return {
            "success": True,
            "primary_model": primary_model,
            "reviewer_model": reviewer_model,
            "review_prompt": review_prompt,
            "committee_review": "ready"
        }


def process_tool(tool_input: dict) -> dict:
    """Process committee review actions"""
    committee = CommitteeReview()

    action = tool_input.get("action", "")

    try:
        if action == "review_code":
            return committee.review_code(
                code=tool_input["code"],
                language=tool_input.get("language", "python"),
                primary_model=tool_input.get("primary_model", "claude-sonnet-4-5-20250929"),
                context=tool_input.get("context")
            )

        elif action == "review_spec":
            return committee.review_spec(
                spec=tool_input["spec"],
                primary_model=tool_input.get("primary_model", "claude-sonnet-4-5-20250929"),
                requirements=tool_input.get("requirements")
            )

        elif action == "review_design":
            return committee.review_design(
                design=tool_input["design"],
                primary_model=tool_input.get("primary_model", "claude-sonnet-4-5-20250929"),
                requirements=tool_input.get("requirements")
            )

        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": ["review_code", "review_spec", "review_design"]
            }

    except Exception as e:
        return {"success": False, "error": str(e)}
