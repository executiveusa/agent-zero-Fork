#!/usr/bin/env python3
import os
import json

os.makedirs("scripts", exist_ok=True)
os.makedirs(".github/workflows", exist_ok=True)

# Create deployment script
with open("scripts/deploy-hostinger.sh", "w") as f:
    f.write("#!/bin/bash\necho 'Agent Zero deployment ready'\n")
os.chmod("scripts/deploy-hostinger.sh", 0o755)

# Create GitHub Actions workflow
workflow = """name: Deploy to Hostinger
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and Deploy
        run: echo "Ready for Coolify deployment"
"""

with open(".github/workflows/deploy-hostinger.yml", "w") as f:
    f.write(workflow)

# Create config
config = {"platform": "hostinger", "deployment": "coolify", "app": "agent-zero"}
with open("hostinger-deployment.json", "w") as f:
    json.dump(config, f, indent=2)

print("\n✅ Files created successfully!")
print("   • scripts/deploy-hostinger.sh")
print("   • .github/workflows/deploy-hostinger.yml")
print("   • hostinger-deployment.json")
print("\n🔐 Your Hostinger Credentials (from vault):")
print("   Coolify Token: 1439|JNBGNRm9lON2g8DpkpKIa5TnRdGc8LaILhTgPTuR8d6b1c26")
print("   Hostinger API: bL59Px9zyPf9JYwbCrXZRwqk82JFvaWrk8HAxqqnbd5caddb")
