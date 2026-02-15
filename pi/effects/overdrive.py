import numpy as np


class Overdrive:
    """Soft-clipping distortion using tanh saturation with tone control."""

    def __init__(self, gain=5.0, tone=0.6, level=0.7):
        self.enabled = True
        self.gain = gain
        self.tone = tone
        self.level = level
        self._filter_state = 0.0  # One-pole low-pass filter state

    def process(self, samples):
        # Boost the signal
        driven = samples * self.gain

        # Soft clip via tanh
        clipped = np.tanh(driven)

        # One-pole low-pass tone filter: higher tone = brighter
        # Coefficient: 0 = very dark, 1 = fully bright (bypass)
        coeff = 0.1 + 0.9 * self.tone
        out = np.empty_like(clipped)
        state = self._filter_state
        for i in range(len(clipped)):
            state = state + coeff * (clipped[i] - state)
            out[i] = state
        self._filter_state = state

        return out * self.level
