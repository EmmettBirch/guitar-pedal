# test_effect_chain.py - Tests for the EffectChain processor

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi'))

from effects.effect_chain import EffectChain
from effects import Overdrive, Fuzz, Chorus, Delay, Reverb


class TestEffectChainInit:
    def test_starts_with_empty_effects(self):
        chain = EffectChain()
        assert chain.effects == []


class TestEffectChainPassthrough:
    def test_no_effects_returns_input_unchanged(self):
        chain = EffectChain()
        samples = np.array([0.0, 0.5, -0.5, 1.0, -1.0])
        result = chain.process(samples.copy())
        np.testing.assert_array_equal(result, samples)

    def test_disabled_effects_are_skipped(self):
        chain = EffectChain()
        od = Overdrive()
        od.enabled = False
        chain.effects = [od]
        samples = np.array([0.1, 0.2, 0.3])
        result = chain.process(samples.copy())
        np.testing.assert_array_equal(result, samples)

    def test_all_disabled_is_passthrough(self):
        chain = EffectChain()
        effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
        for fx in effects:
            fx.enabled = False
        chain.effects = effects
        samples = np.array([0.1, -0.2, 0.3, -0.4, 0.5])
        result = chain.process(samples.copy())
        np.testing.assert_array_equal(result, samples)


class TestEffectChainProcessing:
    def test_enabled_effect_modifies_signal(self):
        chain = EffectChain()
        od = Overdrive(gain=10.0)
        od.enabled = True
        chain.effects = [od]
        samples = np.array([0.5, -0.5, 0.3, -0.3])
        result = chain.process(samples.copy())
        assert not np.array_equal(result, samples)

    def test_output_clipped_to_valid_range(self):
        chain = EffectChain()
        od = Overdrive(gain=50.0, level=5.0)
        od.enabled = True
        chain.effects = [od]
        samples = np.array([1.0, -1.0, 0.8, -0.8])
        result = chain.process(samples)
        assert np.all(result >= -1.0)
        assert np.all(result <= 1.0)

    def test_chain_order_matters(self):
        samples = np.random.uniform(-0.5, 0.5, 512).astype(np.float64)

        chain1 = EffectChain()
        chain1.effects = [Overdrive(gain=8.0), Delay(delay_ms=200, mix=0.5)]
        result1 = chain1.process(samples.copy())

        chain2 = EffectChain()
        chain2.effects = [Delay(delay_ms=200, mix=0.5), Overdrive(gain=8.0)]
        result2 = chain2.process(samples.copy())

        assert not np.array_equal(result1, result2)

    def test_mixed_enabled_disabled(self):
        chain = EffectChain()
        od = Overdrive(gain=5.0)
        od.enabled = True
        fuzz = Fuzz()
        fuzz.enabled = False
        delay = Delay(delay_ms=100, mix=0.5)
        delay.enabled = True
        chain.effects = [od, fuzz, delay]

        samples = np.random.uniform(-0.3, 0.3, 256).astype(np.float64)
        result = chain.process(samples.copy())
        assert not np.array_equal(result, samples)

    def test_all_five_effects_together(self):
        chain = EffectChain()
        chain.effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
        samples = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100)
        result = chain.process(samples.copy())
        assert result.shape == samples.shape
        assert np.all(result >= -1.0)
        assert np.all(result <= 1.0)
