"""Tests for lib/SCLang/Env.py — EnvGen, envelope classes, SC code generation."""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from FoxDot.lib.SCLang.Env import (
    EnvGen, env, mask, perc, linen, sine, ramp, reverse, adsr,
    amp, sus,
)
from FoxDot.lib.SCLang.SCLang import instance


# ── EnvGen base class ────────────────────────────────────────────────────

class TestEnvGen(unittest.TestCase):

    def test_default_value(self):
        e = EnvGen()
        self.assertEqual(e.value, "Env")

    def test_custom_value(self):
        e = EnvGen("Env.perc")
        self.assertEqual(e.value, "Env.perc")

    def test_default_done_action(self):
        e = EnvGen()
        self.assertEqual(e.doneAction, 2)


# ── adsr class ───────────────────────────────────────────────────────────

class TestAdsr(unittest.TestCase):

    def test_str_output(self):
        a = adsr()
        s = str(a)
        self.assertIn("EnvGen.ar", s)
        self.assertIn("Env(", s)
        self.assertIn("peak", s)
        self.assertIn("level", s)
        self.assertIn("atk", s)
        self.assertIn("decay", s)
        self.assertIn("rel", s)
        self.assertIn("sus", s)
        self.assertIn("doneAction: 0", s)

    def test_is_not_envgen(self):
        a = adsr()
        self.assertNotIsInstance(a, EnvGen)


# ── env class ────────────────────────────────────────────────────────────

class TestEnv(unittest.TestCase):

    def test_is_envgen_subclass(self):
        e = env()
        self.assertIsInstance(e, EnvGen)

    def test_str_output(self):
        e = env()
        s = str(e)
        self.assertIn("EnvGen.ar", s)
        self.assertIn("Env(", s)

    def test_default_done_action(self):
        e = env()
        self.assertEqual(e.doneAction, 0)

    def test_custom_done_action(self):
        e = env(doneAction=2)
        self.assertEqual(e.doneAction, 2)
        self.assertIn("doneAction: 2", str(e))

    def test_default_times_uses_sus(self):
        e = env()
        times = e.attr['times']
        self.assertEqual(len(times), 2)
        for t in times:
            self.assertIsInstance(t, instance)
            self.assertIn("sus", str(t))

    def test_default_levels_uses_amp(self):
        e = env()
        levels = e.attr['levels']
        self.assertEqual(len(levels), 3)
        self.assertEqual(levels[0], 0)
        self.assertEqual(levels[2], 0)
        self.assertIsInstance(levels[1], instance)
        self.assertIn("amp", str(levels[1]))

    def test_default_curve(self):
        e = env()
        self.assertEqual(e.attr['curve'], "'lin'")

    def test_custom_sus(self):
        e = env(sus=[0.1, 0.5])
        self.assertEqual(e.attr['times'], [0.1, 0.5])

    def test_custom_amp(self):
        e = env(amp=[0.5])
        levels = e.attr['levels']
        self.assertEqual(levels, [0, 0.5, 0])

    def test_custom_curve(self):
        e = env(curve="'exp'")
        self.assertEqual(e.attr['curve'], "'exp'")

    def test_str_contains_curve(self):
        e = env()
        s = str(e)
        self.assertIn("curve", s)

    def test_str_contains_times(self):
        e = env()
        s = str(e)
        self.assertIn("times", s)

    def test_str_contains_levels(self):
        e = env()
        s = str(e)
        self.assertIn("levels", s)


# ── mask class ───────────────────────────────────────────────────────────

