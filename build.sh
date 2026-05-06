#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="plugin-linkedincli-builder"
SRC_DIR="/tmp/linkedin-rs-private"

if [ -d "$SRC_DIR/.git" ]; then
  echo "Updating linkedin-rs-private checkout..."
  git -C "$SRC_DIR" checkout main
  git -C "$SRC_DIR" pull --ff-only
else
  echo "Cloning linkedin-rs-private..."
  rm -rf "$SRC_DIR"
  gh repo clone askholme/linkedin-rs-private "$SRC_DIR"
fi

echo "Building linkedin-cli inside Docker..."
docker build --platform linux/amd64 -f "$SCRIPT_DIR/Dockerfile.build" -t "$IMAGE_NAME" "$SRC_DIR"

echo "Extracting binary..."
CONTAINER=$(docker create "$IMAGE_NAME")
mkdir -p "$SCRIPT_DIR/bin"
docker cp "$CONTAINER:/build/linkedin/target/release/linkedin-cli" "$SCRIPT_DIR/bin/linkedin-cli"
docker rm "$CONTAINER" > /dev/null

chmod +x "$SCRIPT_DIR/bin/linkedin-cli"
echo "Done. Binary at bin/linkedin-cli:"
ls -la "$SCRIPT_DIR/bin/linkedin-cli"
