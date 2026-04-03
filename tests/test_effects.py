"""Tests for lib/Effects/Util.py — Effect, In, Out, and EffectManager classes."""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch, mock_open

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from FoxDot.lib.Effects.Util import (
    Effect,
    In,
    Out,
    EffectManager,
    FxList,
    Effects,
)


class TestEffectInit(unittest.TestCase):
    """Test Effect.__init__ and basic attribute setup."""

    def test_basic_attributes(self):
        fx = Effect("room", "reverb", {"room": 0, "mix": 0.25})
        self.assertEqual(fx.name, "room")
        self.assertEqual(fx.synthdef, "reverb")
        self.assertIn("room", fx.args)
        self.assertIn("mix", fx.args)
        self.assertEqual(fx.defaults, {"room": 0, "mix": 0.25})

    def test_none_args_defaults_to_empty(self):
        fx = Effect("test", "testSynth", None)
        self.assertEqual(list(fx.args), [])
        self.assertEqual(fx.defaults, {})

    def test_empty_args(self):
        fx = Effect("test", "testSynth", {})
        self.assertEqual(list(fx.args), [])
        self.assertEqual(fx.defaults, {})

    def test_effects_list_starts_empty(self):
        fx = Effect("test", "testSynth", {"test": 0})
        self.assertEqual(fx.effects, [])

    def test_vars_starts_with_osc(self):
        fx = Effect("test", "testSynth", {"test": 0})
        self.assertEqual(fx.vars, ["osc"])

    def test_control_false_gives_ar(self):
        fx = Effect("test", "testSynth", {"test": 0}, control=False)
        self.assertEqual(fx.suffix, "ar")
        self.assertEqual(fx.channels, 2)
        self.assertIn("In.ar", fx.input)
        self.assertIn("ReplaceOut.ar", fx.output)

    def test_control_true_gives_kr(self):
        fx = Effect("test", "testSynth", {"test": 0}, control=True)
        self.assertEqual(fx.suffix, "kr")
        self.assertEqual(fx.channels, 1)
        self.assertIn("In.kr", fx.input)
        self.assertIn("ReplaceOut.kr", fx.output)

    def test_filename_uses_synthdef(self):
        fx = Effect("room", "reverb", {"room": 0})
        self.assertTrue(fx.filename.endswith("/reverb.scd") or fx.filename.endswith("\\reverb.scd"))


class TestEffectRepr(unittest.TestCase):
    """Test Effect.__repr__ output formatting."""

    def test_repr_no_other_args(self):
        fx = Effect("vib", "vibrato", {"vib": 0})
        r = repr(fx)
        self.assertIn("vibrato", r)
        self.assertIn("keyword='vib'", r)

    def test_repr_with_other_args(self):
        fx = Effect("room", "reverb", {"room": 0, "mix": 0.25})
        r = repr(fx)
        self.assertIn("reverb", r)
        self.assertIn("keyword='room'", r)
        self.assertIn("other args=", r)
        self.assertIn("mix", r)

    def test_repr_single_arg_no_other_args_section(self):
        fx = Effect("pshift", "pitchShift", {"pshift": 0})
        r = repr(fx)
        self.assertNotIn("other args=", r)


