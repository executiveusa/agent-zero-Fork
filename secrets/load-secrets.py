#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║     ArchonX OS - Secrets Loader & Environment Generator             ║
║           Converts secrets.json to .env files                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any


class SecretsLoader:
    def __init__(self, secrets_file: str):
        self.secrets_file = secrets_file
        self.secrets = {}

    def load(self) -> Dict[str, Any]:
        """Load secrets from JSON file"""
        with open(self.secrets_file, 'r') as f:
            self.secrets = json.load(f)
        return self.secrets

    def generate_env_file(self, output_file: str = ".env", sections: list = None):
        """Generate .env file from secrets"""

        env_lines = []
        env_lines.append("# ═══════════════════════════════════════════════════════════")
        env_lines.append("# ArchonX OS Ecosystem - Auto-generated from secrets.json")
        env_lines.append("# ═══════════════════════════════════════════════════════════")
        env_lines.append("")

        # If no sections specified, use all
        if sections is None:
            sections = list(self.secrets.keys())

        # Generate environment variables
        for section in sections:
            if section not in self.secrets or section == "metadata":
                continue

            env_lines.append(f"# ─── {section.upper().replace('_', ' ')} ───")
            self._process_section(self.secrets[section], section.upper(), env_lines)
            env_lines.append("")

        # Write to file
        with open(output_file, 'w') as f:
            f.write('\n'.join(env_lines))

        print(f"✓ Generated .env file: {output_file}")

    def _process_section(self, data: Any, prefix: str, env_lines: list, depth: int = 0):
        """Recursively process nested data structures"""

        if isinstance(data, dict):
            for key, value in data.items():
                if key in ["name", "description", "repository"]:
                    # Skip metadata fields
                    continue

                new_prefix = f"{prefix}_{key.upper()}"

                if isinstance(value, dict):
                    self._process_section(value, new_prefix, env_lines, depth + 1)
                elif isinstance(value, list):
                    # Handle lists (comma-separated)
                    env_lines.append(f'{new_prefix}="{",".join(str(v) for v in value)}"')
                elif isinstance(value, bool):
                    env_lines.append(f'{new_prefix}="{str(value).lower()}"')
                elif value is None or value == "":
                    env_lines.append(f'{new_prefix}=""')
                else:
                    # Escape quotes in values
                    safe_value = str(value).replace('"', '\\"')
                    env_lines.append(f'{new_prefix}="{safe_value}"')
        elif isinstance(data, list):
            env_lines.append(f'{prefix}="{",".join(str(v) for v in data)}"')
        else:
            safe_value = str(data).replace('"', '\\"')
            env_lines.append(f'{prefix}="{safe_value}"')

    def generate_docker_compose_env(self, output_file: str = "docker-compose.env"):
        """Generate environment file for Docker Compose"""
        self.generate_env_file(output_file, sections=[
            "archonx_os",
            "agent_zero",
            "ai_providers",
            "databases",
            "monitoring"
        ])

    def generate_service_specific_env(self, service: str, output_file: str = None):
        """Generate environment file for specific service"""

        if output_file is None:
            output_file = f".env.{service}"

        if service not in self.secrets:
            print(f"✗ Service not found: {service}")
            return

        env_lines = []
        env_lines.append(f"# ═══════════════════════════════════════════════════════════")
        env_lines.append(f"# {service.upper().replace('_', ' ')} - Environment Variables")
        env_lines.append(f"# ═══════════════════════════════════════════════════════════")
        env_lines.append("")

        self._process_section(self.secrets[service], service.upper(), env_lines)

        # Add common sections
        if "ai_providers" in self.secrets:
            env_lines.append("")
            env_lines.append("# ─── AI PROVIDERS ───")
            self._process_section(self.secrets["ai_providers"], "AI", env_lines)

        with open(output_file, 'w') as f:
            f.write('\n'.join(env_lines))

        print(f"✓ Generated service-specific .env: {output_file}")

    def export_to_shell(self):
        """Export secrets as shell environment variables"""

        print("# Copy and paste these into your shell:")
        print("")

        for section, data in self.secrets.items():
            if section == "metadata":
                continue

            self._export_section_to_shell(data, section.upper())

    def _export_section_to_shell(self, data: Any, prefix: str):
        """Recursively export to shell format"""

        if isinstance(data, dict):
            for key, value in data.items():
                if key in ["name", "description", "repository"]:
                    continue

                new_prefix = f"{prefix}_{key.upper()}"

                if isinstance(value, dict):
                    self._export_section_to_shell(value, new_prefix)
                elif isinstance(value, list):
                    print(f'export {new_prefix}="{",".join(str(v) for v in value)}"')
                elif isinstance(value, bool):
                    print(f'export {new_prefix}="{str(value).lower()}"')
                elif value:
                    safe_value = str(value).replace('"', '\\"')
                    print(f'export {new_prefix}="{safe_value}"')


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} <secrets.json> [command]")
        print("")
        print("Commands:")
        print("  generate-env              - Generate main .env file")
        print("  generate-docker           - Generate docker-compose.env")
        print("  generate-service <name>   - Generate .env for specific service")
        print("  export-shell              - Export as shell variables")
        print("")
        print("Examples:")
        print(f"  {sys.argv[0]} secrets.json generate-env")
        print(f"  {sys.argv[0]} secrets.json generate-service agent_zero")
        print(f"  {sys.argv[0]} secrets.json export-shell > export.sh")
        sys.exit(1)

    secrets_file = sys.argv[1]

    if not os.path.exists(secrets_file):
        print(f"✗ Secrets file not found: {secrets_file}")
        sys.exit(1)

    loader = SecretsLoader(secrets_file)
    loader.load()

    command = sys.argv[2] if len(sys.argv) > 2 else "generate-env"

    if command == "generate-env":
        loader.generate_env_file()

    elif command == "generate-docker":
        loader.generate_docker_compose_env()

    elif command == "generate-service":
        if len(sys.argv) < 4:
            print("✗ Service name required")
            print("Available services:", ", ".join(loader.secrets.keys()))
            sys.exit(1)

        service = sys.argv[3]
        loader.generate_service_specific_env(service)

    elif command == "export-shell":
        loader.export_to_shell()

    else:
        print(f"✗ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
