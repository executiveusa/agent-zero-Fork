#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════╗
# ║     Military-Grade Secrets Encryption Tool (Age + GPG)              ║
# ║                  ArchonX OS Ecosystem                                ║
# ╚══════════════════════════════════════════════════════════════════════╝

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_FILE="${1:-$SCRIPT_DIR/secrets.json}"
OUTPUT_FILE="${SECRETS_FILE}.encrypted"

# Check if secrets file exists
if [ ! -f "$SECRETS_FILE" ]; then
    print_error "Secrets file not found: $SECRETS_FILE"
    print_info "Usage: $0 [secrets-file.json]"
    exit 1
fi

print_info "ArchonX OS - Military-Grade Secrets Encryption"
echo ""

# ══════════════════════════════════════════════════════════════════════
# Option 1: Age Encryption (Modern, Fast, Secure)
# ══════════════════════════════════════════════════════════════════════

encrypt_with_age() {
    print_info "Encrypting with Age (modern cryptography)..."

    # Check if age is installed
    if ! command -v age &> /dev/null; then
        print_warning "Age not installed. Installing..."

        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            if command -v apt-get &> /dev/null; then
                apt-get update && apt-get install -y age
            elif command -v yum &> /dev/null; then
                yum install -y age
            else
                print_error "Please install age manually: https://github.com/FiloSottile/age"
                return 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install age
        else
            print_error "Please install age manually: https://github.com/FiloSottile/age"
            return 1
        fi
    fi

    # Generate age key if it doesn't exist
    AGE_KEY_FILE="$SCRIPT_DIR/.age-key.txt"
    if [ ! -f "$AGE_KEY_FILE" ]; then
        print_info "Generating new age key pair..."
        age-keygen -o "$AGE_KEY_FILE"
        chmod 600 "$AGE_KEY_FILE"
        print_success "Age key pair generated: $AGE_KEY_FILE"
        echo ""
        print_warning "IMPORTANT: Backup this key file! You'll need it to decrypt!"
        print_info "Public key:"
        grep "# public key:" "$AGE_KEY_FILE" | cut -d: -f2 | tr -d ' '
        echo ""
    fi

    # Get recipient (public key)
    RECIPIENT=$(grep "# public key:" "$AGE_KEY_FILE" | cut -d: -f2 | tr -d ' ')

    # Encrypt
    age -e -r "$RECIPIENT" -o "${OUTPUT_FILE}.age" "$SECRETS_FILE"

    if [ $? -eq 0 ]; then
        print_success "Encrypted with Age: ${OUTPUT_FILE}.age"
        print_info "Decrypt with: age -d -i $AGE_KEY_FILE ${OUTPUT_FILE}.age > secrets.json"
        return 0
    else
        print_error "Age encryption failed"
        return 1
    fi
}

# ══════════════════════════════════════════════════════════════════════
# Option 2: GPG Encryption (Industry Standard)
# ══════════════════════════════════════════════════════════════════════

encrypt_with_gpg() {
    print_info "Encrypting with GPG (industry standard)..."

    # Check if gpg is installed
    if ! command -v gpg &> /dev/null; then
        print_warning "GPG not installed. Installing..."

        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                apt-get update && apt-get install -y gnupg
            elif command -v yum &> /dev/null; then
                yum install -y gnupg2
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install gnupg
        fi
    fi

    # Check if GPG key exists
    if ! gpg --list-secret-keys "archonx@executiveusa.com" &> /dev/null; then
        print_info "Generating new GPG key..."

        # Generate GPG key batch mode
        cat > "$SCRIPT_DIR/gpg-gen-key.batch" <<EOF
%echo Generating ArchonX OS GPG key
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: ArchonX OS
Name-Email: archonx@executiveusa.com
Expire-Date: 0
%no-protection
%commit
%echo Done
EOF

        gpg --batch --gen-key "$SCRIPT_DIR/gpg-gen-key.batch"
        rm "$SCRIPT_DIR/gpg-gen-key.batch"

        print_success "GPG key generated"
        print_info "Key ID:"
        gpg --list-secret-keys "archonx@executiveusa.com" | grep -A1 "sec" | tail -1 | tr -d ' '
        echo ""
    fi

    # Encrypt
    gpg --encrypt --recipient "archonx@executiveusa.com" --armor --output "${OUTPUT_FILE}.gpg" "$SECRETS_FILE"

    if [ $? -eq 0 ]; then
        print_success "Encrypted with GPG: ${OUTPUT_FILE}.gpg"
        print_info "Decrypt with: gpg --decrypt ${OUTPUT_FILE}.gpg > secrets.json"
        return 0
    else
        print_error "GPG encryption failed"
        return 1
    fi
}

# ══════════════════════════════════════════════════════════════════════
# Option 3: OpenSSL (Fallback - Password-based)
# ══════════════════════════════════════════════════════════════════════

encrypt_with_openssl() {
    print_info "Encrypting with OpenSSL (password-based)..."

    # Prompt for password
    read -sp "Enter encryption password: " PASSWORD
    echo ""
    read -sp "Confirm password: " PASSWORD2
    echo ""

    if [ "$PASSWORD" != "$PASSWORD2" ]; then
        print_error "Passwords do not match"
        return 1
    fi

    # Encrypt with AES-256-CBC
    echo "$PASSWORD" | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 -in "$SECRETS_FILE" -out "${OUTPUT_FILE}.enc" -pass stdin

    if [ $? -eq 0 ]; then
        print_success "Encrypted with OpenSSL: ${OUTPUT_FILE}.enc"
        print_info "Decrypt with: openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in ${OUTPUT_FILE}.enc -out secrets.json"
        return 0
    else
        print_error "OpenSSL encryption failed"
        return 1
    fi
}

# ══════════════════════════════════════════════════════════════════════
# Main Menu
# ══════════════════════════════════════════════════════════════════════

echo "Select encryption method:"
echo "1) Age (Modern, Fast, Recommended)"
echo "2) GPG (Industry Standard)"
echo "3) OpenSSL (Password-based, Portable)"
echo "4) All of the above (Triple encryption)"
echo ""
read -p "Choice [1-4]: " CHOICE

case $CHOICE in
    1)
        encrypt_with_age
        ;;
    2)
        encrypt_with_gpg
        ;;
    3)
        encrypt_with_openssl
        ;;
    4)
        print_info "Triple encryption - Maximum security"
        encrypt_with_age
        encrypt_with_gpg
        encrypt_with_openssl
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_success "Encryption complete!"
print_warning "Security reminders:"
echo "  1. Backup your encryption keys securely"
echo "  2. Never commit unencrypted secrets to git"
echo "  3. Store keys separately from encrypted files"
echo "  4. Use different passwords for different environments"
echo ""
print_info "Original file: $SECRETS_FILE"
print_info "Consider deleting the original after verifying encryption works"
