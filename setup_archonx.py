#!/usr/bin/env python3
"""
Setup script for ARCHONX Agent Zero configuration
This script creates the ~/.agent-zero/ directory structure and installs
the ARCHONX configuration files.
"""

import os
import shutil
from pathlib import Path


# Simple color printing without external dependencies
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_color(text, color='', bold=False):
    """Print colored text to console."""
    prefix = f"{Colors.BOLD if bold else ''}{color}"
    print(f"{prefix}{text}{Colors.END}")


def setup_archonx():
    """
    Set up the ~/.agent-zero/ directory structure with ARCHONX files.
    
    Directory structure:
    ~/.agent-zero/
    ├── prompts/
    │   └── ARCHONX_AGENT_ZERO_PROMPT.md
    ├── config/
    │   └── archonx-config.json
    └── ...
    """
    
    # Determine the home directory
    home_dir = Path.home()
    agent_zero_dir = home_dir / ".agent-zero"
    
    # Create directory structure
    prompts_dir = agent_zero_dir / "prompts"
    config_dir = agent_zero_dir / "config"
    
    print_color("\n🚀 ARCHONX Setup", Colors.CYAN, bold=True)
    print_color("=" * 60, Colors.WHITE)
    
    # Create directories
    print_color(f"\n📁 Creating directory structure in {agent_zero_dir}...", Colors.YELLOW)
    
    try:
        prompts_dir.mkdir(parents=True, exist_ok=True)
        print_color(f"  ✅ Created: {prompts_dir}", Colors.GREEN)
        
        config_dir.mkdir(parents=True, exist_ok=True)
        print_color(f"  ✅ Created: {config_dir}", Colors.GREEN)
        
    except Exception as e:
        print_color(f"  ❌ Error creating directories: {e}", Colors.RED)
        return False
    
    # Get the script directory to find template files
    script_dir = Path(__file__).parent
    templates_dir = script_dir / "templates"
    
    # Copy ARCHONX prompt template
    print_color("\n📄 Installing ARCHONX files...", Colors.YELLOW)
    
    try:
        # Copy prompt file
        prompt_src = templates_dir / "ARCHONX_AGENT_ZERO_PROMPT.md"
        prompt_dst = prompts_dir / "ARCHONX_AGENT_ZERO_PROMPT.md"
        
        if prompt_src.exists():
            shutil.copy2(prompt_src, prompt_dst)
            print_color(f"  ✅ Installed: {prompt_dst}", Colors.GREEN)
        else:
            print_color(f"  ❌ Template not found: {prompt_src}", Colors.RED)
            return False
        
        # Copy config file
        config_src = templates_dir / "archonx-config.json"
        config_dst = config_dir / "archonx-config.json"
        
        if config_src.exists():
            shutil.copy2(config_src, config_dst)
            print_color(f"  ✅ Installed: {config_dst}", Colors.GREEN)
        else:
            print_color(f"  ❌ Template not found: {config_src}", Colors.RED)
            return False
            
    except Exception as e:
        print_color(f"  ❌ Error copying files: {e}", Colors.RED)
        return False
    
    # Success message
    print_color("\n" + "=" * 60, Colors.WHITE)
    print_color("✅ ARCHONX setup completed successfully!\n", Colors.GREEN, bold=True)
    
    print_color("📍 Files installed to:", Colors.CYAN)
    print_color(f"   • {prompt_dst}", Colors.WHITE)
    print_color(f"   • {config_dst}", Colors.WHITE)
    
    print_color("\n💡 Next steps:", Colors.YELLOW)
    print_color("   1. Review and customize the ARCHONX prompt file", Colors.WHITE)
    print_color("   2. Update archonx-config.json with your settings", Colors.WHITE)
    print_color("   3. Restart Agent Zero to apply changes\n", Colors.WHITE)
    
    return True


def verify_installation():
    """Verify that ARCHONX files are properly installed."""
    home_dir = Path.home()
    agent_zero_dir = home_dir / ".agent-zero"
    
    prompt_file = agent_zero_dir / "prompts" / "ARCHONX_AGENT_ZERO_PROMPT.md"
    config_file = agent_zero_dir / "config" / "archonx-config.json"
    
    print_color("\n🔍 Verifying installation...", Colors.CYAN, bold=True)
    
    all_good = True
    
    if prompt_file.exists():
        print_color(f"  ✅ Found: {prompt_file}", Colors.GREEN)
    else:
        print_color(f"  ❌ Missing: {prompt_file}", Colors.RED)
        all_good = False
    
    if config_file.exists():
        print_color(f"  ✅ Found: {config_file}", Colors.GREEN)
    else:
        print_color(f"  ❌ Missing: {config_file}", Colors.RED)
        all_good = False
    
    if all_good:
        print_color("\n✅ All files verified!\n", Colors.GREEN, bold=True)
    else:
        print_color("\n❌ Some files are missing. Please run setup again.\n", Colors.RED, bold=True)
    
    return all_good


if __name__ == "__main__":
    import sys
    
    # Check if running in verify mode
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_installation()
    else:
        success = setup_archonx()
        if success:
            verify_installation()
        sys.exit(0 if success else 1)
