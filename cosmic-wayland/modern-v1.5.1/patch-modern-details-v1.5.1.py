#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

DETAILS_METHODS = r''' def set_details(self, lines):
  try:
   self.info.configure(state='normal')
   self.info.delete('1.0','end')
   self.info.insert('1.0','\n'.join(lines))
   self.info.configure(state='disabled')
  except Exception:
   pass
 def refresh_status(self):
  if self.status_running: return
  self.status_running=True
  self.status.set('Checking status...')
  def safe(name, fn):
   try:
    return fn()
   except Exception as e:
    return f'{name} error: {e}'
  def worker():
   state=safe('Service',lambda:(run(['systemctl','--user','is-active','magic-mouse-gestures'],10).stdout or 'unknown').strip() or 'unknown')
   data=safe('Profile',read_profile)
   if not isinstance(data,dict): data={}
   mapping=safe('Mapping',lambda:self.map_status(data))
   hid=safe('HID',self.hid_status)
   scroll=safe('Scroll',self.scroll_status)
   lines=[
    f'Service: {state}',
    f'Mapping: {mapping}',
    f'HID: {hid}',
    f'Scroll: {scroll}',
    '',
    '== Sensitivity ==',
    f'X threshold: {data.get("SWIPE_THRESHOLD_X","unset")}',
    f'Y threshold: {data.get("SWIPE_THRESHOLD_Y","unset")}',
    f'Cooldown ms: {data.get("SWIPE_COOLDOWN_MS","unset")}',
    f'Axis lock: {data.get("AXIS_LOCK_RATIO","unset")}',
    '',
   ]
   if PROFILE.exists():
    lines.append('== Profile ==')
    try:
     lines.append(PROFILE.read_text())
    except Exception as e:
     lines.append(f'Could not read profile: {e}')
   else:
    lines.append(f'Profile missing: {PROFILE}')
   def apply():
    self.status_running=False
    self.mode.set('Mode: '+str(mapping))
    self.status.set(f'Service: {state} | HID: {hid} | Scroll: {scroll}')
    self.set_details(lines)
   self.root.after(0,apply)
  threading.Thread(target=worker,daemon=True).start()
'''


def patch(path: Path) -> None:
    text = path.read_text()
    text = text.replace('Status details will appear here.', 'Loading status and profile details...')
    start = text.find('\n def refresh_status(self):')
    end = text.find('\ndef main():', start)
    if start == -1 or end == -1:
        raise RuntimeError('Could not locate refresh_status method')
    text = text[:start] + '\n' + DETAILS_METHODS + text[end:]
    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print('usage: patch-modern-details-v1.5.1.py /path/to/magic-mouse-control-panel', file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f'control panel not found: {target}', file=sys.stderr)
        return 1
    patch(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
