"""
Project Analyzer — Auto-detect project type from repo
=====================================================
Inspects GitHub repos or local directories to determine:
  - Framework (Next.js, Flask, Express, etc.)
  - Language, port, build/test commands
  - Database needs, Dockerfile presence
"""

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


# ── Framework Detection Rules ────────────────────────────────

INDICATORS = {
    # filename → (type, port, language)
    "next.config.js": ("nextjs", 3000, "typescript"),
    "next.config.mjs": ("nextjs", 3000, "typescript"),
    "next.config.ts": ("nextjs", 3000, "typescript"),
    "nuxt.config.ts": ("nuxt", 3000, "typescript"),
    "svelte.config.js": ("svelte", 5173, "typescript"),
    "astro.config.mjs": ("astro", 4321, "typescript"),
    "remix.config.js": ("remix", 3000, "typescript"),
    "angular.json": ("angular", 4200, "typescript"),
    "vue.config.js": ("vue", 8080, "typescript"),
    "Cargo.toml": ("rust", 8080, "rust"),
    "go.mod": ("go", 8080, "go"),
    "mix.exs": ("elixir", 4000, "elixir"),
    "Gemfile": ("ruby", 3000, "ruby"),
}

PYTHON_FRAMEWORKS = {
    "flask": ("flask", 5000),
    "django": ("django", 8000),
    "fastapi": ("fastapi", 8000),
    "streamlit": ("streamlit", 8501),
    "gradio": ("gradio", 7860),
}

DB_INDICATORS = {
    "prisma",
    "drizzle.config.ts",
    "drizzle.config.js",
    "alembic.ini",
    "sqlalchemy",
    "typeorm",
    "knexfile.js",
    "sequelize",
    "schema.prisma",
}


def analyze_github_repo(repo_url: str) -> dict[str, Any]:
    """Analyze a GitHub repo URL → project metadata."""
    match = re.search(r"github\.com/([^/]+/[^/.]+)", repo_url)
    if not match:
        return _unknown_project()

    owner_repo = match.group(1)
    file_names = _fetch_repo_files(owner_repo)
    if not file_names:
        return _unknown_project()

    result = {
        "type": "unknown",
        "language": "unknown",
        "port": 3000,
        "needs_db": False,
        "has_dockerfile": "Dockerfile" in file_names,
        "has_docker_compose": "docker-compose.yml" in file_names or "compose.yml" in file_names,
        "has_tests": False,
        "build_cmd": None,
        "test_cmd": None,
        "start_cmd": None,
        "env_vars_needed": [],
    }

    # Framework detection
    for filename, (ftype, fport, flang) in INDICATORS.items():
        if filename in file_names:
            result["type"] = ftype
            result["port"] = fport
            result["language"] = flang
            break

    # Python detection (needs requirements.txt inspection)
    if result["type"] == "unknown" and "requirements.txt" in file_names:
        result["language"] = "python"
        reqs_text = _fetch_raw_file(owner_repo, "requirements.txt")
        for pkg, (ftype, fport) in PYTHON_FRAMEWORKS.items():
            if pkg in reqs_text.lower():
                result["type"] = ftype
                result["port"] = fport
                break
        if result["type"] == "unknown":
            result["type"] = "python"
            result["port"] = 5000

    # Node.js fallback
    if result["type"] == "unknown" and "package.json" in file_names:
        result["language"] = "javascript"
        pkg_json = _fetch_raw_file(owner_repo, "package.json")
        try:
            pkg = json.loads(pkg_json)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                result["type"] = "nextjs"
                result["port"] = 3000
            elif "express" in deps:
                result["type"] = "express"
                result["port"] = 3000
            elif "hono" in deps:
                result["type"] = "hono"
                result["port"] = 3000
            else:
                result["type"] = "node"
                result["port"] = 3000
            # Extract scripts
            scripts = pkg.get("scripts", {})
            result["build_cmd"] = scripts.get("build")
            result["test_cmd"] = scripts.get("test")
            result["start_cmd"] = scripts.get("start")
            if scripts.get("test"):
                result["has_tests"] = True
        except (json.JSONDecodeError, KeyError):
            result["type"] = "node"

    # Static site fallback
    if result["type"] == "unknown" and "index.html" in file_names:
        result["type"] = "static"
        result["port"] = 80
        result["language"] = "html"

    # Database needs
    result["needs_db"] = bool(file_names & DB_INDICATORS)
    if "prisma" in file_names:
        result["needs_db"] = True

    # Check for .env.example
    if ".env.example" in file_names:
        env_example = _fetch_raw_file(owner_repo, ".env.example")
        result["env_vars_needed"] = _parse_env_keys(env_example)

    return result


