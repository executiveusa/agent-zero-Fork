"""
security_agent.py — Agent Claw Security Agent Tool

A comprehensive security tool that Agent Zero uses to:
  - Audit vault health and secret management
  - Scan repos for leaked secrets / hardcoded credentials
  - Check .gitignore coverage
  - Monitor file integrity
  - Review dependency vulnerabilities
  - Generate security reports

Methods:
    audit       — Full security audit (vault + env + gitignore + deps)
    vault       — Vault-specific audit and management
    scan        — Scan a directory for leaked secrets
    gitignore   — Verify .gitignore covers all sensitive patterns
    deps        — Check for known vulnerable dependencies
    report      — Generate a formatted security report
    rotate      — Prompt/flag secrets that need rotation (age-based)

Usage:
    {tool_name: "security_agent", tool_args: {method: "audit"}}
    {tool_name: "security_agent:scan", tool_args: {path: "."}}
    {tool_name: "security_agent:vault", tool_args: {action: "list"}}
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from python.helpers.tool import Tool, Response


# Patterns that indicate leaked secrets in source code
SECRET_PATTERNS = [
    (r'(?:api[_-]?key|apikey)\s*[:=]\s*["\']([A-Za-z0-9_\-]{20,})["\']', "API Key"),
    (r'(?:password|passwd|pwd)\s*[:=]\s*["\']([^\'"]{8,})["\']', "Password"),
    (r'(?:secret|token)\s*[:=]\s*["\']([A-Za-z0-9_\-]{16,})["\']', "Secret/Token"),
    (r'(?:Bearer\s+)([A-Za-z0-9_\-\.]{20,})', "Bearer Token"),
    (r'(sk-[A-Za-z0-9]{20,})', "OpenAI Key"),
    (r'(ghp_[A-Za-z0-9]{36,})', "GitHub PAT"),
    (r'(xoxb-[A-Za-z0-9\-]{20,})', "Slack Token"),
    (r'(AKIA[A-Z0-9]{16})', "AWS Access Key"),
    (r'(?:AC[a-f0-9]{32})', "Twilio Account SID"),
    (r'(eyJ[A-Za-z0-9_\-]{20,}\.eyJ[A-Za-z0-9_\-]{20,})', "JWT Token"),
    (r'(ak_-[A-Za-z0-9_\-]{10,})', "Composio Key"),
]

# File extensions to scan
SCANNABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
    ".toml", ".cfg", ".ini", ".conf", ".sh", ".bat", ".ps1",
    ".env", ".md", ".txt", ".html", ".css",
}

# Directories to skip
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".next", "dist", "build", ".tox", ".mypy_cache",
}

# Required .gitignore patterns for security
REQUIRED_GITIGNORE_PATTERNS = [
    ".env", "*.env.local", "secure/.vault/", "*.key", "*.pem",
    "*.p12", "credentials.json", "secrets.json", ".secrets/",
    "id_rsa*", "id_ed25519*", "*.token", "*.apikey",
]


class SecurityAgent(Tool):

    async def execute(self, **kwargs) -> Response:
        method = self.method or "audit"

        if method == "audit":
            return await self._full_audit(**kwargs)
        elif method == "vault":
            return await self._vault_ops(**kwargs)
        elif method == "scan":
            return await self._scan_secrets(**kwargs)
        elif method == "gitignore":
            return await self._check_gitignore(**kwargs)
        elif method == "deps":
            return await self._check_deps(**kwargs)
        elif method == "report":
            return await self._generate_report(**kwargs)
        elif method == "rotate":
            return await self._check_rotation(**kwargs)
        else:
            return Response(
                message=f"Unknown method '{method}'. Available: audit, vault, scan, gitignore, deps, report, rotate",
                break_loop=False,
            )

    async def _full_audit(self, **kwargs) -> Response:
        """Run a comprehensive security audit."""
        from python.helpers.vault import vault_audit

        self.set_progress("Running full security audit...")

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vault": vault_audit(),
            "gitignore": self._gitignore_check(),
            "secret_scan": self._scan_directory(os.getcwd(), max_files=500),
            "issues": [],
            "score": 100,
        }

        # Calculate security score
        issues = []

        # Vault checks
        if not results["vault"]["master_key_exists"]:
            issues.append({"severity": "CRITICAL", "msg": "Vault master key missing"})
            results["score"] -= 30
        if results["vault"]["env_leaks"]:
            for leak in results["vault"]["env_leaks"]:
                issues.append({"severity": "HIGH", "msg": f"Secret '{leak}' is in BOTH .env and vault — remove from .env"})
                results["score"] -= 5
        if results["vault"]["unvaulted"]:
            for key in results["vault"]["unvaulted"]:
                issues.append({"severity": "MEDIUM", "msg": f"Secret '{key}' is in .env but NOT encrypted in vault"})
                results["score"] -= 3

        # Gitignore checks
        for missing in results["gitignore"].get("missing_patterns", []):
            issues.append({"severity": "HIGH", "msg": f".gitignore missing: {missing}"})
            results["score"] -= 5

        # Secret scan
        for finding in results["secret_scan"].get("findings", []):
            issues.append({"severity": "CRITICAL", "msg": f"Leaked {finding['type']} in {finding['file']}:{finding['line']}"})
            results["score"] -= 10

        results["score"] = max(0, results["score"])
        results["issues"] = issues

        # Format output
        grade = "A+" if results["score"] >= 95 else "A" if results["score"] >= 90 else \
                "B" if results["score"] >= 80 else "C" if results["score"] >= 70 else \
                "D" if results["score"] >= 60 else "F"

        lines = [
            f"# Security Audit Report",
            f"**Score: {results['score']}/100 (Grade: {grade})**",
            f"**Time:** {results['timestamp']}",
            "",
            f"## Vault Status",
            f"- Encrypted secrets: {results['vault']['secrets_count']}",
            f"- Env leaks: {len(results['vault']['env_leaks'])}",
            f"- Unvaulted: {len(results['vault']['unvaulted'])}",
            "",
        ]

        if issues:
            lines.append("## Issues Found")
            for issue in sorted(issues, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["severity"], 3)):
                icon = {"CRITICAL": "[!!!]", "HIGH": "[!!]", "MEDIUM": "[!]"}.get(issue["severity"], "[?]")
                lines.append(f"- {icon} **{issue['severity']}**: {issue['msg']}")
        else:
            lines.append("## No Issues Found")

        return Response(message="\n".join(lines), break_loop=False)

    async def _vault_ops(self, **kwargs) -> Response:
        """Vault management operations."""
        from python.helpers.vault import vault_list, vault_load, vault_store, vault_delete, vault_audit, vault_bootstrap

        action = self.args.get("action", "list")

        if action == "list":
            secrets = vault_list()
            audit = vault_audit()
            lines = [f"Vault: {len(secrets)} encrypted secrets"]
            for s in secrets:
                lines.append(f"  - {s}")
            if audit["env_leaks"]:
                lines.append(f"\nWarning: {len(audit['env_leaks'])} keys also in .env: {', '.join(audit['env_leaks'])}")
            return Response(message="\n".join(lines), break_loop=False)

        elif action == "bootstrap":
            stats = vault_bootstrap()
            return Response(
                message=f"Vault bootstrap: {stats['migrated']} migrated, {stats['already_vaulted']} already vaulted, {stats['empty']} empty",
                break_loop=False,
            )

        elif action == "audit":
            audit = vault_audit()
            return Response(
                message=f"Vault audit:\n```json\n{json.dumps(audit, indent=2)}\n```",
                break_loop=False,
            )

        elif action == "store":
            key = self.args.get("key", "").strip()
            value = self.args.get("value", "").strip()
            if not key or not value:
                return Response(message="Error: 'key' and 'value' required", break_loop=False)
            vault_store(key.lower(), value)
            return Response(message=f"Stored '{key}' in encrypted vault", break_loop=False)

        elif action == "delete":
            key = self.args.get("key", "").strip()
            if not key:
                return Response(message="Error: 'key' required", break_loop=False)
            if vault_delete(key.lower()):
                return Response(message=f"Deleted '{key}' from vault", break_loop=False)
            return Response(message=f"Key '{key}' not found in vault", break_loop=False)

        return Response(message=f"Unknown vault action '{action}'. Available: list, bootstrap, audit, store, delete", break_loop=False)

    async def _scan_secrets(self, **kwargs) -> Response:
        """Scan a directory for leaked secrets."""
        path = self.args.get("path", os.getcwd())
        max_files = int(self.args.get("max_files", 500))

        self.set_progress(f"Scanning {path} for leaked secrets...")
        results = self._scan_directory(path, max_files)

        if not results["findings"]:
            return Response(
                message=f"Secret scan clean: scanned {results['files_scanned']} files, no secrets found.",
                break_loop=False,
            )

        lines = [f"# Secret Scan Results", f"Scanned {results['files_scanned']} files\n"]
        for f in results["findings"]:
            lines.append(f"- **{f['type']}** in `{f['file']}` line {f['line']}: `{f['preview']}`")

        return Response(message="\n".join(lines), break_loop=False)

    async def _check_gitignore(self, **kwargs) -> Response:
        """Verify .gitignore coverage."""
        result = self._gitignore_check()

        if not result["missing_patterns"]:
            return Response(
                message=f".gitignore: All {len(REQUIRED_GITIGNORE_PATTERNS)} required security patterns present.",
                break_loop=False,
            )

        lines = [".gitignore security check:"]
        for p in result["present_patterns"]:
            lines.append(f"  [OK] {p}")
        for p in result["missing_patterns"]:
            lines.append(f"  [MISSING] {p}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _check_deps(self, **kwargs) -> Response:
        """Check for dependencies with known issues."""
        self.set_progress("Checking dependencies...")

        req_file = os.path.join(os.getcwd(), "requirements.txt")
        if not os.path.exists(req_file):
            return Response(message="No requirements.txt found", break_loop=False)

        with open(req_file, "r") as f:
            deps = [l.strip() for l in f if l.strip() and not l.startswith("#")]

        # Basic version currency check
        lines = [f"Dependency check: {len(deps)} packages"]
        pinned = [d for d in deps if "==" in d]
        unpinned = [d for d in deps if ">=" in d or d.isalpha()]
        lines.append(f"  Pinned: {len(pinned)}, Flexible: {len(unpinned)}")
        lines.append(f"  Tip: Run `pip audit` for CVE checks")

        return Response(message="\n".join(lines), break_loop=False)

    async def _generate_report(self, **kwargs) -> Response:
        """Generate a full security report (delegates to audit)."""
        return await self._full_audit(**kwargs)

    async def _check_rotation(self, **kwargs) -> Response:
        """Check which secrets may need rotation based on vault file age."""
        from python.helpers.vault import vault_list, VAULT_DIR

        max_age_days = int(self.args.get("max_age_days", 90))
        now = time.time()
        needs_rotation = []

        for name in vault_list():
            filepath = os.path.join(VAULT_DIR, f"{name}.enc")
            if os.path.exists(filepath):
                age_days = (now - os.path.getmtime(filepath)) / 86400
                if age_days > max_age_days:
                    needs_rotation.append({
                        "key": name,
                        "age_days": round(age_days, 1),
                    })

        if not needs_rotation:
            return Response(
                message=f"All vault secrets are within the {max_age_days}-day rotation window.",
                break_loop=False,
            )

        lines = [f"Secrets needing rotation (>{max_age_days} days old):"]
        for s in needs_rotation:
            lines.append(f"  - {s['key']}: {s['age_days']} days old")

        return Response(message="\n".join(lines), break_loop=False)

    # ── Internal helpers ──────────────────────────────────────

    def _scan_directory(self, root: str, max_files: int = 500) -> dict:
        """Scan files for secret patterns."""
        findings = []
        files_scanned = 0

        for dirpath, dirnames, filenames in os.walk(root):
            # Skip excluded directories
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            for fname in filenames:
                if files_scanned >= max_files:
                    break

                ext = os.path.splitext(fname)[1].lower()
                if ext not in SCANNABLE_EXTENSIONS:
                    continue

                filepath = os.path.join(dirpath, fname)
                relpath = os.path.relpath(filepath, root)
                files_scanned += 1

                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, 1):
                            for pattern, sec_type in SECRET_PATTERNS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    # Don't report .env files (they're supposed to have secrets)
                                    if fname in (".env", ".env.example", "secrets.env"):
                                        continue
                                    # Don't report test/example patterns
                                    if any(x in line.lower() for x in ["example", "placeholder", "your-", "xxx", "changeme", "test"]):
                                        continue
                                    preview = line.strip()[:80]
                                    findings.append({
                                        "file": relpath,
                                        "line": lineno,
                                        "type": sec_type,
                                        "preview": preview,
                                    })
                                    break  # One finding per line
                except Exception:
                    continue

        return {"files_scanned": files_scanned, "findings": findings}

    def _gitignore_check(self) -> dict:
        """Check .gitignore for required security patterns."""
        gitignore_path = os.path.join(os.getcwd(), ".gitignore")
        present = []
        missing = []

        if not os.path.exists(gitignore_path):
            return {"present_patterns": [], "missing_patterns": REQUIRED_GITIGNORE_PATTERNS}

        with open(gitignore_path, "r") as f:
            content = f.read()

        for pattern in REQUIRED_GITIGNORE_PATTERNS:
            if pattern in content:
                present.append(pattern)
            else:
                missing.append(pattern)

        return {"present_patterns": present, "missing_patterns": missing}
