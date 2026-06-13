#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

EXAMPLE = "Example / default custom: X 550 · Y 480 · Cooldown 550 ms · Axis lock 1.35"


def patch(path: Path) -> None:
    text = path.read_text()

    # Better busy/action-running dialog.
    text = text.replace(
        "messagebox.showinfo('Busy','Another action is already running.')",
        "messagebox.showinfo('Action already running','Another action is already running. Please wait for it to finish.')",
    )

    # Let long labels wrap instead of clipping on the right column.
    text = text.replace(
        "def label(self,p,text=None,var=None,size=10,color=None,bold=False,**g):\n"
        "  w=tk.Label(p,text=text,textvariable=var,bg=p['bg'],fg=color or C['text'],font=(\"Inter\",size,\"bold\" if bold else \"normal\"),anchor='w',justify='left'); w.grid(**g); return w",
        "def label(self,p,text=None,var=None,size=10,color=None,bold=False,**g):\n"
        "  wrap=g.pop('wraplength', 0)\n"
        "  w=tk.Label(p,text=text,textvariable=var,bg=p['bg'],fg=color or C['text'],font=(\"Inter\",size,\"bold\" if bold else \"normal\"),anchor='w',justify='left',wraplength=wrap); w.grid(**g); return w",
    )

    # Add a global vertical scrollbar around the whole content area.
    # Linux/COSMIC can emit Button-4/Button-5 instead of MouseWheel, so bind both.
    text = text.replace(
        "m=tk.Frame(self.root,bg=C['bg'],padx=12,pady=12); m.pack(fill='both',expand=True); m.columnconfigure(0,weight=2); m.columnconfigure(1,weight=1); m.rowconfigure(1,weight=1)",
        "canvas=tk.Canvas(self.root,bg=C['bg'],highlightthickness=0,bd=0)\n"
        "  vsb=tk.Scrollbar(self.root,orient='vertical',command=canvas.yview)\n"
        "  canvas.configure(yscrollcommand=vsb.set)\n"
        "  canvas.pack(side='left',fill='both',expand=True)\n"
        "  vsb.pack(side='right',fill='y')\n"
        "  m=tk.Frame(canvas,bg=C['bg'],padx=12,pady=12)\n"
        "  win=canvas.create_window((0,0),window=m,anchor='nw')\n"
        "  m.bind('<Configure>',lambda e: canvas.configure(scrollregion=canvas.bbox('all')))\n"
        "  canvas.bind('<Configure>',lambda e: canvas.itemconfigure(win,width=e.width))\n"
        "  canvas.bind_all('<MouseWheel>',lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),'units'))\n"
        "  canvas.bind_all('<Button-4>',lambda e: canvas.yview_scroll(-3,'units'))\n"
        "  canvas.bind_all('<Button-5>',lambda e: canvas.yview_scroll(3,'units'))\n"
        "  m.columnconfigure(0,weight=2); m.columnconfigure(1,weight=1); m.rowconfigure(1,weight=1)",
    )
    # Existing installs may already have the canvas patch; add missing Linux wheel bindings if needed.
    if "<Button-4>" not in text:
        text = text.replace(
            "canvas.bind_all('<MouseWheel>',lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),'units'))",
            "canvas.bind_all('<MouseWheel>',lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),'units'))\n"
            "  canvas.bind_all('<Button-4>',lambda e: canvas.yview_scroll(-3,'units'))\n"
            "  canvas.bind_all('<Button-5>',lambda e: canvas.yview_scroll(3,'units'))",
        )

    # More modern header logo/badge.
    text = text.replace(
        "h=tk.Frame(m,bg=C['panel'],padx=18,pady=14); h.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,8)); h.columnconfigure(0,weight=1)\n"
        "  self.label(h,\"Magic Mouse\",size=22,bold=True,row=0,column=0,sticky='w'); self.label(h,var=self.session,size=10,color=C['muted'],row=1,column=0,sticky='w',pady=(6,0)); self.label(h,var=self.mode,size=10,color=C['cyan'],bold=True,row=2,column=0,sticky='w',pady=(4,0)); self.label(h,var=self.status,size=10,color=C['muted'],row=3,column=0,sticky='w',pady=(4,0)); self.button(h,\"Refresh\",self.refresh_status,row=0,column=1,rowspan=2,padx=(12,0),sticky='e')",
        "h=tk.Frame(m,bg=C['panel'],padx=18,pady=14); h.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,8)); h.columnconfigure(1,weight=1)\n"
        "  logo=tk.Canvas(h,width=58,height=58,bg=C['panel'],highlightthickness=0,bd=0)\n"
        "  logo.grid(row=0,column=0,rowspan=4,sticky='nw',padx=(0,14))\n"
        "  logo.create_oval(5,5,53,53,fill=C['card'],outline=C['border'],width=2)\n"
        "  logo.create_oval(18,13,40,45,fill=C['card2'],outline=C['cyan'],width=2)\n"
        "  logo.create_line(29,16,29,27,fill=C['cyan'],width=2)\n"
        "  logo.create_arc(14,18,44,48,start=205,extent=130,style='arc',outline=C['blue'],width=3)\n"
        "  logo.create_arc(11,14,47,51,start=25,extent=130,style='arc',outline=C['purple'],width=3)\n"
        "  logo.create_text(29,31,text='↔',fill=C['text'],font=('Inter',13,'bold'))\n"
        "  self.label(h,\"Magic Mouse\",size=22,bold=True,row=0,column=1,sticky='w'); self.label(h,var=self.session,size=10,color=C['muted'],row=1,column=1,sticky='w',pady=(6,0)); self.label(h,var=self.mode,size=10,color=C['cyan'],bold=True,row=2,column=1,sticky='w',pady=(4,0)); self.label(h,var=self.status,size=10,color=C['muted'],row=3,column=1,sticky='w',pady=(4,0)); self.button(h,\"Refresh\",self.refresh_status,row=0,column=2,rowspan=2,padx=(12,0),sticky='e')",
    )

    # Remove the separate Very Relaxed button; it remains available in the dropdown.
    text = text.replace(
        "self.button(sp,\"Apply Preset\",self.apply_sens,True,row=2,column=1,padx=4,pady=4,sticky='ew'); self.button(sp,\"Tihulu\",lambda:self.apply_named('Tihulu'),row=2,column=2,padx=4,pady=4,sticky='ew'); self.button(sp,\"Very Relaxed\",lambda:self.apply_named('Very Relaxed'),row=2,column=3,padx=4,pady=4,sticky='ew')",
        "self.button(sp,\"Apply Preset\",self.apply_sens,True,row=2,column=1,padx=4,pady=4,sticky='ew'); self.button(sp,\"Tihulu\",lambda:self.apply_named('Tihulu'),row=2,column=2,columnspan=2,padx=4,pady=4,sticky='ew')",
    )

    # Add/keep custom example text under the entry fields.
    if EXAMPLE not in text:
        old = "self.button(sp,\"Apply Custom Sensitivity\",self.apply_custom,row=5,column=0,columnspan=4,padx=4,pady=(8,0),sticky='ew')"
        new = "self.label(sp,\"" + EXAMPLE + "\",size=9,color=C['muted'],row=5,column=0,columnspan=4,sticky='w',padx=4,pady=(8,0),wraplength=560); " + \
              "self.button(sp,\"Apply Custom Sensitivity\",self.apply_custom,row=6,column=0,columnspan=4,padx=4,pady=(8,0),sticky='ew')"
        text = text.replace(old, new, 1)
    else:
        text = text.replace(
            "self.label(sp,\"" + EXAMPLE + "\",size=9,color=C['muted'],row=5,column=0,columnspan=4,sticky='w',padx=4,pady=(8,0));",
            "self.label(sp,\"" + EXAMPLE + "\",size=9,color=C['muted'],row=5,column=0,columnspan=4,sticky='w',padx=4,pady=(8,0),wraplength=560);",
        )

    # Wrap right-column guide text.
    text = text.replace(
        "self.label(test,\"Browser uses X. Workspace uses Y. Use Custom for separate tuning.\",size=9,color=C['muted'],row=2,column=0,columnspan=2,sticky='w',pady=(10,0))",
        "self.label(test,\"Browser uses X. Workspace uses Y. Use Custom for separate tuning.\",size=9,color=C['muted'],row=2,column=0,columnspan=2,sticky='w',pady=(10,0),wraplength=300)",
    )
    text = text.replace(
        "self.label(guide,\"Tihulu: safer browser swipes, lighter vertical workspace swipes.\\n\\nVery Relaxed: safest option if accidental gestures still happen.\\n\\nCustom: manual X/Y/Cooldown/Axis Lock.\",size=10,color=C['muted'],row=1,column=0,sticky='nw')",
        "self.label(guide,\"Tihulu: safer browser swipes, lighter vertical workspace swipes.\\n\\nVery Relaxed: safest option if accidental gestures still happen.\\n\\nCustom: manual X/Y/Cooldown/Axis Lock.\",size=10,color=C['muted'],row=1,column=0,sticky='nw',wraplength=300)",
    )

    # After a background action finishes, the status line should say Done instead of staying on the last progress text.
    text = text.replace(
        "if done: done(res)\n     self.refresh_status()\n     if show and success: messagebox.showinfo(title,success)",
        "if done: done(res)\n     self.status.set('Done')\n     self.root.after(250,self.refresh_status)\n     self.root.after(900,lambda:self.status.set('Done'))\n     if show and success: messagebox.showinfo(title,success)",
    )

    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-modern-panel-v1.5.1.py /path/to/magic-mouse-control-panel", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f"control panel not found: {target}", file=sys.stderr)
        return 1
    patch(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
