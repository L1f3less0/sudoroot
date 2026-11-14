
SUDOROOT | Rooting Linux

Your device is only yours. Even if it's Linux.
Welcome to SUDORoot—an interactive superuser authorization manager, SUDO_ASKPASS socket bridge, and ROOTHide sandboxing suite for Linux (tested on Arch / CachyOS on PS4 Linux).

# Requirements

1. PC or PS3 / PS4 / PS5 running Linux (Arch / CachyOS recommended)
2. Basic knowledge of the Linux terminal
3. Dependencies:
	• python (3.10+) & tk
	• customtkinter (installed via venv or system Python)
	• bubblewrap (bwrap)
	• fish shell (for automatic sudo -k and terminal cloaking hooks)

Included Files

Download or clone the repository containing these 3 core files:
1. root.py — The main CustomTkinter manager GUI (Dashboard, Allowed Apps whitelist, ROOTHide sandboxer, Audit Log, and Test Commands).
2. askpass_sudoroot.py — Lightweight Unix-socket bridge that intercepts sudo -A requests and passes the parent command to the manager.
3. inject.sh — One-click installer script that deploys binaries, sets SUDO_ASKPASS, injects fish shell hooks, and configures auto-start.

# Installation & Setup


1. Install Dependencies

On Arch / CachyOS:
```
sudo pacman -S python tk bubblewrap fish
python -m venv ~/ctk-venv
~/ctk-venv/bin/pip install customtkinter
```
(Optional: Open the folder in VS Code or Code - OSS with your ~/ctk-venv interpreter selected if you want to customize the UI.)

2. Inject Into Your System

Place root.py, askpass_sudoroot.py, and inject.sh in your home directory (~/), then run:
```
chmod +x ~/inject.sh
~/inject.sh
```
# How to Use It

1. Unlock Your Session:
	• Open SUDORoot (launches automatically on boot or via /usr/local/bin/sudoroot).
	• Click Unlock Session and enter your sudo password. Your password is held strictly in RAM and never written to disk.
2. Approve or Deny Root Requests:
	• Whenever any terminal command or script runs sudo, an authorization popup appears showing the exact command requesting root.
	• Click Agree to authorize it once, tick Always allow to add it to your Allowed Apps whitelist, or click Deny to block it.
	• After every command finishes, sudo -k runs automatically so credentials never stay cached in the background.
3. Cloak Root Access (ROOTHide):
	• Open the ROOTHide tab and click Enable Terminal Block to hide sudo, su, and pkexec in all open shells (command not found).
	• Use Launch Cloaked to run any app inside a bubblewrap sandbox where root binaries and sockets are masked at the kernel level.
4. Lock Anytime:
	• Click Clear Password on the Dashboard to immediately wipe your cached password from RAM and block all incoming root requests.
# Screen grab's
screen14.jpg
screen13.jpg

# Credits
L1f3less0 - Idea, tester
Google AI Mode - code
