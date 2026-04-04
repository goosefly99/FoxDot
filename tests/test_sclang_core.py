"""Tests for lib/SCLang/SCLang.py — cls, instance, format_args, UGens, helpers."""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from FoxDot.lib.SCLang.SCLang import (
    cls, instance, format_args,
    SinOsc, SinOscFB, Saw, LFSaw, VarSaw, LFTri, LFPar,
    PlayBuf, LFNoise0, LFNoise1, LFNoise2,
    Gendy1, Gendy2, Gendy3, Gendy4, Gendy5,
    Formant, Pulse, LFPulse, PMOsc, Crackle, LFCub,
    PinkNoise, Impulse, Blip, Klank, Resonz,
    K2A, Out, AudioIn, Lag, Vibrato, Line, XLine,
    FreeVerb, GVerb, Pan2, LPF, RLPF, BPF, HPF, RHPF,
    DelayC, DelayN, DelayL, CombN, CombL, CombC,
    Limiter, Ringz, Dust, Formlet, ClipNoise,
    BufRateScale, BufSampleRate, BufFrames, BufChannels, BufDur,
    BufGrain, Decimator, SmoothDecimator,
    CrossoverDistortion, Disintegrator, MdaPiano,
    stutter, dup,
)


# ── format_args ──────────────────────────────────────────────────────────

