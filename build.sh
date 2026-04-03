#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="plugin-linkedincli-builder"

echo "Building linkedin-cli inside Docker..."
docker build --platform linux/amd64 -f "$SCRIPT_DIR/Dockerfile.build" -t "$IMAGE_NAME" "$SCRIPT_DIR"

echo "Extracting binary..."
CONTAINER=$(docker create "$IMAGE_NAME")
mkdir -p "$SCRIPT_DIR/bin"
docker cp "$CONTAINER:/build/linkedin/target/release/linkedin-cli" "$SCRIPT_DIR/bin/linkedin-cli"
docker rm "$CONTAINER" > /dev/null

chmod +x "$SCRIPT_DIR/bin/linkedin-cli"
echo "Done. Binary at bin/linkedin-cli:"
ls -la "$SCRIPT_DIR/bin/linkedin-cli"