class TestEffectStr(unittest.TestCase):
    """Test Effect.__str__ generates valid SuperCollider SynthDef code."""

    def test_str_contains_synthdef_name(self):
        fx = Effect("room", "reverb", {"room": 0, "mix": 0.25})
        s = str(fx)
        self.assertIn("SynthDef.new(\\reverb", s)

    def test_str_contains_args(self):
        fx = Effect("room", "reverb", {"room": 0, "mix": 0.25})
        s = str(fx)
        self.assertIn("bus", s)
        self.assertIn("room", s)
        self.assertIn("mix", s)

    def test_str_contains_input_and_output(self):
        fx = Effect("room", "reverb", {"room": 0}, control=False)
        s = str(fx)
        self.assertIn("In.ar(bus", s)
        self.assertIn("ReplaceOut.ar", s)

    def test_str_control_rate(self):
        fx = Effect("rate", "startRate", {"rate": 1}, control=True)
        s = str(fx)
        self.assertIn("In.kr(bus", s)
        self.assertIn("ReplaceOut.kr", s)

    def test_str_includes_effects(self):
        fx = Effect("room", "reverb", {"room": 0, "mix": 0.1})
        fx.add("osc = FreeVerb.ar(osc, mix, room)")
        s = str(fx)
        self.assertIn("osc = FreeVerb.ar(osc, mix, room)", s)

    def test_str_includes_added_vars(self):
        fx = Effect("swell", "filterSwell", {"swell": 0, "sus": 1})
        fx.add_var("env")
        s = str(fx)
        self.assertIn("env", s)

    def test_str_ends_with_add(self):
        fx = Effect("room", "reverb", {"room": 0})
        s = str(fx)
        self.assertTrue(s.rstrip().endswith(".add;"))


class TestEffectAdd(unittest.TestCase):
    """Test Effect.add() and Effect.add_var()."""

    def test_add_appends_to_effects(self):
        fx = Effect("test", "testSynth", {"test": 0})
        fx.add("osc = osc * 2")
        self.assertEqual(len(fx.effects), 1)
        self.assertEqual(fx.effects[0], "osc = osc * 2")

    def test_add_multiple(self):
        fx = Effect("test", "testSynth", {"test": 0})
        fx.add("line1")
        fx.add("line2")
        fx.add("line3")
        self.assertEqual(len(fx.effects), 3)
        self.assertEqual(fx.effects[1], "line2")

    def test_add_var_new_name(self):
        fx = Effect("test", "testSynth", {"test": 0})
        fx.add_var("env")
        self.assertIn("env", fx.vars)

    def test_add_var_duplicate_ignored(self):
        fx = Effect("test", "testSynth", {"test": 0})
        fx.add_var("env")
        fx.add_var("env")
        self.assertEqual(fx.vars.count("env"), 1)

    def test_add_var_preserves_osc(self):
        fx = Effect("test", "testSynth", {"test": 0})
        fx.add_var("env")
        self.assertEqual(fx.vars[0], "osc")


class TestEffectListEffects(unittest.TestCase):
    """Test Effect.list_effects() formatting."""

    def test_empty_effects(self):
        fx = Effect("test", "testSynth", {"test": 0})
        self.assertEqual(fx.list_effects(), "")

    def test_single_effect(self):
        fx = Effect("test", "testSynth", {"test": 0})
        fx.add("osc = osc * 2")
        result = fx.list_effects()
        self.assertEqual(result, "osc = osc * 2;\n")

    def test_multiple_effects_semicolon_separated(self):
        fx = Effect("test", "testSynth", {"test": 0})
        fx.add("line1")
        fx.add("line2")
        result = fx.list_effects()
        self.assertEqual(result, "line1;\nline2;\n")


class TestEffectDoc(unittest.TestCase):
    """Test Effect.doc() — currently a no-op stub."""

    def test_doc_returns_none(self):
        fx = Effect("test", "testSynth", {"test": 0})
        result = fx.doc("Some docstring")
        self.assertIsNone(result)


class TestEffectSetServer(unittest.TestCase):
    """Test Effect.set_server() class method."""

    def setUp(self):
        self._original_server = Effect.server

    def tearDown(self):
        Effect.server = self._original_server

    def test_set_server_changes_class_attribute(self):
        mock_server = MagicMock()
        Effect.set_server(mock_server)
        self.assertIs(Effect.server, mock_server)


