# Workspace Module (`lib/Workspace/`) — GUI Editor

## Overview

The Tkinter-based GUI editor for FoxDot. **This module is slated for replacement** — see ADR-001 Decision 2 (Frontend Editor). The fork will use Flok (browser-based) initially and a custom Tauri+CodeMirror 6 editor long-term.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `Editor.py` (52KB) | Main workspace class | `workspace` — the primary GUI application |
| `Console.py` (13KB) | Output console/REPL | Console widget for stdout display |
| `MenuBar.py` (10KB) | Menu system | Code, File, Help menus |
| `TextBox.py` (4KB) | Thread-safe text widget | `ThreadedText` — Tkinter Text with thread safety |
| `BracketHandler.py` (7KB) | Auto-bracket matching | Bracket highlight and completion |
| `Format.py` (7KB) | Syntax highlighting | FoxDot-specific keyword coloring |
| `LineNumbers.py` | Line number display | Gutter line numbers |
| `Prompt.py` (5KB) | Dialog prompts | User input dialogs |
| `AppFunctions.py` (2KB) | GUI callback utilities | Helper functions for editor actions |
| `ConfigFile.py` | Configuration file handling | User preference storage and retrieval |
| `tkimport.py` | Tkinter version abstraction | Handles `tkinter` (Py3) vs `Tkinter` (Py2) |
| `Simple/` | wxPython alternative editor | `SimpleEditor`, `SimpleMenu`, `SimpleText` |
| `img/` | GUI icons and images | FoxDot icon resources |
| `tmp/` | Temporary files | Work recovery files |

## Key Interactions

```
workspace.__init__(CodeClass=FoxDotCode)
  ├── Creates Tkinter root window
  ├── Creates ThreadedText editor widget
  ├── Creates Console output widget
  ├── Creates MenuBar
  ├── Binds Ctrl+Return → execute code block
  └── workspace.run() → starts Tkinter mainloop
```

### Code Execution Flow
1. User selects code block (or cursor position determines block)
2. Ctrl+Return fires `execute` callback
3. Code string extracted from TextBox
4. Passed to `FoxDotCode.__call__(code_string)`
5. Output displayed in Console

## Platform-Specific Code

- **Windows DPI:** `Editor.py` lines 10–14 call `windll.shcore.SetProcessDpiAwareness(1)` via ctypes
- **Tkinter import:** `tkimport.py` handles Py2/Py3 module name differences
- **Simple mode:** `Simple/` subdirectory uses wxPython instead of Tkinter (activated with `--simple` flag)

## Fork Strategy

> See `docs/architecture/HANDOFF-02-repl-interface.md` for the REPL module that decouples code execution from this editor.

### Phase 1: Keep As-Is
The Tkinter editor still works on Python 3.13. Keep it functional as a fallback during migration.

### Phase 2A: Flok Integration
Instead of modifying this module, use Flok's browser-based editor with `flok-repl -t foxdot`. The Workspace module becomes optional.

### Phase 4: Custom Editor (Tauri + CodeMirror 6)
The long-term replacement. This module's responsibilities inform what the new editor must support:
- Code block detection and execution
- Syntax highlighting (see `Format.py` for keyword lists)
- Line number tracking for Players (see `FoxDotCode.update_line_numbers()`)
- Console output display
- Flash-on-eval visual feedback
- File operations (open, save, recovery)

### What to Extract Before Replacing
- **Keyword lists** from `Format.py` — needed for any new syntax highlighter
- **Code block detection logic** from `Editor.py` — determines what gets executed on Ctrl+Return
- **Player line tracking** — maps editor lines to Player objects for debugging
