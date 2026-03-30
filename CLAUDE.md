# CLAUDE.md — Project Context for AI Assistants

## What this project is
A digital guitar effects pedal UI running on a Raspberry Pi 4 with a 3.5" touchscreen LCD. The Pi handles the UI (pygame) and controls. An Electrosmith Daisy (not yet integrated) will handle real-time audio DSP.

## Critical: entry point
**`project.py` is the real entry point** — it contains `main()` and is what the desktop launcher and auto-start run.
`pi/main.py` exists but is NOT called by anything currently. Do not edit `pi/main.py` expecting changes to show up in the running app.

## SSH access
- Host: `emmett@192.168.1.220`
- Key auth configured, no password needed

## How to run the app
```
DISPLAY=:0 python3 ~/guitar-pedal/project.py
```

## How to add a new screen
1. Create `pi/ui/your_screen.py` with a class that has `handle_event(event)` and `draw(dt)` methods. Return `"back"` from `handle_event` to go back to the menu.
2. Add `STATE_YOUR_SCREEN = "your_screen"` constant in `project.py`
3. Import and instantiate the screen inside `main()` in `project.py`
4. Add a menu item in `pi/ui/menu.py` (the `self.items` list)
5. Add selection handler in the `STATE_MENU` event block in `project.py`
6. Add event handler block (`elif state == STATE_YOUR_SCREEN`)
7. Add draw call (`elif state == STATE_YOUR_SCREEN: your_screen.draw(dt)`)

## Encoder GPIO wiring
| | CLK | DT | SW (click) |
|---|---|---|---|
| ENC1 (navigation) | GPIO 5 | GPIO 6 | GPIO 13 |
| ENC2 (value) | GPIO 19 | GPIO 26 | GPIO 16 |

Encoders post custom pygame events — import from `hardware.encoders`:
- `ENC1_ROTATE` / `ENC2_ROTATE` — event has `.delta` (+1 CW, -1 CCW)
- `ENC1_CLICK` / `ENC2_CLICK`

## Testing encoders without the app
```
python3 /tmp/test_encoders.py
```
Make sure the app is not running first (`pkill -f project.py`) or GPIO pins will be busy.

## Touchscreen back navigation
Other screens (tuner, effects, etc.) use a `btn_back = pygame.Rect(5, 5, 50, 32)` hit area for the back button — only return `"back"` when that rect is tapped, NOT on any tap anywhere on screen. Tapping anywhere causes the screen to immediately close due to event ordering with the menu tap.

## Known issues / gotchas
- `pi/main.py` is a dead entry point — ignore it, edit `project.py` instead
- GPIO pins error with "GPIO busy" if the app is already running when you try to use gpiozero directly
- Touchscreen tap-to-select in the menu uses `MOUSEBUTTONUP`, so screens must not return `"back"` on `MOUSEBUTTONDOWN` anywhere (it fires before state transition completes)
