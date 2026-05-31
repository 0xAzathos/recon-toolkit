#!/usr/bin/env bash
# recon-toolkit installer
# Usage: ./install.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}recon-toolkit installer${NC}"
echo "─────────────────────────────────"

# Check Python version
PY=$(python3 --version 2>&1 | awk '{print $2}')
PYMAJ=$(echo "$PY" | cut -d. -f1)
PYMIN=$(echo "$PY" | cut -d. -f2)
if [ "$PYMAJ" -lt 3 ] || { [ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -lt 10 ]; }; then
    echo -e "${RED}Error: Python 3.10+ required (found $PY)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PY${NC}"

# Install
echo -e "${YELLOW}Installing recon-toolkit...${NC}"
pip install -e . --break-system-packages --quiet

echo -e "${GREEN}✓ Installed${NC}"
echo ""
echo -e "Run with: ${GREEN}recon${NC}"
echo -e "Help:     ${GREEN}recon --help${NC}"
echo -e "Version:  ${GREEN}recon --version${NC}"
