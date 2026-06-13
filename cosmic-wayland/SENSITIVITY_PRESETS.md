# COSMIC sensitivity presets

The control panel presets are:

| Preset | X threshold | Y threshold | Cooldown | Axis lock |
|---|---:|---:|---:|---:|
| Default | 360 | 420 | 450 ms | 1.15 |
| Tihulu | 550 | 480 | 550 ms | 1.35 |
| Sensitive | 280 | 340 | 380 ms | 1.10 |
| Relaxed | 460 | 520 | 550 ms | 1.20 |
| Very Relaxed | 720 | 820 | 900 ms | 1.35 |
| Custom | user value | user value | user value | user value |

Use `Custom` to enter your own X threshold, Y threshold, cooldown in milliseconds, and axis lock ratio directly in the GUI.

Install stable v1.4.8 with these presets and the Custom sensitivity fields:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.8-relaxed.sh)"
```

The modern UI preview receives the same preset values and Custom controls through its patch script.
