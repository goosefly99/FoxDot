# EspGrid Module (`lib/EspGrid/`)

## Overview

Network synchronization for ensemble live coding performances. Connects FoxDot to EspGrid, a UDP-based clock synchronization system that allows multiple performers on separate machines to share a common tempo.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Module exports |
| `EspGridHelper.py` | UDP client for EspGrid protocol |

## How It Works

EspGrid maintains a shared clock across networked machines. The `EspGrid` class:
1. Connects to a running EspGrid server via UDP
2. Receives tempo/beat synchronization messages
3. Adjusts FoxDot's `Clock` to match the shared time

This enables multiple FoxDot (or TidalCycles, Sonic Pi, etc.) instances to play in sync across a network.

## Integration Points

- **TempoClock:** EspGrid adjusts the Clock's beat position and BPM
- **ServerManager:** May relay sync messages to SuperCollider

## Implementation Notes

### For the Fork
- EspGrid is an external application that must be installed separately
- This module is optional — FoxDot works without it
- Consider whether Flok's built-in collaboration (Phase 2A) replaces the need for EspGrid sync
- If keeping, verify UDP socket code works on Python 3.13 (should be fine — standard `socket` module)
