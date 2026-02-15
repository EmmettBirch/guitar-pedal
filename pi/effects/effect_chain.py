import numpy as np

# effect_chain.py - Processes audio samples through an ordered list of effects.
# Currently a passthrough skeleton — effects will be added later.
#
# Each effect must follow this interface:
#   - effect.enabled (bool)       — whether the effect is active
#   - effect.process(samples)     — takes and returns a numpy array of samples
#
# With no effects loaded, process() returns the input unchanged.


class EffectChain:
    def __init__(self):
        self.effects = []   # Ordered list of effect objects (empty for now)

    def process(self, samples):
        """Run samples through each enabled effect in order.

        Effects are applied in list order (first added = first in the chain).
        Disabled effects are skipped. With no effects loaded, this returns
        the input unchanged — a clean passthrough.

        Args:
            samples: numpy array of audio samples in [-1.0, 1.0]

        Returns:
            numpy array of processed samples (same shape as input)
        """
        for effect in self.effects:
            if effect.enabled:
                samples = effect.process(samples)
        return np.clip(samples, -1.0, 1.0)
