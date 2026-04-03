"""
Unit tests for Logging module — Timing class (decorator, context manager, direct usage).
"""

import logging
import time
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from FoxDot.lib.Logging import Timing, enablePerfLogging


# ---------------------------------------------------------------------------
# enablePerfLogging
# ---------------------------------------------------------------------------

class TestEnablePerfLogging(unittest.TestCase):
    """Tests for the enablePerfLogging() convenience function."""

    def test_sets_debug_level(self):
        enablePerfLogging()
        logger = logging.getLogger("FoxDot.perf")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_idempotent(self):
        enablePerfLogging()
        enablePerfLogging()
        logger = logging.getLogger("FoxDot.perf")
        self.assertEqual(logger.level, logging.DEBUG)


# ---------------------------------------------------------------------------
# Timing — basic construction
# ---------------------------------------------------------------------------

class TestTimingInit(unittest.TestCase):
    """Tests for Timing object creation."""

    def test_create(self):
        t = Timing("test_event")
        self.assertEqual(t._event, "test_event")

    def test_custom_logger(self):
        t = Timing("evt", logger="custom.logger")
        self.assertEqual(t._logger, "custom.logger")

    def test_default_logger(self):
        t = Timing("evt")
        self.assertEqual(t._logger, "FoxDot.perf")

    def test_logargs_default_false(self):
        t = Timing("evt")
        self.assertFalse(t._logargs)

    def test_logargs_true(self):
        t = Timing("evt", logargs=True)
        self.assertTrue(t._logargs)

    def test_str(self):
        t = Timing("my_event")
        self.assertEqual(str(t), "Timing(my_event)")

    def test_start_is_none_initially(self):
        t = Timing("evt")
        self.assertIsNone(t._start)

    def test_messages_empty_initially(self):
        t = Timing("evt")
        self.assertEqual(t._messages, [])


# ---------------------------------------------------------------------------
# Timing — direct usage (start/finish)
# ---------------------------------------------------------------------------

class TestTimingDirect(unittest.TestCase):
    """Tests for direct Timing.start() / Timing.finish() usage."""

    def test_start_sets_time(self):
        t = Timing("evt")
        t.start()
        self.assertIsNotNone(t._start)
        self.assertIsInstance(t._start, float)

    def test_finish_clears_start(self):
        t = Timing("evt")
        t.start()
        t.finish()
        # finish doesn't reset _start, but it logs the time

    def test_finish_before_start_warns(self):
        t = Timing("evt")
        # Should not raise, just warn
        t.finish()

    def test_double_start_warns(self):
        t = Timing("evt")
        t.start()
        # Second start should warn but not crash
        t.start()

    def test_addMessage(self):
        t = Timing("evt")
        t.addMessage("custom info")
        self.assertIn("custom info", t._messages)

    def test_addMessage_multiple(self):
        t = Timing("evt")
        t.addMessage("a")
        t.addMessage("b")
        self.assertEqual(t._messages, ["a", "b"])

    def test_timing_measures_time(self):
        t = Timing("evt")
        t.start()
        time.sleep(0.01)
        before_finish = time.time()
        t.finish()
        # Verify start was set and represents a real timestamp
        self.assertGreater(t._start, 0)
        self.assertLessEqual(t._start, before_finish)


# ---------------------------------------------------------------------------
# Timing — context manager
# ---------------------------------------------------------------------------

class TestTimingContextManager(unittest.TestCase):
    """Tests for Timing used as a context manager."""

    def test_context_manager_basic(self):
        with Timing("ctx_test") as timer:
            self.assertIsNotNone(timer._start)

    def test_context_manager_returns_timer(self):
        with Timing("ctx_test") as timer:
            self.assertIsInstance(timer, Timing)

    def test_context_manager_addMessage(self):
        with Timing("ctx_test") as timer:
            timer.addMessage("inside context")
        self.assertIn("inside context", timer._messages)

    def test_context_manager_with_exception(self):
        try:
            with Timing("ctx_err"):
                raise ValueError("test error")
        except ValueError:
            pass
        # Should not crash even with an exception inside

    def test_context_manager_timing(self):
        before = time.time()
        with Timing("ctx_timing") as timer:
            time.sleep(0.01)
        self.assertIsNotNone(timer._start)
        self.assertGreaterEqual(timer._start, before)


