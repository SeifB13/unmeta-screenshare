#!/usr/bin/env bash
# Install UnMeta Screenshare on macOS or Linux:
#   curl -fsSL https://raw.githubusercontent.com/SeifB13/unmeta-screenshare/main/scripts/install.sh | bash
# Installs scrcpy and adb if missing (asking first), then the app with pipx.
set -euo pipefail

REPO="${UNMETA_REPO:-https://github.com/SeifB13/unmeta-screenshare}"
MIN_SCRCPY_MAJOR=3

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

confirm() {
    # Reads from the terminal so it also works through `curl | bash`.
    local answer
    if [ -r /dev/tty ]; then
        read -r -p "$1 [Y/n] " answer </dev/tty || answer=n
    else
        answer=y
    fi
    [[ -z "$answer" || "$answer" =~ ^[Yy] ]]
}

run_root() {
    if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi
}

scrcpy_major() {
    scrcpy --version 2>/dev/null | sed -n 's/^scrcpy \([0-9]*\)\..*/\1/p' | head -n1
}

install_macos() {
    if ! have brew; then
        warn "Homebrew is required: https://brew.sh"
        exit 1
    fi
    local pkgs=()
    have scrcpy || pkgs+=(scrcpy)
    have pipx || pkgs+=(pipx)
    if [ ${#pkgs[@]} -gt 0 ] && confirm "Install ${pkgs[*]} with Homebrew?"; then
        brew install "${pkgs[@]}"
    fi
    if ! have adb && confirm "Install adb (android-platform-tools) with Homebrew?"; then
        brew install --cask android-platform-tools
    fi
}

install_linux() {
    local pm=""
    for candidate in apt-get dnf pacman zypper; do
        if have "$candidate"; then pm=$candidate; break; fi
    done
    local pkgs=()
    case "$pm" in
        apt-get)
            have adb || pkgs+=(adb android-sdk-platform-tools-common)
            have scrcpy || pkgs+=(scrcpy)
            have pipx || pkgs+=(pipx) ;;
        dnf)
            have adb || pkgs+=(android-tools)
            have scrcpy || pkgs+=(scrcpy)
            have pipx || pkgs+=(pipx) ;;
        pacman)
            have adb || pkgs+=(android-tools android-udev)
            have scrcpy || pkgs+=(scrcpy)
            have pipx || pkgs+=(python-pipx) ;;
        zypper)
            have adb || pkgs+=(android-tools)
            have scrcpy || pkgs+=(scrcpy)
            have pipx || pkgs+=(python3-pipx) ;;
        *)
            warn "Unknown package manager: install adb, scrcpy (>= $MIN_SCRCPY_MAJOR.0) and pipx yourself." ;;
    esac
    if [ ${#pkgs[@]} -gt 0 ] && confirm "Install ${pkgs[*]} with $pm?"; then
        case "$pm" in
            apt-get) run_root apt-get update && run_root apt-get install -y "${pkgs[@]}" ;;
            dnf) run_root dnf install -y "${pkgs[@]}" ;;
            pacman) run_root pacman -S --needed --noconfirm "${pkgs[@]}" ;;
            zypper) run_root zypper install -y "${pkgs[@]}" ;;
        esac
    fi
}

case "$(uname -s)" in
    Darwin) install_macos ;;
    Linux) install_linux ;;
    *) warn "Unsupported system. On Windows, use the installer from the Releases page."; exit 1 ;;
esac

if ! have pipx; then
    warn "pipx is missing: https://pipx.pypa.io/stable/installation/"
    exit 1
fi

info "Installing UnMeta Screenshare from $REPO"
pipx install --force "git+$REPO"
pipx ensurepath >/dev/null 2>&1 || true

have adb || warn "adb is still missing: the app will not find the headset."
major="$(scrcpy_major || true)"
if [ -z "$major" ]; then
    warn "scrcpy is still missing."
elif [ "$major" -lt "$MIN_SCRCPY_MAJOR" ]; then
    warn "scrcpy $major.x is too old (>= $MIN_SCRCPY_MAJOR.0 required). Install a recent build:"
    warn "https://github.com/Genymobile/scrcpy/blob/master/doc/linux.md"
fi

info "Done. Open a new terminal and run: unmeta"
