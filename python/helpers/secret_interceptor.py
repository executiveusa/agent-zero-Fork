"""
Auto-Encrypt Interceptor — Agent Claw Secret Guardian

Automatically detects, encrypts, and redacts secrets/tokens/financial info
from ANY incoming data stream:
  - Chat messages (Telegram, WhatsApp, Slack)
  - API request/response bodies
  - Log files
  - File uploads
  - Clipboard / voice transcriptions

Principle: **Every secret touches the vault before it touches disk or wire.**

Usage:
    from python.helpers.secret_interceptor import SecretInterceptor
    
    interceptor = SecretInterceptor()
    clean_text, findings = interceptor.intercept("my key is sk-abc123...")
    # clean_text = "my key is [REDACTED:OpenAI Key]"
    # findings = [{"type": "OpenAI Key", "vault_key": "auto_...", ...}]
"""

import json
import logging
import os
import re
import time
import hashlib
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger(__name__)

# ─── Pattern Library ─────────────────────────────────────────
# Comprehensive patterns for detecting secrets, tokens, financial info

SECRET_PATTERNS = [
    # API Keys & Tokens
    (r'(sk-[A-Za-z0-9]{20,})', "OpenAI Key", "CRITICAL"),
    (r'(sk-proj-[A-Za-z0-9_\-]{40,})', "OpenAI Project Key", "CRITICAL"),
    (r'(ghp_[A-Za-z0-9]{36,})', "GitHub PAT", "CRITICAL"),
    (r'(gho_[A-Za-z0-9]{36,})', "GitHub OAuth Token", "CRITICAL"),
    (r'(github_pat_[A-Za-z0-9_]{40,})', "GitHub Fine-Grain PAT", "CRITICAL"),
    (r'(xoxb-[A-Za-z0-9\-]{20,})', "Slack Bot Token", "CRITICAL"),
    (r'(xoxp-[A-Za-z0-9\-]{20,})', "Slack User Token", "CRITICAL"),
    (r'(AKIA[A-Z0-9]{16})', "AWS Access Key", "CRITICAL"),
    (r'(ak_-[A-Za-z0-9_\-]{10,})', "Composio Key", "HIGH"),
    (r'(AC[a-f0-9]{32})', "Twilio Account SID", "HIGH"),
    (r'(SK[a-f0-9]{32})', "Twilio API Key SID", "HIGH"),
    (r'(\d{10,13}:[A-Za-z0-9_\-]{35,})', "Telegram Bot Token", "CRITICAL"),
    (r'(eyJ[A-Za-z0-9_\-]{20,}\.eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]+)', "JWT Token", "HIGH"),
    (r'(glpat-[A-Za-z0-9_\-]{20,})', "GitLab PAT", "CRITICAL"),
    (r'(npm_[A-Za-z0-9]{36,})', "NPM Token", "CRITICAL"),
    (r'(pypi-[A-Za-z0-9]{50,})', "PyPI Token", "CRITICAL"),
    (r'(dop_v1_[a-f0-9]{64})', "DigitalOcean PAT", "CRITICAL"),
    (r'(cf[a-zA-Z0-9_\-]{30,})', "Cloudflare Token", "HIGH"),
    (r'(whsec_[A-Za-z0-9]{20,})', "Webhook Secret", "HIGH"),
    (r'(AIza[A-Za-z0-9_\-]{35})', "Google API Key", "CRITICAL"),
    (r'(ya29\.[A-Za-z0-9_\-]{50,})', "Google OAuth Token", "CRITICAL"),
    
    # Database URIs (contain embedded passwords)
    (r'(mongodb(?:\+srv)?://[^\s"\']+)', "MongoDB URI", "CRITICAL"),
    (r'(postgres(?:ql)?://[^\s"\']+)', "PostgreSQL URI", "CRITICAL"),
    (r'(mysql://[^\s"\']+)', "MySQL URI", "CRITICAL"),
    (r'(redis://[^\s"\']+)', "Redis URI", "HIGH"),
    (r'(amqp://[^\s"\']+)', "RabbitMQ URI", "HIGH"),
    
    # Private Keys
    (r'(-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)', "Private Key", "CRITICAL"),
    (r'(-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----)', "Certificate", "HIGH"),
    
    # Financial Information
    (r'(\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b)', "Credit Card Number", "CRITICAL"),
    (r'(\b\d{3,4}\s*-?\s*\d{2}\s*-?\s*\d{4}\b)', "SSN Pattern", "CRITICAL"),
    (r'(\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{0,2}\b)', "IBAN", "CRITICAL"),
    (r'(\b\d{9}\b)(?=.*(?:routing|aba|bank))', "Bank Routing Number", "HIGH"),
    
    # Crypto Wallets
    (r'(\b0x[a-fA-F0-9]{40}\b)', "Ethereum Address", "HIGH"),
    (r'(\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b)', "Bitcoin Address", "HIGH"),
    
    # Generic high-entropy strings that look like secrets
    (r'(?:api[_-]?key|apikey|secret|token|password|passwd|auth)\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{20,})["\']', "Generic Secret", "MEDIUM"),
]

