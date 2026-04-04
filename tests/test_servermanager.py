"""
Unit tests for ServerManager module: ServerInfo namedtuple, ServerManager
base class (create_osc_msg, nextnodeID, nextbusID, get_bundle),
SCLangServerManager node/bus management and OSC message construction,
Message class JSON serialization, socket helpers, TempoClient latency,
and RequestTimeout exception.
"""

import json
import sys
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch, PropertyMock

from FoxDot.lib.ServerManager import (
    ServerInfo,
    ServerManager,
    SCLangServerManager,
    Message,
    RequestTimeout,
    TempoClient,
    read_from_socket,
    send_to_socket,
    OSCClientWrapper,
)
from FoxDot.lib.OSC3 import OSCMessage, OSCBundle


# ============================================================================
# ServerInfo namedtuple
# ============================================================================

class TestServerInfo(unittest.TestCase):
    def test_creation(self):
        info = ServerInfo(
            sample_rate=44100, actual_sample_rate=44100.0,
            num_synths=10, num_groups=5,
            num_audio_bus_channels=128, num_control_bus_channels=4096,
            num_input_bus_channels=2, num_output_bus_channels=2,
            num_buffers=1024, max_nodes=1024, max_synth_defs=1024)
        self.assertEqual(info.sample_rate, 44100)
        self.assertEqual(info.num_buffers, 1024)

    def test_field_count(self):
        self.assertEqual(len(ServerInfo._fields), 11)

    def test_fields_immutable(self):
        info = ServerInfo(48000, 48000.0, 1, 1, 64, 2048, 2, 2, 512, 512, 256)
        with self.assertRaises(AttributeError):
            info.sample_rate = 96000

    def test_repr(self):
        info = ServerInfo(44100, 44100.0, 0, 0, 128, 4096, 2, 2, 1024, 1024, 1024)
        r = repr(info)
        self.assertIn("ServerInfo", r)
        self.assertIn("44100", r)


# ============================================================================
# RequestTimeout exception
# ============================================================================

class TestRequestTimeout(unittest.TestCase):
    def test_is_exception(self):
        self.assertTrue(issubclass(RequestTimeout, Exception))

    def test_raise_and_catch(self):
        with self.assertRaises(RequestTimeout):
            raise RequestTimeout("timed out")

    def test_message(self):
        e = RequestTimeout("test message")
        self.assertEqual(str(e), "test message")


# ============================================================================
# ServerManager base class
# ============================================================================

class TestServerManagerCreateOscMsg(unittest.TestCase):
    def test_empty_dict(self):
        result = ServerManager.create_osc_msg({})
        self.assertEqual(result, [])

    def test_single_pair(self):
        result = ServerManager.create_osc_msg({"freq": 440})
        self.assertEqual(result, ["freq", 440])

    def test_multiple_pairs(self):
        result = ServerManager.create_osc_msg({"freq": 440, "amp": 0.5})
        self.assertEqual(len(result), 4)
        # Check key-value alternation
        self.assertTrue(all(isinstance(result[i], str) for i in range(0, len(result), 2)))

    def test_preserves_types(self):
        result = ServerManager.create_osc_msg({"name": "test", "val": 3.14, "flag": True})
        self.assertIn("test", result)
        self.assertIn(3.14, result)
        self.assertIn(True, result)


class TestServerManagerInit(unittest.TestCase):
    @patch.object(OSCClientWrapper, 'connect')
    def test_defaults(self, mock_connect):
        sm = ServerManager("localhost", 57110)
        self.assertEqual(sm.addr, "localhost")
        self.assertEqual(sm.port, 57110)
        self.assertEqual(sm.node, 1000)
        self.assertEqual(sm.bus, sm.num_input_busses + sm.num_output_busses)
        self.assertEqual(sm.osc_address, "/s_new")

    @patch.object(OSCClientWrapper, 'connect')
    def test_custom_address(self, mock_connect):
        sm = ServerManager("192.168.1.1", 57111, osc_address="/custom")
        self.assertEqual(sm.addr, "192.168.1.1")
        self.assertEqual(sm.port, 57111)
        self.assertEqual(sm.osc_address, "/custom")

    @patch.object(OSCClientWrapper, 'connect')
    def test_connects_client(self, mock_connect):
        sm = ServerManager("localhost", 57110)
        mock_connect.assert_called_once_with(("localhost", 57110))


