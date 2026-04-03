"""
Unit tests for FoxDot.lib.Code utilities

Tests cover:
- foxdot_func_cmp.func_cmp: compare two functions by bytecode
- foxdot_func_cmp.func_str: serialize a function to string
- foxdot_when_statement._whenStatement: conditional monitoring logic
- foxdot_when_statement._whenLibrary: when-statement collection manager
"""
import pytest
from FoxDot.lib.Code.foxdot_func_cmp import func_cmp, func_str
from FoxDot.lib.Code.foxdot_when_statement import _whenStatement, _whenLibrary


# ──────────────────────────────────────────────
# func_cmp
# ──────────────────────────────────────────────


class TestFuncCmp:
    def test_identical_functions(self):
        def f():
            return 1
        def g():
            return 1
        assert func_cmp(f, g) is True

    def test_different_return(self):
        def f():
            return 1
        def g():
            return 2
        assert func_cmp(f, g) is False

    def test_different_body(self):
        def f():
            x = 1
            return x
        def g():
            x = 2
            return x
        assert func_cmp(f, g) is False

    def test_same_function(self):
        def f():
            return 42
        assert func_cmp(f, f) is True

    def test_different_variable_names_in_scope(self):
        """Functions that reference different global names differ."""
        # co_names captures global variable references
        def f():
            return some_global  # noqa: F821
        def g():
            return other_global  # noqa: F821
        assert func_cmp(f, g) is False

    def test_lambdas_identical(self):
        f = lambda: 5
        g = lambda: 5
        assert func_cmp(f, g) is True

    def test_lambdas_different(self):
        f = lambda: 5
        g = lambda: 10
        assert func_cmp(f, g) is False

    def test_lambda_with_arg(self):
        f = lambda x: x + 1
        g = lambda x: x + 1
        assert func_cmp(f, g) is True

    def test_lambda_different_ops(self):
        f = lambda x: x + 1
        g = lambda x: x - 1
        assert func_cmp(f, g) is False

    def test_no_op_functions(self):
        def f():
            pass
        def g():
            pass
        assert func_cmp(f, g) is True


# ──────────────────────────────────────────────
# func_str
# ──────────────────────────────────────────────


class TestFuncStr:
    def test_returns_string(self):
        def f():
            return 42
        result = func_str(f)
        assert isinstance(result, str)

    def test_contains_function_name(self):
        def my_function():
            return 1
        result = func_str(my_function)
        assert "my_function" in result

    def test_lambda_name(self):
        f = lambda: 5
        result = func_str(f)
        assert "<lambda>" in result

    def test_contains_constants(self):
        def f():
            return 99
        result = func_str(f)
        assert "99" in result

    def test_comma_separated(self):
        def f():
            return 1
        result = func_str(f)
        parts = result.split(",")
        assert len(parts) >= 3  # name, co_names, co_consts

    def test_different_functions_different_strings(self):
        def f():
            return 1
        def g():
            return 2
        assert func_str(f) != func_str(g)


# ──────────────────────────────────────────────
# _whenStatement
# ──────────────────────────────────────────────


