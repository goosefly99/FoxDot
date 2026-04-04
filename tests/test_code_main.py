"""
Unit tests for the Code module: main_lib and foxdot_live_function.

Covers:
- CodeString (construction, readline iteration, __str__)
- clean() (unicode lambda replacement)
- stdout() (shell output formatting)
- _StartupFile (path management, loading from nonexistent paths)
- FoxDotCode._compile() (bytecode compilation)
- Module introspection helpers (classes, instances, functions)
- get_now() (value extraction from plain and time-varying objects)
- write_to_file() (file I/O with error handling)
- re_player regex (player line detection)
- WarningMsg() (output format)
- _live_function (construction, calling, updating, dependency)
- livefunction decorator (wrapping, calling, re-wrapping)
- _whenStatement (init, evaluate, toggle, reset, remove, context manager)
- _whenLibrary (call, len, reset, editing helpers)
"""

import os
import sys
import types

import pytest


# ===========================================================================
# CodeString
# ===========================================================================

class TestCodeString:
    """Tests for main_lib.CodeString."""

    def _make(self, raw):
        from FoxDot.lib.Code.main_lib import CodeString
        return CodeString(raw)

    def test_raw_preserved(self):
        cs = self._make("hello")
        assert cs.raw == "hello"

    def test_str_returns_raw(self):
        cs = self._make("x = 1\ny = 2")
        assert str(cs) == "x = 1\ny = 2"

    def test_readline_returns_lines_with_newline(self):
        cs = self._make("a\nb\nc")
        assert cs.readline() == "a\n"
        assert cs.readline() == "b\n"
        assert cs.readline() == "c\n"

    def test_readline_ends_with_empty(self):
        cs = self._make("one")
        cs.readline()  # "one\n"
        last = cs.readline()  # ""
        assert last == ""

    def test_empty_string(self):
        cs = self._make("")
        line1 = cs.readline()
        assert line1 == "\n"
        line2 = cs.readline()
        assert line2 == ""

    def test_single_line_no_newline(self):
        cs = self._make("x = 42")
        assert cs.readline() == "x = 42\n"
        assert cs.readline() == ""

    def test_multiline_count(self):
        cs = self._make("a\nb\nc\nd")
        # 4 content lines + 1 empty sentinel
        count = 0
        for _ in range(10):
            line = cs.readline()
            count += 1
            if line == "":
                break
        assert count == 5  # a, b, c, d, ""

    def test_iter_starts_at_negative_one(self):
        cs = self._make("x")
        assert cs.iter == -1


# ===========================================================================
# clean()
# ===========================================================================

class TestClean:
    """Tests for main_lib.clean()."""

    def _call(self, s):
        from FoxDot.lib.Code.main_lib import clean
        return clean(s)

    def test_lambda_replacement(self):
        result = self._call("\u03BB x: x + 1")
        assert result == "lambda x: x + 1"

    def test_no_lambda_unchanged(self):
        result = self._call("x = 1 + 2")
        assert result == "x = 1 + 2"

    def test_multiple_lambdas(self):
        result = self._call("\u03BB: 1, \u03BB: 2")
        assert result == "lambda: 1, lambda: 2"

    def test_empty_string(self):
        result = self._call("")
        assert result == ""

    def test_mixed_content(self):
        result = self._call("f = \u03BB x: x * 2")
        assert result == "f = lambda x: x * 2"


# ===========================================================================
# stdout()
# ===========================================================================

class TestStdout:
    """Tests for main_lib.stdout()."""

    def _call(self, code):
        from FoxDot.lib.Code.main_lib import stdout
        return stdout(code)

    def test_single_line(self):
        result = self._call("x = 1")
        assert result == ">>> x = 1"

    def test_multiline(self):
        result = self._call("x = 1\ny = 2")
        assert result == ">>> x = 1\n... y = 2"

    def test_strips_leading_trailing_whitespace(self):
        result = self._call("  x = 1  ")
        assert result == ">>> x = 1"

    def test_multiline_with_whitespace(self):
        result = self._call("  a = 1\n  b = 2  ")
        # strip() only removes leading/trailing whitespace from the whole string,
        # then each line is joined with "... " prefix preserving internal whitespace
        assert result == ">>> a = 1\n...   b = 2"

    def test_empty_after_strip(self):
        result = self._call("   ")
        assert result == ">>> "


# ===========================================================================
# _StartupFile
# ===========================================================================

