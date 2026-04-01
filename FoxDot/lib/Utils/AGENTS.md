# Utils Module (`lib/Utils/`)

## Overview

General-purpose utility functions used across the FoxDot codebase. Covers version checking, math helpers, Euclidean rhythm generation, and type introspection.

## Key Exports (`__init__.py`)

| Function | Purpose |
|----------|---------|
| `get_pypi_version()` | Check PyPI for newer FoxDot version (uses `urllib.request`) |
| `stdout(*args)` | Formatted print to stdout |
| `sliceToRange(s, length)` | Convert slice to range object |
| `LCM(a, b)` | Lowest common multiple |
| `EuclidsAlgorithm(n, k)` | Generate Euclidean rhythms (evenly distributed beats) |
| `modi(array, index)` | Modulo-wrapping index access (core to Pattern system) |
| `get_expanded_len(data)` | Calculate length of nested Pattern after expansion |
| `isiterable(obj)` | Type check for iterables |
| `dots(n)` | String representation helper |

## Euclidean Rhythms

`EuclidsAlgorithm(pulses, steps)` generates rhythms by distributing `pulses` beats as evenly as possible across `steps` slots. This is a fundamental tool in algorithmic composition:
- `EuclidsAlgorithm(3, 8)` = `[1,0,0,1,0,0,1,0]` (Cuban tresillo)
- `EuclidsAlgorithm(5, 8)` = `[1,0,1,1,0,1,1,0]` (West African bell pattern)

## Python 3.13 Migration

- **Lines 15–19:** Conditional import `urllib.request` (Py3) vs `urllib2` (Py2). Remove the Py2 path.
- `get_pypi_version()` makes an HTTP request to PyPI. Consider whether to keep this in the fork (the fork won't be on PyPI initially).