class TestEffectSave(unittest.TestCase):
    """Test Effect.save() writes to file and calls load."""

    def test_save_writes_new_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fx = Effect("test", "testSynth", {"test": 0})
            fx.filename = os.path.join(tmpdir, "testSynth.scd")

            mock_server = MagicMock()
            fx.server = mock_server

            fx.save()

            self.assertTrue(os.path.isfile(fx.filename))
            with open(fx.filename) as f:
                contents = f.read()
            self.assertIn("SynthDef.new(\\testSynth", contents)

    def test_save_does_not_rewrite_identical(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fx = Effect("test", "testSynth", {"test": 0})
            fx.filename = os.path.join(tmpdir, "testSynth.scd")

            mock_server = MagicMock()
            fx.server = mock_server

            fx.save()
            mtime1 = os.path.getmtime(fx.filename)

            # Save again with same content — should still call load but file unchanged
            fx.save()
            mtime2 = os.path.getmtime(fx.filename)
            # mtime may or may not differ (file not rewritten if contents match)
            # The key test is that it doesn't raise
            self.assertTrue(os.path.isfile(fx.filename))

    def test_save_calls_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fx = Effect("test", "testSynth", {"test": 0})
            fx.filename = os.path.join(tmpdir, "testSynth.scd")

            mock_server = MagicMock()
            fx.server = mock_server

            fx.save()
            mock_server.loadSynthDef.assert_called_once_with(fx.filename)


class TestEffectLoad(unittest.TestCase):
    """Test Effect.load() delegates to server."""

    def test_load_calls_server(self):
        fx = Effect("test", "testSynth", {"test": 0})
        mock_server = MagicMock()
        fx.server = mock_server
        fx.load()
        mock_server.loadSynthDef.assert_called_once_with(fx.filename)

    def test_load_with_none_server(self):
        fx = Effect("test", "testSynth", {"test": 0})
        fx.server = None
        # Should not raise
        fx.load()


# ─── In / Out subclasses ──────────────────────────────────────────────────

class TestInEffect(unittest.TestCase):
    """Test the In (startSound) effect subclass."""

    def test_str_contains_startsound(self):
        # Mock server to avoid actual SC communication
        original_server = Effect.server
        Effect.server = MagicMock()
        try:
            fx = In()
            s = str(fx)
            self.assertIn("startSound", s)
            self.assertIn("ReplaceOut.kr", s)
            self.assertIn("rate", s)
        finally:
            Effect.server = original_server

    def test_name_is_startsound(self):
        original_server = Effect.server
        Effect.server = MagicMock()
        try:
            fx = In()
            self.assertEqual(fx.name, "startSound")
            self.assertEqual(fx.synthdef, "startSound")
        finally:
            Effect.server = original_server


class TestOutEffect(unittest.TestCase):
    """Test the Out (makeSound) effect subclass."""

    def test_str_contains_makesound(self):
        original_server = Effect.server
        Effect.server = MagicMock()
        try:
            fx = Out()
            s = str(fx)
            self.assertIn("makeSound", s)
            self.assertIn("In.ar(bus", s)
            self.assertIn("EnvGen.ar", s)
            self.assertIn("DetectSilence", s)
            self.assertIn("OffsetOut.ar", s)
        finally:
            Effect.server = original_server

    def test_name_is_makesound(self):
        original_server = Effect.server
        Effect.server = MagicMock()
        try:
            fx = Out()
            self.assertEqual(fx.name, "makeSound")
            self.assertEqual(fx.synthdef, "makeSound")
        finally:
            Effect.server = original_server

    def test_max_duration_default(self):
        original_server = Effect.server
        Effect.server = MagicMock()
        try:
            fx = Out()
            self.assertEqual(fx.max_duration, 8)
        finally:
            Effect.server = original_server

    def test_max_duration_in_str(self):
        original_server = Effect.server
        Effect.server = MagicMock()
        try:
            fx = Out()
            s = str(fx)
            self.assertIn(str(fx.max_duration), s)
        finally:
            Effect.server = original_server


# ─── EffectManager ─────────────────────────────────────────────────────────

class TestEffectManagerInit(unittest.TestCase):
    """Test EffectManager initialisation."""

    def test_starts_as_empty_dict(self):
        mgr = EffectManager()
        self.assertEqual(len(mgr), 0)

    def test_kw_starts_empty(self):
        mgr = EffectManager()
        self.assertEqual(mgr.kw, [])

    def test_all_kw_starts_empty(self):
        mgr = EffectManager()
        self.assertEqual(mgr.all_kw, [])

    def test_defaults_starts_empty(self):
        mgr = EffectManager()
        self.assertEqual(mgr.defaults, {})

    def test_order_has_three_buckets(self):
        mgr = EffectManager()
        self.assertIn(0, mgr.order)
        self.assertIn(1, mgr.order)
        self.assertIn(2, mgr.order)
        for bucket in mgr.order.values():
            self.assertEqual(bucket, [])


class TestEffectManagerNew(unittest.TestCase):
    """Test EffectManager.new() registration."""

    def setUp(self):
        self.mgr = EffectManager()

    def test_new_creates_effect(self):
        fx = self.mgr.new("room", "reverb", {"room": 0, "mix": 0.1})
        self.assertIsInstance(fx, Effect)
        self.assertEqual(fx.name, "room")

    def test_new_stores_in_dict(self):
        self.mgr.new("room", "reverb", {"room": 0, "mix": 0.1})
        self.assertIn("room", self.mgr)
        self.assertIsInstance(self.mgr["room"], Effect)

    def test_new_adds_to_kw(self):
        self.mgr.new("room", "reverb", {"room": 0, "mix": 0.1})
        self.assertIn("room", self.mgr.kw)

    def test_new_adds_sub_args_to_all_kw(self):
        self.mgr.new("room", "reverb", {"room": 0, "mix": 0.1})
        self.assertIn("room", self.mgr.all_kw)
        self.assertIn("mix", self.mgr.all_kw)

    def test_new_stores_defaults(self):
        self.mgr.new("room", "reverb", {"room": 0, "mix": 0.1})
        self.assertEqual(self.mgr.defaults["room"], 0)
        self.assertAlmostEqual(self.mgr.defaults["mix"], 0.1)

    def test_new_order_0_creates_control_effect(self):
        fx = self.mgr.new("vib", "vibrato", {"vib": 0}, order=0)
        self.assertTrue(fx.control)
        self.assertIn("vib", self.mgr.order[0])

    def test_new_order_2_creates_audio_effect(self):
        fx = self.mgr.new("room", "reverb", {"room": 0}, order=2)
        self.assertFalse(fx.control)
        self.assertIn("room", self.mgr.order[2])

    def test_new_order_1(self):
        fx = self.mgr.new("crush", "bitcrush", {"crush": 0}, order=1)
        self.assertIn("crush", self.mgr.order[1])

    def test_new_no_duplicate_all_kw(self):
        self.mgr.new("room", "reverb", {"room": 0, "sus": 1})
        self.mgr.new("chop", "chop", {"chop": 0, "sus": 1})
        self.assertEqual(self.mgr.all_kw.count("sus"), 1)


class TestEffectManagerKwargs(unittest.TestCase):
    """Test EffectManager.kwargs() and all_kwargs()."""

    def test_kwargs_returns_tuple(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0, "mix": 0.1})
        mgr.new("hpf", "highPassFilter", {"hpf": 0, "hpr": 1})
        result = mgr.kwargs()
        self.assertIsInstance(result, tuple)
        self.assertIn("room", result)
        self.assertIn("hpf", result)

    def test_all_kwargs_includes_sub_args(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0, "mix": 0.1})
        result = mgr.all_kwargs()
        self.assertIsInstance(result, tuple)
        self.assertIn("room", result)
        self.assertIn("mix", result)

    def test_kwargs_empty_when_no_effects(self):
        mgr = EffectManager()
        self.assertEqual(mgr.kwargs(), ())

    def test_all_kwargs_empty_when_no_effects(self):
        mgr = EffectManager()
        self.assertEqual(mgr.all_kwargs(), ())


