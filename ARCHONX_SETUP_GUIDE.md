# ARCHONX Setup Guide

## Overview

ARCHONX is an advanced configuration profile for Agent Zero that provides enhanced capabilities for autonomous operations. This guide will help you install and configure ARCHONX in your Agent Zero instance.

## Quick Start

### Installation

1. Navigate to your Agent Zero directory:
   ```bash
   cd /path/to/agent-zero-Fork
   ```

2. Run the setup script:
   ```bash
   python3 setup_archonx.py
   ```

3. The script will:
   - Create the `~/.agent-zero/` directory structure
   - Install `ARCHONX_AGENT_ZERO_PROMPT.md` to `~/.agent-zero/prompts/`
   - Install `archonx-config.json` to `~/.agent-zero/config/`
   - Verify the installation

### Verification

To verify your installation at any time:
```bash
python3 setup_archonx.py --verify
```

## Directory Structure

After installation, you'll have:

```
~/.agent-zero/
├── prompts/
│   └── ARCHONX_AGENT_ZERO_PROMPT.md  ✅ Agent personality and behavior
│
├── config/
│   └── archonx-config.json            ✅ Runtime configuration
│
└── ...
```

## What's Installed

### 1. ARCHONX_AGENT_ZERO_PROMPT.md

This file defines ARCHONX's:
- **Core Identity**: Name, role, and purpose
- **Enhanced Capabilities**: Autonomous operation, multi-agent coordination, strategic thinking
- **Operating Principles**: Transparency, efficiency, reliability, security, scalability
- **Interaction Guidelines**: How ARCHONX communicates and collaborates
- **Task Execution Protocol**: Step-by-step approach to solving problems
- **Communication Style**: Professional, technical, solution-oriented

### 2. archonx-config.json

This JSON configuration file contains:
- **Persona Settings**: Display name, avatar, theme color, greeting
- **Capabilities Flags**: Enable/disable advanced features
- **Behavior Settings**: Communication style, decision autonomy, risk tolerance
- **Memory Configuration**: Context length, consolidation settings
- **Tool Enablement**: Which tools and languages are available
- **Security Settings**: Credential management, audit logging
- **Integration Options**: GitHub, Slack, Telegram configurations
- **Resource Limits**: Execution time, memory, rate limiting

## Configuration

### Basic Customization

1. **Edit the Prompt File**:
   ```bash
   nano ~/.agent-zero/prompts/ARCHONX_AGENT_ZERO_PROMPT.md
   ```
   
   Customize:
   - Core identity and role
   - Operating principles
   - Communication style
   - Task execution approach

2. **Edit the Config File**:
   ```bash
   nano ~/.agent-zero/config/archonx-config.json
   ```
   
   Configure:
   - Persona (name, avatar, colors)
   - Capabilities (enable/disable features)
   - Behavior (autonomy level, risk tolerance)
   - Integrations (GitHub, Slack, etc.)
   - Resource limits

### Advanced Configuration

#### Enable Specific Features

To enable advanced features, edit `archonx-config.json`:

```json
{
  "advanced_features": {
    "multi_agent_swarm": true,      // Enable swarm intelligence
    "autonomous_scheduling": true,  // Enable self-scheduling
    "predictive_planning": true,    // Enable predictive planning
    "self_optimization": true       // Enable self-optimization
  }
}
```

#### Adjust Resource Limits

```json
{
  "limits": {
    "max_execution_time": 600,           // 10 minutes
    "max_file_size_mb": 200,             // 200 MB
    "max_memory_mb": 2048,               // 2 GB
    "rate_limit_requests_per_minute": 120 // 120 req/min
  }
}
```

#### Configure Integrations

```json
{
  "integrations": {
    "github": {
      "enabled": true,
      "auto_pr": true  // Automatically create PRs
    },
    "slack": {
      "enabled": true,
      "notifications": true
    },
    "telegram": {
      "enabled": true,
      "admin_notifications": true
    }
  }
}
```

## Integration with Agent Zero

### Option 1: Use as a Custom Persona

Add ARCHONX to `conf/agent_personas.yaml`:

```yaml
archonx:
  display_name: "ARCHONX"
  tagline: "Advanced Executive AI Assistant"
  avatar: "🚀"
  theme_color: "#00d4ff"
  voice_persona: "professional"
  greeting: "ARCHONX online. Ready for advanced operations."
  system_style: |
    {{include:~/.agent-zero/prompts/ARCHONX_AGENT_ZERO_PROMPT.md}}
```

Then set as default:
```yaml
default_persona: "archonx"
```

### Option 2: Use as an Agent Profile

Create a new agent profile in `agents/archonx/`:

```bash
mkdir -p agents/archonx/prompts
cp ~/.agent-zero/prompts/ARCHONX_AGENT_ZERO_PROMPT.md agents/archonx/prompts/agent.system.main.role.md
```

Set in your configuration:
```python
agent_profile = "archonx"
```

### Option 3: Runtime Configuration Loading

Load the ARCHONX config at runtime in your initialization code:

```python
import json
from pathlib import Path

# Load ARCHONX config
archonx_config_path = Path.home() / ".agent-zero" / "config" / "archonx-config.json"
with open(archonx_config_path) as f:
    archonx_config = json.load(f)

# Apply settings
# ... your integration logic here ...
```

## Features

ARCHONX configuration provides:

### ✅ Autonomous Operation
- Self-directed task planning and execution
- Proactive problem identification
- Intelligent resource allocation