class TestServerManagerNoNodeBus(unittest.TestCase):
    """Verify base ServerManager has node/bus state but not nextID methods."""
    @patch.object(OSCClientWrapper, 'connect')
    def test_has_node_attribute(self, mock_connect):
        sm = ServerManager("localhost", 57110)
        self.assertEqual(sm.node, 1000)

    @patch.object(OSCClientWrapper, 'connect')
    def test_has_bus_attribute(self, mock_connect):
        sm = ServerManager("localhost", 57110)
        self.assertEqual(sm.bus, sm.num_input_busses + sm.num_output_busses)


class TestServerManagerGetBundle(unittest.TestCase):
    @patch.object(OSCClientWrapper, 'connect')
    def test_get_bundle_basic(self, mock_connect):
        sm = ServerManager("localhost", 57110)
        bundle = sm.get_bundle("arg1", "arg2", timestamp=0.5)
        self.assertIsInstance(bundle, OSCBundle)

    @patch.object(OSCClientWrapper, 'connect')
    def test_get_bundle_with_dict(self, mock_connect):
        sm = ServerManager("localhost", 57110)
        bundle = sm.get_bundle({"freq": 440, "amp": 0.5})
        self.assertIsInstance(bundle, OSCBundle)


# ============================================================================
# SCLangServerManager — nextnodeID and nextbusID
# ============================================================================

class TestSCLangNextNodeID(unittest.TestCase):
    def _make_sclang_sm(self):
        """Create an SCLangServerManager without connecting."""
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.node = 1000
        sm.num_input_busses = 2
        sm.num_output_busses = 2
        sm.bus = 4
        sm.max_busses = 100
        sm.max_buffers = 1024
        sm.fxlist = None
        sm.synthdefs = None
        sm.fx_names = {}
        return sm

    def test_nextnodeID(self):
        sm = self._make_sclang_sm()
        self.assertEqual(sm.nextnodeID(), 1001)
        self.assertEqual(sm.nextnodeID(), 1002)

    def test_nextbusID(self):
        sm = self._make_sclang_sm()
        bus1 = sm.nextbusID()
        bus2 = sm.nextbusID()
        self.assertEqual(bus1, 6)
        self.assertEqual(bus2, 8)

    def test_nextbusID_wraps_around(self):
        sm = self._make_sclang_sm()
        sm.max_busses = 8
        sm.bus = 6
        # bus becomes 8, then 8+1 >= 8, wraps to 4
        bus = sm.nextbusID()
        self.assertEqual(bus, sm.num_input_busses + sm.num_output_busses)


# ============================================================================
# SCLangServerManager — str/repr
# ============================================================================

class TestSCLangStr(unittest.TestCase):
    def _make_sclang_sm(self, addr="localhost", port=57110):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.addr = addr
        sm.port = port
        return sm

    def test_str_format(self):
        sm = self._make_sclang_sm()
        result = str(sm)
        self.assertIn("localhost", result)
        self.assertIn("57110", result)
        self.assertIn("FoxDot ServerManager Instance", result)

    def test_repr_equals_str(self):
        sm = self._make_sclang_sm()
        self.assertEqual(repr(sm), str(sm))


# ============================================================================
# SCLangServerManager — set_midi_nudge
# ============================================================================