class TestStartupFile:
    """Tests for main_lib._StartupFile."""

    def _make(self, path):
        from FoxDot.lib.Code.main_lib import _StartupFile
        return _StartupFile(path)

    def test_set_path_none(self):
        sf = self._make(None)
        assert sf.path is None

    def test_set_path_resolves(self, tmp_path):
        p = tmp_path / "startup.py"
        p.touch()
        sf = self._make(str(p))
        assert os.path.isabs(sf.path)

    def test_load_none_path_returns_empty(self):
        sf = self._make(None)
        assert sf.load() == ""

    def test_load_nonexistent_returns_empty(self):
        sf = self._make("/nonexistent/path/startup.py")
        result = sf.load()
        assert result == ""

    def test_load_real_file(self, tmp_path):
        p = tmp_path / "my_startup.py"
        p.write_text("print('hello')")
        sf = self._make(str(p))
        assert sf.load() == "print('hello')"

    def test_set_path_updates(self, tmp_path):
        sf = self._make(None)
        assert sf.path is None
        p = tmp_path / "new.py"
        p.write_text("# new")
        sf.set_path(str(p))
        assert sf.path is not None
        assert sf.load() == "# new"


# ===========================================================================
# FoxDotCode._compile
# ===========================================================================

class TestFoxDotCodeCompile:
    """Tests for FoxDotCode._compile static method."""

    def _compile(self, code_str):
        from FoxDot.lib.Code.main_lib import FoxDotCode
        return FoxDotCode._compile(code_str)

    def test_returns_code_object(self):
        result = self._compile("x = 1")
        assert isinstance(result, types.CodeType)

    def test_compiled_code_is_runnable(self):
        code = self._compile("result = 2 + 3")
        ns = {}
        # Use exec to run the compiled code
        eval(compile("pass", "<test>", "exec"))  # warm up
        ns_exec = {}
        co = self._compile("result = 2 + 3")
        # Execute via the built-in
        builtins_exec = __builtins__["exec"] if isinstance(__builtins__, dict) else getattr(__builtins__, "exec")
        builtins_exec(co, ns_exec)
        assert ns_exec["result"] == 5

    def test_multiline_compile(self):
        co = self._compile("a = 1\nb = 2\nc = a + b")
        ns = {}
        builtins_exec = __builtins__["exec"] if isinstance(__builtins__, dict) else getattr(__builtins__, "exec")
        builtins_exec(co, ns)
        assert ns["c"] == 3

    def test_syntax_error_raises(self):
        with pytest.raises(SyntaxError):
            self._compile("if if if")

    def test_simple_expression(self):
        co = self._compile("x = 42")
        ns = {}
        builtins_exec = __builtins__["exec"] if isinstance(__builtins__, dict) else getattr(__builtins__, "exec")
        builtins_exec(co, ns)
        assert ns["x"] == 42


# ===========================================================================
# re_player regex
# ===========================================================================

class TestRePlayerRegex:
    """Tests for the re_player regex that matches player definitions."""

    @pytest.fixture
    def regex(self):
        from FoxDot.lib.Code.main_lib import re_player
        return re_player

    def test_basic_player(self, regex):
        m = regex.match("p1 >> pads()")
        assert m is not None
        assert m.group(2) == "p1"

    def test_whitespace_prefix(self, regex):
        m = regex.match("    p1 >> pads()")
        assert m is not None
        assert m.group(1) == "    "
        assert m.group(2) == "p1"

    def test_no_whitespace(self, regex):
        m = regex.match("d1 >> play()")
        assert m is not None
        assert m.group(1) == ""
        assert m.group(2) == "d1"

    def test_complex_player_name(self, regex):
        m = regex.match("myPlayer >> bass()")
        assert m is not None
        assert m.group(2) == "myPlayer"

    def test_no_match_for_assignment(self, regex):
        m = regex.match("x = 42")
        assert m is None

    def test_no_match_for_comment(self, regex):
        m = regex.match("# p1 >> pads()")
        assert m is None

    def test_tab_whitespace(self, regex):
        m = regex.match("\tp1 >> pads()")
        assert m is not None
        assert m.group(1) == "\t"


# ===========================================================================
# Module introspection helpers
# ===========================================================================

