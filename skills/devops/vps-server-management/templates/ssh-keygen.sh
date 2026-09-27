#!/bin/bash
# SSH Key Generation Script for VPS Access
# Run locally on your machine

set -e

KEY_NAME="vps_key"
KEY_PATH="$HOME/.ssh/$KEY_NAME"
KEY_TYPE="rsa"
KEY_BITS="4096"

echo "Generating SSH key pair..."
echo "Key will be saved to: $KEY_PATH"

if [ -f "$KEY_PATH" ]; then
    echo "Key already exists at $KEY_PATH"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

ssh-keygen -t "$KEY_TYPE" -b "$KEY_BITS" -f "$KEY_PATH" -C "vps-connection"

echo ""
echo "✅ SSH key pair generated!"
echo ""
echo "Public key (copy this to VPS):"
cat "$KEY_PATH.pub"
echo ""
echo "Private key (keep secure):"
echo "$KEY_PATH"
echo ""
echo "Next steps:"
echo "1. Add public key to GreenCloud panel → SSH Keys"
echo "2. Restart VPS in GreenCloud panel"
echo "3. Open port 22 in GreenCloud firewall"
echo "4. Open port 22 in aaPanel firewall"
echo "5. Test: ssh -i $KEY_PATH root@<VPS_IP> uptime"