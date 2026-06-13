# COSMIC sensitivity presets

The relaxed sensitivity update changes the control panel presets as follows:

| Preset | X threshold | Y threshold | Cooldown | Axis lock |
|---|---:|---:|---:|---:|
| Default | 360 | 420 | 450 ms | 1.15 |
| Sensitive | 280 | 340 | 380 ms | 1.10 |
| Relaxed | 560 | 640 | 700 ms | 1.25 |
| Very Relaxed | 720 | 820 | 900 ms | 1.35 |

Use `Very Relaxed` if workspace or browser gestures still trigger too easily.

Install stable v1.4.8 with the relaxed presets:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.8-relaxed.sh)"
```

The modern UI preview also receives the same preset values through its patch script.
