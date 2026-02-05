#!/bin/bash
# vault_access_guard.sh
# ─────────────────────────────────────────────────────────────────────
# Standalone vault-access checker.  Can be called from:
#   • Claude Code PreToolUse hook  (.claude/hooks/vault-guard.sh)
#   • Agent Zero input_sanitizer
#   • Any other pre-execution gate
#
# Exit 0 = allowed.  Exit 1 = blocked.
#
# Usage:
#   scripts/vault_access_guard.sh "the command to check"
#   echo "$CMD" | scripts/vault_access_guard.sh
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

# Read command from arg or stdin
if [[ $# -gt 0 ]]; then
    COMMAND="$1"
elif [[ ! -t 0 ]]; then
    COMMAND=$(cat)
else
    COMMAND=""
fi

# Already authorised for this shell session?
if [[ "${VAULT_ACCESS_AUTHORIZED:-false}" == "true" ]]; then
    exit 0
fi

# Guarded paths / keywords
declare -a GUARDED=(
    "secure/"
    ".vault/"
    "tmp/vault"
    "secrets_vault"
    "vault_manager"
    "vault_cli"
    "master.key"
    "vault.key"
)

for pat in "${GUARDED[@]}"; do
    if echo "$COMMAND" | grep -qF "$pat" 2>/dev/null; then
        echo "[VAULT GUARD] BLOCKED -- command references '$pat'"
        echo "[VAULT GUARD] Set VAULT_ACCESS_AUTHORIZED=true to allow."
        exit 1
    fi
done

exit 0