class TestModuleIntrospection:
    """Tests for classes(), instances(), functions() helpers."""

    def _make_module(self):
        """Create a mock module with known contents."""
        mod = types.ModuleType("test_mod")

        class MyClass:
            pass

        def my_func():
            pass

        mod.MyClass = MyClass
        mod.my_func = my_func
        mod.my_instance = MyClass()
        mod.some_int = 42
        return mod, MyClass

    def test_classes_finds_class(self):
        from FoxDot.lib.Code.main_lib import classes
        mod, MyClass = self._make_module()
        result = classes(mod)
        assert "MyClass" in result

    def test_classes_excludes_function(self):
        from FoxDot.lib.Code.main_lib import classes
        mod, _ = self._make_module()
        result = classes(mod)
        assert "my_func" not in result

    def test_functions_finds_function(self):
        from FoxDot.lib.Code.main_lib import functions
        mod, _ = self._make_module()
        result = functions(mod)
        assert "my_func" in result

    def test_functions_excludes_class(self):
        from FoxDot.lib.Code.main_lib import functions
        mod, _ = self._make_module()
        result = functions(mod)
        assert "MyClass" not in result

    def test_instances_finds_instance(self):
        from FoxDot.lib.Code.main_lib import instances
        mod, MyClass = self._make_module()
        result = instances(mod, MyClass)
        assert "my_instance" in result

    def test_instances_excludes_non_instance(self):
        from FoxDot.lib.Code.main_lib import instances
        mod, MyClass = self._make_module()
        result = instances(mod, MyClass)
        assert "some_int" not in result
        assert "my_func" not in result


# ===========================================================================
# get_now()
# ===========================================================================

class TestGetNow:
    """Tests for main_lib.get_now()."""

    def _call(self, obj):
        from FoxDot.lib.Code.main_lib import get_now
        return get_now(obj)

    def test_plain_int(self):
        assert self._call(42) == 42

    def test_plain_string(self):
        assert self._call("hello") == "hello"

    def test_plain_list(self):
        assert self._call([1, 2, 3]) == [1, 2, 3]

    def test_object_with_now_method(self):
        class TimeVarLike:
            def now(self):
                return 99

        assert self._call(TimeVarLike()) == 99

    def test_none(self):
        assert self._call(None) is None


# ===========================================================================
# write_to_file()
# ===========================================================================

class TestWriteToFile:
    """Tests for main_lib.write_to_file()."""

    def _call(self, fn, text):
        from FoxDot.lib.Code.main_lib import write_to_file
        return write_to_file(fn, text)

    def test_writes_content(self, tmp_path):
        p = tmp_path / "out.py"
        self._call(str(p), "x = 1")
        assert p.read_text() == "x = 1"

    def test_cleans_lambda_unicode(self, tmp_path):
        p = tmp_path / "out.py"
        self._call(str(p), "f = \u03BB x: x")
        assert p.read_text() == "f = lambda x: x"

    def test_invalid_path_prints_error(self, capsys):
        self._call("/nonexistent/dir/file.py", "content")
        captured = capsys.readouterr()
        assert "Unable to write" in captured.out

    def test_overwrite_existing(self, tmp_path):
        p = tmp_path / "out.py"
        p.write_text("old content")
        self._call(str(p), "new content")
        assert p.read_text() == "new content"


# ===========================================================================
# WarningMsg()
# ===========================================================================

class TestWarningMsg:
    """Tests for main_lib.WarningMsg()."""

    def test_single_arg(self, capsys):
        from FoxDot.lib.Code.main_lib import WarningMsg
        WarningMsg("something broke")
        captured = capsys.readouterr()
        assert "Warning: something broke" in captured.out

    def test_multiple_args(self, capsys):
        from FoxDot.lib.Code.main_lib import WarningMsg
        WarningMsg("file", "not", "found")
        captured = capsys.readouterr()
        assert "Warning: file not found" in captured.out


# ===========================================================================
# _live_function
# ===========================================================================

class TestLiveFunction:
    """Tests for Code.foxdot_live_function._live_function."""

    def _make(self, func, dependency=None):
        from FoxDot.lib.Code.foxdot_live_function import _live_function
        return _live_function(func, dependency)

    def test_init_stores_func(self):
        def f():
            return 1
        lf = self._make(f)
        assert lf.func is f

    def test_init_stores_name(self):
        def my_function():
            pass
        lf = self._make(my_function)
        assert lf.name == "my_function"

    def test_init_not_live(self):
        lf = self._make(lambda: None)
        assert lf.live is False

    def test_init_dependency_none(self):
        lf = self._make(lambda: None)
        assert lf.dependency is None

    def test_call_returns_result(self):
        def f(x):
            return x * 2
        lf = self._make(f)
        assert lf(5) == 10

    def test_call_sets_live_true(self):
        lf = self._make(lambda: 42)
        lf()
        assert lf.live is True

    def test_call_with_args_and_kwargs(self):
        def f(a, b, c=10):
            return a + b + c
        lf = self._make(f)
        assert lf(1, 2, c=3) == 6

    def test_update_replaces_func(self):
        def f1():
            return 1
        def f2():
            return 2
        lf = self._make(f1)
        lf.update(f2)
        assert lf() == 2

    def test_update_with_dependency(self):
        def f1():
            return 1
        dep = self._make(lambda: None)
        lf = self._make(f1)
        lf.update(f1, dep)
        assert lf.dependency is dep

    def test_dependency_set_not_live_on_call(self):
        dep = self._make(lambda: None)
        dep.live = True
        lf = self._make(lambda: 42, dependency=dep)
        lf()
        assert dep.live is False

    def test_no_dependency_does_not_crash(self):
        lf = self._make(lambda: 1, dependency=None)
        lf()  # should not raise


