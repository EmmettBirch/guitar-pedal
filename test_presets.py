# test_presets.py - Tests for the preset data layer

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi'))

import effects.presets as presets_mod
from effects.presets import (
    FACTORY_PRESETS, EFFECT_PARAMS,
    load_user_presets, save_user_presets, get_all_presets,
    snapshot_chain, apply_preset,
)
from effects.effect_chain import EffectChain
from effects import Overdrive, Fuzz, Chorus, Delay, Reverb


class TestFactoryPresets:
    def test_three_factory_presets_exist(self):
        assert len(FACTORY_PRESETS) == 3

    def test_factory_preset_names(self):
        names = [p["name"] for p in FACTORY_PRESETS]
        assert "Rock" in names
        assert "Metal" in names
        assert "Hip-Hop" in names

    def test_factory_presets_flagged_as_factory(self):
        for p in FACTORY_PRESETS:
            assert p["factory"] is True

    def test_factory_presets_have_effects_dict(self):
        for p in FACTORY_PRESETS:
            assert "effects" in p
            assert isinstance(p["effects"], dict)

    def test_factory_presets_cover_all_effects(self):
        expected_effects = {"Overdrive", "Fuzz", "Chorus", "Delay", "Reverb"}
        for p in FACTORY_PRESETS:
            assert set(p["effects"].keys()) == expected_effects


class TestEffectParams:
    def test_all_effects_registered(self):
        expected = {"Overdrive", "Fuzz", "Chorus", "Delay", "Reverb"}
        assert set(EFFECT_PARAMS.keys()) == expected

    def test_overdrive_params(self):
        attrs = EFFECT_PARAMS["Overdrive"]
        assert "gain" in attrs
        assert "tone" in attrs
        assert "level" in attrs

    def test_fuzz_params(self):
        attrs = EFFECT_PARAMS["Fuzz"]
        assert "gain" in attrs
        assert "threshold" in attrs

    def test_delay_params(self):
        attrs = EFFECT_PARAMS["Delay"]
        assert "delay_ms" in attrs
        assert "feedback" in attrs
        assert "mix" in attrs


class TestUserPresetPersistence:
    def setup_method(self):
        """Redirect user presets to a temp file for each test."""
        self._tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self._tmp.close()
        self._orig_path = presets_mod._USER_PRESETS_PATH
        presets_mod._USER_PRESETS_PATH = self._tmp.name
        # Start with no user presets
        os.unlink(self._tmp.name)

    def teardown_method(self):
        presets_mod._USER_PRESETS_PATH = self._orig_path
        if os.path.exists(self._tmp.name):
            os.unlink(self._tmp.name)

    def test_load_returns_empty_when_no_file(self):
        assert load_user_presets() == []

    def test_save_and_load_round_trip(self):
        data = [{"name": "Test", "factory": False, "effects": {}}]
        save_user_presets(data)
        loaded = load_user_presets()
        assert len(loaded) == 1
        assert loaded[0]["name"] == "Test"

    def test_save_creates_file(self):
        save_user_presets([])
        assert os.path.exists(self._tmp.name)

    def test_load_handles_corrupt_json(self):
        with open(self._tmp.name, "w") as f:
            f.write("not valid json{{{")
        assert load_user_presets() == []

    def test_get_all_includes_factory_and_user(self):
        save_user_presets([{"name": "Custom", "factory": False, "effects": {}}])
        all_presets = get_all_presets()
        names = [p["name"] for p in all_presets]
        assert "Rock" in names
        assert "Custom" in names
        assert len(all_presets) == len(FACTORY_PRESETS) + 1


class TestSnapshotChain:
    def test_snapshot_captures_all_effects(self):
        chain = EffectChain()
        chain.effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
        snap = snapshot_chain(chain, "MyPreset")
        assert snap["name"] == "MyPreset"
        assert snap["factory"] is False
        assert "Overdrive" in snap["effects"]
        assert "Fuzz" in snap["effects"]
        assert "Chorus" in snap["effects"]
        assert "Delay" in snap["effects"]
        assert "Reverb" in snap["effects"]

    def test_snapshot_captures_enabled_state(self):
        chain = EffectChain()
        od = Overdrive()
        od.enabled = False
        chain.effects = [od]
        snap = snapshot_chain(chain, "Test")
        assert snap["effects"]["Overdrive"]["enabled"] is False

    def test_snapshot_captures_param_values(self):
        chain = EffectChain()
        od = Overdrive(gain=12.0, tone=0.9, level=0.4)
        chain.effects = [od]
        snap = snapshot_chain(chain, "Test")
        assert snap["effects"]["Overdrive"]["gain"] == 12.0
        assert snap["effects"]["Overdrive"]["tone"] == 0.9
        assert snap["effects"]["Overdrive"]["level"] == 0.4

    def test_snapshot_is_json_serializable(self):
        chain = EffectChain()
        chain.effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
        snap = snapshot_chain(chain, "SerTest")
        # Should not raise
        json.dumps(snap)


class TestApplyPreset:
    def test_apply_sets_enabled_state(self):
        chain = EffectChain()
        od = Overdrive()
        od.enabled = True
        chain.effects = [od]

        preset = {
            "effects": {
                "Overdrive": {"enabled": False}
            }
        }
        apply_preset(chain, preset)
        assert od.enabled is False

    def test_apply_sets_param_values(self):
        chain = EffectChain()
        od = Overdrive(gain=5.0, tone=0.6, level=0.7)
        chain.effects = [od]

        preset = {
            "effects": {
                "Overdrive": {"enabled": True, "gain": 15.0, "tone": 0.3, "level": 0.9}
            }
        }
        apply_preset(chain, preset)
        assert od.gain == 15.0
        assert od.tone == 0.3
        assert od.level == 0.9

    def test_apply_ignores_unknown_effects(self):
        chain = EffectChain()
        od = Overdrive()
        chain.effects = [od]

        preset = {
            "effects": {
                "Overdrive": {"enabled": True, "gain": 8.0},
                "UnknownFX": {"enabled": True, "param": 42},
            }
        }
        # Should not raise
        apply_preset(chain, preset)
        assert od.gain == 8.0

    def test_round_trip_snapshot_apply(self):
        chain = EffectChain()
        chain.effects = [
            Overdrive(gain=12.0, tone=0.8, level=0.5),
            Fuzz(gain=20.0, threshold=0.4, tone=0.7, level=0.8),
            Chorus(rate=2.0, depth=0.008, mix=0.6),
            Delay(delay_ms=400, feedback=0.3, mix=0.4),
            Reverb(room_size=0.6, damping=0.4, mix=0.35),
        ]
        snap = snapshot_chain(chain, "RoundTrip")

        # Create a new chain with default values
        chain2 = EffectChain()
        chain2.effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
        apply_preset(chain2, snap)

        # Verify all values match
        assert chain2.effects[0].gain == 12.0
        assert chain2.effects[1].threshold == 0.4
        assert chain2.effects[2].rate == 2.0
        assert chain2.effects[3].delay_ms == 400
        assert chain2.effects[4].room_size == 0.6
