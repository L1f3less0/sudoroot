# SUDOROOT | Rooting Linux

SUDORoot v1.3.2 is a single-file superuser authorization manager and systemless injector for Linux (Arch, CachyOS, PS4 Linux). 

## Core Features
* **Interactive Root Authorization:** Manages `sudo -A` requests via a Unix socket.
* **Systemless RAM Overlay:** Uses `OverlayFS` in `/dev/shm` to leave no permanent disk footprint.
* **ROOTHide Cloaking:** Terminal cloaking and `bubblewrap` sandbox support.
* **Module Support:** Magisk-style Python `.zip` module engine.

## Quick Start
```bash
sudo pacman -S python tk bubblewrap fish
python -m venv ~/ctk-venv
~/ctk-venv/bin/pip install customtkinter

git clone https://github.com/L1f3less0/sudoroot
cd sudoroot
~/ctk-venv/bin/python sudoroot.py
```
