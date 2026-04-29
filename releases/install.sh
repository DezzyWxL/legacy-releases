#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Legacy Install Script
#  Usage: curl -fsSL <url>/install.sh | bash
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

VERSION="1.0.0"
BASE_URL="${LEGACY_DOWNLOAD_URL:-https://github.com/DezzyWxL/legacy-releases/releases/download/v${VERSION}}"
CORE_PKG="legacy-core-${VERSION}.tgz"
CLI_PKG="legacy-cli-${VERSION}.tgz"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "\n${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║          Installing Legacy CLI v${VERSION}        ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}\n"

OS="$(uname -s)"
ARCH="$(uname -m)"

# ── Check / install Node.js ────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo -e "${YELLOW}⟳ Node.js not found — installing...${NC}"
  if [ "$OS" = "Darwin" ]; then
    if command -v brew &>/dev/null; then
      brew install node
    else
      NODE_URL="https://nodejs.org/dist/v22.20.0/node-v22.20.0-darwin-$([ "$ARCH" = "arm64" ] && echo arm64 || echo x64).tar.gz"
      curl -fsSL "$NODE_URL" | sudo tar -xz --strip-components=1 -C /usr/local
    fi
  elif [ "$OS" = "Linux" ]; then
    if command -v apt-get &>/dev/null; then
      curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
      sudo apt-get install -y nodejs
    elif command -v dnf &>/dev/null; then
      sudo dnf install -y nodejs
    else
      echo -e "${RED}✗ Please install Node.js 18+ manually: https://nodejs.org${NC}"
      exit 1
    fi
  else
    echo -e "${RED}✗ Unsupported OS: $OS${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Node $(node --version) installed${NC}"
else
  echo -e "${GREEN}✓ Node $(node --version) found${NC}"
fi

# ── Download packages ──────────────────────────────────────────
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo -e "${YELLOW}⟳ Downloading Legacy...${NC}"
curl -fsSL --progress-bar "${BASE_URL}/${CORE_PKG}" -o "${TMP_DIR}/${CORE_PKG}"
curl -fsSL --progress-bar "${BASE_URL}/${CLI_PKG}"  -o "${TMP_DIR}/${CLI_PKG}"
echo -e "${GREEN}✓ Downloaded${NC}"

# ── Install ────────────────────────────────────────────────────
echo -e "${YELLOW}⟳ Installing...${NC}"
if [ "$(id -u)" -eq 0 ]; then
  npm install -g "${TMP_DIR}/${CORE_PKG}" "${TMP_DIR}/${CLI_PKG}"
else
  sudo npm install -g "${TMP_DIR}/${CORE_PKG}" "${TMP_DIR}/${CLI_PKG}"
fi

# ── Verify ─────────────────────────────────────────────────────
if command -v legacy &>/dev/null; then
  echo -e "\n${GREEN}${BOLD}✓ Legacy installed successfully!${NC}"
  echo -e "${CYAN}  Run: ${BOLD}legacy${NC}"
else
  echo -e "${RED}✗ Installation failed — 'legacy' command not found${NC}"
  exit 1
fi

echo -e "\n${BOLD}Welcome to Legacy. Type 'legacy' to begin.\n${NC}"
