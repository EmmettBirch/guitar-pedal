# Changelog

## [Unreleased] - 2026-03-30

### Added
- Rotary encoder support (`pi/hardware/encoders.py`) — two encoders post pygame custom events (ENC1_ROTATE, ENC1_CLICK, ENC2_ROTATE, ENC2_CLICK) so all screens can handle them via the normal event loop. Gracefully no-ops if gpiozero is unavailable (e.g. dev PC).
- Encoder Test screen (`pi/ui/encoder_test_screen.py`) — shows live rotation direction, click flashes, and a running count per encoder. Accessible from the main menu. Useful for verifying GPIO wiring without needing the full app.
- Desktop launcher (`~/Desktop/guitar-pedal.desktop`) — double-click to launch the app from the Pi desktop without a terminal.

### Changed
- Menu now includes "Enc Test" option (first item for easy access during hardware debugging).
- Encoder navigation wired into Menu, Effect Chain, and Effects screens (ENC1 scrolls/selects, ENC2 adjusts values or goes back).
