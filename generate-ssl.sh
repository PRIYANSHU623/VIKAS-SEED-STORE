#!/bin/bash
# ============================================================
# SSL Certificate Generation for KrishiSathi
# ============================================================
# This script generates self-signed SSL certificates for development/testing
# For production, use Let's Encrypt with Certbot

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="$SCRIPT_DIR/nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"
DAYS_VALID=365

echo "=================================================="
echo "SSL Certificate Generation"
echo "=================================================="

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Check if certificates already exist
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "✓ SSL certificates already exist"
    echo "  Certificate: $CERT_FILE"
    echo "  Key: $KEY_FILE"
    exit 0
fi

echo ""
echo "Generating self-signed certificate..."
echo "Validity: $DAYS_VALID days"
echo ""

# Generate self-signed certificate (for development/testing)
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -days "$DAYS_VALID" \
    -subj "/C=IN/ST=State/L=City/O=KrishiSathi/CN=localhost"

# Set proper permissions
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo ""
echo "✓ SSL certificates generated successfully"
echo "  Certificate: $CERT_FILE"
echo "  Key: $KEY_FILE"
echo ""
echo "=================================================="
echo "IMPORTANT: For Production Use"
echo "=================================================="
echo "Replace these self-signed certificates with:"
echo "  - Let's Encrypt certificates (recommended)"
echo "  - Valid CA-signed certificates"
echo ""
echo "Use certbot for automatic Let's Encrypt setup:"
echo "  certbot certonly --standalone -d yourdomain.com"
echo "=================================================="
