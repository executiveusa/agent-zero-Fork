# ARCHONX Configuration Setup

This directory contains the ARCHONX configuration templates for Agent Zero. ARCHONX is an enhanced configuration profile that provides advanced capabilities for autonomous operations.

## Files

### ARCHONX_AGENT_ZERO_PROMPT.md
The system prompt that defines ARCHONX's personality, capabilities, and operating principles. This prompt configures the agent's:
- Core identity and role
- Enhanced capabilities
- Operating principles
- Interaction guidelines
- Task execution protocol
- Communication style

### archonx-config.json
Runtime configuration file that defines ARCHONX's technical settings, including:
- Persona configuration (display name, avatar, theme)
- Capability flags (autonomous operation, multi-agent coordination)
- Behavior settings (communication style, decision autonomy)
- Memory configuration
- Tool enablement
- Security settings
- Integration options
- Resource limits

## Installation

To install ARCHONX configuration to your Agent Zero instance:

```bash
# Run the setup script
python3 setup_archonx.py

# Or verify existing installation
python3 setup_archonx.py --verify
```

This will create the following directory structure in your home directory:

```
~/.agent-zero/
├── prompts/
│   └── ARCHONX_AGENT_ZERO_PROMPT.md
├── config/
│   └── archonx-config.json
└── ...
```

## Customization

After installation, you can customize the ARCHONX configuration:

1. **Edit the prompt file**: Modify `~/.agent-zero/prompts/ARCHONX_AGENT_ZERO_PROMPT.md` to adjust the agent's personality and operating principles.

2. **Edit the config file**: Update `~/.agent-zero/config/archonx-config.json` to:
   - Enable/disable specific capabilities
   - Adjust behavior settings
   - Configure integrations
   - Set resource limits
   - Update metadata

3. **Restart Agent Zero**: Apply your changes by restarting the Agent Zero service.

## Integration with Agent Zero

The ARCHONX configuration can be integrated with Agent Zero in several ways:

### As a Custom Profile
You can reference the ARCHONX prompt in your agent configuration by setting the appropriate profile or prompt path.

### As a Runtime Override
Load the archonx-config.json settings at runtime to apply ARCHONX-specific configurations.

### As a Persona
Add ARCHONX as a new persona in `conf/agent_personas.yaml`:

```yaml
archonx:
  display_name: "ARCHONX"
  tagline: "Advanced Executive AI Assistant"
  avatar: "🚀"
  avatar_image: ""
  theme_color: "#00d4ff"
  voice_persona: "professional"
  greeting: "ARCHONX online. Ready for advanced operations."
  system_style: |
    {{include:~/.agent-zero/prompts/ARCHONX_AGENT_ZERO_PROMPT.md}}
```

## Features

ARCHONX configuration enables:

- ✅ **Autonomous Operation**: Self-directed task planning and execution
- ✅ **Multi-Agent Coordination**: Intelligent delegation and collaboration
- ✅ **Advanced Planning**: Strategic thinking and roadmap development
- ✅ **Proactive Monitoring**: Continuous health checks and optimization
- ✅ **Enhanced Security**: Vault-based credential management and audit logging
- ✅ **Flexible Integration**: Support for GitHub, Slack, Telegram, and more

## Troubleshooting

### Files Not Found
If the setup script can't find template files, ensure you're running it from the Agent Zero root directory:
```bash
cd /path/to/agent-zero
python3 setup_archonx.py
```

### Permission Denied
If you encounter permission errors, ensure you have write access to your home directory:
```bash
chmod u+w ~/.agent-zero
```

### Configuration Not Loading
After installation, you may need to:
1. Restart Agent Zero completely
2. Clear any cached configurations
3. Verify file permissions are correct

## Support

For issues or questions about ARCHONX configuration:
1. Check the Agent Zero documentation
2. Review the template files in the `templates/` directory
3. Verify installation with `python3 setup_archonx.py --verify`
4. Open an issue on the Agent Zero GitHub repository

## Version History

- **v1.0.0** (2026-02-11): Initial ARCHONX configuration release
  - Core identity and capabilities defined
  - Security and monitoring features
  - Integration support for major platforms
  - Resource limits and optimization settings
