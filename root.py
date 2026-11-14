#!/usr/bin/env python3
from datetime import datetime
import os
import queue
import socket
import subprocess
import threading
from tkinter import filedialog
import customtkinter as ctk

RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
SOCKET_PATH = os.path.join(RUNTIME_DIR, "sudoroot.sock")
CLOAK_FLAG = os.path.join(RUNTIME_DIR, "roothide.active")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PasswordModal(ctk.CTkToplevel):

  def __init__(self, parent):
    super().__init__(parent)
    self.title("Unlock SUDORoot")
    self.geometry("380x200")
    self.resizable(False, False)
    self.password = None

    self.attributes("-topmost", True)
    self.grab_set()

    ctk.CTkLabel(
        self,
        text="Enter sudo password to unlock session:",
        font=ctk.CTkFont(size=13, weight="bold"),
    ).pack(anchor="w", padx=22, pady=(22, 10))

    self.entry = ctk.CTkEntry(
        self, show="*", placeholder_text="Password", height=36
    )
    self.entry.pack(fill="x", padx=22, pady=(0, 18))
    self.entry.focus_set()

    row = ctk.CTkFrame(self, fg_color="transparent")
    row.pack(fill="x", padx=22)

    ctk.CTkButton(
        row,
        text="Cancel",
        fg_color="#475569",
        hover_color="#334155",
        width=120,
        command=self.destroy,
    ).pack(side="left")

    ctk.CTkButton(
        row,
        text="Unlock",
        width=120,
        command=self.submit,
    ).pack(side="right")

    self.bind("<Return>", lambda e: self.submit())
    self.bind("<Escape>", lambda e: self.destroy())

  def submit(self):
    self.password = self.entry.get()
    self.destroy()


class ApprovalModal(ctk.CTkToplevel):

  def __init__(self, parent, command_str):
    super().__init__(parent)
    self.title("SUDORoot Authorization")
    self.geometry("450x250")
    self.resizable(False, False)
    self.approved = False
    self.remember = ctk.BooleanVar(value=False)

    self.attributes("-topmost", True)
    self.grab_set()

    ctk.CTkLabel(
        self,
        text="SUPERUSER PRIVILEGE REQUEST",
        text_color="#f59e0b",
        font=ctk.CTkFont(size=13, weight="bold"),
    ).pack(anchor="w", padx=22, pady=(18, 6))

    cmd_box = ctk.CTkTextbox(
        self, height=65, font=ctk.CTkFont(family="Monospace", size=12)
    )
    cmd_box.pack(fill="x", padx=22, pady=(0, 10))
    cmd_box.insert("1.0", command_str)
    cmd_box.configure(state="disabled")

    ctk.CTkCheckBox(
        self,
        text="Always allow this command (add to Allowed Apps)",
        variable=self.remember,
        font=ctk.CTkFont(size=12),
    ).pack(anchor="w", padx=22, pady=(0, 14))

    row = ctk.CTkFrame(self, fg_color="transparent")
    row.pack(fill="x", padx=22)

    ctk.CTkButton(
        row,
        text="Deny",
        fg_color="#dc2626",
        hover_color="#b91c1c",
        width=140,
        command=self.deny,
    ).pack(side="left")

    ctk.CTkButton(
        row,
        text="Agree",
        fg_color="#16a34a",
        hover_color="#15803d",
        width=140,
        command=self.agree,
    ).pack(side="right")

    self.bind("<Return>", lambda e: self.agree())
    self.bind("<Escape>", lambda e: self.deny())
    self.protocol("WM_DELETE_WINDOW", self.deny)

  def agree(self):
    self.approved = True
    self.destroy()

  def deny(self):
    self.approved = False
    self.destroy()
