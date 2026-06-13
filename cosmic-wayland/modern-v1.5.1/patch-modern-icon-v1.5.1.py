#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ICON_DATA = """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"""


def patch(path: Path) -> None:
    text = path.read_text()
    if "ICON_DATA =" not in text:
        text = text.replace("C={", "ICON_DATA=" + repr(ICON_DATA) + "\nC={", 1)

    text = text.replace(
        "self.root=root; root.title(f\"Magic Mouse Control Panel {VERSION}\"); root.geometry(\"1040x760\"); root.minsize(920,640); root.configure(bg=C['bg'])",
        "self.root=root; root.title(f\"Magic Mouse Control Panel {VERSION}\"); root.geometry(\"1040x760\"); root.minsize(920,640); root.configure(bg=C['bg'])\n"
        "  try:\n"
        "   self.app_icon_img=tk.PhotoImage(data=ICON_DATA)\n"
        "   root.iconphoto(True,self.app_icon_img)\n"
        "  except Exception:\n"
        "   pass",
        1,
    )

    old = """  logo=tk.Canvas(h,width=58,height=58,bg=C['panel'],highlightthickness=0,bd=0)
  logo.grid(row=0,column=0,rowspan=4,sticky='nw',padx=(0,14))
  logo.create_oval(5,5,53,53,fill=C['card'],outline=C['border'],width=2)
  logo.create_oval(18,13,40,45,fill=C['card2'],outline=C['cyan'],width=2)
  logo.create_line(29,16,29,27,fill=C['cyan'],width=2)
  logo.create_arc(14,18,44,48,start=205,extent=130,style='arc',outline=C['blue'],width=3)
  logo.create_arc(11,14,47,51,start=25,extent=130,style='arc',outline=C['purple'],width=3)
  logo.create_text(29,31,text='↔',fill=C['text'],font=('Inter',13,'bold'))"""
    new = """  try:
   self.logo_img=tk.PhotoImage(data=ICON_DATA)
   tk.Label(h,image=self.logo_img,bg=C['panel'],bd=0,highlightthickness=0).grid(row=0,column=0,rowspan=4,sticky='nw',padx=(0,14))
  except Exception:
   logo=tk.Canvas(h,width=58,height=58,bg=C['panel'],highlightthickness=0,bd=0)
   logo.grid(row=0,column=0,rowspan=4,sticky='nw',padx=(0,14))
   logo.create_oval(5,5,53,53,fill=C['card'],outline=C['border'],width=2)
   logo.create_oval(18,13,40,45,fill=C['card2'],outline=C['cyan'],width=2)
   logo.create_line(29,16,29,27,fill=C['cyan'],width=2)
   logo.create_arc(14,18,44,48,start=205,extent=130,style='arc',outline=C['blue'],width=3)
   logo.create_arc(11,14,47,51,start=25,extent=130,style='arc',outline=C['purple'],width=3)"""
    text = text.replace(old, new, 1)
    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-modern-icon-v1.5.1.py /path/to/magic-mouse-control-panel", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f"control panel not found: {target}", file=sys.stderr)
        return 1
    patch(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
