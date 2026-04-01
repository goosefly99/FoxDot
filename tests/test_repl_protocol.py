"""Tests for REPL protocol message serialization and parsing."""
import json
import unittest

from FoxDot.lib.REPL.protocol import (
    EvalMessage, ResultMessage, StateMessage, ProtocolErrorMessage,
    ClockState, PlayerState,
    MSG_EVAL, MSG_RESULT, MSG_STATE, MSG_ERROR,
    parse_message, read_stdin_block,
)


class TestEvalMessage(unittest.TestCase):

    def test_defaults(self):
        msg = EvalMessage()
        self.assertEqual(msg.type, MSG_EVAL)
        self.assertEqual(msg.id, "")
        self.assertEqual(msg.code, "")

    def test_to_json_roundtrip(self):
        msg = EvalMessage(id="abc", code="d1 >> pluck()")
        raw = msg.to_json()
        d = json.loads(raw)
        self.assertEqual(d["type"], MSG_EVAL)
        self.assertEqual(d["id"], "abc")
        self.assertEqual(d["code"], "d1 >> pluck()")

    def test_from_dict(self):
        d = {"type": "eval", "id": "42", "code": "print(1)"}
        msg = EvalMessage.from_dict(d)
        self.assertEqual(msg.id, "42")
        self.assertEqual(msg.code, "print(1)")

    def test_from_dict_missing_fields(self):
        msg = EvalMessage.from_dict({"type": "eval"})
        self.assertEqual(msg.id, "")
        self.assertEqual(msg.code, "")


class TestResultMessage(unittest.TestCase):

    def test_success_result(self):
        msg = ResultMessage.success_result("id1", stdout="hello\n")
        self.assertTrue(msg.success)
        self.assertEqual(msg.id, "id1")
        self.assertEqual(msg.stdout, "hello\n")

    def test_error_result(self):
        msg = ResultMessage.error_result("id2", "NameError", "traceback...")
        self.assertFalse(msg.success)
        self.assertEqual(msg.error, "NameError")
        self.assertEqual(msg.traceback, "traceback...")

    def test_success_to_json_omits_error_fields(self):
        msg = ResultMessage.success_result("x")
        d = json.loads(msg.to_json())
        self.assertNotIn("error", d)
        self.assertNotIn("traceback", d)

    def test_error_to_json_includes_error_fields(self):
        msg = ResultMessage.error_result("x", "err", "tb")
        d = json.loads(msg.to_json())
        self.assertIn("error", d)
        self.assertIn("traceback", d)

    def test_success_with_players(self):
        players = {"d1": {"synth": "pluck", "active": True}}
        msg = ResultMessage.success_result("x", players=players)
        d = json.loads(msg.to_json())
        self.assertIn("players", d)
        self.assertEqual(d["players"]["d1"]["synth"], "pluck")

    def test_success_without_players_omits_key(self):
        msg = ResultMessage.success_result("x")
        d = json.loads(msg.to_json())
        self.assertNotIn("players", d)


class TestPlayerState(unittest.TestCase):

    def test_to_dict_without_amp(self):
        ps = PlayerState(synth="pluck", active=True)
        d = ps.to_dict()
        self.assertEqual(d, {"synth": "pluck", "active": True})
        self.assertNotIn("amp", d)

    def test_to_dict_with_amp(self):
        ps = PlayerState(synth="bass", active=False, amp=0.5)
        d = ps.to_dict()
        self.assertEqual(d["amp"], 0.5)
        self.assertFalse(d["active"])


class TestStateMessage(unittest.TestCase):

    def test_from_runtime(self):
        clock = ClockState(bpm=140.0, beat=32.5, bar=8)
        players = {"d1": PlayerState(synth="pluck", active=True, amp=1.0)}
        msg = StateMessage.from_runtime(clock, players)

        d = json.loads(msg.to_json())
        self.assertEqual(d["type"], MSG_STATE)
        self.assertEqual(d["clock"]["bpm"], 140.0)
        self.assertEqual(d["clock"]["beat"], 32.5)
        self.assertEqual(d["clock"]["bar"], 8)
        self.assertEqual(d["players"]["d1"]["synth"], "pluck")

    def test_to_json(self):
        msg = StateMessage(clock={"bpm": 120}, players={})
        d = json.loads(msg.to_json())
        self.assertEqual(d["type"], MSG_STATE)


class TestProtocolErrorMessage(unittest.TestCase):

    def test_to_json(self):
        msg = ProtocolErrorMessage(reason="bad json")
        d = json.loads(msg.to_json())
        self.assertEqual(d["type"], MSG_ERROR)
        self.assertEqual(d["reason"], "bad json")


class TestParseMessage(unittest.TestCase):

    def test_valid_eval(self):
        raw = json.dumps({"type": "eval", "id": "1", "code": "x = 1"})
        msg = parse_message(raw)
        self.assertIsInstance(msg, EvalMessage)
        self.assertEqual(msg.code, "x = 1")

    def test_malformed_json_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_message("{bad json")
        self.assertIn("Malformed JSON", str(ctx.exception))

    def test_unknown_type_raises(self):
        raw = json.dumps({"type": "unknown"})
        with self.assertRaises(ValueError) as ctx:
            parse_message(raw)
        self.assertIn("Unknown message type", str(ctx.exception))

    def test_missing_type_raises(self):
        raw = json.dumps({"code": "print(1)"})
        with self.assertRaises(ValueError):
            parse_message(raw)


class TestReadStdinBlock(unittest.TestCase):

    def test_joins_lines(self):
        lines = ["d1 >> pluck()", "d2 >> bass()"]
        result = read_stdin_block(lines)
        self.assertEqual(result, "d1 >> pluck()\nd2 >> bass()")

    def test_empty_list(self):
        self.assertEqual(read_stdin_block([]), "")


if __name__ == "__main__":
    unittest.main()
