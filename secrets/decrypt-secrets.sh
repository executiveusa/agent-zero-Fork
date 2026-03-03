#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════╗
# ║     Military-Grade Secrets Decryption Tool (Age + GPG)              ║
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
ENCRYPTED_FILE="${1}"
OUTPUT_FILE="${2:-$SCRIPT_DIR/secrets.json}"

if [ -z "$ENCRYPTED_FILE" ]; then
    print_error "Usage: $0 <encrypted-file> [output-file]"
    print_info "Examples:"
    echo "  $0 secrets.json.encrypted.age"
    echo "  $0 secrets.json.encrypted.gpg"
    echo "  $0 secrets.json.encrypted.enc"
    exit 1
fi

if [ ! -f "$ENCRYPTED_FILE" ]; then
    print_error "Encrypted file not found: $ENCRYPTED_FILE"
    exit 1
fi

print_info "ArchonX OS - Military-Grade Secrets Decryption"
echo ""

# Detect encryption type
if [[ "$ENCRYPTED_FILE" == *.age ]]; then
    print_info "Detected Age encryption"

    AGE_KEY_FILE="$SCRIPT_DIR/.age-key.txt"

    if [ ! -f "$AGE_KEY_FILE" ]; then
        print_error "Age key not found: $AGE_KEY_FILE"
        print_info "Please provide the age key file"
        read -p "Enter path to age key file: " AGE_KEY_FILE

        if [ ! -f "$AGE_KEY_FILE" ]; then
            print_error "Key file not found"
            exit 1
        fi
    fi

    age -d -i "$AGE_KEY_FILE" "$ENCRYPTED_FILE" > "$OUTPUT_FILE"

    if [ $? -eq 0 ]; then
        print_success "Decrypted with Age: $OUTPUT_FILE"
    else
        print_error "Age decryption failed"
        exit 1
    fi

elif [[ "$ENCRYPTED_FILE" == *.gpg ]] || [[ "$ENCRYPTED_FILE" == *.asc ]]; then
    print_info "Detected GPG encryption"

    gpg --decrypt "$ENCRYPTED_FILE" > "$OUTPUT_FILE" 2>/dev/null

    if [ $? -eq 0 ]; then
        print_success "Decrypted with GPG: $OUTPUT_FILE"
    else
        print_error "GPG decryption failed"
        exit 1
    fi

elif [[ "$ENCRYPTED_FILE" == *.enc ]]; then
    print_info "Detected OpenSSL encryption"

    read -sp "Enter decryption password: " PASSWORD
    echo ""

    echo "$PASSWORD" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in "$ENCRYPTED_FILE" -out "$OUTPUT_FILE" -pass stdin

    if [ $? -eq 0 ]; then
        print_success "Decrypted with OpenSSL: $OUTPUT_FILE"
    else
        print_error "OpenSSL decryption failed"
        rm -f "$OUTPUT_FILE"
        exit 1
    fi

else
    print_error "Unknown encryption type"
    print_info "Supported: .age, .gpg, .asc, .enc"
    exit 1
fi

echo ""
print_success "Decryption complete!"
print_info "Decrypted file: $OUTPUT_FILE"
print_warning "Remember to delete this file after use!"