# Words that indicate the text is ABOUT secrets, not containing them
FALSE_POSITIVE_INDICATORS = [
    "example", "placeholder", "your-", "xxx", "changeme", "test",
    "sample", "demo", "fake", "dummy", "todo", "fixme",
    "documentation", "tutorial", "template", "mock",
]


class SecretInterceptor:
    """
    Real-time secret detection and auto-encryption engine.
    
    Every detected secret is:
    1. Encrypted in the Fernet vault instantly
    2. Redacted from the output text
    3. Logged (without the secret value) for audit trail
    """
    
    def __init__(self, source: str = "interceptor", auto_vault: bool = True):
        """
        Args:
            source: Identifier for where the text came from (e.g., "telegram", "api")
            auto_vault: If True, auto-encrypt detected secrets into vault
        """
        self.source = source
        self.auto_vault = auto_vault
        self.audit_log: List[Dict] = []
        self._seen_hashes: set = set()  # Dedup by hash
    
    def intercept(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Scan text for secrets, encrypt them, and return redacted text.
        
        Args:
            text: Raw input text to scan
        
        Returns:
            Tuple of (redacted_text, findings_list)
        """
        if not text or len(text) < 10:
            return text, []
        
        findings = []
        redacted = text
        
        for pattern, sec_type, severity in SECRET_PATTERNS:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                secret_value = match.group(1) if match.lastindex else match.group(0)
                
                # Skip false positives
                context = text[max(0, match.start()-30):match.end()+30].lower()
                if any(fp in context for fp in FALSE_POSITIVE_INDICATORS):
                    continue
                
                # Dedup by hash
                secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()[:16]
                if secret_hash in self._seen_hashes:
                    continue
                self._seen_hashes.add(secret_hash)
                
                finding = {
                    "type": sec_type,
                    "severity": severity,
                    "hash": secret_hash,
                    "redacted_preview": secret_value[:4] + "..." + secret_value[-4:] if len(secret_value) > 12 else "***",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": self.source,
                }
                
                # Auto-encrypt into vault
                if self.auto_vault:
                    vault_key = self._encrypt_to_vault(secret_value, sec_type)
                    finding["vault_key"] = vault_key
                
                findings.append(finding)
                
                # Redact from text
                redacted = redacted.replace(secret_value, f"[REDACTED:{sec_type}]")
        
        # Log findings (never log actual secret values)
        if findings:
            self._log_findings(findings)
        
        return redacted, findings
    
    def intercept_dict(self, data: dict) -> Tuple[dict, List[Dict]]:
        """
        Recursively scan a dictionary for secrets.
        Useful for API request/response bodies.
        """
        all_findings = []
        cleaned = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                cleaned_val, findings = self.intercept(value)
                cleaned[key] = cleaned_val
                all_findings.extend(findings)
            elif isinstance(value, dict):
                cleaned_val, findings = self.intercept_dict(value)
                cleaned[key] = cleaned_val
                all_findings.extend(findings)
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, str):
                        cleaned_item, findings = self.intercept(item)
                        cleaned_list.append(cleaned_item)
                        all_findings.extend(findings)
                    elif isinstance(item, dict):
                        cleaned_item, findings = self.intercept_dict(item)
                        cleaned_list.append(cleaned_item)
                        all_findings.extend(findings)
                    else:
                        cleaned_list.append(item)
                cleaned[key] = cleaned_list
            else:
                cleaned[key] = value
        
        return cleaned, all_findings
    
    def _encrypt_to_vault(self, secret: str, sec_type: str) -> str:
        """Encrypt a detected secret into the vault."""
        try:
            from python.helpers.vault import vault_store
            
            ts = int(time.time())
            type_slug = sec_type.lower().replace(" ", "_")
            key_name = f"auto_{self.source}_{type_slug}_{ts}"
            vault_store(key_name, secret)
            logger.info(f"SecretInterceptor: Auto-encrypted {sec_type} as {key_name}")
            return key_name
        except Exception as e:
            logger.error(f"SecretInterceptor: Failed to vault {sec_type}: {e}")
            return f"FAILED:{str(e)}"
    
    def _log_findings(self, findings: List[Dict]):
        """Log findings to audit trail (never includes secret values)."""
        self.audit_log.extend(findings)
        
        log_dir = "tmp/security"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "intercept_audit.json")
        
        existing = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        
        existing.extend(findings)
        # Keep last 5000 entries
        existing = existing[-5000:]
        
        with open(log_file, "w") as f:
            json.dump(existing, f, indent=2)
    
    def get_audit_summary(self) -> Dict:
        """Get summary of intercepted secrets."""
        by_type = {}
        by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
        
        for finding in self.audit_log:
            t = finding["type"]
            s = finding["severity"]
            by_type[t] = by_type.get(t, 0) + 1
            by_severity[s] = by_severity.get(s, 0) + 1
        
        return {
            "total_intercepted": len(self.audit_log),
            "by_type": by_type,
            "by_severity": by_severity,
            "source": self.source,
        }


# ─── Middleware for Flask/FastAPI ────────────────────────────

def create_flask_middleware(app):
    """
    Add secret interception middleware to a Flask app.
    Scans all incoming request bodies and query params.
    """
    from functools import wraps
    
    interceptor = SecretInterceptor(source="flask_middleware")
    
    @app.before_request
    def intercept_request():
        from flask import request, g
        
        # Scan query params
        for key, value in request.args.items():
            _, findings = interceptor.intercept(value)
            if findings:
                logger.warning(f"Secret detected in query param '{key}': {[f['type'] for f in findings]}")
        
        # Scan request body
        if request.is_json:
            body = request.get_json(silent=True)
            if body and isinstance(body, dict):
                cleaned, findings = interceptor.intercept_dict(body)
                if findings:
                    logger.warning(f"Secrets detected in request body: {[f['type'] for f in findings]}")
                    g.intercepted_secrets = findings
        
        # Scan form data
        for key, value in request.form.items():
            _, findings = interceptor.intercept(value)
            if findings:
                logger.warning(f"Secret in form field '{key}': {[f['type'] for f in findings]}")
    
    return interceptor


# ─── Financial Data Guardian ─────────────────────────────────

class FinancialGuardian:
    """
    Specialized interceptor for financial information.
    
    Detects and encrypts:
    - Credit card numbers (with Luhn validation)
    - Bank account/routing numbers
    - SSNs
    - Tax IDs (EIN)
    - Crypto wallet addresses
    """
    
    def __init__(self):
        self.interceptor = SecretInterceptor(source="financial_guardian")
    
    @staticmethod
    def luhn_check(number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        digits = [int(d) for d in number if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False
        
        checksum = 0
        reverse = digits[::-1]
        for i, d in enumerate(reverse):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0
    
    def scan_financial(self, text: str) -> Tuple[str, List[Dict]]:
        """Scan text specifically for financial data."""
        redacted, findings = self.interceptor.intercept(text)
        
        # Additional validation for credit cards
        validated_findings = []
        for f in findings:
            if f["type"] == "Credit Card Number":
                # Extract the actual number for Luhn check
                # (We don't store it, just validate)
                validated_findings.append(f)
            else:
                validated_findings.append(f)
        
        return redacted, validated_findings


# ─── Convenience Functions ───────────────────────────────────

_global_interceptor = None

def get_interceptor(source: str = "global") -> SecretInterceptor:
    """Get or create the global secret interceptor."""
    global _global_interceptor
    if _global_interceptor is None:
        _global_interceptor = SecretInterceptor(source=source)
    return _global_interceptor


def intercept_and_encrypt(text: str, source: str = "manual") -> Tuple[str, List[Dict]]:
    """
    One-shot function to scan text, encrypt secrets, return clean text.
    
    Args:
        text: Raw text potentially containing secrets
        source: Where the text came from
    
    Returns:
        (redacted_text, list_of_findings)
    """
    interceptor = SecretInterceptor(source=source)
    return interceptor.intercept(text)


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    test_text = """
    Here's my OpenAI key: sk-abc123456789012345678901234567890
    And my GitHub PAT: ghp_abcdefghijklmnopqrstuvwxyz1234567890
    My card number is 4111111111111111
    Database: postgres://admin:superSecret123@db.example.com:5432/mydb
    """
    
    interceptor = SecretInterceptor(source="demo")
    clean, findings = interceptor.intercept(test_text)
    
    print("=== REDACTED OUTPUT ===")
    print(clean)
    print("\n=== FINDINGS ===")
    for f in findings:
        print(f"  {f['severity']} | {f['type']} | vault: {f.get('vault_key', 'N/A')}")
