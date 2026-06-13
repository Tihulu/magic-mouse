# Magic Mouse COSMIC Wayland stable v1.4.8

This folder keeps the stable v1.4.8 control panel path available as a safe fallback.

Use this if you want the simple, known-good v1.4.8 interface instead of trying the modern preview UI.

## Install stable v1.4.8

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/stable-v1.4.8/install.sh)"
```

Alternative with `wget`:

```bash
bash -c "$(wget -qO- https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/stable-v1.4.8/install.sh)"
```

## Notes

- This installer runs the stable `setup-cosmic-v1.4.8.sh` path.
- v1.4.8 fixes the v1.4.7 unterminated f-string regression.
- It keeps the lightweight Tk GUI and background actions.
