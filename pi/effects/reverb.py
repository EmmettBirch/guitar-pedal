import numpy as np


class _CombFilter:
    """Comb filter with damping for Schroeder reverb."""

    def __init__(self, delay_length, feedback, damping):
        self.buffer = np.zeros(delay_length, dtype=np.float64)
        self.pos = 0
        self.feedback = feedback
        self.damping = damping
        self._filter_state = 0.0

    def process_sample(self, x):
        out = self.buffer[self.pos]

        # One-pole low-pass damping filter on the feedback path
        self._filter_state = (out * (1.0 - self.damping)
                              + self._filter_state * self.damping)

        self.buffer[self.pos] = x + self._filter_state * self.feedback
        self.pos = (self.pos + 1) % len(self.buffer)
        return out


class _AllpassFilter:
    """Allpass filter for Schroeder reverb."""

    def __init__(self, delay_length, gain=0.5):
        self.buffer = np.zeros(delay_length, dtype=np.float64)
        self.pos = 0
        self.gain = gain

    def process_sample(self, x):
        delayed = self.buffer[self.pos]
        out = -x * self.gain + delayed
        self.buffer[self.pos] = x + delayed * self.gain
        self.pos = (self.pos + 1) % len(self.buffer)
        return out


class Reverb:
    """Schroeder reverb with 4 parallel comb filters and 2 series allpass filters."""

    def __init__(self, room_size=0.7, damping=0.5, mix=0.3):
        self.enabled = True
        self.room_size = room_size
        self.damping = damping
        self.mix = mix

        # Comb filter delay lengths (classic Schroeder values), scaled by room_size
        comb_delays = [1116, 1188, 1277, 1356]
        self._combs = [
            _CombFilter(
                delay_length=int(d * room_size),
                feedback=0.84,
                damping=damping
            )
            for d in comb_delays
        ]

        # Allpass filter delay lengths (fixed)
        allpass_delays = [225, 556]
        self._allpasses = [
            _AllpassFilter(delay_length=d, gain=0.5)
            for d in allpass_delays
        ]

    def process(self, samples):
        out = np.empty_like(samples)

        for i in range(len(samples)):
            x = samples[i]

            # Sum parallel comb filters
            comb_sum = 0.0
            for comb in self._combs:
                comb_sum += comb.process_sample(x)

            comb_sum /= len(self._combs)

            # Series allpass filters
            ap_out = comb_sum
            for ap in self._allpasses:
                ap_out = ap.process_sample(ap_out)

            # Mix dry and wet
            out[i] = x * (1.0 - self.mix) + ap_out * self.mix

        return out
