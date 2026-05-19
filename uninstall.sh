#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/GridLink"
DESKTOP_FILE="$HOME/.local/share/applications/gridlink.desktop"

echo "Removing GridLink ..."

rm -f "$DESKTOP_FILE"
rm -rf "$INSTALL_DIR"

echo "GridLink removed."