class TestWhenStatement:
    def test_creation_default_expr(self):
        ws = _whenStatement()
        # Default expression is lambda: True
        assert ws.expr() is True

    def test_creation_custom_expr(self):
        ws = _whenStatement(func=lambda: False)
        assert ws.expr() is False

    def test_reset_clears_actions(self):
        ws = _whenStatement()
        called = []
        ws.action = lambda: called.append("action")
        ws.reset()
        ws.action()  # Should be no-op after reset
        assert called == []

    def test_then_sets_action(self):
        ws = _whenStatement()
        called = []
        ws.then(lambda: called.append("then"))
        ws.action()
        assert called == ["then"]

    def test_elsedo_sets_notaction(self):
        ws = _whenStatement()
        called = []
        ws.elsedo(lambda: called.append("else"))
        ws.notaction()
        assert called == ["else"]

    def test_when_sets_expr(self):
        ws = _whenStatement()
        ws.when(lambda: 42)
        assert ws.expr() == 42

    def test_evaluate_true_runs_action(self):
        ws = _whenStatement(func=lambda: True)
        called = []
        ws.then(lambda: called.append("action"))
        ws.evaluate()
        assert called == ["action"]

    def test_evaluate_false_runs_notaction(self):
        ws = _whenStatement(func=lambda: False)
        called = []
        ws.elsedo(lambda: called.append("else"))
        ws.evaluate()
        assert called == ["else"]

    def test_evaluate_only_fires_once_per_switch(self):
        """The action should only fire once per state change (edge-triggered)."""
        ws = _whenStatement(func=lambda: True)
        count = []
        ws.then(lambda: count.append(1))
        ws.evaluate()
        ws.evaluate()
        ws.evaluate()
        # Only first evaluation should fire
        assert len(count) == 1

    def test_evaluate_toggles_on_state_change(self):
        """Action fires again when condition changes and returns."""
        state = [True]
        ws = _whenStatement(func=lambda: state[0])
        action_count = []
        else_count = []
        ws.then(lambda: action_count.append(1))
        ws.elsedo(lambda: else_count.append(1))

        ws.evaluate()  # True -> fires action
        assert len(action_count) == 1
        assert len(else_count) == 0

        state[0] = False
        ws.evaluate()  # False -> fires else
        assert len(action_count) == 1
        assert len(else_count) == 1

        state[0] = True
        ws.evaluate()  # True again -> fires action again
        assert len(action_count) == 2
        assert len(else_count) == 1

    def test_stop_resets(self):
        ws = _whenStatement()
        called = []
        ws.then(lambda: called.append(1))
        ws.stop()
        ws.action()  # Should be no-op after stop
        assert called == []

    def test_remove_sets_flag(self):
        ws = _whenStatement()
        assert ws.remove_me is False
        ws.remove()
        assert ws.remove_me is True

    def test_remove_also_resets(self):
        ws = _whenStatement()
        called = []
        ws.then(lambda: called.append(1))
        ws.remove()
        ws.action()
        assert called == []

    def test_chaining_then_returns_self(self):
        ws = _whenStatement()
        result = ws.then(lambda: None)
        assert result is ws

    def test_chaining_elsedo_returns_self(self):
        ws = _whenStatement()
        result = ws.elsedo(lambda: None)
        assert result is ws

    def test_chaining_when_returns_self(self):
        ws = _whenStatement()
        result = ws.when(lambda: True)
        assert result is ws

    def test_chaining_stop_returns_self(self):
        ws = _whenStatement()
        result = ws.stop()
        assert result is ws

    def test_chaining_remove_returns_self(self):
        ws = _whenStatement()
        result = ws.remove()
        assert result is ws

    def test_do_switch_initially_false(self):
        ws = _whenStatement()
        assert ws.do_switch is False

    def test_elsedo_switch_initially_false(self):
        ws = _whenStatement()
        assert ws.elsedo_switch is False

    def test_toggle_live_functions_with_no_live_attr(self):
        """toggle_live_functions should not error if action has no .live attr."""
        ws = _whenStatement()
        ws.then(lambda: None)
        ws.elsedo(lambda: None)
        # Should not raise
        ws.toggle_live_functions(True)
        ws.toggle_live_functions(False)


# ──────────────────────────────────────────────
# _whenLibrary
# ──────────────────────────────────────────────


class TestWhenLibrary:
    def test_creation_empty(self):
        lib = _whenLibrary()
        assert len(lib) == 0

    def test_call_creates_statement(self):
        lib = _whenLibrary()
        # Monkey-patch start_thread to avoid spawning a real thread
        lib.start_thread = lambda: None
        ws = lib("test1")
        assert isinstance(ws, _whenStatement)
        assert len(lib) == 1

    def test_call_returns_existing(self):
        lib = _whenLibrary()
        lib.start_thread = lambda: None
        ws1 = lib("test1")
        ws2 = lib("test1")
        assert ws1 is ws2

    def test_call_different_names(self):
        lib = _whenLibrary()
        lib.start_thread = lambda: None
        ws1 = lib("a")
        ws2 = lib("b")
        assert ws1 is not ws2
        assert len(lib) == 2

    def test_reset_clears_library(self):
        lib = _whenLibrary()
        lib.start_thread = lambda: None
        lib("a")
        lib("b")
        assert len(lib) == 2
        lib.reset()
        assert len(lib) == 0

    def test_reset_returns_self(self):
        lib = _whenLibrary()
        result = lib.reset()
        assert result is lib

    def test_editing_initially_none(self):
        lib = _whenLibrary()
        assert lib.editing is None

    def test_repr(self):
        lib = _whenLibrary()
        # Should not raise
        result = repr(lib)
        assert isinstance(result, str)

    def test_first_statement_starts_thread(self):
        """First statement creation should attempt to start the thread."""
        lib = _whenLibrary()
        started = []
        lib.start_thread = lambda: started.append(True)
        lib("first")
        assert len(started) == 1

    def test_second_statement_no_thread(self):
        """Second statement should not start another thread."""
        lib = _whenLibrary()
        started = []
        lib.start_thread = lambda: started.append(True)
        lib("first")
        lib("second")
        assert len(started) == 1

    def test_set_namespace_static(self):
        """set_namespace should delegate to _whenStatement.set_namespace."""
        class FakeEnv:
            namespace = {"test": True}
        # Save original
        orig = _whenStatement.namespace
        try:
            _whenLibrary.set_namespace(FakeEnv())
            assert _whenStatement.namespace == {"test": True}
        finally:
            _whenStatement.namespace = orig
