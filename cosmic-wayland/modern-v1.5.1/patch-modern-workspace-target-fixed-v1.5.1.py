#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def patch(path: Path) -> None:
    text = path.read_text()

    text = text.replace(
        'order=["MIN_TOUCHES","MAX_FINGERS","SWIPE_THRESHOLD_X","SWIPE_THRESHOLD_Y","SWIPE_COOLDOWN_MS","AXIS_LOCK_RATIO","INVERT_X_1F","INVERT_Y_1F","INVERT_X_2F","INVERT_Y_2F","GESTURE_LEFT","GESTURE_RIGHT","GESTURE_UP","GESTURE_DOWN"]',
        'order=["MIN_TOUCHES","MAX_FINGERS","SWIPE_THRESHOLD_X","SWIPE_THRESHOLD_Y","SWIPE_COOLDOWN_MS","AXIS_LOCK_RATIO","INVERT_X_1F","INVERT_Y_1F","INVERT_X_2F","INVERT_Y_2F","GESTURE_LEFT","GESTURE_RIGHT","GESTURE_UP","GESTURE_DOWN","WORKSPACE_TARGET"]',
        1,
    )

    text = text.replace(
        'self.preset=tk.StringVar(value="Tihulu"); self.cx=tk.StringVar(value="550"); self.cy=tk.StringVar(value="480"); self.cc=tk.StringVar(value="550"); self.ca=tk.StringVar(value="1.35")',
        'self.preset=tk.StringVar(value="Tihulu"); self.cx=tk.StringVar(value="550"); self.cy=tk.StringVar(value="480"); self.cc=tk.StringVar(value="550"); self.ca=tk.StringVar(value="1.35")\n'
        '  self.ws_target_values={"Auto (stable / active window)":"auto","Screen 1 only":"screen1","Screen 2 only":"screen2","Both screens":"all"}\n'
        '  cur_target=read_profile().get("WORKSPACE_TARGET","auto")\n'
        '  self.ws_target=tk.StringVar(value=next((k for k,v in self.ws_target_values.items() if v==cur_target),"Auto (stable / active window)"))',
        1,
    )

    text = text.replace(
        "return f'{ws} · {br}'",
        "target=d.get('WORKSPACE_TARGET','auto'); return f'{ws} · {br} · Target: {target}'",
        1,
    )

    old_plain = 'test=self.card(right,"Workspace test",1,0); test.columnconfigure(0,weight=1); test.columnconfigure(1,weight=1); self.button(test,"Test Up",lambda:self.test_ws(\'up\'),row=1,column=0,padx=4,pady=4,sticky=\'ew\'); self.button(test,"Test Down",lambda:self.test_ws(\'down\'),row=1,column=1,padx=4,pady=4,sticky=\'ew\'); self.label(test,"Browser uses X. Workspace uses Y. Use Custom for separate tuning.",size=9,color=C[\'muted\'],row=2,column=0,columnspan=2,sticky=\'w\',pady=(10,0))'
    old_wrapped = 'test=self.card(right,"Workspace test",1,0); test.columnconfigure(0,weight=1); test.columnconfigure(1,weight=1); self.button(test,"Test Up",lambda:self.test_ws(\'up\'),row=1,column=0,padx=4,pady=4,sticky=\'ew\'); self.button(test,"Test Down",lambda:self.test_ws(\'down\'),row=1,column=1,padx=4,pady=4,sticky=\'ew\'); self.label(test,"Browser uses X. Workspace uses Y. Use Custom for separate tuning.",size=9,color=C[\'muted\'],row=2,column=0,columnspan=2,sticky=\'w\',pady=(10,0),wraplength=300)'
    new = '''test=self.card(right,"Workspace test",1,0); test.columnconfigure(0,weight=1); test.columnconfigure(1,weight=1)
  self.label(test,"Workspace target",size=9,color=C['muted'],row=1,column=0,sticky='w',padx=4)
  wtm=tk.OptionMenu(test,self.ws_target,*self.ws_target_values.keys()); wtm.configure(bg=C['card2'],fg=C['text'],activebackground=C['panel'],activeforeground=C['text'],highlightthickness=1,highlightbackground=C['border'],relief='flat',font=("Inter",10,"bold")); wtm['menu'].configure(bg=C['card2'],fg=C['text'],activebackground=C['blue'],activeforeground=C['text']); wtm.grid(row=2,column=0,padx=4,pady=4,sticky='ew')
  self.button(test,"Apply Target",self.apply_ws_target,True,row=2,column=1,padx=4,pady=4,sticky='ew')
  self.button(test,"Test Up",lambda:self.test_ws('up'),row=3,column=0,padx=4,pady=4,sticky='ew'); self.button(test,"Test Down",lambda:self.test_ws('down'),row=3,column=1,padx=4,pady=4,sticky='ew')
  self.button(test,"Target Status",lambda:self.test_ws('status'),row=4,column=0,columnspan=2,padx=4,pady=4,sticky='ew')
  self.label(test,"Default Auto matches the stable rule: active window decides. Use Screen 1/2 on empty desktop if COSMIC keeps old focus.",size=9,color=C['muted'],row=5,column=0,columnspan=2,sticky='w',pady=(10,0),wraplength=300)'''
    if old_wrapped in text:
        text = text.replace(old_wrapped, new, 1)
    elif old_plain in text:
        text = text.replace(old_plain, new, 1)
    elif 'Workspace target' not in text:
        raise RuntimeError('workspace test block not found')

    method = ''' def apply_ws_target(self):
  label=self.ws_target.get(); mode=self.ws_target_values.get(label,'auto')
  self.apply_map({'WORKSPACE_TARGET':mode},f'Workspace target set to {label}.')
'''
    if 'def apply_ws_target' not in text:
        text = text.replace(' def open_cli(self):', method + ' def open_cli(self):', 1)

    old_test = ''' def test_ws(self,direction):
  if not COSMIC_WS.exists(): messagebox.showerror('Missing helper',f'Helper not found:\n{COSMIC_WS}'); return
  def worker(p):
   p(50,f'Running cosmic-ws {direction}...'); r=run([str(COSMIC_WS),direction],10)
   if r.returncode: raise RuntimeError(r.stderr or r.stdout or 'Workspace command failed')
   return r
  self.bg(f'Workspace {direction}',worker,f'Ran cosmic-ws {direction}','Workspace test failed')
'''
    new_test = ''' def test_ws(self,direction):
  if not COSMIC_WS.exists(): messagebox.showerror('Missing helper',f'Helper not found:\n{COSMIC_WS}'); return
  def worker(p):
   p(50,f'Running cosmic-ws {direction}...'); r=run([str(COSMIC_WS),direction],10); out=(r.stdout or '')+('\n'+r.stderr if r.stderr else '')
   if r.returncode: raise RuntimeError(out or 'Workspace command failed')
   return out
  if direction=='status': self.bg('Workspace target status',worker,err='Workspace status failed',show=False,done=lambda out:self.output('Workspace target status',out or 'No output'))
  else: self.bg(f'Workspace {direction}',worker,f'Ran cosmic-ws {direction}','Workspace test failed')
'''
    if old_test in text:
        text = text.replace(old_test, new_test, 1)

    # Clean up any older broken install that may have received a 3-space raw-cache copy.
    for bad in (
        '   self.ws_target_values=', '   cur_target=', '   self.ws_target=',
        '   self.label(test,', '   wtm=', '   self.button(test,',
    ):
        text = text.replace(bad, bad[1:])

    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print('usage: patch-modern-workspace-target-fixed-v1.5.1.py /path/to/magic-mouse-control-panel', file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    patch(target)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
