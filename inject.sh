#!/usr/bin/env bash
set -e

echo "*** Starting SUDORoot Auto-Injector... ***"

# 1. Ensure dependencies are installed
for pkg in tk bubblewrap; do
    if ! pacman -Qi "$pkg" &>/dev/null; then
        echo "[*] Installing missing package: $pkg"
        sudo pacman -S --noconfirm "$pkg"
    fi
done

# 2. Detect Python interpreter (prefer ctk-venv if present)
if [ -x "$HOME/ctk-venv/bin/python" ]; then
    PY_BIN="$HOME/ctk-venv/bin/python"
else
    PY_BIN="/usr/bin/python3"
fi
echo "[*] Using Python interpreter: $PY_BIN"

# 3. Install main manager binary
if [ ! -f "$HOME/root.py" ]; then
    echo "[!] Error: ~/root.py not found! Save your SUDORoot app to ~/root.py first."
    exit 1
fi

sudo cp "$HOME/root.py" /usr/local/bin/sudoroot
sudo sed -i "1s|^.*$|#!$PY_BIN|" /usr/local/bin/sudoroot
sudo chmod +x /usr/local/bin/sudoroot
echo "[+] Installed /usr/local/bin/sudoroot"

# 4. Install askpass bridge helper
sudo tee /usr/local/bin/sudoroot-askpass >/dev/null <<'EOF'
#!/usr/bin/env python3
import os, socket, subprocess, sys

SOCKET_PATH = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "sudoroot.sock")
if not os.path.exists(SOCKET_PATH):
    sys.exit(1)

try:
    cmd = subprocess.check_output(["ps", "-p", str(os.getppid()), "-o", "args="], text=True).strip()
except Exception:
    cmd = "sudo request"

try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
    s.sendall(cmd.encode())
    res = s.recv(1024).decode()
    s.close()
except Exception:
    sys.exit(1)

if res and res != "DENIED":
    sys.stdout.write(res + "\n")
    sys.exit(0)
sys.exit(1)
EOF
sudo chmod +x /usr/local/bin/sudoroot-askpass
echo "[+] Installed /usr/local/bin/sudoroot-askpass"

# 5. Inject global environment variable
mkdir -p "$HOME/.config/environment.d"
echo "SUDO_ASKPASS=/usr/local/bin/sudoroot-askpass" > "$HOME/.config/environment.d/sudoroot.conf"
echo "[+] Configured ~/.config/environment.d/sudoroot.conf"

# 6. Inject fish shell hooks (idempotent)
mkdir -p "$HOME/.config/fish"
FISH_CFG="$HOME/.config/fish/config.fish"
touch "$FISH_CFG"

if ! grep -q "# SUDORoot + ROOTHide Hook" "$FISH_CFG"; then
    cat >> "$FISH_CFG" <<'EOF'

# SUDORoot + ROOTHide Hook
set -gx SUDO_ASKPASS /usr/local/bin/sudoroot-askpass

function sudo
    if test -e "$XDG_RUNTIME_DIR/roothide.active"
        echo "fish: sudo: command not found" >&2
        return 127
    end
    command sudo -A $argv
    set -l exit_code $status
    command sudo -k
    return $exit_code
end

function su
    if test -e "$XDG_RUNTIME_DIR/roothide.active"
        echo "fish: su: command not found" >&2
        return 127
    end
    command su $argv
end

function pkexec
    if test -e "$XDG_RUNTIME_DIR/roothide.active"
        echo "fish: pkexec: command not found" >&2
        return 127
    end
    command pkexec $argv
end
EOF
    echo "[+] Injected hooks into ~/.config/fish/config.fish"
else
    echo "[*] Fish hooks already present, skipping."
fi

# 7. Create and enable systemd user autostart service
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/sudoroot.service" <<EOF
[Unit]
Description=SUDORoot Authorization Manager
After=graphical-session.target

[Service]
ExecStart=$PY_BIN /usr/local/bin/sudoroot
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now sudoroot.service
echo "[+] Enabled and started sudoroot.service!"
echo "[✓] Injection complete. Open a new terminal or run: source ~/.config/fish/config.fish"
