# encoders.py - Rotary encoder GPIO input.
# Posts pygame custom events so the UI event loop can react to encoder turns and clicks.
# Gracefully no-ops when gpiozero is not available (e.g. on a dev PC).

import pygame

try:
    from gpiozero import RotaryEncoder, Button
    _GPIOZERO = True
except ImportError:
    _GPIOZERO = False

# Custom pygame event type IDs
ENC1_ROTATE = pygame.USEREVENT + 1   # .delta = +1 (CW) or -1 (CCW)
ENC1_CLICK  = pygame.USEREVENT + 2
ENC2_ROTATE = pygame.USEREVENT + 3   # .delta = +1 (CW) or -1 (CCW)
ENC2_CLICK  = pygame.USEREVENT + 4


def _post(event_type, **kwargs):
    pygame.event.post(pygame.event.Event(event_type, **kwargs))


def setup_encoders():
    """
    Register GPIO callbacks for both rotary encoders.
    Returns the gpiozero device objects — keep the return value alive in the
    caller to prevent them being garbage-collected.
    Returns None if gpiozero is unavailable.

    Encoder 1 (navigation):  CLK=GPIO5, DT=GPIO6,  SW=GPIO13
    Encoder 2 (value):       CLK=GPIO19, DT=GPIO26, SW=GPIO16
    """
    if not _GPIOZERO:
        return None

    enc1 = RotaryEncoder(5, 6)
    btn1 = Button(13, pull_up=True, bounce_time=0.05)

    enc2 = RotaryEncoder(19, 26)
    btn2 = Button(16, pull_up=True, bounce_time=0.05)

    enc1.when_rotated_clockwise         = lambda: _post(ENC1_ROTATE, delta=+1)
    enc1.when_rotated_counter_clockwise = lambda: _post(ENC1_ROTATE, delta=-1)
    btn1.when_pressed                   = lambda: _post(ENC1_CLICK)

    enc2.when_rotated_clockwise         = lambda: _post(ENC2_ROTATE, delta=+1)
    enc2.when_rotated_counter_clockwise = lambda: _post(ENC2_ROTATE, delta=-1)
    btn2.when_pressed                   = lambda: _post(ENC2_CLICK)

    return enc1, btn1, enc2, btn2
