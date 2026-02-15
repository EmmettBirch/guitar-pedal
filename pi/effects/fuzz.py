import numpy as np


class Fuzz:
    """Hard-clipping distortion with asymmetric clipping and high-pass pre-filter."""

    def __init__(self, gain=15.0, threshold=0.3, tone=0.5, level=0.6):
        self.enabled = True
        self.gain = gain
        self.threshold = threshold
        self.tone = tone
        self.level = level
        self._hp_state = 0.0   # High-pass pre-filter state
        self._lp_state = 0.0   # Low-pass tone filter state

    def process(self, samples):
        # High-pass pre-filter (~35 Hz at 44100 Hz) to remove mud
        # RC constant for ~35 Hz: alpha = 1 / (1 + 2*pi*35/44100) ~ 0.995
        hp_alpha = 0.995
        hp_out = np.empty_like(samples)
        hp_state = self._hp_state
        prev_sample = hp_state
        for i in range(len(samples)):
            hp_out[i] = hp_alpha * (hp_out[i - 1] if i > 0 else 0.0) + hp_alpha * (samples[i] - prev_sample)
            prev_sample = samples[i]
        self._hp_state = samples[-1] if len(samples) > 0 else hp_state

        # Massive gain boost
        gained = hp_out * self.gain

        # Asymmetric hard clipping: positive clips tighter
        pos_thresh = self.threshold
        neg_thresh = self.threshold * 1.5
        clipped = np.where(
            gained > pos_thresh, pos_thresh,
            np.where(gained < -neg_thresh, -neg_thresh, gained)
        )

        # Normalise to [-1, 1] range
        max_thresh = max(pos_thresh, neg_thresh)
        if max_thresh > 0:
            clipped = clipped / max_thresh

        # One-pole low-pass tone filter
        coeff = 0.1 + 0.9 * self.tone
        out = np.empty_like(clipped)
        state = self._lp_state
        for i in range(len(clipped)):
            state = state + coeff * (clipped[i] - state)
            out[i] = state
        self._lp_state = state

        return out * self.level
