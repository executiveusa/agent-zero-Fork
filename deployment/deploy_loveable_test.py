#!/usr/bin/env python3
"""
Deploy and run Loveable test on Hostinger VPS via SSH

Usage:
    python3 deploy_loveable_test.py --host <ip> --user <user> --key <key_path>
"""

import subprocess
import json
import sys
import argparse
from pathlib import Path


class HostingerDeployment:
    """Deploy Loveable test to Hostinger VPS"""

    def __init__(self, host: str, user: str = "root", port: int = 22, key_path: str = None):
        self.host = host
        self.user = user
        self.port = port
        self.key_path = key_path
        self.ssh_cmd = self._build_ssh_command()

    def _build_ssh_command(self) -> list:
        """Build SSH command"""
        cmd = ["ssh"]
        if self.key_path:
            cmd.extend(["-i", self.key_path])
        cmd.extend(["-p", str(self.port)])
        cmd.append(f"{self.user}@{self.host}")
        return cmd

    def run_remote_command(self, command: str) -> tuple:
        """Run command on remote server"""
        try:
            full_cmd = self._ssh_cmd + [command]
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timeout"
        except Exception as e:
            return 1, "", str(e)

    def deploy_test_script(self) -> bool:
        """Deploy test script to Hostinger"""
        print("[1] Copying test script to Hostinger...")

        script_path = Path(__file__).parent.parent / "test_loveable_with_credentials.py"

        try:
            subprocess.run(
                ["scp", "-P", str(self.port)] +
                (["-i", self.key_path] if self.key_path else []) +
                [str(script_path), f"{self.user}@{self.host}:/root/"],
                timeout=60
            )
            print("✅ Script copied")
            return True
        except Exception as e:
            print(f"❌ Failed to copy: {e}")
            return False

    def setup_environment(self) -> bool:
        """Setup Python environment on Hostinger"""
        print("[2] Setting up Python environment...")

        commands = [
            "apt-get update -qq",
            "apt-get install -y python3 python3-pip",
            "pip install -q playwright requests beautifulsoup4",
            "python3 -m playwright install chromium"
        ]

        for cmd in commands:
            code, out, err = self.run_remote_command(cmd)
            if code != 0 and "already" not in err.lower():
                print(f"⚠️  Warning: {err[:100]}")

        print("✅ Environment setup complete")
        return True

    def run_test(self) -> dict:
        """Run test on Hostinger"""
        print("[3] Running Loveable test on Hostinger...")

        cmd = 'cd /root && python3 test_loveable_with_credentials.py'
        code, out, err = self.run_remote_command(cmd)

        if code == 0:
            print("✅ Test completed successfully")
            try:
                # Try to extract JSON from output
                if "{" in out:
                    json_start = out.rfind("{")
                    json_str = out[json_start:]
                    results = json.loads(json_str)
                    return results
            except:
                pass
        else:
            print(f"❌ Test failed: {err[:200]}")

        return {"success": False, "error": err[:200]}

    def retrieve_results(self) -> dict:
        """Retrieve results from Hostinger"""
        print("[4] Retrieving results...")

        cmd = "cat /root/loveable_login_results.json"
        code, out, err = self.run_remote_command(cmd)

        if code == 0:
            try:
                results = json.loads(out)
                print("✅ Results retrieved")
                return results
            except:
                pass

        return None

    def deploy_and_run(self) -> dict:
        """Complete deployment and test"""
        print("="*80)
        print(f"DEPLOYING TO HOSTINGER: {self.user}@{self.host}:{self.port}")
        print("="*80)
        print()

        if not self.deploy_test_script():
            return {"success": False, "error": "Failed to deploy script"}

        self.setup_environment()

        results = self.run_test()

        if results.get("success"):
            print("\n" + "="*80)
            print("✅ LOVEABLE.DEV LOGIN SUCCESSFUL!")
            print("="*80)
            password = results.get("successful_password", "")
            print(f"Working password: {password[:1]}****")
            print(f"Projects found: {len(results.get('projects_found', []))}")
            return results

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Deploy Loveable test to Hostinger VPS"
    )
    parser.add_argument("--host", required=True, help="Hostinger VPS IP address")
    parser.add_argument("--user", default="root", help="SSH user (default: root)")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    parser.add_argument("--key", help="Path to SSH private key")

    args = parser.parse_args()

    deployment = HostingerDeployment(
        host=args.host,
        user=args.user,
        port=args.port,
        key_path=args.key
    )

    results = deployment.deploy_and_run()

    print("\nResults JSON:")
    print(json.dumps(results, indent=2))

    return 0 if results.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