class TestFormatArgs(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(format_args(), "")

    def test_none_args_and_kwargs(self):
        self.assertEqual(format_args(None, None), "")

    def test_positional_only(self):
        self.assertEqual(format_args([1, 2, 3]), "1, 2, 3")

    def test_kwargs_only(self):
        result = format_args(kwargs={"freq": 440, "amp": 1})
        self.assertIn("freq: 440", result)
        self.assertIn("amp: 1", result)

    def test_mixed_args_and_kwargs(self):
        result = format_args([1], {"key": "val"})
        self.assertTrue(result.startswith("1, "))
        self.assertIn("key: val", result)

    def test_custom_delimiter(self):
        result = format_args(kwargs={"x": 10}, delim='=')
        self.assertEqual(result, "x=10")

    def test_args_with_instance_objects(self):
        a = instance("freq")
        result = format_args([a, 440])
        self.assertEqual(result, "freq, 440")

    def test_empty_args_list(self):
        self.assertEqual(format_args([], {}), "")

    def test_single_positional(self):
        self.assertEqual(format_args([42]), "42")

    def test_single_kwarg(self):
        result = format_args(kwargs={"out": 0})
        self.assertEqual(result, "out: 0")


# ── cls class ────────────────────────────────────────────────────────────

class TestCls(unittest.TestCase):

    def test_str(self):
        c = cls("SinOsc")
        self.assertEqual(str(c), "SinOsc")

    def test_repr(self):
        c = cls("SinOsc")
        self.assertEqual(repr(c), "SinOsc")

    def test_ar_no_args(self):
        c = cls("SinOsc")
        result = c.ar()
        self.assertIsInstance(result, instance)
        self.assertEqual(str(result), "SinOsc.ar()")

    def test_ar_with_positional_args(self):
        c = cls("SinOsc")
        result = c.ar(440, 0)
        self.assertEqual(str(result), "SinOsc.ar(440, 0)")

    def test_ar_with_kwargs(self):
        c = cls("SinOsc")
        result = c.ar(freq=440)
        self.assertEqual(str(result), "SinOsc.ar(freq: 440)")

    def test_ar_mixed(self):
        c = cls("SinOsc")
        result = c.ar(440, mul=0.5)
        self.assertEqual(str(result), "SinOsc.ar(440, mul: 0.5)")

    def test_kr_no_args(self):
        c = cls("LFNoise0")
        result = c.kr()
        self.assertEqual(str(result), "LFNoise0.kr()")

    def test_kr_with_args(self):
        c = cls("LFNoise0")
        result = c.kr(10)
        self.assertEqual(str(result), "LFNoise0.kr(10)")

    def test_ir_no_args(self):
        c = cls("Control")
        result = c.ir()
        self.assertEqual(str(result), "Control.ir()")

    def test_ir_with_args(self):
        c = cls("Control")
        result = c.ir(0)
        self.assertEqual(str(result), "Control.ir(0)")

    def test_call_no_args(self):
        c = cls("Env")
        result = c()
        self.assertIsInstance(result, instance)
        self.assertEqual(str(result), "Env()")

    def test_call_with_args(self):
        c = cls("Env")
        result = c(0, 1, 0)
        self.assertEqual(str(result), "Env(0, 1, 0)")

    def test_call_with_kwargs(self):
        c = cls("Env")
        result = c(times=[0.1, 0.5])
        self.assertIn("times: [0.1, 0.5]", str(result))

    def test_ref_keyword(self):
        c = cls("Klank", ref="`")
        result = c.ar(instance("freqs"))
        self.assertIn("`", str(result))
        self.assertEqual(str(result), "Klank.ar(`freqs)")

    def test_ref_empty(self):
        c = cls("SinOsc", ref="")
        result = c.ar(440)
        self.assertEqual(str(result), "SinOsc.ar(440)")

    def test_chained_ar_returns_instance(self):
        c = cls("SinOsc")
        result = c.ar(440)
        self.assertIsInstance(result, instance)

    def test_chained_kr_returns_instance(self):
        c = cls("LFNoise0")
        result = c.kr(10)
        self.assertIsInstance(result, instance)


# ── instance class ───────────────────────────────────────────────────────

class TestInstance(unittest.TestCase):

    def test_str(self):
        i = instance("freq")
        self.assertEqual(str(i), "freq")

    def test_repr(self):
        i = instance("amp")
        self.assertEqual(repr(i), "amp")

    def test_from_number(self):
        i = instance(440)
        self.assertEqual(str(i), "440")

    def test_add(self):
        a = instance("freq")
        b = instance("fmod")
        result = a + b
        self.assertEqual(str(result), "(freq + fmod)")

    def test_sub(self):
        a = instance("freq")
        b = instance("offset")
        result = a - b
        self.assertEqual(str(result), "(freq - offset)")

    def test_mul(self):
        a = instance("osc")
        b = instance("amp")
        result = a * b
        self.assertEqual(str(result), "(osc * amp)")

    def test_div(self):
        a = instance("freq")
        b = instance(2)
        result = a / b
        self.assertEqual(str(result), "(freq / 2)")

    def test_pow(self):
        a = instance("x")
        b = instance(2)
        result = a ** b
        self.assertEqual(str(result), "(x ** 2)")

    def test_xor_is_pow(self):
        a = instance("x")
        b = instance(3)
        result = a ^ b
        self.assertEqual(str(result), "(x ** 3)")

    def test_truediv(self):
        a = instance("a")
        b = instance("b")
        result = a.__truediv__(b)
        self.assertEqual(str(result), "(a / b)")

    def test_getitem(self):
        a = instance("buf")
        result = a[0]
        self.assertEqual(str(result), "(buf[0])")

    def test_radd(self):
        a = instance("freq")
        result = 100 + a
        self.assertEqual(str(result), "(100 + freq)")

    def test_rsub(self):
        a = instance("freq")
        result = 1000 - a
        self.assertEqual(str(result), "(1000 - freq)")

    def test_rmul(self):
        a = instance("amp")
        result = 2 * a
        self.assertEqual(str(result), "(2 * amp)")

    def test_rdiv(self):
        a = instance("rate")
        result = instance(1).__rdiv__(a)
        self.assertEqual(str(result), "(rate / 1)")

    def test_rpow(self):
        a = instance("x")
        result = a.__rpow__(2)
        self.assertEqual(str(result), "(2 ** x)")

    def test_rxor(self):
        a = instance("x")
        result = a.__rxor__(2)
        self.assertEqual(str(result), "(2 ** x)")

    def test_rtruediv(self):
        a = instance("x")
        result = a.__rtruediv__(10)
        self.assertEqual(str(result), "(10 / x)")

    def test_mod_with_percent(self):
        a = instance("signal %s filtered")
        result = a % "is"
        self.assertEqual(str(result), "signal is filtered")

    def test_mod_without_percent(self):
        a = instance("signal")
        result = a % "ignored"
        self.assertIs(result, a)

    def test_nested_arithmetic(self):
        freq = instance("freq")
        fmod = instance("fmod")
        result = (freq + fmod) * instance("2")
        self.assertEqual(str(result), "((freq + fmod) * 2)")

    def test_deep_nesting(self):
        a = instance("a")
        b = instance("b")
        c = instance("c")
        result = (a + b) * c - instance("1")
        self.assertEqual(str(result), "(((a + b) * c) - 1)")

    def test_string_method(self):
        i = instance("osc")
        self.assertEqual(i.string(), "osc{}")

    def test_custom_method(self):
        i = instance("osc")
        result = i.custom(".clip")
        self.assertIsInstance(result, instance)
        self.assertEqual(str(result), "osc.clip")

    def test_getattr_chaining(self):
        i = instance("osc")
        result = i.clip
        self.assertIsInstance(result, instance)
        self.assertEqual(str(result), "osc.clip")

    def test_call_on_instance(self):
        i = instance("SinOsc.ar")
        result = i(440, 0)
        self.assertIn("440", str(result))
        self.assertIn("0", str(result))

    def test_coerce(self):
        i = instance("x")
        result = i.__coerce__(42)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], instance)
        self.assertIsInstance(result[1], instance)

    def test_add_with_numeric(self):
        i = instance("freq")
        result = i + 100
        self.assertEqual(str(result), "(freq + 100)")

    def test_sub_with_numeric(self):
        i = instance("freq")
        result = i - 50
        self.assertEqual(str(result), "(freq - 50)")

    def test_mul_with_numeric(self):
        i = instance("amp")
        result = i * 0.5
        self.assertEqual(str(result), "(amp * 0.5)")


