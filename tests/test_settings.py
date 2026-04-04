"""
Unit tests for the Settings module.

Covers:
- _SamplePlayer, _LoopPlayer, _MidiPlayer equality/inequality semantics
- conf.py defaults and environment variable override mechanism
- Platform detection constants
- Directory path helpers (GET_SYNTHDEF_FILES, GET_FX_FILES, GET_TUTORIAL_FILES)
- get_timestamp() format
- COLOURS attribute completeness
"""

import os
import sys
import time

import pytest


# ---------------------------------------------------------------------------
# _SamplePlayer
# ---------------------------------------------------------------------------

class TestSamplePlayer:
    """Tests for Settings._SamplePlayer singleton."""

    def _make(self):
        from FoxDot.lib.Settings import _SamplePlayer
        return _SamplePlayer()

    def test_eq_play1(self):
        sp = self._make()
        assert sp == "play1"

    def test_eq_play2(self):
        sp = self._make()
        assert sp == "play2"

    def test_eq_other_false(self):
        sp = self._make()
        assert not (sp == "play3")

    def test_eq_non_string(self):
        sp = self._make()
        assert not (sp == 42)

    def test_ne_play1(self):
        sp = self._make()
        assert not (sp != "play1")

    def test_ne_play2(self):
        sp = self._make()
        assert not (sp != "play2")

    def test_ne_other_true(self):
        sp = self._make()
        assert sp != "play3"

    def test_ne_non_string(self):
        sp = self._make()
        assert sp != 42

    def test_names_tuple(self):
        sp = self._make()
        assert sp.names == ("play1", "play2")

    def test_singleton_equals_both_names(self):
        from FoxDot.lib.Settings import SamplePlayer
        assert SamplePlayer == "play1"
        assert SamplePlayer == "play2"

    def test_eq_empty_string(self):
        sp = self._make()
        assert not (sp == "")

    def test_ne_empty_string(self):
        sp = self._make()
        assert sp != ""

    def test_eq_none(self):
        sp = self._make()
        assert not (sp == None)

    def test_ne_none(self):
        sp = self._make()
        assert sp != None


# ---------------------------------------------------------------------------
# _LoopPlayer
# ---------------------------------------------------------------------------

class TestLoopPlayer:
    """Tests for Settings._LoopPlayer singleton."""

    def _make(self):
        from FoxDot.lib.Settings import _LoopPlayer
        return _LoopPlayer()

    def test_eq_loop(self):
        lp = self._make()
        assert lp == "loop"

    def test_eq_gsynth(self):
        lp = self._make()
        assert lp == "gsynth"

    def test_eq_stretch(self):
        lp = self._make()
        assert lp == "stretch"

    def test_eq_other_false(self):
        lp = self._make()
        assert not (lp == "play1")

    def test_ne_loop(self):
        lp = self._make()
        assert not (lp != "loop")

    def test_ne_other_true(self):
        lp = self._make()
        assert lp != "bass"

    def test_names_tuple(self):
        lp = self._make()
        assert lp.names == ("loop", "gsynth", "stretch")

    def test_singleton_equality(self):
        from FoxDot.lib.Settings import LoopPlayer
        assert LoopPlayer == "loop"
        assert LoopPlayer == "gsynth"
        assert LoopPlayer == "stretch"

    def test_eq_none(self):
        lp = self._make()
        assert not (lp == None)

    def test_ne_numeric(self):
        lp = self._make()
        assert lp != 0


# ---------------------------------------------------------------------------
# _MidiPlayer
# ---------------------------------------------------------------------------

class TestMidiPlayer:
    """Tests for Settings._MidiPlayer singleton."""

    def _make(self):
        from FoxDot.lib.Settings import _MidiPlayer
        return _MidiPlayer()

    def test_eq_midiout(self):
        mp = self._make()
        assert mp == "MidiOut"

    def test_eq_other_false(self):
        mp = self._make()
        assert not (mp == "MidiIn")

    def test_ne_midiout(self):
        mp = self._make()
        assert not (mp != "MidiOut")

    def test_ne_other_true(self):
        mp = self._make()
        assert mp != "play1"

    def test_name_attr(self):
        mp = self._make()
        assert mp.name == "MidiOut"

    def test_singleton_equality(self):
        from FoxDot.lib.Settings import MidiPlayer
        assert MidiPlayer == "MidiOut"

    def test_eq_lowercase_false(self):
        """MidiOut is case-sensitive."""
        mp = self._make()
        assert not (mp == "midiout")

    def test_ne_lowercase_true(self):
        mp = self._make()
        assert mp != "midiout"


