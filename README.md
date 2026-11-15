
SUDOROOT | Rooting Linux

Your device is only yours. Even if it's Linux.
# Welcome to SUDORoot v1.2—a 
Magisk-inspired superuser authorization manager, 100% RAM-based OverlayFS systemless injector, ROOTHide sandboxer, and Python .zip module engine for Linux (built and tested on Arch / CachyOS on PS4 Linux).

# Features

• Interactive Root Authorization (SUDO_ASKPASS): Intercepts sudo -A calls over a private Unix socket (0600) and prompts you to Agree, Deny, or Always Allow the exact command requesting root.
• Zero Cached Sessions: Automatically runs sudo -k after every command so root privileges never stay silently cached in the background.
• 100% Systemless RAM Overlay (OverlayFS): Stages binaries inside /dev/shm and merges them over /usr/local/bin purely in volatile memory—leaving zero files on your root filesystem when unmounted or rebooted.
• Magisk-Style Python Modules (.zip): Install, toggle, and run custom .zip plugins built with the built-in SudoModuleAPI.
• ROOTHide Cloaking: One-click terminal cloak to block sudo, su, and pkexec in open shells, plus a bubblewrap sandbox launcher that masks root binaries at the kernel level.

# Requirements

1. PC or PS3 / PS4 / PS5 running Linux (Arch / CachyOS, Debian / Ubuntu, or Fedora)
2. Dependencies:
	• python (3.10+) & tk
	• customtkinter
	• bubblewrap (bwrap)
	• fish, bash, or zsh

# Quick Start (EJECTF0RINJECT)

Clone the repository and run the universal injector:
```
git clone https://github.com/L1f3less0/sudoroot
cd sudoroot
chmod +x ejectf0rinject.sh
./ejectf0rinject.sh
```
Select from the interactive menu:
1. Systemless Inject — Mounts SUDORoot into /usr/local/bin purely in RAM via OverlayFS (0 bytes written to system directories).
2. Standard Inject — Installs binaries directly into /usr/local/bin.
3. Eject / Uninstall Everything — Unmounts RAM overlays, removes all hooks, and restores stock sudo.
4. Force Show GUI — Launches the SUDORoot manager window immediately.

# Building Custom Modules (.zip)

Create a .zip archive containing module.json and module.py, then install it from the Modules tab:

1. module.json

```
{
  "id": "my_module",
  "name": "System Inspector",
  "version": "1.0",
  "author": "L1f3less0",
  "description": "Runs privileged checks using SudoModuleAPI."
}
```
2. module.py
```
def run(api):
    api.log("Running custom module...")
    code, out, err = api.run_root(["uname", "-r"])
    if code == 0:
        api.log(f"Kernel: {out}")
    else:
        api.log(f"Error: {err}")
```
Available SudoModuleAPI Methods

• api.log("text") — Prints a timestamped message to the SUDORoot Audit Log.


• api.run_root(["cmd", "arg"]) — Runs a root command using the unlocked RAM session (returns code, stdout, stderr).


• api.run_user(["cmd", "arg"]) — Runs a standard unprivileged command.


• api.allow_command("sudo -A ...") — Adds a command rule to Allowed Apps.


• api.set_cloak(True / False) — Toggles ROOTHide terminal blocking.


• api.data_dir — Path to the module's persistent storage folder.

Credits

• L1f3less0 / r3gardless — Creator, architecture, PS4 Linux & Android testing
• Google AI Mode — Code assistance
