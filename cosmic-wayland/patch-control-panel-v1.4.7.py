#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        return text
    end = text.find(end_marker, start)
    if end == -1:
        return text
    return text[:start] + replacement + text[end:]


def patch_control_panel(path: Path) -> None:
    text = path.read_text()
    text = re.sub(r'VERSION = "[^"]+"', 'VERSION = "1.4.7"', text, count=1)
    text = text.replace(
        'def run_command(cmd):\n    return subprocess.run(cmd, text=True, capture_output=True)\n',
        'def run_command(cmd, timeout=None):\n    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)\n',
    )

    if 'run_background_action' not in text:
        text = text.replace(
            '        self.root.after(150, self.refresh_status_async)\n\n    def _build_ui(self):\n',
            '        self._background_action_running = False\n        self._progress_win = None\n        self._progress_value = tk.IntVar(value=0)\n        self._progress_text = tk.StringVar(value="Idle")\n        self.root.after(150, self.refresh_status_async)\n\n'
            '    def _place_progress_window(self, win, width=360, height=120):\n        try:\n            sw = self.root.winfo_screenwidth()\n            sh = self.root.winfo_screenheight()\n            win.geometry(f"{width}x{height}+{max(0, sw-width-24)}+{max(0, sh-height-64)}")\n        except Exception:\n            win.geometry(f"{width}x{height}")\n\n'
            '    def _progress_start(self, title):\n        try:\n            if self._progress_win is not None and self._progress_win.winfo_exists():\n                self._progress_win.destroy()\n        except Exception:\n            pass\n        self._progress_value.set(0)\n        self._progress_text.set("Starting...")\n        win = tk.Toplevel(self.root)\n        win.title(title)\n        win.resizable(False, False)\n        win.attributes("-topmost", True)\n        frame = ttk.Frame(win, padding=12)\n        frame.pack(fill="both", expand=True)\n        ttk.Label(frame, text=title, font=("Sans", 10, "bold")).pack(anchor="w")\n        ttk.Label(frame, textvariable=self._progress_text, wraplength=320).pack(anchor="w", pady=(6, 8))\n        ttk.Progressbar(frame, maximum=100, variable=self._progress_value, length=320).pack(fill="x")\n        self._progress_win = win\n        self._place_progress_window(win)\n\n'
            '    def _progress_update(self, percent, message):\n        def update():\n            self._progress_value.set(max(0, min(100, int(percent))))\n            self._progress_text.set(message)\n        self.root.after(0, update)\n\n'
            '    def _progress_finish(self, success, message, close_delay_ms=1200):\n        def update():\n            if success:\n                self._progress_value.set(100)\n            self._progress_text.set(message)\n            win = self._progress_win\n            if win is not None and win.winfo_exists():\n                win.after(close_delay_ms, win.destroy)\n        self.root.after(0, update)\n\n'
            '    def run_background_action(self, title, worker, on_success=None, success_message=None, error_title=None, show_success=True):\n        if getattr(self, "_background_action_running", False):\n            messagebox.showinfo("Busy", "Another action is already running. Please wait for it to finish.")\n            return\n        self._background_action_running = True\n        self._progress_start(title)\n        def progress(percent, message):\n            self._progress_update(percent, message)\n        def thread_main():\n            try:\n                result = worker(progress)\n                def finish_success():\n                    self._background_action_running = False\n                    if on_success:\n                        on_success(result)\n                    self.refresh_status_async()\n                    self._progress_finish(True, "Done")\n                    if show_success and success_message:\n                        messagebox.showinfo(title, success_message)\n                self.root.after(0, finish_success)\n            except Exception as exc:\n                def finish_error():\n                    self._background_action_running = False\n                    self.refresh_status_async()\n                    self._progress_finish(False, "Failed")\n                    messagebox.showerror(error_title or f"{title} failed", str(exc))\n                self.root.after(0, finish_error)\n        threading.Thread(target=thread_main, daemon=True).start()\n\n'
            '    def _restart_service_sync(self):\n        subprocess.run(["systemctl", "--user", "daemon-reload"], text=True, capture_output=True)\n        return run_command(["systemctl", "--user", "restart", "magic-mouse-gestures"])\n\n'
            '    def _build_ui(self):\n',
            1,
        )

    mapping_block = '''    def apply_only(self):
        try:
            values = self.collect_values()
            self.validate_values(values)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        def worker(progress):
            progress(20, "Backing up current profile...")
            backup_profile()
            progress(55, "Saving settings...")
            write_profile(values)
            return values
        def done(_):
            self.load_profile_to_ui(refresh_info=False)
        self.run_background_action("Save settings", worker, on_success=done, success_message=f"Settings saved to:\n{PROFILE}", error_title="Save failed")

    def apply_and_restart(self):
        try:
            values = self.collect_values()
            self.validate_values(values)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        def worker(progress):
            progress(15, "Backing up current profile...")
            backup_profile()
            progress(40, "Saving settings...")
            write_profile(values)
            progress(70, "Restarting gesture service...")
            result = self._restart_service_sync()
            if result.returncode != 0:
                raise RuntimeError(result.stderr or result.stdout or "Service restart failed")
            return values
        def done(_):
            self.load_profile_to_ui(refresh_info=False)
        self.run_background_action("Apply and restart", worker, on_success=done, success_message="Settings saved and the gesture service was restarted.", error_title="Apply failed")

    def restart_service(self, show_message=True):
        if not show_message:
            result = self._restart_service_sync()
            return result.returncode == 0
        def worker(progress):
            progress(35, "Reloading user systemd...")
            subprocess.run(["systemctl", "--user", "daemon-reload"], text=True, capture_output=True)
            progress(70, "Restarting gesture service...")
            result = run_command(["systemctl", "--user", "restart", "magic-mouse-gestures"])
            if result.returncode != 0:
                raise RuntimeError(result.stderr or result.stdout or "Unknown error")
            return result
        self.run_background_action("Restart gesture service", worker, success_message="magic-mouse-gestures was restarted.", error_title="Service restart failed")
        return True

    def apply_mapping_values(self, values, message=None):
        def worker(progress):
            progress(15, "Reading current profile...")
            current = read_profile()
            current.update(values)
            progress(35, "Backing up current profile...")
            backup_profile()
            progress(55, "Writing gesture mapping...")
            write_profile(current)
            progress(80, "Restarting gesture service...")
            result = self._restart_service_sync()
            if result.returncode != 0:
                raise RuntimeError(result.stderr or result.stdout or "Service restart failed")
            return current
        def done(_):
            self.load_profile_to_ui(refresh_info=False)
        self.run_background_action("Apply gesture mapping", worker, on_success=done, success_message=message, error_title="Gesture mapping failed", show_success=bool(message))

    def apply_stable_mapping(self):
        self.apply_mapping_values(DEFAULT_MAPPING, "Stable default mapping applied and the gesture service was restarted.")

'''
    text = replace_between(text, '    def apply_only(self):\n', '    def normal_workspace_direction(self):\n', mapping_block)

    repair_block = '''    def repair_permissions(self):
        if not REPAIR.exists():
            messagebox.showerror("Missing script", f"Repair script not found:\n{REPAIR}")
            return False
        password = self.ensure_sudo_auth()
        if password is None:
            return False
        def worker(progress):
            progress(15, "Preparing HID permission repair...")
            env = os.environ.copy()
            if password:
                env["MM_SUDO_PASSWORD"] = password
            progress(45, "Running repair script...")
            result = subprocess.run([str(REPAIR)], text=True, capture_output=True, env=env, timeout=180)
            out = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
            if result.returncode != 0:
                raise RuntimeError(out or "HID permission repair did not complete.")
            return out
        def done(out):
            show_output_window("Repair HID permissions", out or "No output")
        self.run_background_action("Repair HID permissions", worker, on_success=done, success_message="HID permission repair completed.", error_title="Repair failed")
        return True

    def run_verify(self):
        if not VERIFY.exists():
            messagebox.showerror("Missing script", f"Verify script not found:\n{VERIFY}")
            return
        def worker(progress):
            progress(25, "Running verification report...")
            result = run_command([str(VERIFY)], timeout=60)
            out = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
            if result.returncode != 0:
                raise RuntimeError(out or "Verify failed")
            return out
        def done(out):
            show_output_window("Verify report", out or "No output")
        self.run_background_action("Verify setup", worker, on_success=done, error_title="Verify failed", show_success=False)

'''
    text = replace_between(text, '    def repair_permissions(self):\n', '    def open_status_report(self):\n', repair_block)

    text = text.replace('command=self.refresh_status)', 'command=self.refresh_status_async)')

    if 'self._progress_start("Scroll direction")' not in text:
        text = text.replace('        self._scroll_direction_running = True\n        self.status_var.set(f"Scroll direction: applying {mode}...")\n        self.setup_status_vars["5"].set("Applying...")\n', '        self._scroll_direction_running = True\n        self.status_var.set(f"Scroll direction: applying {mode}...")\n        self.setup_status_vars["5"].set("Applying...")\n        self._progress_start("Scroll direction")\n        self._progress_update(20, f"Applying {mode} scroll direction...")\n')
        text = text.replace('                self._scroll_direction_running = False\n                self.refresh_status_async()\n                if show_output or result.returncode != 0:\n', '                self._scroll_direction_running = False\n                self.refresh_status_async()\n                self._progress_finish(result.returncode == 0, "Done" if result.returncode == 0 else "Failed")\n                if show_output or result.returncode != 0:\n', 1)

    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-control-panel-v1.4.7.py /path/to/magic-mouse-control-panel", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f"control panel not found: {target}", file=sys.stderr)
        return 1
    patch_control_panel(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