def analyze_local_dir(path: str) -> dict[str, Any]:
    """Analyze a local directory → project metadata."""
    p = Path(path)
    if not p.is_dir():
        return _unknown_project()

    file_names = {f.name for f in p.iterdir() if f.is_file()}
    dir_names = {d.name for d in p.iterdir() if d.is_dir()}
    all_names = file_names | dir_names

    result = {
        "type": "unknown",
        "language": "unknown",
        "port": 3000,
        "needs_db": False,
        "has_dockerfile": "Dockerfile" in file_names,
        "has_docker_compose": "docker-compose.yml" in file_names or "compose.yml" in file_names,
        "has_tests": "tests" in dir_names or "test" in dir_names or "__tests__" in dir_names,
        "build_cmd": None,
        "test_cmd": None,
        "start_cmd": None,
        "env_vars_needed": [],
    }

    for filename, (ftype, fport, flang) in INDICATORS.items():
        if filename in all_names:
            result["type"] = ftype
            result["port"] = fport
            result["language"] = flang
            break

    if result["type"] == "unknown" and "requirements.txt" in file_names:
        result["language"] = "python"
        reqs_text = (p / "requirements.txt").read_text(errors="ignore").lower()
        for pkg, (ftype, fport) in PYTHON_FRAMEWORKS.items():
            if pkg in reqs_text:
                result["type"] = ftype
                result["port"] = fport
                break
        if result["type"] == "unknown":
            result["type"] = "python"
            result["port"] = 5000

    if result["type"] == "unknown" and "package.json" in file_names:
        result["language"] = "javascript"
        try:
            pkg = json.loads((p / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                result["type"] = "nextjs"
            elif "express" in deps:
                result["type"] = "express"
            else:
                result["type"] = "node"
            scripts = pkg.get("scripts", {})
            result["build_cmd"] = scripts.get("build")
            result["test_cmd"] = scripts.get("test")
            result["start_cmd"] = scripts.get("start")
        except Exception:
            result["type"] = "node"

    if result["type"] == "unknown" and "index.html" in file_names:
        result["type"] = "static"
        result["port"] = 80
        result["language"] = "html"

    result["needs_db"] = bool(all_names & DB_INDICATORS)

    if ".env.example" in file_names:
        result["env_vars_needed"] = _parse_env_keys(
            (p / ".env.example").read_text(errors="ignore")
        )

    return result


# ── Helpers ──────────────────────────────────────────────────

def _unknown_project() -> dict[str, Any]:
    return {
        "type": "unknown",
        "language": "unknown",
        "port": 3000,
        "needs_db": False,
        "has_dockerfile": False,
        "has_docker_compose": False,
        "has_tests": False,
        "build_cmd": None,
        "test_cmd": None,
        "start_cmd": None,
        "env_vars_needed": [],
    }


def _fetch_repo_files(owner_repo: str) -> set:
    """Fetch root-level file/dir names from GitHub API."""
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner_repo}/contents/",
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "AgentClaw/1.0"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        items = json.loads(resp.read().decode())
        return {item["name"] for item in items}
    except Exception:
        return set()


def _fetch_raw_file(owner_repo: str, filename: str) -> str:
    """Fetch a raw file from GitHub."""
    for branch in ("main", "master"):
        try:
            req = urllib.request.Request(
                f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{filename}",
                headers={"User-Agent": "AgentClaw/1.0"},
            )
            resp = urllib.request.urlopen(req, timeout=10)
            return resp.read().decode()
        except Exception:
            continue
    return ""


def _parse_env_keys(env_text: str) -> list[str]:
    """Extract KEY names from a .env file (ignoring values and comments)."""
    keys = []
    for line in env_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if key and re.match(r"^[A-Z_][A-Z0-9_]*$", key):
                keys.append(key)
    return keys