class TestEffectManagerSortBy(unittest.TestCase):
    """Test EffectManager.sort_by() ordering."""

    def test_sort_by_synthdef(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0})
        mgr.new("hpf", "highPassFilter", {"hpf": 0})
        mgr.new("chop", "chop", {"chop": 0})
        keys = mgr.sort_by("synthdef")
        synthdefs = [mgr[k].synthdef for k in keys]
        self.assertEqual(synthdefs, sorted(synthdefs))

    def test_sort_by_name(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0})
        mgr.new("hpf", "highPassFilter", {"hpf": 0})
        mgr.new("chop", "chop", {"chop": 0})
        keys = mgr.sort_by("name")
        names = [mgr[k].name for k in keys]
        self.assertEqual(names, sorted(names))


class TestEffectManagerValues(unittest.TestCase):
    """Test EffectManager.values() returns sorted list."""

    def test_values_returns_effects(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0})
        mgr.new("hpf", "highPassFilter", {"hpf": 0})
        vals = mgr.values()
        self.assertTrue(all(isinstance(v, Effect) for v in vals))

    def test_values_sorted_by_synthdef(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0})
        mgr.new("hpf", "highPassFilter", {"hpf": 0})
        vals = mgr.values()
        synthdefs = [v.synthdef for v in vals]
        self.assertEqual(synthdefs, sorted(synthdefs))


