# Magic Mouse COSMIC modern UI v1.5.0

This folder contains the lightweight modern UI experiment for the COSMIC Wayland Magic Mouse control panel.

It keeps the stable v1.4.8 backend and applies a small Tk/ttk styling patch for a cleaner Apple-like feel. It does not add GTK, Qt, Electron, or any heavy UI dependency.

## Install modern UI preview

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/modern-v1.5.0/install.sh)"
```

Alternative with `wget`:

```bash
bash -c "$(wget -qO- https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/modern-v1.5.0/install.sh)"
```

## What changes

- Cleaner Apple-like spacing and typography.
- Lighter modern card/panel colors through Tk/ttk styling.
- Accent styling for the stable defaults button.
- The stable v1.4.8 background action and progress behavior stays intact.

## Fallback

To return to the simple stable UI:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/stable-v1.4.8/install.sh)"
```