### ✅ Multi-Agent Coordination
- Intelligent delegation of subtasks
- Collaborative problem-solving
- Swarm intelligence (when enabled)

### ✅ Advanced Planning
- Strategic thinking and roadmap development
- Risk assessment and mitigation
- Long-term project planning

### ✅ Enhanced Security
- Vault-based credential management
- Comprehensive audit logging
- Sandboxed code execution
- Secret scanning

### ✅ Flexible Integration
- GitHub (repository management, PRs)
- Slack (team notifications)
- Telegram (admin alerts)
- Custom integrations (via API)

## Troubleshooting

### Installation Issues

**Problem**: Template files not found
```
❌ Template not found: /path/to/templates/ARCHONX_AGENT_ZERO_PROMPT.md
```

**Solution**: Ensure you're running the script from the Agent Zero root directory:
```bash
cd /path/to/agent-zero-Fork
python3 setup_archonx.py
```

---

**Problem**: Permission denied when creating directories
```
❌ Error creating directories: [Errno 13] Permission denied
```

**Solution**: Check your home directory permissions:
```bash
chmod u+w ~/.agent-zero
# or run with appropriate permissions
```

### Configuration Not Loading

**Problem**: Changes to ARCHONX config are not reflected

**Solution**:
1. Verify files are in the correct location:
   ```bash
   python3 setup_archonx.py --verify
   ```

2. Restart Agent Zero completely:
   ```bash
   # Stop all Agent Zero processes
   pkill -f "agent"
   # Restart
   python3 run_ui.py
   ```

3. Clear any cached configurations:
   ```bash
   rm -rf /tmp/agent-zero-cache
   ```

### File Permission Issues

**Problem**: Cannot read configuration files

**Solution**: Ensure proper permissions:
```bash
chmod 644 ~/.agent-zero/prompts/ARCHONX_AGENT_ZERO_PROMPT.md
chmod 644 ~/.agent-zero/config/archonx-config.json
```

## Maintenance

### Updating Configuration

To update your ARCHONX configuration:

1. **Backup current config**:
   ```bash
   cp ~/.agent-zero/config/archonx-config.json ~/.agent-zero/config/archonx-config.json.backup
   ```

2. **Make your changes**:
   ```bash
   nano ~/.agent-zero/config/archonx-config.json
   ```

3. **Validate JSON syntax**:
   ```bash
   python3 -m json.tool ~/.agent-zero/config/archonx-config.json
   ```

4. **Restart Agent Zero** to apply changes

### Reinstalling

To reinstall ARCHONX (this will overwrite your custom changes):

```bash
python3 setup_archonx.py
```

To keep your customizations, backup first:
```bash
cp ~/.agent-zero/config/archonx-config.json ~/archonx-config.backup.json
python3 setup_archonx.py
# Then merge your changes back
```

## Support

### Getting Help

1. **Check the templates README**:
   ```bash
   cat templates/README.md
   ```

2. **Verify installation**:
   ```bash
   python3 setup_archonx.py --verify
   ```

3. **Review configuration**:
   ```bash
   cat ~/.agent-zero/config/archonx-config.json
   ```

4. **Check Agent Zero logs** for any errors related to ARCHONX

### Reporting Issues

When reporting issues:
1. Run verification: `python3 setup_archonx.py --verify`
2. Include Agent Zero version
3. Include relevant log snippets
4. Describe your customizations (if any)

## Examples

### Example 1: Development Agent

Configure ARCHONX for software development:

```json
{
  "capabilities": {
    "autonomous_operation": true,
    "multi_agent_coordination": true,
    "advanced_planning": true
  },
  "tools": {
    "code_execution": {
      "enabled": true,
      "languages": ["python", "javascript", "typescript", "rust", "go"]
    }
  },
  "integrations": {
    "github": {
      "enabled": true,
      "auto_pr": true
    }
  }
}
```

### Example 2: Operations Agent

Configure ARCHONX for DevOps and operations:

```json
{
  "capabilities": {
    "proactive_monitoring": true,
    "autonomous_operation": true
  },
  "tools": {
    "code_execution": {
      "enabled": true,
      "languages": ["bash", "python"]
    }
  },
  "integrations": {
    "slack": {
      "enabled": true,
      "notifications": true
    }
  },
  "monitoring": {
    "health_checks": true,
    "error_reporting": true
  }
}
```

### Example 3: Research Agent

Configure ARCHONX for research and analysis:

```json
{
  "capabilities": {
    "advanced_planning": true,
    "continuous_learning": true
  },
  "behavior": {
    "communication_style": "detailed",
    "reporting_frequency": "frequent"
  },
  "memory": {
    "enabled": true,
    "consolidation": true,
    "max_context_length": 64000
  }
}
```

## Version History

- **v1.0.0** (2026-02-11):
  - Initial ARCHONX configuration release
  - Core identity and capabilities
  - Security and monitoring features
  - Integration support for major platforms
  - Resource limits and optimization settings

## Next Steps

After installing ARCHONX:

1. ✅ **Customize the prompt** to match your needs
2. ✅ **Configure integrations** (GitHub, Slack, etc.)
3. ✅ **Set resource limits** appropriate for your environment
4. ✅ **Test basic functionality** with simple tasks
5. ✅ **Enable advanced features** as needed
6. ✅ **Monitor performance** and adjust settings

For more information, see:
- `templates/README.md` - Template documentation
- `docs/` - Agent Zero documentation
- Agent Zero main README

---

**Welcome to ARCHONX** - Advanced autonomous operations powered by Agent Zero! 🚀