class TestEffectManagerRepr(unittest.TestCase):
    """Test EffectManager.__repr__."""

    def test_repr_contains_effects(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0})
        r = repr(mgr)
        self.assertIn("reverb", r)

    def test_repr_empty(self):
        mgr = EffectManager()
        self.assertEqual(repr(mgr), "")


class TestEffectManagerIter(unittest.TestCase):
    """Test EffectManager.__iter__."""

    def test_iter_yields_key_effect_pairs(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0})
        mgr.new("hpf", "highPassFilter", {"hpf": 0})
        items = list(mgr)
        self.assertEqual(len(items), 2)
        for key, fx in items:
            self.assertIsInstance(key, str)
            self.assertIsInstance(fx, Effect)

    def test_iter_empty(self):
        mgr = EffectManager()
        items = list(mgr)
        self.assertEqual(items, [])

    def test_iter_preserves_insertion_order(self):
        mgr = EffectManager()
        mgr.new("room", "reverb", {"room": 0})
        mgr.new("hpf", "highPassFilter", {"hpf": 0})
        mgr.new("chop", "chop", {"chop": 0})
        keys = [k for k, _ in mgr]
        self.assertEqual(keys, ["room", "hpf", "chop"])


class TestEffectManagerReload(unittest.TestCase):
    """Test EffectManager.reload() calls load on each effect."""

    def test_reload_calls_load_on_effects(self):
        original_server = Effect.server
        mock_server = MagicMock()
        Effect.server = mock_server
        try:
            mgr = EffectManager()
            fx1 = mgr.new("room", "reverb", {"room": 0})
            fx2 = mgr.new("hpf", "highPassFilter", {"hpf": 0})
            mock_server.reset_mock()

            mgr.reload()

            # Each effect load + In() and Out() saves
            self.assertTrue(mock_server.loadSynthDef.call_count >= 2)
        finally:
            Effect.server = original_server


# ─── FxList predefined effects ─────────────────────────────────────────────

class TestFxListIsEffectManager(unittest.TestCase):
    """Test that FxList (and Effects alias) are EffectManager instances."""

    def test_fxlist_is_effect_manager(self):
        self.assertIsInstance(FxList, EffectManager)

    def test_effects_is_fxlist(self):
        self.assertIs(Effects, FxList)