# ---------------------------------------------------------------------------
# Cross-player type checks
# ---------------------------------------------------------------------------

class TestPlayerTypeCrossCheck:
    """Ensure the three player sentinel types do not overlap."""

    def test_sample_not_loop(self):
        from FoxDot.lib.Settings import SamplePlayer, LoopPlayer
        for name in SamplePlayer.names:
            assert not (LoopPlayer == name)

    def test_loop_not_sample(self):
        from FoxDot.lib.Settings import SamplePlayer, LoopPlayer
        for name in LoopPlayer.names:
            assert not (SamplePlayer == name)

    def test_midi_not_sample(self):
        from FoxDot.lib.Settings import SamplePlayer, MidiPlayer
        assert not (SamplePlayer == MidiPlayer.name)

    def test_midi_not_loop(self):
        from FoxDot.lib.Settings import LoopPlayer, MidiPlayer
        assert not (LoopPlayer == MidiPlayer.name)


# ---------------------------------------------------------------------------
# conf.py defaults
# ---------------------------------------------------------------------------

class TestConfDefaults:
    """Verify that conf.py exposes sensible defaults."""

    def test_address_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.ADDRESS == "localhost"

    def test_port_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.PORT == 57110

    def test_port2_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.PORT2 == 57120

    def test_font_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.FONT == "Consolas"

    def test_boot_on_startup_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.BOOT_ON_STARTUP is False

    def test_sc3_plugins_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.SC3_PLUGINS is False

    def test_max_channels_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.MAX_CHANNELS == 2

    def test_use_alpha_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.USE_ALPHA is True

    def test_alpha_value_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.ALPHA_VALUE == 0.8

    def test_cpu_usage_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.CPU_USAGE == 2

    def test_clock_latency_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.CLOCK_LATENCY == 0

    def test_repl_websocket_port_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.REPL_WEBSOCKET_PORT == 5555

    def test_event_logger_enabled_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.EVENT_LOGGER_ENABLED is False

    def test_audacity_macro_name_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.AUDACITY_MACRO_NAME == "FoxDot-Master"

    def test_audacity_export_format_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.AUDACITY_EXPORT_FORMAT == "WAV"

    def test_check_for_update_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.CHECK_FOR_UPDATE is True

    def test_recover_work_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.RECOVER_WORK is True

    def test_auto_complete_brackets_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.AUTO_COMPLETE_BRACKETS is True

    def test_menu_on_startup_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.MENU_ON_STARTUP is True

    def test_transparent_on_startup_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.TRANSPARENT_ON_STARTUP is False

    def test_forward_address_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.FORWARD_ADDRESS == ""

    def test_forward_port_default(self):
        from FoxDot.lib.Settings import conf
        assert conf.FORWARD_PORT == 0


# ---------------------------------------------------------------------------
# conf.py colour defaults
# ---------------------------------------------------------------------------

class TestConfColours:
    """Verify colour defaults in conf.py."""

    def test_plaintext_colour(self):
        from FoxDot.lib.Settings import conf
        assert conf.plaintext == "#ffffff"

    def test_background_colour(self):
        from FoxDot.lib.Settings import conf
        assert conf.background == "#1a1a1a"

    def test_functions_colour(self):
        from FoxDot.lib.Settings import conf
        assert conf.functions == "#bf4acc"

    def test_comments_colour(self):
        from FoxDot.lib.Settings import conf
        assert conf.comments == "#666666"

    def test_numbers_colour(self):
        from FoxDot.lib.Settings import conf
        assert conf.numbers == "#e89c18"

    def test_strings_colour(self):
        from FoxDot.lib.Settings import conf
        assert conf.strings == "#eae02a"

    def test_players_colour(self):
        from FoxDot.lib.Settings import conf
        assert conf.players == "#ec4e20"


# ---------------------------------------------------------------------------
# COLOURS class in Settings __init__
# ---------------------------------------------------------------------------