# ── instance defaults and shortarg ───────────────────────────────────────

class TestInstanceDefaults(unittest.TestCase):

    def setUp(self):
        self._orig_defaults = instance.defaults.copy()
        self._orig_shortarg = instance.shortarg.copy()

    def tearDown(self):
        instance.defaults = self._orig_defaults
        instance.shortarg = self._orig_shortarg

    def test_defaults_applied_on_call(self):
        instance.defaults = {"mul": 1}
        i = instance("SinOsc.ar")
        result = i()
        self.assertIn("mul: 1", str(result))

    def test_defaults_overridden_by_kwargs(self):
        instance.defaults = {"mul": 1}
        i = instance("SinOsc.ar")
        result = i(mul=0.5)
        self.assertIn("mul: 0.5", str(result))

    def test_empty_defaults(self):
        instance.defaults = {}
        instance.shortarg = {}
        i = instance("Out.ar")
        result = i(0, instance("osc"))
        self.assertEqual(str(result), "Out.ar(0, osc)")


# ── UGen module-level instances ──────────────────────────────────────────

class TestUGens(unittest.TestCase):

    def test_sinosc_is_cls(self):
        self.assertIsInstance(SinOsc, cls)
        self.assertEqual(str(SinOsc), "SinOsc")

    def test_sinosc_ar(self):
        result = SinOsc.ar(440)
        self.assertEqual(str(result), "SinOsc.ar(440)")

    def test_sinoscfb(self):
        self.assertEqual(str(SinOscFB), "SinOscFB")

    def test_saw(self):
        self.assertEqual(str(Saw), "Saw")
        result = Saw.ar(100)
        self.assertEqual(str(result), "Saw.ar(100)")

    def test_lfsaw(self):
        self.assertEqual(str(LFSaw), "LFSaw")

    def test_varsaw(self):
        self.assertEqual(str(VarSaw), "VarSaw")

    def test_lftri(self):
        self.assertEqual(str(LFTri), "LFTri")

    def test_lfpar(self):
        self.assertEqual(str(LFPar), "LFPar")

    def test_playbuf(self):
        self.assertEqual(str(PlayBuf), "PlayBuf")

    def test_lfnoise_family(self):
        self.assertEqual(str(LFNoise0), "LFNoise0")
        self.assertEqual(str(LFNoise1), "LFNoise1")
        self.assertEqual(str(LFNoise2), "LFNoise2")

    def test_gendy_family(self):
        for i, g in enumerate([Gendy1, Gendy2, Gendy3, Gendy4, Gendy5], start=1):
            self.assertEqual(str(g), f"Gendy{i}")

    def test_formant(self):
        self.assertEqual(str(Formant), "Formant")

    def test_pulse(self):
        self.assertEqual(str(Pulse), "Pulse")

    def test_lfpulse(self):
        self.assertEqual(str(LFPulse), "LFPulse")

    def test_pmosc(self):
        self.assertEqual(str(PMOsc), "PMOsc")

    def test_crackle(self):
        self.assertEqual(str(Crackle), "Crackle")

    def test_lfcub(self):
        self.assertEqual(str(LFCub), "LFCub")

    def test_pinknoise(self):
        self.assertEqual(str(PinkNoise), "PinkNoise")

    def test_impulse(self):
        self.assertEqual(str(Impulse), "Impulse")

    def test_blip(self):
        self.assertEqual(str(Blip), "Blip")

    def test_klank_has_ref(self):
        self.assertEqual(str(Klank), "Klank")
        result = Klank.ar(instance("spec"))
        self.assertIn("`", str(result))

    def test_resonz(self):
        self.assertEqual(str(Resonz), "Resonz")

    def test_filters(self):
        for name, obj in [("LPF", LPF), ("RLPF", RLPF), ("BPF", BPF),
                          ("HPF", HPF), ("RHPF", RHPF)]:
            self.assertEqual(str(obj), name)

    def test_delays(self):
        for name, obj in [("DelayC", DelayC), ("DelayN", DelayN), ("DelayL", DelayL)]:
            self.assertEqual(str(obj), name)

    def test_combs(self):
        for name, obj in [("CombN", CombN), ("CombL", CombL), ("CombC", CombC)]:
            self.assertEqual(str(obj), name)

    def test_effects_ugens(self):
        for name, obj in [("FreeVerb", FreeVerb), ("GVerb", GVerb),
                          ("Limiter", Limiter), ("Ringz", Ringz)]:
            self.assertEqual(str(obj), name)

    def test_pan2(self):
        self.assertEqual(str(Pan2), "Pan2")

    def test_out(self):
        self.assertEqual(str(Out), "Out")

    def test_audioin(self):
        self.assertEqual(str(AudioIn), "AudioIn")

    def test_misc_ugens(self):
        for name, obj in [("K2A", K2A), ("Lag", Lag), ("Vibrato", Vibrato),
                          ("Line", Line), ("XLine", XLine), ("Dust", Dust),
                          ("Formlet", Formlet), ("ClipNoise", ClipNoise)]:
            self.assertEqual(str(obj), name)

    def test_buf_info_ugens(self):
        for name, obj in [("BufRateScale", BufRateScale),
                          ("BufSampleRate", BufSampleRate),
                          ("BufFrames", BufFrames),
                          ("BufChannels", BufChannels),
                          ("BufDur", BufDur)]:
            self.assertEqual(str(obj), name)

    def test_sc3_plugins(self):
        for name, obj in [("BufGrain", BufGrain), ("Decimator", Decimator),
                          ("SmoothDecimator", SmoothDecimator),
                          ("CrossoverDistortion", CrossoverDistortion),
                          ("Disintegrator", Disintegrator),
                          ("MdaPiano", MdaPiano)]:
            self.assertEqual(str(obj), name)

    def test_ugen_ar_returns_instance(self):
        result = SinOsc.ar(440)
        self.assertIsInstance(result, instance)

    def test_ugen_kr_returns_instance(self):
        result = LFNoise0.kr(10)
        self.assertIsInstance(result, instance)

    def test_ugen_composition(self):
        """Test combining UGens like SC code: SinOsc.ar(440) * LFNoise0.kr(10)"""
        osc = SinOsc.ar(440)
        mod = LFNoise0.kr(10)
        result = osc * mod
        self.assertIn("SinOsc.ar(440)", str(result))
        self.assertIn("LFNoise0.kr(10)", str(result))
        self.assertIn("*", str(result))

    def test_ugen_pan2(self):
        osc = SinOsc.ar(440)
        result = Pan2.ar(osc, 0)
        self.assertIn("Pan2.ar", str(result))
        self.assertIn("SinOsc.ar(440)", str(result))

    def test_ugen_out(self):
        osc = SinOsc.ar(440)
        result = Out.ar(0, osc)
        self.assertIn("Out.ar", str(result))

    def test_ugen_filter_chain(self):
        """LPF.ar(SinOsc.ar(440), 1000)"""
        osc = SinOsc.ar(440)
        result = LPF.ar(osc, 1000)
        self.assertIn("LPF.ar", str(result))
        self.assertIn("SinOsc.ar(440)", str(result))
        self.assertIn("1000", str(result))

    def test_ugen_with_kwargs(self):
        result = SinOsc.ar(freq=440, mul=0.5)
        s = str(result)
        self.assertIn("SinOsc.ar", s)
        self.assertIn("freq: 440", s)
        self.assertIn("mul: 0.5", s)