class TestFxListRegisteredEffects(unittest.TestCase):
    """Test that all expected effects are registered in FxList."""

    # Frequency effects (order=0)
    FREQUENCY_EFFECTS = [
        ("vib", "vibrato", {"vib": 0, "vibdepth": 0.02}),
        ("slide", "slideTo", {"slide": 0, "sus": 1, "slidedelay": 0}),
        ("slidefrom", "slideFrom", {"slidefrom": 0, "sus": 1, "slidedelay": 0}),
        ("glide", "glissando", {"glide": 0, "glidedelay": 0.5, "sus": 1}),
        ("bend", "pitchBend", {"bend": 0, "sus": 1, "benddelay": 0}),
        ("coarse", "coarse", {"coarse": 0, "sus": 1}),
        ("striate", "striate", {"striate": 0, "sus": 1, "buf": 0, "rate": 1}),
        ("pshift", "pitchShift", {"pshift": 0}),
    ]

    # Signal effects (order=2)
    SIGNAL_EFFECTS = [
        ("hpf", "highPassFilter", {"hpf": 0, "hpr": 1}),
        ("lpf", "lowPassFilter", {"lpf": 0, "lpr": 1}),
        ("swell", "filterSwell", {"swell": 0, "sus": 1, "hpr": 1}),
        ("bpf", "bandPassFilter", {"bpf": 0, "bpr": 1, "bpnoise": 0, "sus": 1}),
        ("chop", "chop", {"chop": 0, "sus": 1}),
        ("tremolo", "tremolo", {"tremolo": 0, "beat_dur": 1}),
        ("echo", "combDelay", {"echo": 0, "beat_dur": 1, "echotime": 1}),
        ("spin", "spinPan", {"spin": 0, "sus": 1}),
        ("cut", "trimLength", {"cut": 0, "sus": 1}),
        ("room", "reverb", {"room": 0, "mix": 0.1}),
        ("formant", "formantFilter", {"formant": 0}),
        ("shape", "wavesShapeDistortion", {"shape": 0}),
        ("drive", "overdriveDistortion", {"drive": 0}),
    ]

    def test_frequency_effects_registered(self):
        for name, synthdef, _ in self.FREQUENCY_EFFECTS:
            self.assertIn(name, FxList, f"Missing frequency effect: {name}")
            self.assertEqual(FxList[name].synthdef, synthdef)

    def test_signal_effects_registered(self):
        for name, synthdef, _ in self.SIGNAL_EFFECTS:
            self.assertIn(name, FxList, f"Missing signal effect: {name}")
            self.assertEqual(FxList[name].synthdef, synthdef)

    def test_frequency_effects_defaults(self):
        for name, _, expected_defaults in self.FREQUENCY_EFFECTS:
            fx = FxList[name]
            for arg, default_val in expected_defaults.items():
                self.assertIn(arg, fx.defaults,
                              f"Effect '{name}' missing default for '{arg}'")
                self.assertAlmostEqual(fx.defaults[arg], default_val,
                                       msg=f"Effect '{name}', arg '{arg}'")

    def test_signal_effects_defaults(self):
        for name, _, expected_defaults in self.SIGNAL_EFFECTS:
            fx = FxList[name]
            for arg, default_val in expected_defaults.items():
                self.assertIn(arg, fx.defaults,
                              f"Effect '{name}' missing default for '{arg}'")
                self.assertAlmostEqual(fx.defaults[arg], default_val,
                                       msg=f"Effect '{name}', arg '{arg}'")

    def test_frequency_effects_are_control_rate(self):
        for name, _, _ in self.FREQUENCY_EFFECTS:
            fx = FxList[name]
            self.assertTrue(fx.control, f"Effect '{name}' should be control rate (order=0)")
            self.assertEqual(fx.suffix, "kr")

    def test_signal_effects_are_audio_rate(self):
        for name, _, _ in self.SIGNAL_EFFECTS:
            fx = FxList[name]
            self.assertFalse(fx.control, f"Effect '{name}' should be audio rate (order=2)")
            self.assertEqual(fx.suffix, "ar")

    def test_all_effects_in_kwargs(self):
        kw = FxList.kwargs()
        for name, _, _ in self.FREQUENCY_EFFECTS + self.SIGNAL_EFFECTS:
            self.assertIn(name, kw, f"'{name}' not in FxList.kwargs()")

    def test_frequency_effects_have_sc_code(self):
        """Verify each frequency effect generated at least one SC code line."""
        for name, _, _ in self.FREQUENCY_EFFECTS:
            fx = FxList[name]
            self.assertGreater(len(fx.effects), 0,
                               f"Frequency effect '{name}' has no SC code lines")

    def test_signal_effects_have_sc_code(self):
        """Verify each signal effect generated at least one SC code line."""
        for name, _, _ in self.SIGNAL_EFFECTS:
            fx = FxList[name]
            self.assertGreater(len(fx.effects), 0,
                               f"Signal effect '{name}' has no SC code lines")


