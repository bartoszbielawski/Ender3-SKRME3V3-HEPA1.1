# Klipper tuning notes (Ender 3, SKR Mini E3 V3)

- `NOTES.md` — working notes of the tuning (Polish); host names, IPs and logins replaced by placeholders.
- `cura-settings.md` — Cura profile matching the tune.
- `config/` — Klipper config snapshot from 2026-11-18. **Taken before the last changes of that day**; differences vs. the live printer:
  `z_offset` 1.844 -> 1.814, `axes_map` y,-z,-x -> y,x,z, new `[firmware_retraction]` (0.6 mm / 40 mm/s),
  `END_PRINT` retracts while lifting (`G1 E-3 Z2 F2400`, then `G1 Z8`). To be refreshed when the printer is reachable again.
- `firmware-configs/` — MCU build configs. `scripts/` — G-code test generators.