class TestMask(unittest.TestCase):

    def test_is_envgen_subclass(self):
        m = mask()
        self.assertIsInstance(m, EnvGen)

    def test_str_output(self):
        m = mask()
        s = str(m)
        self.assertIn("EnvGen.ar", s)

    def test_default_times_length(self):
        m = mask()
        times = m.attr['times']
        self.assertEqual(len(times), 3)

    def test_default_times_values(self):
        m = mask()
        times = m.attr['times']
        self.assertEqual(times[0], 0.01)
        self.assertIsInstance(times[1], instance)
        self.assertIn("sus", str(times[1]))
        self.assertEqual(times[2], 0.01)

    def test_default_levels(self):
        m = mask()
        self.assertEqual(m.attr['levels'], [0, 1, 1, 0])

    def test_default_curve(self):
        m = mask()
        self.assertEqual(m.attr['curve'], "'lin'")

    def test_default_done_action(self):
        m = mask()
        self.assertEqual(m.doneAction, 0)

    def test_custom_sus(self):
        m = mask(sus=[0.1, 0.5, 0.1])
        self.assertEqual(m.attr['times'], [0.1, 0.5, 0.1])

    def test_custom_done_action(self):
        m = mask(doneAction=2)
        self.assertEqual(m.doneAction, 2)


# ── perc class ───────────────────────────────────────────────────────────

class TestPerc(unittest.TestCase):

    def test_is_envgen_subclass(self):
        p = perc()
        self.assertIsInstance(p, EnvGen)

    def test_value_is_env_perc(self):
        p = perc()
        self.assertEqual(p.value, "Env.perc")

    def test_str_output(self):
        p = perc()
        s = str(p)
        self.assertIn("EnvGen.ar", s)
        self.assertIn("Env.perc", s)

    def test_default_atk(self):
        p = perc()
        self.assertEqual(p.attr['attackTime'], 0.01)

    def test_default_release_uses_sus(self):
        p = perc()
        self.assertIsInstance(p.attr['releaseTime'], instance)
        self.assertIn("sus", str(p.attr['releaseTime']))

    def test_default_level_uses_amp(self):
        p = perc()
        self.assertIsInstance(p.attr['level'], instance)
        self.assertIn("amp", str(p.attr['level']))

    def test_default_curve(self):
        p = perc()
        self.assertEqual(p.attr['curve'], 0)

    def test_default_done_action(self):
        p = perc()
        self.assertEqual(p.doneAction, 0)

    def test_custom_atk(self):
        p = perc(atk=0.1)
        self.assertEqual(p.attr['attackTime'], 0.1)

    def test_custom_sus(self):
        p = perc(sus=2.0)
        self.assertEqual(p.attr['releaseTime'], 2.0)

    def test_custom_amp(self):
        p = perc(amp=0.5)
        self.assertEqual(p.attr['level'], 0.5)

    def test_custom_curve(self):
        p = perc(curve=-4)
        self.assertEqual(p.attr['curve'], -4)

    def test_custom_done_action(self):
        p = perc(doneAction=2)
        self.assertEqual(p.doneAction, 2)
        self.assertIn("doneAction: 2", str(p))

    def test_str_contains_attacktime(self):
        p = perc()
        s = str(p)
        self.assertIn("attackTime", s)

    def test_str_contains_releasetime(self):
        p = perc()
        s = str(p)
        self.assertIn("releaseTime", s)


# ── linen class ──────────────────────────────────────────────────────────

class TestLinen(unittest.TestCase):

    def test_is_perc_subclass(self):
        l = linen()
        self.assertIsInstance(l, perc)

    def test_is_envgen_subclass(self):
        l = linen()
        self.assertIsInstance(l, EnvGen)

    def test_value_is_env_linen(self):
        l = linen()
        self.assertEqual(l.value, "Env.linen")

    def test_str_output(self):
        l = linen()
        s = str(l)
        self.assertIn("EnvGen.ar", s)
        self.assertIn("Env.linen", s)

    def test_inherits_perc_defaults(self):
        l = linen()
        self.assertEqual(l.attr['attackTime'], 0.01)
        self.assertIn("sus", str(l.attr['releaseTime']))

    def test_custom_atk(self):
        l = linen(atk=0.5)
        self.assertEqual(l.attr['attackTime'], 0.5)


# ── sine class ───────────────────────────────────────────────────────────