# ===========================================================================
# livefunction decorator
# ===========================================================================

class TestLivefunctionDecorator:
    """Tests for the livefunction() decorator."""

    def setup_method(self):
        """Clear the live functions dict before each test."""
        from FoxDot.lib.Code import foxdot_live_function
        foxdot_live_function._live_functions_dict.clear()

    def test_wraps_function(self):
        from FoxDot.lib.Code.foxdot_live_function import livefunction, _live_function

        @livefunction
        def my_func():
            return 42
        assert isinstance(my_func, _live_function)

    def test_first_call_not_live(self):
        from FoxDot.lib.Code.foxdot_live_function import livefunction

        @livefunction
        def my_func():
            return 42
        assert my_func.live is False

    def test_after_calling_becomes_live(self):
        from FoxDot.lib.Code.foxdot_live_function import livefunction

        @livefunction
        def my_func():
            return 42
        my_func()
        assert my_func.live is True

    def test_re_wrapping_updates_function(self):
        from FoxDot.lib.Code.foxdot_live_function import livefunction, _live_functions_dict

        @livefunction
        def evolving():
            return 1

        evolving()  # now live

        # "Re-define" the same function name
        @livefunction
        def evolving():
            return 2

        # The live function should have been updated and re-called
        # because it was live
        assert evolving() == 2

    def test_added_to_dict(self):
        from FoxDot.lib.Code.foxdot_live_function import livefunction, _live_functions_dict

        @livefunction
        def tracked():
            return 1

        assert "tracked" in _live_functions_dict

    def test_return_value(self):
        from FoxDot.lib.Code.foxdot_live_function import livefunction

        @livefunction
        def adder(a, b):
            return a + b

        assert adder(3, 4) == 7


# ===========================================================================
# _whenStatement
# ===========================================================================

