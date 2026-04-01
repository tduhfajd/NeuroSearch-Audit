#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

log() {
  printf '\n[%s] %s\n' "setup" "$1"
}

note() {
  printf '[%s] %s\n' "setup" "$1"
}

have() {
  command -v "$1" >/dev/null 2>&1
}

ensure_homebrew() {
  if have brew; then
    return 0
  fi
  log "Homebrew not found. Installing Homebrew."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if ! have brew; then
    if [[ -x /opt/homebrew/bin/brew ]]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -x /usr/local/bin/brew ]]; then
      eval "$(/usr/local/bin/brew shellenv)"
    fi
  fi
}

install_macos_deps() {
  ensure_homebrew

  local brew_packages=()
  local brew_casks=()

  have git || brew_packages+=("git")
  have go || brew_packages+=("go")
  have python3 || brew_packages+=("python")
  have node || brew_packages+=("node")
  have npm || brew_packages+=("node")
  have pandoc || brew_packages+=("pandoc")

  if ! have lualatex && ! have xelatex && ! have pdflatex; then
    brew_casks+=("mactex-no-gui")
  fi

  if ((${#brew_packages[@]} > 0)); then
    log "Installing missing packages with Homebrew: ${brew_packages[*]}"
    brew install "${brew_packages[@]}"
  else
    note "Core Homebrew packages are already installed"
  fi

  if ((${#brew_casks[@]} > 0)); then
    log "Installing LaTeX with Homebrew Cask: ${brew_casks[*]}"
    brew install --cask "${brew_casks[@]}" || brew install --cask mactex
  else
    note "A LaTeX engine is already available"
  fi
}

install_apt_deps() {
  if ! have apt-get; then
    echo "Unsupported Linux distribution. Install git, go, python3, python3-venv, python3-pip, nodejs, npm, pandoc, and a LaTeX engine manually." >&2
    exit 1
  fi

  log "Installing system dependencies with apt"
  sudo apt-get update
  sudo apt-get install -y \
    git \
    golang \
    python3 \
    python3-venv \
    python3-pip \
    nodejs \
    npm \
    pandoc \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    lmodern
}

install_system_deps() {
  case "$(uname -s)" in
    Darwin)
      install_macos_deps
      ;;
    Linux)
      install_apt_deps
      ;;
    *)
      echo "Unsupported OS: $(uname -s). Use the manual instructions in README.md." >&2
      exit 1
      ;;
  esac
}

setup_python() {
  log "Creating Python virtual environment"
  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
  else
    note "Virtual environment .venv already exists"
  fi
  . .venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
}

setup_node() {
  log "Installing Node.js dependencies"
  npm install
}

setup_playwright() {
  log "Installing Playwright Chromium browser"
  if [[ "$(uname -s)" == "Linux" ]]; then
    npx playwright install --with-deps chromium
  else
    npx playwright install chromium
  fi
}

print_summary() {
  log "Setup completed"
  echo "Verification:"
  echo "  python run_audit.py --help"
  echo "Next steps:"
  echo "1. Activate the environment: source .venv/bin/activate"
  echo "2. Run an audit: python run_audit.py https://example.com"
}

install_system_deps
setup_python
setup_node
setup_playwright
print_summary
