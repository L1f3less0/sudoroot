#!/usr/bin/env python3
import os, socket, subprocess, sys

SOCKET_PATH = os.path.join(
    os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "sudoroot.sock"
)
if not os.path.exists(SOCKET_PATH):
  sys.exit(1)

try:
  cmd = subprocess.check_output(
      ["ps", "-p", str(os.getppid()), "-o", "args="], text=True
  ).strip()
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