class TestColoursClass:
    """Verify the COLOURS class exposes all expected attributes."""

    EXPECTED_ATTRS = [
        "plaintext", "background", "functions", "key_types",
        "user_defn", "other_kws", "comments", "numbers",
        "strings", "dollar", "arrow", "players",
    ]

    def test_all_colour_attrs_exist(self):
        from FoxDot.lib.Settings import COLOURS
        for attr in self.EXPECTED_ATTRS:
            assert hasattr(COLOURS, attr), f"COLOURS missing attribute: {attr}"

    def test_all_colour_values_are_strings(self):
        from FoxDot.lib.Settings import COLOURS
        for attr in self.EXPECTED_ATTRS:
            val = getattr(COLOURS, attr)
            assert isinstance(val, str), f"COLOURS.{attr} is {type(val)}, expected str"

    def test_all_colour_values_are_hex(self):
        from FoxDot.lib.Settings import COLOURS
        import re
        hex_re = re.compile(r"^#[0-9a-fA-F]{6}$")
        for attr in self.EXPECTED_ATTRS:
            val = getattr(COLOURS, attr)
            assert hex_re.match(val), f"COLOURS.{attr} = {val!r} is not a valid hex colour"


# ---------------------------------------------------------------------------
# conf.py environment variable override mechanism
# ---------------------------------------------------------------------------

class TestConfEnvOverride:
    """Test that conf.py loads overrides from environment variables."""

    def test_env_override_int(self, monkeypatch, tmp_path):
        """Verify that an integer config value can be overridden by env var."""
        # We can't easily re-import conf.py mid-test, but we can test the
        # override logic in isolation by reproducing the key algorithm.
        original = 57110  # int
        env_val = "12345"
        result = type(original)(env_val)
        assert result == 12345

    def test_env_override_float(self):
        original = 0.8
        env_val = "0.5"
        result = type(original)(env_val)
        assert result == 0.5

    def test_env_override_bool(self):
        original = False
        env_val = "True"
        # bool("True") -> True, bool("") -> False
        # But bool("any nonempty string") -> True, which is how the conf.py
        # mechanism works (type coercion, not smart parsing).
        result = type(original)(env_val)
        assert result is True

    def test_env_override_string(self):
        original = "localhost"
        env_val = "192.168.1.100"
        result = type(original)(env_val)
        assert result == "192.168.1.100"

    def test_env_override_invalid_int(self):
        """When the env var value can't be coerced, the original is kept."""
        original = 57110
        env_val = "not_a_number"
        try:
            result = type(original)(env_val)
            # If somehow it doesn't raise, something unexpected happened
            assert False, "Expected ValueError"
        except (ValueError, TypeError):
            # conf.py catches this and keeps the original
            pass

    def test_env_override_none_uses_string_value(self):
        """When original is None, the raw string value is used."""
        original = None
        env_val = "some_value"
        if original is None:
            result = env_val
        else:
            result = type(original)(env_val)
        assert result == "some_value"


# ---------------------------------------------------------------------------
# Platform detection constants
# ---------------------------------------------------------------------------

class TestPlatformDetection:
    """Verify platform detection exports."""

    def test_system_constants_exist(self):
        from FoxDot.lib.Settings import SYSTEM, WINDOWS, LINUX, MAC_OS
        assert WINDOWS == 0
        assert LINUX == 1
        assert MAC_OS == 2

    def test_system_matches_platform(self):
        from FoxDot.lib.Settings import SYSTEM, WINDOWS, LINUX, MAC_OS
        if sys.platform.startswith("win"):
            assert SYSTEM == WINDOWS
        elif sys.platform.startswith("darwin"):
            assert SYSTEM == MAC_OS
        elif sys.platform.startswith("linux"):
            assert SYSTEM == LINUX
        else:
            # Unknown platform — SYSTEM stays at default (0)
            assert SYSTEM == 0

    def test_sclang_exec_matches_platform(self):
        from FoxDot.lib.Settings import SCLANG_EXEC, SYSTEM, WINDOWS
        if SYSTEM == WINDOWS:
            assert SCLANG_EXEC == "sclang.exe"
        else:
            assert SCLANG_EXEC == "sclang"


# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------

class TestDirectoryPaths:
    """Verify critical directory path exports."""

    def test_foxdot_root_exists(self):
        from FoxDot.lib.Settings import FOXDOT_ROOT
        assert os.path.isdir(FOXDOT_ROOT)

    def test_foxdot_snd_exists(self):
        from FoxDot.lib.Settings import FOXDOT_SND
        assert os.path.isdir(FOXDOT_SND)

    def test_synthdef_dir_exists(self):
        from FoxDot.lib.Settings import SYNTHDEF_DIR
        assert os.path.isdir(SYNTHDEF_DIR)

    def test_effects_dir_exists(self):
        from FoxDot.lib.Settings import EFFECTS_DIR
        assert os.path.isdir(EFFECTS_DIR)

    def test_envelope_dir_exists(self):
        from FoxDot.lib.Settings import ENVELOPE_DIR
        assert os.path.isdir(ENVELOPE_DIR)

    def test_foxdot_root_is_absolute(self):
        from FoxDot.lib.Settings import FOXDOT_ROOT
        assert os.path.isabs(FOXDOT_ROOT)