# ── stutter and dup helpers ──────────────────────────────────────────────

class TestHelpers(unittest.TestCase):

    def test_stutter_basic(self):
        self.assertEqual(stutter([1, 2, 3], 2), [1, 1, 2, 2, 3, 3])

    def test_stutter_n1(self):
        self.assertEqual(stutter([1, 2], 1), [1, 2])

    def test_stutter_n3(self):
        self.assertEqual(stutter(["a", "b"], 3), ["a", "a", "a", "b", "b", "b"])

    def test_stutter_empty(self):
        self.assertEqual(stutter([], 5), [])

    def test_dup(self):
        self.assertEqual(dup(42), [42, 42])

    def test_dup_string(self):
        self.assertEqual(dup("x"), ["x", "x"])

    def test_dup_list(self):
        result = dup([1, 2])
        self.assertEqual(result, [[1, 2], [1, 2]])


# ── SynthDefProxy ────────────────────────────────────────────────────────

class TestSynthDefProxy(unittest.TestCase):

    def setUp(self):
        from FoxDot.lib.SCLang.SynthDef import SynthDefProxy
        self.SynthDefProxy = SynthDefProxy

    def test_str(self):
        p = self.SynthDefProxy("pluck", 0, {})
        self.assertEqual(str(p), "<SynthDef Proxy 'pluck'>")

    def test_add_sets_mod(self):
        p = self.SynthDefProxy("pluck", 0, {})
        result = p + 2
        self.assertEqual(result.mod, 2)
        self.assertIs(result, p)

    def test_coerce(self):
        p = self.SynthDefProxy("pluck", 0, {})
        self.assertIsNone(p.__coerce__(42))

    def test_method_chaining(self):
        p = self.SynthDefProxy("pluck", 0, {"dur": 1})
        result = p.slide(0.5).bend(1)
        self.assertIs(result, p)
        self.assertEqual(len(p.methods), 2)
        self.assertEqual(p.methods[0][0], "slide")
        self.assertEqual(p.methods[1][0], "bend")

    def test_kwargs_stored(self):
        p = self.SynthDefProxy("pluck", 3, {"amp": 0.5, "dur": 2})
        self.assertEqual(p.kwargs["amp"], 0.5)
        self.assertEqual(p.kwargs["dur"], 2)

    def test_degree_stored(self):
        p = self.SynthDefProxy("pluck", 7, {})
        self.assertEqual(p.degree, 7)


# ── SynthDict ────────────────────────────────────────────────────────────

class TestSynthDict(unittest.TestCase):

    def setUp(self):
        from FoxDot.lib.SCLang.SynthDef import SynthDict
        self.SynthDict = SynthDict

    def test_str(self):
        d = self.SynthDict(a=1, b=2)
        result = str(d)
        self.assertIn("a", result)
        self.assertIn("b", result)

    def test_repr(self):
        d = self.SynthDict(x=10)
        self.assertEqual(str(d), repr(d))

    def test_call(self):
        d = self.SynthDict(pluck="synth_obj")
        self.assertEqual(d("pluck"), "synth_obj")

    def test_is_dict(self):
        d = self.SynthDict()
        self.assertIsInstance(d, dict)


if __name__ == '__main__':
    unittest.main()