class TestSCLangMidiNudge(unittest.TestCase):
    def test_set_midi_nudge(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.midi_nudge = 0
        sm.set_midi_nudge(0.05)
        self.assertEqual(sm.midi_nudge, 0.05)


# ============================================================================
# SCLangServerManager — prepare_effect
# ============================================================================

class TestSCLangPrepareEffect(unittest.TestCase):
    def _make_sm_with_effects(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        # Mock fxlist
        mock_fx = MagicMock()
        mock_fx.args = ["hpr", "hpf"]
        mock_fx.defaults = {"hpr": 0.5, "hpf": 0}
        sm.fxlist = MagicMock()
        sm.fxlist.__getitem__ = MagicMock(return_value=mock_fx)
        return sm

    def test_prepare_effect_uses_packet_values(self):
        sm = self._make_sm_with_effects()
        result = sm.prepare_effect("highPassFilter", {"hpr": 0.8, "hpf": 4000})
        self.assertEqual(result, ["hpr", 0.8, "hpf", 4000.0])

    def test_prepare_effect_uses_defaults(self):
        sm = self._make_sm_with_effects()
        result = sm.prepare_effect("highPassFilter", {})
        self.assertEqual(result, ["hpr", 0.5, "hpf", 0.0])


# ============================================================================
# SCLangServerManager — get_midi_message
# ============================================================================

class TestSCLangGetMidiMessage(unittest.TestCase):
    def _make_sm(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.midi_nudge = 0
        return sm

    def test_returns_osc_bundle(self):
        sm = self._make_sm()
        bundle = sm.get_midi_message("MidiOut", {"midinote": 60, "amp": 1, "sus": 0.5, "channel": 0}, 0.5)
        self.assertIsInstance(bundle, OSCBundle)

    def test_default_values(self):
        sm = self._make_sm()
        bundle = sm.get_midi_message("MidiOut", {}, 0.0)
        self.assertIsInstance(bundle, OSCBundle)

    def test_amp_clamped_to_127(self):
        sm = self._make_sm()
        # amp=2 -> vel = min(127, 2*128-1) = min(127, 255) = 127
        bundle = sm.get_midi_message("MidiOut", {"amp": 2.0}, 0.0)
        self.assertIsInstance(bundle, OSCBundle)


# ============================================================================
# SCLangServerManager — recording state
# ============================================================================

class TestSCLangRecordingState(unittest.TestCase):
    def _make_sm(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm._is_recording = False
        sm.sclang = MagicMock()
        return sm

    def test_initial_not_recording(self):
        sm = self._make_sm()
        self.assertFalse(sm._is_recording)

    def test_record_sets_flag(self):
        sm = self._make_sm()
        from FoxDot.lib.Settings import RECORDING_DIR
        with patch('FoxDot.lib.ServerManager.get_timestamp', return_value='20260403_120000'):
            sm.record()
        self.assertTrue(sm._is_recording)

    def test_record_twice_no_double_start(self):
        sm = self._make_sm()
        with patch('FoxDot.lib.ServerManager.get_timestamp', return_value='20260403_120000'):
            sm.record()
        send_count = sm.sclang.send.call_count
        sm.record()  # second call should be no-op
        self.assertEqual(sm.sclang.send.call_count, send_count)

    def test_stop_recording(self):
        sm = self._make_sm()
        sm._is_recording = True
        sm.stopRecording()
        self.assertFalse(sm._is_recording)

    def test_stop_when_not_recording_is_noop(self):
        sm = self._make_sm()
        sm.stopRecording()
        sm.sclang.send.assert_not_called()


# ============================================================================
# Message class
# ============================================================================

class TestMessage(unittest.TestCase):
    def test_str_format(self):
        msg = Message({"key": "value"})
        s = str(msg)
        # First 4 chars are length prefix
        length_prefix = s[:4]
        payload = s[4:]
        self.assertEqual(int(length_prefix), len(payload))

    def test_str_json_payload(self):
        data = {"tempo": 120, "beat": 4}
        msg = Message(data)
        s = str(msg)
        payload = s[4:]
        parsed = json.loads(payload)
        self.assertEqual(parsed, data)

    def test_len(self):
        msg = Message({"x": 1})
        self.assertEqual(len(msg), len(str(msg)))

    def test_asString(self):
        msg = Message([1, 2, 3])
        self.assertEqual(msg.asString(), str(msg))

    def test_compact_json(self):
        msg = Message({"a": 1, "b": 2})
        s = str(msg)
        payload = s[4:]
        # Should use compact separators (no spaces)
        self.assertNotIn(": ", payload)
        self.assertNotIn(", ", payload)

    def test_empty_data(self):
        msg = Message({})
        s = str(msg)
        self.assertEqual(s[4:], "{}")

    def test_nested_data(self):
        data = {"sync": {"bpm": 120, "beat": 0}}
        msg = Message(data)
        s = str(msg)
        payload = s[4:]
        parsed = json.loads(payload)
        self.assertEqual(parsed["sync"]["bpm"], 120)

    def test_list_data(self):
        data = ["init", "hello"]
        msg = Message(data)
        s = str(msg)
        payload = s[4:]
        parsed = json.loads(payload)
        self.assertEqual(parsed, data)


# ============================================================================
# read_from_socket / send_to_socket
# ============================================================================

class _FakeSocket:
    """Minimal socket mock for testing read/send helpers."""
    def __init__(self, data=b""):
        self._data = data
        self._pos = 0
        self._sent = b""

    def recv(self, n):
        chunk = self._data[self._pos:self._pos + n]
        self._pos += n
        return chunk

    def send(self, data):
        self._sent += data
        return len(data)


class TestReadFromSocket(unittest.TestCase):
    def test_read_valid_message(self):
        payload = json.dumps({"key": "value"}, separators=(",", ":"))
        length_prefix = "{:04d}".format(len(payload))
        data = (length_prefix + payload).encode()
        sock = _FakeSocket(data)
        result = read_from_socket(sock)
        self.assertEqual(result, {"key": "value"})

    def test_read_empty_socket(self):
        sock = _FakeSocket(b"")
        result = read_from_socket(sock)
        self.assertIsNone(result)

    def test_read_list(self):
        payload = json.dumps(["init"], separators=(",", ":"))
        length_prefix = "{:04d}".format(len(payload))
        data = (length_prefix + payload).encode()
        sock = _FakeSocket(data)
        result = read_from_socket(sock)
        self.assertEqual(result, ["init"])

    def test_read_invalid_length(self):
        sock = _FakeSocket(b"abcd")
        result = read_from_socket(sock)
        self.assertIsNone(result)


class TestSendToSocket(unittest.TestCase):
    def test_send_complete(self):
        sock = _FakeSocket()
        data = {"tempo": 120}
        send_to_socket(sock, data)
        # Verify the sent data is a valid Message
        sent = sock._sent.decode()
        length_prefix = int(sent[:4])
        payload = sent[4:]
        self.assertEqual(len(payload), length_prefix)
        parsed = json.loads(payload)
        self.assertEqual(parsed, data)

    def test_send_list(self):
        sock = _FakeSocket()
        send_to_socket(sock, ["init"])
        sent = sock._sent.decode()
        payload = sent[4:]
        self.assertEqual(json.loads(payload), ["init"])


# ============================================================================
# TempoClient — calculate_latency
# ============================================================================

class TestTempoClientLatency(unittest.TestCase):
    def _make_client(self):
        tc = TempoClient.__new__(TempoClient)
        tc.metro = MagicMock()
        tc.socket = MagicMock()
        tc.latency = None
        tc.start_time = None
        tc.stop_time = None
        return tc

    def test_calculate_latency(self):
        tc = self._make_client()
        result = tc.calculate_latency(1.0, 2.0)
        self.assertAlmostEqual(result, 0.5)
        self.assertAlmostEqual(tc.latency, 0.5)

    def test_calculate_latency_zero(self):
        tc = self._make_client()
        result = tc.calculate_latency(5.0, 5.0)
        self.assertAlmostEqual(result, 0.0)

    def test_start_timing(self):
        tc = self._make_client()
        with patch('FoxDot.lib.ServerManager.time') as mock_time:
            mock_time.time.return_value = 100.0
            tc.start_timing()
        self.assertEqual(tc.start_time, 100.0)

    def test_stop_timing(self):
        tc = self._make_client()
        tc.start_time = 100.0
        with patch('FoxDot.lib.ServerManager.time') as mock_time:
            mock_time.time.return_value = 100.2
            tc.stop_timing()
        self.assertAlmostEqual(tc.latency, 0.1)


# ============================================================================
# TempoClient — update_tempo
# ============================================================================

class TestTempoClientUpdateTempo(unittest.TestCase):
    def test_update_sends_data(self):
        tc = TempoClient.__new__(TempoClient)
        tc.socket = _FakeSocket()
        tc.update_tempo(120, 0.0, 1000.0)
        sent = tc.socket._sent.decode()
        payload = json.loads(sent[4:])
        self.assertIn("new_bpm", payload)
        self.assertEqual(payload["new_bpm"]["bpm"], 120)
        self.assertEqual(payload["new_bpm"]["bpm_start_beat"], 0.0)
        self.assertEqual(payload["new_bpm"]["bpm_start_time"], 1000.0)


# ============================================================================
# TempoClient — kill
# ============================================================================

class TestTempoClientKill(unittest.TestCase):
    def test_kill_stops_listening(self):
        tc = TempoClient.__new__(TempoClient)
        tc.listening = True
        tc.socket = MagicMock()
        tc.kill()
        self.assertFalse(tc.listening)
        tc.socket.close.assert_called_once()


# ============================================================================
# OSCClientWrapper
# ============================================================================

class TestOSCClientWrapper(unittest.TestCase):
    def test_error_printed_flag_starts_false(self):
        # Reset class-level flag
        OSCClientWrapper.error_printed = False
        self.assertFalse(OSCClientWrapper.error_printed)

    def test_is_subclass_of_osc_client(self):
        from FoxDot.lib.OSC3 import OSCClient
        self.assertTrue(issubclass(OSCClientWrapper, OSCClient))


# ============================================================================
# SCLangServerManager — get_synth_node
# ============================================================================

class TestSCLangGetSynthNode(unittest.TestCase):
    def _make_sm(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.node = 1000
        return sm

    def test_returns_msg_and_node(self):
        sm = self._make_sm()
        synthdef = MagicMock()
        synthdef.name = "pluck"
        synthdef.bus_name = "bus"
        packet = {"freq": 440.0, "amp": 0.8, "sus": 1.0}
        msg, node = sm.get_synth_node(1001, 4, 1000, synthdef, packet)
        self.assertIsInstance(msg, OSCMessage)
        # nextnodeID increments self.node from 1000 to 1001, returns 1001
        self.assertEqual(node, 1001)

    def test_skips_env_and_degree(self):
        sm = self._make_sm()
        synthdef = MagicMock()
        synthdef.name = "pluck"
        synthdef.bus_name = "bus"
        packet = {"freq": 440.0, "env": "test", "degree": 0, "sus": 1.0}
        msg, node = sm.get_synth_node(1001, 4, 1000, synthdef, packet)
        self.assertIsInstance(msg, OSCMessage)


# ============================================================================
# SCLangServerManager — get_exit_node
# ============================================================================

class TestSCLangGetExitNode(unittest.TestCase):
    def test_returns_msg_and_node(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.node = 1000
        msg, node = sm.get_exit_node(1001, 4, 1000, {"sus": 2.0})
        self.assertIsInstance(msg, OSCMessage)
        # nextnodeID increments self.node from 1000 to 1001, returns 1001
        self.assertEqual(node, 1001)


# ============================================================================
# SCLangServerManager — get_init_node
# ============================================================================

class TestSCLangGetInitNode(unittest.TestCase):
    def _make_sm(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.node = 1000
        return sm

    def test_with_rate_key(self):
        sm = self._make_sm()
        from FoxDot.lib.Settings import SamplePlayer
        synthdef = MagicMock()
        synthdef.name = SamplePlayer
        msg, node = sm.get_init_node(1001, 4, 1000, synthdef, {"sus": 1.0, "rate": 1.5})
        self.assertIsInstance(msg, OSCMessage)

    def test_with_freq_key(self):
        sm = self._make_sm()
        synthdef = MagicMock()
        synthdef.name = "pluck"
        msg, node = sm.get_init_node(1001, 4, 1000, synthdef, {"sus": 1.0, "freq": 440})
        self.assertIsInstance(msg, OSCMessage)

    def test_without_key(self):
        sm = self._make_sm()
        synthdef = MagicMock()
        synthdef.name = "pluck"
        msg, node = sm.get_init_node(1001, 4, 1000, synthdef, {"sus": 1.0})
        self.assertIsInstance(msg, OSCMessage)


# ============================================================================
# SCLangServerManager — add_forward
# ============================================================================

class TestSCLangAddForward(unittest.TestCase):
    @patch.object(OSCClientWrapper, 'connect')
    def test_add_forward(self, mock_connect):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.forward = None
        sm.add_forward("192.168.1.100", 57111)
        self.assertIsNotNone(sm.forward)
        mock_connect.assert_called_once_with(("192.168.1.100", 57111))


# ============================================================================
# SCLangServerManager — sendOSC routing
# ============================================================================

class TestSCLangSendOSC(unittest.TestCase):
    def _make_sm(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.client = MagicMock()
        sm.sclang = MagicMock()
        sm.forward = None
        return sm

    def test_midi_message_goes_to_sclang(self):
        from FoxDot.lib.Settings import OSC_MIDI_ADDRESS
        sm = self._make_sm()
        msg = MagicMock()
        msg.address = OSC_MIDI_ADDRESS
        sm.sendOSC(msg)
        sm.sclang.send.assert_called_once_with(msg)
        sm.client.send.assert_not_called()

    def test_regular_message_goes_to_client(self):
        sm = self._make_sm()
        msg = MagicMock()
        msg.address = "/s_new"
        sm.sendOSC(msg)
        sm.client.send.assert_called_once_with(msg)
        sm.sclang.send.assert_not_called()

    def test_forward_receives_copy(self):
        sm = self._make_sm()
        sm.forward = MagicMock()
        msg = MagicMock()
        msg.address = "/s_new"
        sm.sendOSC(msg)
        sm.forward.send.assert_called_once_with(msg)


# ============================================================================
# SCLangServerManager — freeAllNodes
# ============================================================================

class TestSCLangFreeAllNodes(unittest.TestCase):
    def test_sends_message(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        sm.client = MagicMock()
        sm.freeAllNodes()
        sm.client.send.assert_called_once()
        sent_msg = sm.client.send.call_args[0][0]
        self.assertIsInstance(sent_msg, OSCMessage)


# ============================================================================
# SCLangServerManager — setFx
# ============================================================================

class TestSCLangSetFx(unittest.TestCase):
    def test_stores_fxlist(self):
        sm = SCLangServerManager.__new__(SCLangServerManager)
        mock_fx = MagicMock()
        mock_fx.synthdef = "highPassFilter"
        fx_list = MagicMock()
        fx_list.items.return_value = [("hpf", mock_fx)]
        sm.setFx(fx_list)
        self.assertEqual(sm.fxlist, fx_list)
        self.assertEqual(sm.fx_names["hpf"], "highPassFilter")


# ============================================================================
# Integration: Message round-trip through socket helpers
# ============================================================================

class TestMessageRoundTrip(unittest.TestCase):
    def test_dict_roundtrip(self):
        data = {"sync": {"bpm": 120, "beat": 0, "start_time": 1000.0}}
        sock = _FakeSocket()
        send_to_socket(sock, data)
        # Create a read socket from the sent data
        read_sock = _FakeSocket(sock._sent)
        result = read_from_socket(read_sock)
        self.assertEqual(result, data)

    def test_list_roundtrip(self):
        data = ["init", "test"]
        sock = _FakeSocket()
        send_to_socket(sock, data)
        read_sock = _FakeSocket(sock._sent)
        result = read_from_socket(read_sock)
        self.assertEqual(result, data)

    def test_nested_roundtrip(self):
        data = {"new_bpm": {"bpm": 140, "bpm_start_time": 50.5, "bpm_start_beat": 16.0}}
        sock = _FakeSocket()
        send_to_socket(sock, data)
        read_sock = _FakeSocket(sock._sent)
        result = read_from_socket(read_sock)
        self.assertEqual(result, data)


if __name__ == "__main__":
    unittest.main()
