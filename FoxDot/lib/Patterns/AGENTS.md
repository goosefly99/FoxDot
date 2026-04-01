# Patterns Module (`lib/Patterns/`)

## Overview

The pattern system is FoxDot's core musical abstraction. Patterns are list-like containers with special behaviors: wrapping index access, arithmetic broadcasting, nested expansion, and time-dependent evaluation.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `Main.py` (54KB) | Core Pattern and PGroup classes | `metaPattern`, `Pattern`, `PGroup`, `PatternMethod` |
| `Operations.py` | Arithmetic operator implementation | `PAdd`, `PSub`, `PMul`, `PDiv`, etc. |
| `Sequences.py` (12KB) | Pattern generators and utilities | `P`, `PShuf`, `PAlt`, `PStretch`, `PPairs`, `PZip`, `PDur`, `PEuclid`, etc. |
| `PGroups.py` (8KB) | Grouped pattern operations | `PGroupStar`, `PGroupPlus`, etc. |
| `Generators.py` (10KB) | Generator-based patterns | `GeneratorPattern`, `Pvar`, `Cycle`, `Rand`, `PRand`, `PWhite` |
| `PlayString.py` | Sample rhythm parser | Parses `"x-o-"` syntax for `play` SynthDef |
| `Parse.py` | Pattern literal parser | Parses `P[0,1,2,3]` syntax |
| `Utils.py` | Pattern utilities | Helper functions for pattern manipulation |

## Core Concepts

### Pattern
A `Pattern` behaves like a list but with musical semantics:
- **Wrapping access:** `P[0,1,2][5]` returns `P[0,1,2][5 % 3]` = `2`
- **Arithmetic broadcasting:** `P[0,1,2] + 3` = `P[3,4,5]`
- **Nesting:** `P[0,1,[2,3]]` expands to `P[0,1,2,0,1,3]` over time
- **Operator chaining:** All arithmetic returns new Patterns

### PGroup
A `PGroup` returns all values simultaneously (polyphony) instead of alternating:
- `PGroup(0,2,4)` plays all three notes at once (a chord)
- Arithmetic on PGroups applies to each element

### GeneratorPattern
Infinite patterns that compute values on demand:
- `PRand([0,1,2])` — random selection each beat
- `PWhite(0, 7)` — random float in range
- `Cycle` — repeating sequence

### PlayString
Parses rhythm notation for the `play` SynthDef:
- `"x-o-"` = kick, rest, snare, rest
- `"(xo)"` = both simultaneously
- `"[xx]"` = subdivide beat
- `"{xo}"` = alternate each cycle

## Class Hierarchy

```
metaPattern (abstract base)
├── Pattern (list-based)
│   ├── PGroup (simultaneous values)
│   │   ├── PGroupStar
│   │   ├── PGroupPlus
│   │   └── PGroupPrime
│   └── PatternContainer
└── GeneratorPattern (infinite/computed)
    ├── Pvar (time-varying)
    ├── PRand (random selection)
    ├── PWhite (random range)
    └── Cycle (repeating)
```

## Decorators

- `@loop_pattern_func` — Makes a function work element-wise on Patterns
- `@loop_pattern_method` — Same for methods
- `@PatternMethod` — Registers a function as a method on all Pattern types
- `@ClassPatternMethod` — Registers as a classmethod

## Integration Points

- **Players:** Every Player attribute (degree, dur, amp, oct, etc.) is a Pattern
- **TimeVar:** `Pvar` bridges Patterns with time-varying behavior
- **Scale:** Pattern values are interpreted as scale degrees by Players
- **Clock:** Pattern index advances with each beat

## Implementation Requirements

### No Changes Needed for Python 3.13
The Pattern system uses only standard Python features: lists, arithmetic operators, `functools`, `itertools`, `inspect.getfullargspec()`. All are available in 3.13.

### Potential Enhancements
- Consider adding `__match_args__` for Python 3.10+ structural pattern matching support
- The PlayString parser could benefit from type hints for editor integration