class TestWhenStatement:
    """Tests for _whenStatement from foxdot_when_statement."""

    def _make(self, func=None):
        from FoxDot.lib.Code.foxdot_when_statement import _whenStatement
        if func is None:
            return _whenStatement()
        return _whenStatement(func)

    def test_default_expr_is_true(self):
        ws = self._make()
        assert ws.expr() is True

    def test_custom_expr(self):
        ws = self._make(lambda: False)
        assert ws.expr() is False

    def test_reset_clears_actions(self):
        ws = self._make()
        ws.action = lambda: 42
        ws.notaction = lambda: 99
        ws.reset()
        assert ws.action() is None
        assert ws.notaction() is None
        assert ws.do_switch is False
        assert ws.elsedo_switch is False

    def test_remove_sets_flag(self):
        ws = self._make()
        ws.remove()
        assert ws.remove_me is True

    def test_stop_resets(self):
        ws = self._make()
        ws.do_switch = True
        ws.stop()
        assert ws.do_switch is False

    def test_when_sets_expr(self):
        ws = self._make()
        new_expr = lambda: 42
        ws.when(new_expr)
        assert ws.expr is new_expr

    def test_then_sets_action(self):
        ws = self._make()
        action = lambda: "do"
        result = ws.then(action)
        assert ws.action is action
        assert result is ws  # returns self for chaining

    def test_elsedo_sets_notaction(self):
        ws = self._make()
        notaction = lambda: "dont"
        result = ws.elsedo(notaction)
        assert ws.notaction is notaction
        assert result is ws

    def test_evaluate_true_branch(self):
        calls = []
        ws = self._make(lambda: True)
        ws.action = lambda: calls.append("do")
        ws.notaction = lambda: calls.append("else")

        ws.evaluate()
        assert calls == ["do"]
        assert ws.do_switch is True

    def test_evaluate_false_branch(self):
        calls = []
        ws = self._make(lambda: False)
        ws.action = lambda: calls.append("do")
        ws.notaction = lambda: calls.append("else")

        ws.evaluate()
        assert calls == ["else"]
        assert ws.elsedo_switch is True

    def test_evaluate_true_only_fires_once(self):
        calls = []
        ws = self._make(lambda: True)
        ws.action = lambda: calls.append("do")

        ws.evaluate()
        ws.evaluate()
        assert calls == ["do"]  # only once

    def test_evaluate_false_only_fires_once(self):
        calls = []
        ws = self._make(lambda: False)
        ws.notaction = lambda: calls.append("else")

        ws.evaluate()
        ws.evaluate()
        assert calls == ["else"]

    def test_evaluate_switches_on_state_change(self):
        state = [True]
        calls = []
        ws = self._make(lambda: state[0])
        ws.action = lambda: calls.append("do")
        ws.notaction = lambda: calls.append("else")

        ws.evaluate()  # True -> fires "do"
        state[0] = False
        ws.evaluate()  # False -> fires "else"
        state[0] = True
        ws.evaluate()  # True again -> fires "do"

        assert calls == ["do", "else", "do"]

    def test_toggle_live_functions_true(self):
        class FakeLive:
            live = False
        ws = self._make()
        ws.action = FakeLive()
        ws.notaction = FakeLive()
        ws.toggle_live_functions(True)
        assert ws.action.live is True
        assert ws.notaction.live is False

    def test_toggle_live_functions_false(self):
        class FakeLive:
            live = True
        ws = self._make()
        ws.action = FakeLive()
        ws.notaction = FakeLive()
        ws.toggle_live_functions(False)
        assert ws.action.live is False
        assert ws.notaction.live is True

    def test_toggle_live_functions_no_attr_ok(self):
        """Plain lambdas don't have .live -- should not raise."""
        ws = self._make()
        ws.action = lambda: None
        ws.notaction = lambda: None
        ws.toggle_live_functions(True)  # should not raise

    def test_context_manager(self):
        from FoxDot.lib.Code.foxdot_when_statement import when
        ws = self._make()
        with ws:
            assert when.editing is ws
        assert when.editing is None

    def test_set_namespace(self):
        from FoxDot.lib.Code.foxdot_when_statement import _whenStatement
        ns = {"x": 1}
        _whenStatement.set_namespace(ns)
        assert _whenStatement.namespace is ns
        # Clean up
        _whenStatement.set_namespace({})


# ===========================================================================
# _whenLibrary
# ===========================================================================

class TestWhenLibrary:
    """Tests for _whenLibrary from foxdot_when_statement."""

    def _make(self):
        from FoxDot.lib.Code.foxdot_when_statement import _whenLibrary
        return _whenLibrary()

    def test_init_empty(self):
        wl = self._make()
        assert len(wl) == 0

    def test_call_creates_statement(self):
        from FoxDot.lib.Code.foxdot_when_statement import _whenStatement
        wl = self._make()
        # Monkey-patch start_thread to avoid actual threading
        wl.start_thread = lambda: None
        result = wl("test_expr")
        assert isinstance(result, _whenStatement)
        assert len(wl) == 1

    def test_call_same_name_returns_existing(self):
        wl = self._make()
        wl.start_thread = lambda: None
        s1 = wl("expr1")
        s2 = wl("expr1")
        assert s1 is s2

    def test_call_different_names(self):
        wl = self._make()
        wl.start_thread = lambda: None
        s1 = wl("a")
        s2 = wl("b")
        assert s1 is not s2
        assert len(wl) == 2

    def test_reset_clears_library(self):
        wl = self._make()
        wl.start_thread = lambda: None
        wl("a")
        wl("b")
        assert len(wl) == 2
        wl.reset()
        assert len(wl) == 0

    def test_repr(self):
        wl = self._make()
        # repr should not crash
        r = repr(wl)
        assert isinstance(r, str)

    def test_editing_starts_none(self):
        wl = self._make()
        assert wl.editing is None

    def test_a_helper_with_editing(self):
        wl = self._make()
        wl.start_thread = lambda: None
        ws = wl("test")
        wl.editing = ws
        new_expr = lambda: 42
        wl.a(new_expr)
        assert ws.expr is new_expr
        wl.editing = None

    def test_a_helper_without_editing(self):
        wl = self._make()
        # Should not raise when no editing target
        result = wl.a(lambda: 1)
        assert result is None

    def test_c_helper_with_editing(self):
        wl = self._make()
        wl.start_thread = lambda: None
        ws = wl("test")
        wl.editing = ws
        else_fn = lambda: "else"
        wl.c(else_fn)
        assert ws.notaction is else_fn
        wl.editing = None