class TestSine(unittest.TestCase):

    def test_is_envgen_subclass(self):
        s = sine()
        self.assertIsInstance(s, EnvGen)

    def test_value_is_env_sine(self):
        s = sine()
        self.assertEqual(s.value, "Env.sine")

    def test_str_output(self):
        s = sine()
        out = str(s)
        self.assertIn("EnvGen.ar", out)
        self.assertIn("Env.sine", out)

    def test_default_dur_uses_sus(self):
        s = sine()
        self.assertIsInstance(s.attr['dur'], instance)
        self.assertEqual(str(s.attr['dur']), "sus")

    def test_default_level_uses_amp(self):
        s = sine()
        self.assertIsInstance(s.attr['level'], instance)
        self.assertEqual(str(s.attr['level']), "amp")

    def test_default_done_action(self):
        s = sine()
        self.assertEqual(s.doneAction, 0)

    def test_custom_dur(self):
        s = sine(dur=2.0)
        self.assertEqual(s.attr['dur'], 2.0)

    def test_custom_amp(self):
        s = sine(amp=0.3)
        self.assertEqual(s.attr['level'], 0.3)

    def test_custom_done_action(self):
        s = sine(doneAction=2)
        self.assertEqual(s.doneAction, 2)


# ── ramp class ───────────────────────────────────────────────────────────

class TestRamp(unittest.TestCase):

    def test_is_envgen_subclass(self):
        r = ramp()
        self.assertIsInstance(r, EnvGen)

    def test_str_output(self):
        r = ramp()
        s = str(r)
        self.assertIn("EnvGen.ar", s)

    def test_default_times_uses_sus(self):
        r = ramp()
        times = r.attr['times']
        self.assertEqual(len(times), 1)
        self.assertIsInstance(times[0], instance)
        self.assertIn("sus", str(times[0]))

    def test_default_levels_use_amp(self):
        r = ramp()
        levels = r.attr['levels']
        self.assertEqual(len(levels), 2)
        for l in levels:
            self.assertIsInstance(l, instance)

    def test_default_curve(self):
        r = ramp()
        self.assertEqual(r.attr['curve'], "'step'")

    def test_default_done_action(self):
        r = ramp()
        self.assertEqual(r.doneAction, 0)

    def test_custom_sus(self):
        r = ramp(sus=[0.5, 0.5])
        self.assertEqual(r.attr['times'], [0.5, 0.5])

    def test_custom_amp(self):
        r = ramp(amp=[0.5, 1.0])
        levels = r.attr['levels']
        self.assertEqual(len(levels), 2)

    def test_custom_curve(self):
        r = ramp(curve="'lin'")
        self.assertEqual(r.attr['curve'], "'lin'")


# ── reverse class ────────────────────────────────────────────────────────

class TestReverse(unittest.TestCase):

    def test_is_envgen_subclass(self):
        r = reverse()
        self.assertIsInstance(r, EnvGen)

    def test_str_output(self):
        r = reverse()
        s = str(r)
        self.assertIn("EnvGen.ar", s)

    def test_default_times(self):
        r = reverse()
        times = r.attr['times']
        self.assertEqual(len(times), 2)
        self.assertIsInstance(times[0], instance)
        self.assertIn("sus", str(times[0]))
        self.assertEqual(times[1], 0.001)

    def test_default_levels(self):
        r = reverse()
        levels = r.attr['levels']
        self.assertEqual(len(levels), 3)
        self.assertEqual(levels[0], 0.0001)
        self.assertIsInstance(levels[1], instance)
        self.assertIn("amp", str(levels[1]))
        self.assertEqual(levels[2], 0)

    def test_default_curve(self):
        r = reverse()
        self.assertEqual(r.attr['curve'], "'exp'")

    def test_default_done_action(self):
        r = reverse()
        self.assertEqual(r.doneAction, 0)

    def test_custom_sus(self):
        r = reverse(sus=2.0)
        self.assertEqual(r.attr['times'][0], 2.0)

    def test_custom_amp(self):
        r = reverse(amp=[0.5])
        self.assertEqual(r.attr['levels'], [0.0001, 0.5, 0])

    def test_custom_curve(self):
        r = reverse(curve="'lin'")
        self.assertEqual(r.attr['curve'], "'lin'")

    def test_custom_done_action(self):
        r = reverse(doneAction=2)
        self.assertEqual(r.doneAction, 2)


