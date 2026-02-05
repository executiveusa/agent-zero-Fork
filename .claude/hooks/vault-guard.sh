#!/bin/bash
# vault-guard.sh
# ─────────────────────────────────────────────────────────────────────
# Claude Code PreToolUse hook for Bash commands.
# Blocks any command that reads or writes vault/secrets paths unless
# explicitly authorised via VAULT_ACCESS_AUTHORIZED=true.
#
# This is a defence-in-depth layer on top of the encrypted vault itself.
# Even if an agent hallucinates a command that touches the vault, this
# hook intercepts it before the shell runs it.
# ─────────────────────────────────────────────────────────────────────

# The command being attempted is passed as $1 (or via CLAUDE_TOOL_INPUT)
COMMAND="${1:-${CLAUDE_TOOL_INPUT:-}}"

# Paths we guard
VAULT_PATTERNS=(
    "secure/"
    ".vault/"
    "tmp/vault"
    "secrets_vault"
    "vault_manager"
    "vault_cli"
)

# Already authorised?
if [[ "${VAULT_ACCESS_AUTHORIZED:-false}" == "true" ]]; then
    exit 0
fi

# Check each guarded pattern
for pat in "${VAULT_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$pat"; then
        echo "HOOK BLOCKED: command touches a guarded vault path ($pat)."
        echo "To proceed, set VAULT_ACCESS_AUTHORIZED=true in your environment."
        exit 1
    fi
done

# Nothing matched -- allow
exit 0
