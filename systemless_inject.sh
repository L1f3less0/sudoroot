#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYS_DIR="$HOME/.sudoroot"

echo "[*] Initializing Systemless SUDORoot in $SYS_DIR..."

# 1. Clean up any legacy /usr/local/bin files if present
if [ -f /usr/local/bin/sudoroot ] || [ -f /usr/local/bin/sudoroot-askpass ]; then
    echo "[*] Removing legacy /usr/local/bin binaries for pure systemless mode..."
    sudo rm -f /usr/local/bin/sudoroot /usr/local/bin/sudoroot-askpass
fi

# 2. Build self-contained systemless directory structure
mkdir -p "$SYS_DIR"/{bin,modules,config}

# Detect Python interpreter (prefer ctk-venv)
if [ -x "$HOME/ctk-venv/bin/python" ]; then
    PY_BIN="$HOME/ctk-venv/bin/python"
else
    PY_BIN="/usr/bin/python3"
fi

# 3. Stage binaries inside ~/.sudoroot/bin (zero system files touched)
cp "$SCRIPT_DIR/root.py" "$SYS_DIR/bin/sudoroot"
sed -i "1s|^.*$|#!$PY_BIN|" "$SYS_DIR/bin/sudoroot"
chmod +x "$SYS_DIR/bin/sudoroot"

cp "$SCRIPT_DIR/askpass_sudoroot.py" "$SYS_DIR/bin/sudoroot-askpass"
chmod +x "$SYS_DIR/bin/sudoroot-askpass"

# 4. Create RAM-only Mount / Unmount Scripts
cat > "$SYS_DIR/mount.sh" <<EOF
#!/usr/bin/env bash
if ! mountpoint -q /usr/local/bin; then
    sudo mount --bind "$SYS_DIR/bin" /usr/local/bin
    echo "[+] Systemless overlay MOUNTED in RAM (/usr/local/bin -> ~/.sudoroot/bin)"
else
    echo "[*] Systemless overlay is already mounted."
fi
EOF

cat > "$SYS_DIR/unmount.sh" <<EOF
#!/usr/bin/env bash
if mountpoint -q /usr/local/bin; then
    sudo umount /usr/local/bin
    echo "[+] Systemless overlay UNMOUNTED. System /usr/local/bin is completely clean."
else
    echo "[*] Systemless overlay is not currently mounted."
fi
EOF
chmod +x "$SYS_DIR/mount.sh" "$SYS_DIR/unmount.sh"

# 5. Update fish shell hook to point to ~/.sudoroot/bin
mkdir -p "$HOME/.config/fish"
FISH_CFG="$HOME/.config/fish/config.fish"
touch "$FISH_CFG"

# Remove old hook if present so we can write the systemless path cleanly
sed -i '/# SUDORoot + ROOTHide Hook/,$d' "$FISH_CFG"

cat >> "$FISH_CFG" <<EOF

# SUDORoot + ROOTHide Hook (Systemless)
set -gx SUDO_ASKPASS "$SYS_DIR/bin/sudoroot-askpass"
fish_add_path -g "$SYS_DIR/bin"

function sudo
    if test -e "\$XDG_RUNTIME_DIR/roothide.active"
        echo "fish: sudo: command not found" >&2
        return 127
    end
    command sudo -A \$argv
    set -l exit_code \$status
    command sudo -k
    return \$exit_code
end

function su
    if test -e "\$XDG_RUNTIME_DIR/roothide.active"
        echo "fish: su: command not found" >&2
        return 127
    end
    command su \$argv
end

function pkexec
    if test -e "\$XDG_RUNTIME_DIR/roothide.active"
        echo "fish: pkexec: command not found" >&2
        return 127
    end
    command pkexec \$argv
end
EOF

# 6. Update systemd user service to run directly from ~/.sudoroot/bin
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/sudoroot.service" <<EOF
[Unit]
Description=SUDORoot Authorization Manager (Systemless)
After=graphical-session.target

[Service]
ExecStart=$PY_BIN $SYS_DIR/bin/sudoroot
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user restart sudoroot.service

echo "[✓] Systemless SUDORoot installed in ~/.sudoroot!"
echo "    - Run '~/.sudoroot/mount.sh' to bind-mount into /usr/local/bin in RAM"
echo "    - Run '~/.sudoroot/unmount.sh' to unmount cleanly anytime"