# ── Module-level instances ───────────────────────────────────────────────

class TestModuleLevelInstances(unittest.TestCase):

    def test_amp_is_instance(self):
        self.assertIsInstance(amp, instance)
        self.assertEqual(str(amp), "amp")

    def test_sus_is_instance(self):
        self.assertIsInstance(sus, instance)
        self.assertEqual(str(sus), "sus")


# ── SC code string validity ─────────────────────────────────────────────

class TestSCCodeValidity(unittest.TestCase):
    """Verify generated SC code has valid structure (balanced parens etc.)."""

    def _check_balanced(self, s):
        count = 0
        for ch in s:
            if ch == '(':
                count += 1
            elif ch == ')':
                count -= 1
            if count < 0:
                return False
        return count == 0

    def test_env_balanced_parens(self):
        e = env()
        self.assertTrue(self._check_balanced(str(e)))

    def test_mask_balanced_parens(self):
        m = mask()
        self.assertTrue(self._check_balanced(str(m)))

    def test_perc_balanced_parens(self):
        p = perc()
        self.assertTrue(self._check_balanced(str(p)))

    def test_linen_balanced_parens(self):
        l = linen()
        self.assertTrue(self._check_balanced(str(l)))

    def test_sine_balanced_parens(self):
        s = sine()
        self.assertTrue(self._check_balanced(str(s)))

    def test_ramp_balanced_parens(self):
        r = ramp()
        self.assertTrue(self._check_balanced(str(r)))

    def test_reverse_balanced_parens(self):
        r = reverse()
        self.assertTrue(self._check_balanced(str(r)))

    def test_adsr_balanced_parens(self):
        a = adsr()
        self.assertTrue(self._check_balanced(str(a)))

    def test_all_envs_contain_envgen_ar(self):
        """Every envelope class should produce code with EnvGen.ar"""
        for klass in [env, mask, perc, linen, sine, ramp, reverse, adsr]:
            s = str(klass())
            self.assertIn("EnvGen.ar", s,
                          f"{klass.__name__} output missing 'EnvGen.ar'")

    def test_all_envs_contain_doneaction(self):
        """Every envelope should specify doneAction"""
        for klass in [env, mask, perc, linen, sine, ramp, reverse, adsr]:
            s = str(klass())
            self.assertIn("doneAction", s,
                          f"{klass.__name__} output missing 'doneAction'")


# ── Envelope interaction with instance arithmetic ────────────────────────

class TestEnvWithInstance(unittest.TestCase):

    def test_env_multiplied_by_osc(self):
        """Simulates `osc = osc * env` pattern used in SynthDef.add()"""
        osc = instance("Mix(osc)")
        e = env()
        result = osc * e
        self.assertIsInstance(result, instance)
        s = str(result)
        self.assertIn("Mix(osc)", s)
        self.assertIn("EnvGen.ar", s)

    def test_perc_multiplied_by_osc(self):
        osc = instance("SinOsc.ar(freq)")
        p = perc()
        result = osc * p
        s = str(result)
        self.assertIn("SinOsc.ar(freq)", s)
        self.assertIn("Env.perc", s)

    def test_sine_multiplied_by_osc(self):
        osc = instance("Saw.ar(freq)")
        s_env = sine()
        result = osc * s_env
        s = str(result)
        self.assertIn("Saw.ar(freq)", s)
        self.assertIn("Env.sine", s)


if __name__ == '__main__':
    unittest.main()
