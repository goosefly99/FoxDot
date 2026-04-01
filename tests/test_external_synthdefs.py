"""Tests for lib/SCLang/_ExternalSynthDefs.py — QuarkSynthDef wrappers."""

import unittest
import sys
import os

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from FoxDot.lib.SCLang._ExternalSynthDefs import (
    QuarkSynthDef,
    cheappiano, rhodey, harpsichord, kalimba,
    everythingrhodes, dreamyrhodes,
    plucking, marimbasynth, xylophone,
    hoover,
    organdonor, moogbass, sqrgrn,
    henontri, ring1,
)
from FoxDot.lib.SCLang.SynthDef import SynthDefs, SynthDefBaseClass


class TestQuarkSynthDefClass(unittest.TestCase):
    """Test the QuarkSynthDef subclass behaviour."""

    def test_inherits_from_base(self):
        self.assertTrue(issubclass(QuarkSynthDef, SynthDefBaseClass))

    def test_write_returns_none(self):
        """write() is a no-op for Quark synths (no .scd file)."""
        s = QuarkSynthDef("_test_write_noop")
        self.assertIsNone(s.write())
        # Cleanup
        SynthDefs.pop("_test_write_noop", None)

    def test_load_returns_none(self):
        """load() is a no-op for Quark synths (compiled at SC boot)."""
        s = QuarkSynthDef("_test_load_noop")
        self.assertIsNone(s.load())
        SynthDefs.pop("_test_load_noop", None)

    def test_str_returns_repr(self):
        s = QuarkSynthDef("_test_str_repr")
        self.assertEqual(str(s), repr(s))
        SynthDefs.pop("_test_str_repr", None)

    def test_registered_in_container(self):
        """Creating a QuarkSynthDef should register it in SynthDefs."""
        s = QuarkSynthDef("_test_registration")
        self.assertIn("_test_registration", SynthDefs)
        self.assertIs(SynthDefs["_test_registration"], s)
        SynthDefs.pop("_test_registration", None)


class TestModuleLevelSynths(unittest.TestCase):
    """Test that all module-level synth instances are properly created."""

    # All synths defined in the module
    ALL_SYNTHS = [
        ("cheappiano", cheappiano),
        ("rhodey", rhodey),
        ("harpsichord", harpsichord),
        ("kalimba", kalimba),
        ("everythingrhodes", everythingrhodes),
        ("dreamyrhodes", dreamyrhodes),
        ("plucking", plucking),
        ("marimbasynth", marimbasynth),
        ("xylophone", xylophone),
        ("hoover", hoover),
        ("organdonor", organdonor),
        ("moogbass", moogbass),
        ("sqrgrn", sqrgrn),
        ("henontri", henontri),
        ("ring1", ring1),
    ]

    def test_all_are_quark_synthdef_instances(self):
        for name, synth in self.ALL_SYNTHS:
            with self.subTest(synth=name):
                self.assertIsInstance(synth, QuarkSynthDef)

    def test_all_registered_in_synthdefs(self):
        for name, synth in self.ALL_SYNTHS:
            with self.subTest(synth=name):
                self.assertIn(name, SynthDefs)
                self.assertIs(SynthDefs[name], synth)

    def test_names_match(self):
        for name, synth in self.ALL_SYNTHS:
            with self.subTest(synth=name):
                self.assertEqual(synth.name, name)

    def test_all_have_base_defaults(self):
        """Every synth should inherit standard defaults (amp, sus, pan, etc.)."""
        base_keys = {"amp", "sus", "pan", "freq"}
        for name, synth in self.ALL_SYNTHS:
            with self.subTest(synth=name):
                for key in base_keys:
                    self.assertIn(key, synth.defaults,
                                  f"{name} missing default '{key}'")


class TestSynthDefaults(unittest.TestCase):
    """Test that custom defaults are applied correctly."""

    def test_cheappiano_defaults(self):
        self.assertAlmostEqual(cheappiano.defaults["vel"], 0.8)
        self.assertAlmostEqual(cheappiano.defaults["decay"], 0.3)

    def test_rhodey_defaults(self):
        self.assertAlmostEqual(rhodey.defaults["lfoSpeed"], 0.4)
        self.assertAlmostEqual(rhodey.defaults["lfoDepth"], 0.1)

    def test_kalimba_defaults(self):
        self.assertAlmostEqual(kalimba.defaults["clickrel"], 0.01)

    def test_everythingrhodes_defaults(self):
        d = everythingrhodes.defaults
        self.assertAlmostEqual(d["vel"], 0.8)
        self.assertAlmostEqual(d["modIndex"], 0.2)
        self.assertAlmostEqual(d["mix"], 0.2)
        self.assertAlmostEqual(d["lfoSpeed"], 0.4)
        self.assertAlmostEqual(d["lfoDepth"], 0.1)

    def test_dreamyrhodes_defaults(self):
        d = dreamyrhodes.defaults
        self.assertAlmostEqual(d["vel"], 0.6)
        self.assertAlmostEqual(d["modIndex"], 0.2)

    def test_plucking_defaults(self):
        self.assertAlmostEqual(plucking.defaults["coef"], 0.2)

    def test_hoover_defaults(self):
        self.assertAlmostEqual(hoover.defaults["glide"], 0.5)

    def test_moogbass_defaults(self):
        self.assertEqual(moogbass.defaults["cutoff"], 1000)
        self.assertAlmostEqual(moogbass.defaults["gain"], 2.0)

    def test_sqrgrn_defaults(self):
        self.assertEqual(sqrgrn.defaults["detune"], 2)
        self.assertEqual(sqrgrn.defaults["grainFreq"], 10)

    def test_henontri_defaults(self):
        d = henontri.defaults
        self.assertAlmostEqual(d["a"], 1.3)
        self.assertAlmostEqual(d["b"], 0.3)
        self.assertEqual(d["mFreq"], 2)

    def test_ring1_defaults(self):
        self.assertAlmostEqual(ring1.defaults["spread"], 0.5)

    def test_no_defaults_synths_still_have_base(self):
        """Synths without custom defaults should still have base defaults."""
        for synth in (harpsichord, marimbasynth, xylophone, organdonor):
            with self.subTest(synth=synth.name):
                self.assertIn("amp", synth.defaults)
                self.assertIn("sus", synth.defaults)


if __name__ == "__main__":
    unittest.main()