class SudoRootCTK(ctk.CTk):

  def __init__(self):
    super().__init__()
    self.title("SUDORoot Manager")
    self.geometry("640x480")
    self.resizable(False, False)

    self.pwd = None
    self.ok_n = 0
    self.no_n = 0
    self.q = queue.Queue()
    self.allowed_cmds = set()

    # ================= HEADER BAR =================
    hdr = ctk.CTkFrame(self, corner_radius=8)
    hdr.pack(fill="x", padx=14, pady=(14, 8))

    ctk.CTkLabel(
        hdr, text="SUDORoot", font=ctk.CTkFont(size=18, weight="bold")
    ).pack(side="left", padx=14, pady=10)

    self.theme_switch = ctk.CTkSwitch(
        hdr,
        text="Dark Mode",
        command=lambda: ctk.set_appearance_mode(self.theme_switch.get()),
        onvalue="dark",
        offvalue="light",
    )
    self.theme_switch.select()
    self.theme_switch.pack(side="right", padx=14)

    self.cloak_badge = ctk.CTkLabel(
        hdr,
        text="UNCLOAKED",
        text_color="#94a3b8",
        font=ctk.CTkFont(family="Monospace", size=11, weight="bold"),
    )
    self.cloak_badge.pack(side="right", padx=10)

    self.badge = ctk.CTkLabel(
        hdr,
        text="LOCKED",
        text_color="#ef4444",
        font=ctk.CTkFont(family="Monospace", size=11, weight="bold"),
    )
    self.badge.pack(side="right", padx=10)

    # ================= TABVIEW =================
    self.tabs = ctk.CTkTabview(self, corner_radius=8)
    self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    t_dash = self.tabs.add("Dashboard")
    t_allow = self.tabs.add("Allowed Apps")
    t_hide = self.tabs.add("ROOTHide")
    t_log = self.tabs.add("Audit Log")
    t_test = self.tabs.add("Test Commands")

    self._build_dashboard(t_dash)
    self._build_allowed(t_allow)
    self._build_roothide(t_hide)
    self._build_log(t_log)
    self._build_tests(t_test)

    self._sync_cloak_badge()
    threading.Thread(target=self.serve, daemon=True).start()
    self.after(100, self.poll)

  def _build_dashboard(self, parent):
    stats_card = ctk.CTkFrame(parent)
    stats_card.pack(fill="x", padx=12, pady=(16, 14))

    self.stats = ctk.CTkLabel(
        stats_card,
        text="Approved: 0   |   Denied: 0   |   Allowed Rules: 0",
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    self.stats.pack(pady=20)

    btn_row = ctk.CTkFrame(parent, fg_color="transparent")
    btn_row.pack(fill="x", padx=12, pady=6)

    ctk.CTkButton(
        btn_row,
        text="Unlock Session",
        height=40,
        font=ctk.CTkFont(weight="bold"),
        command=self.unlock,
    ).pack(side="left", fill="x", expand=True, padx=(0, 6))

    ctk.CTkButton(
        btn_row,
        text="Clear Password",
        height=40,
        fg_color="#475569",
        hover_color="#334155",
        font=ctk.CTkFont(weight="bold"),
        command=self.lock,
    ).pack(side="right", fill="x", expand=True, padx=(6, 0))

    ctk.CTkLabel(
        parent,
        text="Commands in Allowed Apps auto-approve without popups.",
        text_color="#94a3b8",
        font=ctk.CTkFont(size=11),
    ).pack(side="bottom", pady=14)

  def _build_allowed(self, parent):
    add_row = ctk.CTkFrame(parent, fg_color="transparent")
    add_row.pack(fill="x", padx=10, pady=(10, 8))

    self.allow_entry = ctk.CTkEntry(
        add_row, placeholder_text="e.g. sudo -A whoami"
    )
    self.allow_entry.insert(0, "sudo -A whoami")
    self.allow_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    ctk.CTkButton(
        add_row,
        text="Add Rule",
        width=90,
        fg_color="#16a34a",
        hover_color="#15803d",
        command=lambda: self.add_allowed(self.allow_entry.get().strip()),
    ).pack(side="right")

    self.allow_scroll = ctk.CTkScrollableFrame(parent)
    self.allow_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    self.rule_widgets = {}

  def add_allowed(self, cmd):
    if cmd and cmd not in self.allowed_cmds:
      self.allowed_cmds.add(cmd)
      row = ctk.CTkFrame(self.allow_scroll)
      row.pack(fill="x", pady=3, padx=4)
      ctk.CTkLabel(
          row, text=cmd, font=ctk.CTkFont(family="Monospace", size=11)
      ).pack(side="left", padx=10, pady=6)
      ctk.CTkButton(
          row,
          text="Remove",
          width=70,
          height=24,
          fg_color="#dc2626",
          hover_color="#b91c1c",
          command=lambda c=cmd: self.remove_allowed(c),
      ).pack(side="right", padx=8)
      self.rule_widgets[cmd] = row
      self._update_stats()
      self.add_log(f"ADDED RULE: {cmd}")

  def remove_allowed(self, cmd):
    if cmd in self.allowed_cmds:
      self.allowed_cmds.discard(cmd)
      self.rule_widgets[cmd].destroy()
      del self.rule_widgets[cmd]
      self._update_stats()
      self.add_log(f"REMOVED RULE: {cmd}")

  def _update_stats(self):
    self.stats.configure(
        text=(
            f"Approved: {self.ok_n}   |   Denied: {self.no_n}   |   Allowed"
            f" Rules: {len(self.allowed_cmds)}"
        )
    )
  def _build_roothide(self, parent):
    card = ctk.CTkFrame(parent)
    card.pack(fill="x", padx=10, pady=(12, 12))

    ctk.CTkLabel(
        card,
        text="Global Terminal Cloak (Blocks sudo/su/pkexec in open shells)",
        font=ctk.CTkFont(size=12, weight="bold"),
    ).pack(anchor="w", padx=12, pady=(10, 6))

    trow = ctk.CTkFrame(card, fg_color="transparent")
    trow.pack(fill="x", padx=12, pady=(0, 12))

    ctk.CTkButton(
        trow,
        text="Enable Terminal Block",
        fg_color="#7c3aed",
        hover_color="#6d28d9",
        command=self.enable_cloak,
    ).pack(side="left", fill="x", expand=True, padx=(0, 6))

    ctk.CTkButton(
        trow,
        text="Restore Terminal",
        fg_color="#475569",
        hover_color="#334155",
        command=self.disable_cloak,
    ).pack(side="right", fill="x", expand=True, padx=(6, 0))

    ctk.CTkLabel(
        parent,
        text="Launch an app or terminal inside a kernel-cloaked sandbox:",
        font=ctk.CTkFont(size=12),
    ).pack(anchor="w", padx=12, pady=(6, 6))

    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=10)

    self.hide_entry = ctk.CTkEntry(row)
    self.hide_entry.insert(0, "qterminal")
    self.hide_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    ctk.CTkButton(
        row,
        text="Browse",
        width=80,
        fg_color="#475569",
        command=self.browse_hide,
    ).pack(side="left", padx=(0, 6))

    ctk.CTkButton(
        row,
        text="Launch Cloaked",
        width=130,
        fg_color="#16a34a",
        hover_color="#15803d",
        command=self.launch_cloaked,
    ).pack(side="right")

  def _sync_cloak_badge(self):
    if os.path.exists(CLOAK_FLAG):
      self.cloak_badge.configure(text="TERMINAL BLOCKED", text_color="#a855f7")
    else:
      self.cloak_badge.configure(text="UNCLOAKED", text_color="#94a3b8")

  def enable_cloak(self):
    open(CLOAK_FLAG, "w").close()
    self._sync_cloak_badge()
    self.add_log("ROOTHide: Terminal block ENABLED.")

  def disable_cloak(self):
    if os.path.exists(CLOAK_FLAG):
      os.remove(CLOAK_FLAG)
    self._sync_cloak_badge()
    self.add_log("ROOTHide: Terminal block DISABLED.")

  def browse_hide(self):
    path = filedialog.askopenfilename(initialdir="/usr/bin")
    if path:
      self.hide_entry.delete(0, "end")
      self.hide_entry.insert(0, path)

  def launch_cloaked(self):
    cmd_parts = self.hide_entry.get().strip().split()
    if not cmd_parts:
      return
    bwrap = ["bwrap", "--dev-bind", "/", "/"]
    hidden = [
        "/usr/bin/sudo",
        "/usr/bin/su",
        "/usr/bin/pkexec",
        "/usr/local/bin/sudoroot",
        "/usr/local/bin/sudoroot-askpass",
        SOCKET_PATH,
    ]
    for path in hidden:
      if os.path.exists(path):
        bwrap += ["--ro-bind", "/dev/null", path]
    env = os.environ.copy()
    for var in ["SUDO_ASKPASS", "SUDO_USER", "SUDO_UID", "SUDO_GID"]:
      env.pop(var, None)
    self.add_log(f"ROOTHide: Launched cloaked {' '.join(cmd_parts)}")
    subprocess.Popen(bwrap + ["--"] + cmd_parts, env=env)

  def _build_log(self, parent):
    self.log = ctk.CTkTextbox(
        parent, font=ctk.CTkFont(family="Monospace", size=11)
    )
    self.log.pack(fill="both", expand=True, padx=10, pady=(10, 6))
    ctk.CTkButton(
        parent,
        text="Clear Log",
        fg_color="#475569",
        command=lambda: self.log.delete("1.0", "end"),
    ).pack(fill="x", padx=10, pady=(0, 10))
    self.add_log("Ready. Unlock session to start.")

  def _build_tests(self, parent):
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=10, pady=(10, 8))

    for label, cmd in [
        ("whoami", ["whoami"]),
        ("id", ["id"]),
        ("uname -r", ["uname", "-r"]),
    ]:
      ctk.CTkButton(
          row,
          text=label,
          fg_color="#334155",
          command=lambda c=cmd: self.run_test(c),
      ).pack(side="left", fill="x", expand=True, padx=4)

    crow = ctk.CTkFrame(parent, fg_color="transparent")
    crow.pack(fill="x", padx=10, pady=(0, 8))

    self.custom_cmd = ctk.CTkEntry(crow)
    self.custom_cmd.insert(0, "echo Hello from Root")
    self.custom_cmd.pack(side="left", fill="x", expand=True, padx=(0, 6))

    ctk.CTkButton(
        crow,
        text="Run",
        width=90,
        command=lambda: self.run_test(self.custom_cmd.get().split()),
    ).pack(side="right")

    self.test_out = ctk.CTkTextbox(
        parent, font=ctk.CTkFont(family="Monospace", size=11)
    )
    self.test_out.pack(fill="both", expand=True, padx=10, pady=(0, 10))

  def run_test(self, cmd_list):
    if not cmd_list:
      return

    def task():
      env = os.environ.copy()
      env["SUDO_ASKPASS"] = "/usr/local/bin/sudoroot-askpass"
      res = subprocess.run(
          ["sudo", "-k", "-A"] + cmd_list,
          env=env,
          text=True,
          capture_output=True,
      )
      out = res.stdout.strip() or res.stderr.strip() or "(no output)"
      self.after(
          0, lambda: self._show_test_out(f"$ sudo {' '.join(cmd_list)}\n{out}")
      )

    threading.Thread(target=task, daemon=True).start()

  def _show_test_out(self, text):
    self.test_out.delete("1.0", "end")
    self.test_out.insert("1.0", text)

  def add_log(self, msg):
    self.log.insert("end", f"[{datetime.now():%H:%M:%S}] {msg}\n")
    self.log.see("end")

  def unlock(self):
    p = PasswordModal(self)
    self.wait_window(p)
    if (
        p.password
        and subprocess.run(
            ["sudo", "-S", "-v"],
            input=p.password + "\n",
            text=True,
            capture_output=True,
        ).returncode
        == 0
    ):
      self.pwd = p.password
      self.badge.configure(text="ACTIVE", text_color="#22c55e")
      self.add_log("Unlocked.")
    elif p.password:
      self.add_log("Wrong password.")

  def lock(self):
    self.pwd = None
    subprocess.run(["sudo", "-k"])
    self.badge.configure(text="LOCKED", text_color="#ef4444")
    self.add_log("Locked and password cleared.")

  def serve(self):
    if os.path.exists(SOCKET_PATH):
      os.remove(SOCKET_PATH)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o600)
    s.listen(5)
    while True:
      conn, _ = s.accept()
      cmd = conn.recv(1024).decode().strip() or "sudo request"
      ev, res = threading.Event(), {"ok": False}
      self.q.put((cmd, ev, res))
      ev.wait()
      conn.sendall(
          self.pwd.encode() if (res["ok"] and self.pwd) else b"DENIED"
      )
      conn.close()

  def poll(self):
    while not self.q.empty():
      cmd, ev, res = self.q.get()
      if not self.pwd:
        self.no_n += 1
        self.add_log(f"BLOCKED (locked): {cmd}")
      elif cmd in self.allowed_cmds:
        res["ok"] = True
        self.ok_n += 1
        self.add_log(f"AUTO-ALLOWED: {cmd}")
      else:
        p = ApprovalModal(self, cmd)
        self.wait_window(p)
        res["ok"] = p.approved
        self.ok_n += p.approved
        self.no_n += not p.approved
        if p.approved and p.remember.get():
          self.add_allowed(cmd)
        self.add_log(f"{'ALLOWED' if p.approved else 'DENIED'}: {cmd}")
      self._update_stats()
      ev.set()
    self.after(100, self.poll)


if __name__ == "__main__":
  SudoRootCTK().mainloop()