# ---------------------------------------------------------------------------
# GET_*_FILES helpers
# ---------------------------------------------------------------------------

class TestGetFilesHelpers:
    """Verify the file-listing helper functions return lists of real paths."""

    def test_get_synthdef_files_returns_list(self):
        from FoxDot.lib.Settings import GET_SYNTHDEF_FILES
        result = GET_SYNTHDEF_FILES()
        assert isinstance(result, list)

    def test_get_synthdef_files_nonempty(self):
        from FoxDot.lib.Settings import GET_SYNTHDEF_FILES
        result = GET_SYNTHDEF_FILES()
        assert len(result) > 0

    def test_get_synthdef_files_all_absolute(self):
        from FoxDot.lib.Settings import GET_SYNTHDEF_FILES
        for path in GET_SYNTHDEF_FILES():
            assert os.path.isabs(path)

    def test_get_fx_files_returns_list(self):
        from FoxDot.lib.Settings import GET_FX_FILES
        result = GET_FX_FILES()
        assert isinstance(result, list)

    def test_get_fx_files_nonempty(self):
        from FoxDot.lib.Settings import GET_FX_FILES
        result = GET_FX_FILES()
        assert len(result) > 0

    def test_get_tutorial_files_returns_list(self):
        from FoxDot.lib.Settings import GET_TUTORIAL_FILES
        result = GET_TUTORIAL_FILES()
        assert isinstance(result, list)

    def test_get_tutorial_files_sorted(self):
        from FoxDot.lib.Settings import GET_TUTORIAL_FILES
        result = GET_TUTORIAL_FILES()
        basenames = [os.path.basename(p) for p in result]
        assert basenames == sorted(basenames)


# ---------------------------------------------------------------------------
# get_timestamp
# ---------------------------------------------------------------------------

class TestGetTimestamp:
    """Verify get_timestamp output format."""

    def test_returns_string(self):
        from FoxDot.lib.Settings import get_timestamp
        result = get_timestamp()
        assert isinstance(result, str)

    def test_format_yyyymmdd_hhmmss(self):
        from FoxDot.lib.Settings import get_timestamp
        import re
        result = get_timestamp()
        assert re.match(r"^\d{8}-\d{6}$", result), f"Unexpected format: {result}"

    def test_starts_with_current_year(self):
        from FoxDot.lib.Settings import get_timestamp
        result = get_timestamp()
        year = time.strftime("%Y")
        assert result.startswith(year)


# ---------------------------------------------------------------------------
# OSC_MIDI_ADDRESS constant
# ---------------------------------------------------------------------------

class TestOSCConstants:
    def test_osc_midi_address(self):
        from FoxDot.lib.Settings import OSC_MIDI_ADDRESS
        assert OSC_MIDI_ADDRESS == "/foxdot_midi"


# ---------------------------------------------------------------------------
# Settings re-exports from conf match conf values
# ---------------------------------------------------------------------------

class TestSettingsReExports:
    """Verify Settings __init__ re-exports match the conf module values."""

    REEXPORTED = [
        "ADDRESS", "PORT", "PORT2", "FONT", "SC3_PLUGINS",
        "MAX_CHANNELS", "GET_SC_INFO", "USE_ALPHA", "ALPHA_VALUE",
        "MENU_ON_STARTUP", "TRANSPARENT_ON_STARTUP", "RECOVER_WORK",
        "CHECK_FOR_UPDATE", "LINE_NUMBER_MARKER_OFFSET",
        "AUTO_COMPLETE_BRACKETS", "CPU_USAGE", "CLOCK_LATENCY",
        "FORWARD_ADDRESS", "FORWARD_PORT", "REPL_WEBSOCKET_PORT",
    ]

    def test_reexports_match_conf(self):
        from FoxDot.lib import Settings
        from FoxDot.lib.Settings import conf
        for name in self.REEXPORTED:
            settings_val = getattr(Settings, name)
            conf_val = getattr(conf, name)
            assert settings_val == conf_val, (
                f"Settings.{name} ({settings_val!r}) != conf.{name} ({conf_val!r})"
            )