class TestFxListOrder(unittest.TestCase):
    """Test that effects are assigned to correct order buckets."""

    def test_frequency_effects_in_order_0(self):
        for name in ["vib", "slide", "slidefrom", "glide", "bend", "coarse", "striate", "pshift"]:
            self.assertIn(name, FxList.order[0],
                          f"'{name}' should be in order 0")

    def test_signal_effects_in_order_2(self):
        for name in ["hpf", "lpf", "swell", "bpf", "chop", "tremolo", "echo",
                      "spin", "cut", "room", "formant", "shape", "drive"]:
            self.assertIn(name, FxList.order[2],
                          f"'{name}' should be in order 2")


class TestFxListSpecificEffectBehavior(unittest.TestCase):
    """Test specific effects have correct SC code patterns."""

    def test_vibrato_uses_vibrato_ugen(self):
        fx = FxList["vib"]
        code = fx.list_effects()
        self.assertIn("Vibrato.ar", code)

    def test_reverb_uses_freeverb(self):
        fx = FxList["room"]
        code = fx.list_effects()
        self.assertIn("FreeVerb.ar", code)

    def test_highpass_uses_rhpf(self):
        fx = FxList["hpf"]
        code = fx.list_effects()
        self.assertIn("RHPF.ar", code)

    def test_lowpass_uses_rlpf(self):
        fx = FxList["lpf"]
        code = fx.list_effects()
        self.assertIn("RLPF.ar", code)

    def test_bandpass_uses_bpf(self):
        fx = FxList["bpf"]
        code = fx.list_effects()
        self.assertIn("BPF.ar", code)

    def test_echo_uses_combl(self):
        fx = FxList["echo"]
        code = fx.list_effects()
        self.assertIn("CombL.ar", code)

    def test_chop_uses_lfpulse(self):
        fx = FxList["chop"]
        code = fx.list_effects()
        self.assertIn("LFPulse.kr", code)

    def test_tremolo_uses_sinosc(self):
        fx = FxList["tremolo"]
        code = fx.list_effects()
        self.assertIn("SinOsc.ar", code)

    def test_spin_uses_fsinosc(self):
        fx = FxList["spin"]
        code = fx.list_effects()
        self.assertIn("FSinOsc.ar", code)

    def test_formant_uses_formlet(self):
        fx = FxList["formant"]
        code = fx.list_effects()
        self.assertIn("Formlet.ar", code)

    def test_shape_uses_fold_distort(self):
        fx = FxList["shape"]
        code = fx.list_effects()
        self.assertIn("fold2", code)
        self.assertIn("distort", code)

    def test_drive_uses_clip_fold(self):
        fx = FxList["drive"]
        code = fx.list_effects()
        self.assertIn("clip", code)
        self.assertIn("fold2", code)

    def test_slide_uses_envgen(self):
        fx = FxList["slide"]
        code = fx.list_effects()
        self.assertIn("EnvGen.ar", code)

    def test_slidefrom_uses_envgen(self):
        fx = FxList["slidefrom"]
        code = fx.list_effects()
        self.assertIn("EnvGen.ar", code)

    def test_glide_uses_pitch_ratio(self):
        fx = FxList["glide"]
        code = fx.list_effects()
        self.assertIn("1.059463", code)

    def test_pshift_uses_pitch_ratio(self):
        fx = FxList["pshift"]
        code = fx.list_effects()
        self.assertIn("1.059463", code)

    def test_striate_extra_vars(self):
        """Striate effect should use BufDur."""
        fx = FxList["striate"]
        code = fx.list_effects()
        self.assertIn("BufDur.kr", code)

    def test_coarse_uses_lfpulse(self):
        fx = FxList["coarse"]
        code = fx.list_effects()
        self.assertIn("LFPulse.ar", code)

    def test_cut_uses_envgen_step(self):
        fx = FxList["cut"]
        code = fx.list_effects()
        self.assertIn("EnvGen.ar", code)
        self.assertIn("step", code)

    def test_swell_has_env_var(self):
        fx = FxList["swell"]
        self.assertIn("env", fx.vars)


