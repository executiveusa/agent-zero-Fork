"""
Tests for the PRD generator and reader tools.
Run: python -m pytest tests/deploy/test_prd_generator.py -v
"""
import os
import re
import json
import tempfile
import pytest


# ── PRD Generation ───────────────────────────────────────────

class TestPRDGenerator:
    """Test PRD markdown generation logic (no Agent Zero runtime needed)."""

    STEPS = [
        "ANALYZE — Detect framework, port, dependencies",
        "SECRETS — Vault audit and inject env vars",
        "DOCKERFILE — Generate if missing",
        "BUILD — Validate build config",
        "TEST — Pre-deploy sanity checks",
        "COOLIFY — Create app and configure",
        "DATABASE — Provision if needed",
        "DEPLOY — Trigger and monitor deployment",
        "DNS — Verify domain resolution",
        "VERIFY — External health check",
        "REPORT — Generate deployment report",
    ]

    def generate_prd(self, app_name: str, repo_url: str, analysis: dict) -> str:
        """Replicate the PRD generation logic from the tool."""
        prd = f"# Deploy PRD: {app_name}\n\n"
        prd += f"**Repo:** {repo_url}\n"
        prd += f"**Type:** {analysis.get('type', 'unknown')}\n"
        prd += f"**Port:** {analysis.get('port', 3000)}\n\n"
        prd += "## Pipeline Tasks\n\n"
        for i, step in enumerate(self.STEPS, 1):
            prd += f"- [ ] {i}. {step}\n"
        prd += "\n## Progress Log\n\n"
        return prd

    def test_prd_has_11_unchecked_tasks(self):
        prd = self.generate_prd("test-app", "https://github.com/test/repo", {"type": "nextjs", "port": 3000})
        unchecked = re.findall(r"- \[ \] \d+\.", prd)
        assert len(unchecked) == 11

    def test_prd_contains_app_name(self):
        prd = self.generate_prd("my-cool-app", "https://github.com/test/repo", {})
        assert "my-cool-app" in prd

    def test_prd_contains_repo_url(self):
        prd = self.generate_prd("app", "https://github.com/user/repo", {})
        assert "https://github.com/user/repo" in prd

    def test_prd_steps_are_numbered_sequentially(self):
        prd = self.generate_prd("app", "https://github.com/test/repo", {})
        numbers = re.findall(r"- \[ \] (\d+)\.", prd)
        assert numbers == [str(i) for i in range(1, 12)]

    def test_prd_has_progress_log_section(self):
        prd = self.generate_prd("app", "https://github.com/test/repo", {})
        assert "## Progress Log" in prd


# ── PRD Reader ───────────────────────────────────────────────

class TestPRDReader:
    """Test PRD reading and task finding logic."""

    SAMPLE_PRD = """# Deploy PRD: test-app

**Repo:** https://github.com/test/repo

## Pipeline Tasks

- [x] 1. ANALYZE — Detect framework, port, dependencies
- [x] 2. SECRETS — Vault audit and inject env vars
- [ ] 3. DOCKERFILE — Generate if missing
- [ ] 4. BUILD — Validate build config
- [ ] 5. TEST — Pre-deploy sanity checks
- [ ] 6. COOLIFY — Create app and configure
- [ ] 7. DATABASE — Provision if needed
- [ ] 8. DEPLOY — Trigger and monitor deployment
- [ ] 9. DNS — Verify domain resolution
- [ ] 10. VERIFY — External health check
- [ ] 11. REPORT — Generate deployment report

## Progress Log
"""

    ALL_DONE_PRD = """# Deploy PRD: test-app

## Pipeline Tasks

- [x] 1. ANALYZE
- [x] 2. SECRETS
- [x] 3. DOCKERFILE
- [x] 4. BUILD
- [x] 5. TEST
- [x] 6. COOLIFY
- [x] 7. DATABASE
- [x] 8. DEPLOY
- [x] 9. DNS
- [x] 10. VERIFY
- [x] 11. REPORT
"""

    def find_next_task(self, prd_content: str):
        """Replicate the reader logic."""
        unchecked = re.findall(r"- \[ \] (\d+)\. (.+)", prd_content)
        checked = re.findall(r"- \[x\] (\d+)\.", prd_content)

        if not unchecked:
            return None, len(checked), len(checked)

        step_num, description = unchecked[0]
        return int(step_num), len(checked), len(checked) + len(unchecked)

    def test_finds_next_unchecked_task(self):
        step, done, total = self.find_next_task(self.SAMPLE_PRD)
        assert step == 3
        assert done == 2
        assert total == 11

    def test_all_done_returns_none(self):
        step, done, total = self.find_next_task(self.ALL_DONE_PRD)
        assert step is None
        assert done == 11

    def test_empty_prd_returns_none(self):
        step, done, total = self.find_next_task("")
        assert step is None


# ── Mark Task Done ───────────────────────────────────────────

class TestMarkTaskDone:
    """Test marking tasks as complete in the PRD."""

    def mark_done(self, prd_content: str, step: int, result: str = "passed") -> str:
        """Replicate mark_task_done logic."""
        import time
        pattern = rf"- \[ \] {step}\."
        replacement = f"- [x] {step}."
        updated = re.sub(pattern, replacement, prd_content, count=1)

        log_entry = f"- **Step {step}**: {result} @ {time.strftime('%H:%M:%S')}\n"
        if "## Progress Log" in updated:
            updated = updated.replace("## Progress Log\n", f"## Progress Log\n{log_entry}")
        return updated

    def test_marks_step_as_done(self):
        prd = "- [ ] 3. DOCKERFILE — Generate if missing\n"
        result = self.mark_done(prd, 3)
        assert "- [x] 3." in result
        assert "- [ ] 3." not in result

    def test_only_marks_specified_step(self):
        prd = "- [ ] 3. DOCKERFILE\n- [ ] 4. BUILD\n"
        result = self.mark_done(prd, 3)
        assert "- [x] 3." in result
        assert "- [ ] 4." in result

    def test_adds_progress_log_entry(self):
        prd = "## Progress Log\n"
        result = self.mark_done(prd, 5, "passed")
        assert "Step 5" in result
        assert "passed" in result


# ── Config Generation ────────────────────────────────────────

class TestConfigGeneration:
    """Test config.json creation."""

    def test_config_has_required_fields(self):
        config = {
            "repo_url": "https://github.com/test/repo",
            "app_name": "test-app",
            "branch": "main",
            "type": "nextjs",
            "port": 3000,
            "domain": "test-app.31.220.58.212.sslip.io",
        }
        assert "repo_url" in config
        assert "app_name" in config
        assert "type" in config
        assert "port" in config
        assert config["port"] == 3000

    def test_config_serializes_to_json(self):
        config = {"repo_url": "https://github.com/test/repo", "app_name": "x"}
        result = json.dumps(config)
        loaded = json.loads(result)
        assert loaded["app_name"] == "x"
