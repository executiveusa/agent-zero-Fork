#!/usr/bin/env python3
"""
Input Sanitization & Prompt Injection Defense

Security Features:
- Command whitelisting
- Input validation
- SQL injection prevention
- Path traversal protection
- Secret masking in outputs
- XSS prevention

Author: Agent Zero Security Team
Version: 1.0.0
"""

import re
import os
from typing import List, Optional, Dict, Any
from pathlib import Path


class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"('|\")(\s*)(OR|AND)(\s*)(\d+)(\s*)(=)(\s*)(\d+)",
    ]
    
    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r"ignore (previous|all) (instructions|rules|prompts)",
        r"disregard (previous|all) (instructions|rules)",
        r"you are now",
        r"new (role|character|persona|instructions)",
        r"system (prompt|message|override)",
        r"jailbreak",
        r"developer mode",
        r"sudo mode",
        r"god mode",
        r"admin mode",
        r"pretend (you are|to be)",
        r"act as (if|a|an)",
        r"roleplay as",
        r"simulate (being|that)",
    ]
    
    # Command whitelist (allowed Telegram bot commands)
    ALLOWED_COMMANDS = {
        "/start",
        "/help",
        "/status",
        "/get_secret",
        "/list_secrets",
        "/stats",
        "/backup",
        "/health",
        "/ping",
        "/lock",
    }
    
    # Secret patterns to mask in outputs
    SECRET_PATTERNS = [
        (r"sk-[a-zA-Z0-9]{20,}", "sk-***REDACTED***"),  # OpenAI/Anthropic keys
        (r"xox[baprs]-[a-zA-Z0-9-]+", "xox***REDACTED***"),  # Slack tokens
        (r"ghp_[a-zA-Z0-9]{36}", "ghp_***REDACTED***"),  # GitHub PATs
        (r"AIza[a-zA-Z0-9_-]{35}", "AIza***REDACTED***"),  # Google API keys
        (r"\d{10}:\w{35}", "***TELEGRAM_TOKEN_REDACTED***"),  # Telegram tokens
        (r"-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----.*?-----END (RSA |OPENSSH )?PRIVATE KEY-----", 
         "***PRIVATE_KEY_REDACTED***"),  # SSH keys
        (r"[a-f0-9]{64}", "***HASH_REDACTED***"),  # 64-char hashes
    ]
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
    
    def sanitize_command(self, command: str) -> Optional[str]:
        """Validate and sanitize command input"""
        if not command:
            return None
        
        command = command.strip()
        
        # Extract command (first word)
        cmd_parts = command.split()
        if not cmd_parts:
            return None
        
        base_command = cmd_parts[0].lower()
        
        # Check whitelist
        if base_command not in self.ALLOWED_COMMANDS:
            raise ValueError(f"Command not allowed: {base_command}")
        
        return command
    
    def check_sql_injection(self, text: str) -> bool:
        """Check for SQL injection patterns"""
        text_upper = text.upper()
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        
        return False
    
    def check_prompt_injection(self, text: str) -> bool:
        """Check for prompt injection attempts"""
        text_lower = text.lower()
        
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def validate_input(self, text: str, max_length: int = 1000) -> Dict[str, Any]:
        """Comprehensive input validation"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check length
        if len(text) > max_length:
            result["valid"] = False
            result["errors"].append(f"Input too long (max {max_length} chars)")
        
        # Check for SQL injection
        if self.check_sql_injection(text):
            result["valid"] = False
            result["errors"].append("Potential SQL injection detected")
        
        # Check for prompt injection
        if self.check_prompt_injection(text):
            result["valid"] = False
            result["errors"].append("Potential prompt injection detected")
        
        # Check for suspicious patterns
        if re.search(r"<script|javascript:|onerror=", text, re.IGNORECASE):
            result["valid"] = False
            result["errors"].append("Potential XSS detected")
        
        # Check for path traversal
        if re.search(r"\.\./|\.\.\\", text):
            result["warnings"].append("Path traversal pattern detected")
            if self.strict_mode:
                result["valid"] = False
                result["errors"].append("Path traversal not allowed")
        
        return result
    
    def sanitize_path(self, path: str, base_dir: str = None) -> Optional[str]:
        """Sanitize and validate file path"""
        try:
            # Normalize path
            path = os.path.normpath(path)
            
            # Remove path traversal attempts
            if ".." in path:
                raise ValueError("Path traversal not allowed")
            
            # Convert to absolute path
            if base_dir:
                full_path = os.path.join(base_dir, path)
                full_path = os.path.abspath(full_path)
                
                # Ensure path is within base_dir
                base_dir = os.path.abspath(base_dir)
                if not full_path.startswith(base_dir):
                    raise ValueError("Path outside base directory")
                
                return full_path
            else:
                return os.path.abspath(path)
                
        except Exception as e:
            raise ValueError(f"Invalid path: {e}")
    
    def mask_secrets(self, text: str) -> str:
        """Mask secrets in text output"""
        masked_text = text
        
        for pattern, replacement in self.SECRET_PATTERNS:
            masked_text = re.sub(pattern, replacement, masked_text, flags=re.DOTALL | re.IGNORECASE)
        
        return masked_text
    
    def validate_secret_key(self, key: str) -> bool:
        """Validate secret key format"""
        # Alphanumeric, underscores, hyphens only
        if not re.match(r"^[a-zA-Z0-9_-]+$", key):
            return False
        
        # Length check
        if len(key) < 1 or len(key) > 100:
            return False
        
        return True
    
    def validate_category(self, category: str) -> bool:
        """Validate category name"""
        # Alphanumeric, underscores only
        if not re.match(r"^[a-zA-Z0-9_]+$", category):
            return False
        
        # Length check
        if len(category) < 1 or len(category) > 50:
            return False
        
        return True
    
    def sanitize_telegram_input(self, text: str) -> Dict[str, Any]:
        """Sanitize input from Telegram"""
        result = self.validate_input(text, max_length=2000)
        
        # Additional Telegram-specific checks
        
        # Check for bot command spam
        if text.count("/") > 5:
            result["warnings"].append("Multiple commands detected")
        
        # Check for unusual unicode
        if re.search(r"[\u2000-\u200F\u202A-\u202E]", text):
            result["warnings"].append("Unusual unicode characters detected")
        
        return result
    
    def rate_limit_key(self, user_id: int, command: str) -> str:
        """Generate rate limit key"""
        return f"{user_id}:{command}"
    
    def sanitize_response(self, response: str) -> str:
        """Sanitize bot response before sending"""
        # Mask any secrets that might have leaked
        response = self.mask_secrets(response)
        
        # Remove any ANSI color codes
        response = re.sub(r'\x1b\[[0-9;]*[mGKH]', '', response)
        
        # Limit length
        max_length = 4096  # Telegram message limit
        if len(response) > max_length:
            response = response[:max_length - 50] + "\n\n... (truncated)"
        
        return response


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limit"""
        import time
        
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window"""
        import time
        
        now = time.time()
        
        if key not in self.requests:
            return self.max_requests
        
        # Count recent requests
        recent = sum(1 for req_time in self.requests[key] if now - req_time < self.window_seconds)
        return max(0, self.max_requests - recent)


class AccessControl:
    """Manage user permissions"""
    
    def __init__(self, admin_ids: List[int] = None):
        self.admin_ids = set(admin_ids or [])
        self.user_permissions: Dict[int, set] = {}
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_ids
    
    def add_admin(self, user_id: int):
        """Add admin user"""
        self.admin_ids.add(user_id)
    
    def remove_admin(self, user_id: int):
        """Remove admin user"""
        self.admin_ids.discard(user_id)
    
    def grant_permission(self, user_id: int, permission: str):
        """Grant permission to user"""
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = set()
        self.user_permissions[user_id].add(permission)
    
    def revoke_permission(self, user_id: int, permission: str):
        """Revoke permission from user"""
        if user_id in self.user_permissions:
            self.user_permissions[user_id].discard(permission)
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has permission"""
        # Admins have all permissions
        if self.is_admin(user_id):
            return True
        
        return user_id in self.user_permissions and permission in self.user_permissions[user_id]
    
    def check_command_access(self, user_id: int, command: str) -> bool:
        """Check if user can execute command"""
        # Public commands
        public_commands = {"/start", "/help", "/ping"}
        if command in public_commands:
            return True
        
        # Admin-only commands
        admin_commands = {"/backup", "/stats", "/health"}
        if command in admin_commands:
            return self.is_admin(user_id)
        
        # Protected commands (require specific permissions)
        if command == "/get_secret":
            return self.has_permission(user_id, "read_secrets")
        
        if command == "/list_secrets":
            return self.has_permission(user_id, "list_secrets")
        
        # Default deny
        return False