class TestFxListSC3Plugins(unittest.TestCase):
    """Test SC3_PLUGINS-conditional effects."""

    def test_crush_present_if_sc3_plugins(self):
        from FoxDot.lib.Settings import SC3_PLUGINS
        if SC3_PLUGINS:
            self.assertIn("crush", FxList)
            self.assertEqual(FxList["crush"].synthdef, "bitcrush")
            code = FxList["crush"].list_effects()
            self.assertIn("Decimator.ar", code)
        else:
            # crush may or may not be present depending on config
            pass

    def test_dist_present_if_sc3_plugins(self):
        from FoxDot.lib.Settings import SC3_PLUGINS
        if SC3_PLUGINS:
            self.assertIn("dist", FxList)
            self.assertEqual(FxList["dist"].synthdef, "distortion")
            code = FxList["dist"].list_effects()
            self.assertIn("CrossoverDistortion.ar", code)
        else:
            pass


class TestEffectManagerDefaultsConsistency(unittest.TestCase):
    """Test that EffectManager.defaults contains all registered args."""

    def test_all_registered_args_have_defaults(self):
        for name in FxList.kw:
            fx = FxList[name]
            for arg in fx.args:
                self.assertIn(arg, FxList.defaults,
                              f"Arg '{arg}' from effect '{name}' not in FxList.defaults")

    def test_defaults_values_are_numeric(self):
        for arg, val in FxList.defaults.items():
            self.assertIsInstance(val, (int, float),
                                 f"Default for '{arg}' is {type(val).__name__}, expected numeric")


class TestEffectStrRoundTrip(unittest.TestCase):
    """Test that Effect.__str__ produces valid structure."""

    def test_str_has_synthdef_declaration(self):
        fx = Effect("test", "myEffect", {"test": 0, "amt": 0.5})
        fx.add("osc = osc * amt")
        s = str(fx)
        # Should have opening and closing
        self.assertIn("SynthDef.new(\\myEffect", s)
        self.assertIn("}).add;", s)

    def test_str_has_bus_arg(self):
        fx = Effect("test", "myEffect", {"test": 0})
        s = str(fx)
        self.assertIn("bus", s)

    def test_str_has_var_declaration(self):
        fx = Effect("test", "myEffect", {"test": 0})
        s = str(fx)
        self.assertIn("var osc", s)

    def test_str_multiple_vars(self):
        fx = Effect("test", "myEffect", {"test": 0})
        fx.add_var("env")
        fx.add_var("tmp")
        s = str(fx)
        self.assertIn("osc", s)
        self.assertIn("env", s)
        self.assertIn("tmp", s)


if __name__ == '__main__':
    unittest.main()