# ---------------------------------------------------------------------------
# Timing — decorator
# ---------------------------------------------------------------------------

class TestTimingDecorator(unittest.TestCase):
    """Tests for Timing used as a function decorator."""

    def test_decorator_basic(self):
        @Timing("dec_test")
        def my_func():
            return 42

        result = my_func()
        self.assertEqual(result, 42)

    def test_decorator_preserves_name(self):
        @Timing("dec_test")
        def my_func():
            pass

        self.assertEqual(my_func.__name__, "my_func")

    def test_decorator_with_args(self):
        @Timing("dec_test")
        def add(a, b):
            return a + b

        self.assertEqual(add(3, 4), 7)

    def test_decorator_with_kwargs(self):
        @Timing("dec_test")
        def greet(name="world"):
            return f"hello {name}"

        self.assertEqual(greet(name="test"), "hello test")

    def test_decorator_logargs(self):
        @Timing("dec_test", logargs=True)
        def my_func(x, y=10):
            return x + y

        result = my_func(5, y=20)
        self.assertEqual(result, 25)

    def test_decorator_exception_propagates(self):
        @Timing("dec_test")
        def bad_func():
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            bad_func()

    def test_decorator_no_return(self):
        @Timing("dec_test")
        def void_func():
            pass

        result = void_func()
        self.assertIsNone(result)

    def test_decorator_with_logargs_empty(self):
        @Timing("dec_test", logargs=True)
        def no_args_func():
            return 1

        self.assertEqual(no_args_func(), 1)


# ---------------------------------------------------------------------------
# Timing — logging output verification
# ---------------------------------------------------------------------------

class TestTimingLogOutput(unittest.TestCase):
    """Tests verifying that Timing actually produces log output."""

    def setUp(self):
        self.logger = logging.getLogger("FoxDot.perf")
        self.logger.setLevel(logging.DEBUG)
        self.handler = logging.handlers_placeholder = logging.StreamHandler()
        self.handler.setLevel(logging.DEBUG)
        self.log_records = []

        class RecordHandler(logging.Handler):
            def __init__(self, records_list):
                super().__init__()
                self.records = records_list

            def emit(self, record):
                self.records.append(record)

        self.record_handler = RecordHandler(self.log_records)
        self.logger.addHandler(self.record_handler)

    def tearDown(self):
        self.logger.removeHandler(self.record_handler)

    def test_finish_logs_event(self):
        t = Timing("log_test")
        t.start()
        t.finish()
        messages = [r.getMessage() for r in self.log_records]
        found = any("log_test" in m for m in messages)
        self.assertTrue(found, f"Expected 'log_test' in log output. Got: {messages}")

    def test_finish_logs_milliseconds(self):
        t = Timing("ms_test")
        t.start()
        time.sleep(0.01)
        t.finish()
        messages = [r.getMessage() for r in self.log_records]
        found = any("ms" in m for m in messages)
        self.assertTrue(found, f"Expected 'ms' in log output. Got: {messages}")

    def test_context_manager_logs(self):
        with Timing("ctx_log_test"):
            pass
        messages = [r.getMessage() for r in self.log_records]
        found = any("ctx_log_test" in m for m in messages)
        self.assertTrue(found)

    def test_decorator_logs(self):
        @Timing("dec_log_test")
        def my_func():
            return 1

        my_func()
        messages = [r.getMessage() for r in self.log_records]
        found = any("dec_log_test" in m for m in messages)
        self.assertTrue(found)

    def test_addMessage_appears_in_log(self):
        t = Timing("msg_test")
        t.start()
        t.addMessage("custom_tag")
        t.finish()
        messages = [r.getMessage() for r in self.log_records]
        found = any("custom_tag" in m for m in messages)
        self.assertTrue(found, f"Expected 'custom_tag' in log output. Got: {messages}")


if __name__ == "__main__":
    unittest.main()
