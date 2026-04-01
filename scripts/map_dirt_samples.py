#!/usr/bin/env python3
"""Map Dirt-Samples into FoxDot's snd/ directory structure.

Copies WAV files from a Dirt-Samples clone into the FoxDot sample bank,
mapping each Dirt-Samples folder to a FoxDot character slot.

FoxDot's sample layout:
    snd/<char>/lower/   -> samples triggered by lowercase char in play()
    snd/<char>/upper/   -> samples triggered by uppercase char in play()

Usage:
    python scripts/map_dirt_samples.py --dirt-samples /path/to/Dirt-Samples
    python scripts/map_dirt_samples.py --dirt-samples /path/to/Dirt-Samples --dry-run
    python scripts/map_dirt_samples.py --dirt-samples /path/to/Dirt-Samples --clean

Options:
    --dirt-samples DIR   Path to the cloned Dirt-Samples repository
    --snd DIR            Path to FoxDot snd/ directory (auto-detected if omitted)
    --dry-run            Show what would be copied without copying
    --clean              Remove previously mapped Dirt-Samples before re-mapping
    --list-mapping       Print the mapping table and exit
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Mapping: FoxDot character -> Dirt-Samples folder name
#
# Design principles:
#   - Lowercase letters map to primary sounds (kicks, snares, hats, etc.)
#   - Uppercase letters map to variations or related sounds
#   - Non-alpha characters (&, *, @, etc.) map to FX / one-shots / textures
#   - We only map to slots where adding Dirt-Samples makes musical sense
#     alongside the existing FoxDot samples. Existing samples are NEVER
#     overwritten — Dirt-Samples are appended with a "dirt_" filename prefix.
#
# The character descriptions in Buffers.py inform which Dirt-Samples
# folders are a good semantic fit for each slot.
# ---------------------------------------------------------------------------

# (foxdot_char, case) -> dirt_samples_folder
# case: "lower" or "upper"
MAPPING = {
    # === Kick drums ===
    # x = "Bass drum", X = "Heavy kick" in FoxDot
    ("x", "lower"): "bd",           # standard bass drums
    ("x", "upper"): "hardkick",     # hard kicks

    # v = "Soft kick", V = "Hard kick"
    ("v", "lower"): "clubkick",     # club kicks
    ("v", "upper"): "808bd",        # 808 bass drums

    # === Snare drums ===
    # o = "Snare drum", O = "Heavy snare"
    ("o", "lower"): "sd",           # standard snares
    ("o", "upper"): "808sd",        # 808 snares

    # i = "Jungle snare", I = "Rock snare"
    ("i", "lower"): "sn",           # snare variants
    ("i", "upper"): "drum",         # acoustic drum hits

    # === Hi-hats ===
    # '-' = "Hi hat closed" in FoxDot (nonalpha)
    # h = "Finger snaps", H = "Clap"
    ("h", "lower"): "hh",           # closed hi-hats
    ("h", "upper"): "cp",           # claps (H is already "Clap")

    # === Open hi-hats ===
    # Using nonalpha '-' for closed, let's put open hats on tilde
    ("~", "tilde"): "808oh",         # open hi-hats (808)

    # === Percussion ===
    # t = "Rimshot", T = "Cowbell"
    ("t", "lower"): "rm",           # rimshots
    ("t", "upper"): "cb",           # cowbell

    # m = "808 toms", M = "Acoustic toms"
    ("m", "lower"): "808mt",        # 808 mid toms
    ("m", "upper"): "ht",           # high toms

    # p = "Tabla", P = "Tabla long"
    ("p", "lower"): "tabla",        # tabla hits
    ("p", "upper"): "tabla2",       # tabla long

    # e = "Electronic Cowbell", E = "Ringing percussion"
    ("e", "lower"): "co",           # cowbell / click
    ("e", "upper"): "perc",         # misc percussion

    # y = "Percussive hits", Y = "High buzz"
    ("y", "lower"): "tok",          # percussive tok hits
    ("y", "upper"): "tink",         # tink / metallic

    # === Cymbals ===
    # r = "Metal", R = "Metallic"
    ("r", "lower"): "cr",           # crash cymbals
    ("r", "upper"): "metal",        # metallic sounds

    # === Shakers ===
    # s = "Shaker", S = "Tamborine"
    ("s", "lower"): "future",       # future percussion
    ("s", "upper"): "hand",         # hand percussion

    # === Bass ===
    # b = "Noisy beep", B = "Short saw"
    ("b", "lower"): "bass",         # bass hits
    ("b", "upper"): "bass3",        # bass variant

    # === Electronic ===
    # n = "Noise", N = "Gameboy SFX"
    ("n", "lower"): "noise",        # noise
    ("n", "upper"): "glitch",       # glitch sounds

    # a = "Gameboy hihat", A = "Gameboy kick drum"
    ("a", "lower"): "electro1",     # electro hits
    ("a", "upper"): "gabba",        # gabba kicks

    # === FX / Textures ===
    # q = "Ambient stabs", Q = "Electronic stabs"
    ("q", "lower"): "pad",          # pad sounds
    ("q", "upper"): "stab",         # stab sounds

    # g = "Ominous", G = "Ambient stabs"
    ("g", "lower"): "space",        # space textures
    ("g", "upper"): "industrial",   # industrial sounds

    # w = "Dub hits", W = "Distorted"
    ("w", "lower"): "wobble",       # wobble bass/dub
    ("w", "upper"): "dist",         # distorted hits

    # u = "Soft snare", U = "Misc. Fx"
    ("u", "lower"): "popkick",      # pop kicks
    ("u", "upper"): "tech",         # tech sounds

    # f = "Pops", F = "Trumpet stabs"
    ("f", "lower"): "feel",         # feel sounds
    ("f", "upper"): "fm",           # FM synth hits

    # j = "Whines", J = "Ambient stabs"
    ("j", "lower"): "juno",         # juno synth
    ("j", "upper"): "jazz",         # jazz samples

    # l = "Robot noise", L = "Noisy percussive hits"
    ("l", "lower"): "lighter",      # lighter sounds
    ("l", "upper"): "less",         # less aggressive

    # k = "Wood shaker", K = "Percussive hits"
    ("k", "lower"): "click",        # clicks
    ("k", "upper"): "casio",        # casio sounds

    # c = "Voice/string", C = "Choral"
    ("c", "lower"): "chin",         # vocal/string-like
    ("c", "upper"): "mouth",        # mouth sounds

    # d = "Woodblock", D = "Dirty snare"
    ("d", "lower"): "dr",           # drum machine
    ("d", "upper"): "drumtraks",    # drumtraks

    # z = "Scratch", Z = "Loud stabs"
    ("z", "lower"): "rave",         # rave hits
    ("z", "upper"): "hardcore",     # hardcore stabs

    # === Non-alpha slots ===
    # '-' = "Hi hat closed"
    ("-", "hyphen"): "hh27",        # hi-hat 27 set

    # '=' = currently unused/empty in many installs
    ("=", "equals"): "breaks157",   # breakbeat loops

    # '#' = "hash"
    ("#", "hash"): "909",           # 909 drum machine

    # '$' = "dollar"
    ("$", "dollar"): "808",         # 808 drum machine

    # '+' = "plus"
    ("+", "plus"): "arp",           # arpeggiated sounds

    # '!' = "exclamation"
    ("!", "exclamation"): "blip",    # blip sounds

    # '*' = "asterix"
    ("*", "asterix"): "sid",        # SID chip sounds

    # '@' = "at"
    ("@", "at"): "arpy",            # arpy sounds
}

# Sentinel prefix to identify Dirt-Samples files (for --clean)
DIRT_PREFIX = "dirt_"


def find_foxdot_snd() -> Path:
    """Auto-detect the FoxDot snd/ directory relative to this script."""
    script_dir = Path(__file__).resolve().parent
    # scripts/ is sibling to FoxDot/ package dir
    candidates = [
        script_dir.parent / "FoxDot" / "snd",
        script_dir.parent / "snd",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def resolve_target_dir(snd_root: Path, char: str, case: str) -> Path:
    """Return the snd/ subdirectory for a mapping entry."""
    if char.isalpha():
        return snd_root / char.lower() / case
    else:
        # Non-alpha: snd/_/<named_dir>/
        # The case field doubles as the directory name for non-alpha chars
        return snd_root / "_" / case


def collect_wav_files(dirt_folder: Path) -> list[Path]:
    """Return sorted list of WAV files in a Dirt-Samples subfolder."""
    if not dirt_folder.is_dir():
        return []
    wavs = sorted(
        p for p in dirt_folder.iterdir()
        if p.suffix.lower() == ".wav" and p.is_file()
    )
    return wavs


def copy_samples(
    dirt_root: Path,
    snd_root: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict:
    """Copy Dirt-Samples into FoxDot snd/ structure.

    Returns a summary dict with counts.
    """
    stats = {"folders": 0, "files": 0, "skipped": 0, "errors": []}

    for (char, case), dirt_folder_name in sorted(MAPPING.items()):
        dirt_folder = dirt_root / dirt_folder_name
        wavs = collect_wav_files(dirt_folder)

        if not wavs:
            if verbose:
                print(f"  SKIP {char}({case}) <- {dirt_folder_name}/ (no WAVs found)")
            stats["skipped"] += 1
            continue

        target_dir = resolve_target_dir(snd_root, char, case)

        if verbose:
            print(f"  {char}({case}) <- {dirt_folder_name}/ ({len(wavs)} files) -> {target_dir}")

        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        stats["folders"] += 1

        for wav in wavs:
            dest_name = f"{DIRT_PREFIX}{wav.name}"
            dest_path = target_dir / dest_name

            if dest_path.exists():
                continue  # already mapped, skip

            stats["files"] += 1
            if not dry_run:
                try:
                    shutil.copy2(wav, dest_path)
                except OSError as e:
                    stats["errors"].append(f"{wav} -> {dest_path}: {e}")

    return stats


def clean_dirt_samples(snd_root: Path, dry_run: bool = False, verbose: bool = True) -> int:
    """Remove all files with the DIRT_PREFIX from snd/."""
    removed = 0
    for root, _dirs, files in os.walk(snd_root):
        for f in files:
            if f.startswith(DIRT_PREFIX):
                path = Path(root) / f
                if verbose:
                    print(f"  DELETE {path}")
                if not dry_run:
                    path.unlink()
                removed += 1
    return removed


def print_mapping_table():
    """Print the full mapping in a readable table."""
    print(f"\n{'Char':<6} {'Case':<8} {'Dirt-Samples Folder':<20} {'FoxDot Description'}")
    print("-" * 65)

    # Import descriptions inline to avoid dependency issues
    descriptions = {
        'a': "Gameboy hihat",      'A': "Gameboy kick drum",
        'b': "Noisy beep",         'B': "Short saw",
        'c': "Voice/string",       'C': "Choral",
        'd': "Woodblock",          'D': "Dirty snare",
        'e': "Electronic Cowbell", 'E': "Ringing percussion",
        'f': "Pops",               'F': "Trumpet stabs",
        'g': "Ominous",            'G': "Ambient stabs",
        'h': "Finger snaps",       'H': "Clap",
        'i': "Jungle snare",       'I': "Rock snare",
        'j': "Whines",             'J': "Ambient stabs",
        'k': "Wood shaker",        'K': "Percussive hits",
        'l': "Robot noise",        'L': "Noisy percussive hits",
        'm': "808 toms",           'M': "Acoustic toms",
        'n': "Noise",              'N': "Gameboy SFX",
        'o': "Snare drum",         'O': "Heavy snare",
        'p': "Tabla",              'P': "Tabla long",
        'q': "Ambient stabs",      'Q': "Electronic stabs",
        'r': "Metal",              'R': "Metallic",
        's': "Shaker",             'S': "Tamborine",
        't': "Rimshot",            'T': "Cowbell",
        'u': "Soft snare",         'U': "Misc. Fx",
        'v': "Soft kick",          'V': "Hard kick",
        'w': "Dub hits",           'W': "Distorted",
        'x': "Bass drum",          'X': "Heavy kick",
        'y': "Percussive hits",    'Y': "High buzz",
        'z': "Scratch",            'Z': "Loud stabs",
        '-': "Hi hat closed",      '~': "Tilde",
        '=': "Equals",             '#': "Hash",
        '$': "Dollar",             '+': "Plus",
        '!': "Exclamation",        '*': "Asterix",
        '@': "At",
    }

    for (char, case), dirt_folder in sorted(MAPPING.items(), key=lambda x: (x[0][0].lower(), x[0][1])):
        lookup = char.upper() if case == "upper" else char
        desc = descriptions.get(lookup, "—")
        print(f"{char!r:<6} {case:<8} {dirt_folder:<20} {desc}")


def main():
    parser = argparse.ArgumentParser(
        description="Map Dirt-Samples into FoxDot's snd/ directory structure."
    )
    parser.add_argument(
        "--dirt-samples",
        type=Path,
        help="Path to the cloned Dirt-Samples repository",
    )
    parser.add_argument(
        "--snd",
        type=Path,
        default=None,
        help="Path to FoxDot snd/ directory (auto-detected if omitted)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without actually copying",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove previously mapped Dirt-Samples (files with 'dirt_' prefix)",
    )
    parser.add_argument(
        "--list-mapping",
        action="store_true",
        help="Print the mapping table and exit",
    )

    args = parser.parse_args()

    if args.list_mapping:
        print_mapping_table()
        return

    snd_root = args.snd or find_foxdot_snd()

    if not snd_root.is_dir():
        print(f"ERROR: snd/ directory not found at {snd_root}", file=sys.stderr)
        sys.exit(1)

    print(f"FoxDot snd/ directory: {snd_root}")

    if args.clean:
        print("\nCleaning previously mapped Dirt-Samples...")
        count = clean_dirt_samples(snd_root, dry_run=args.dry_run)
        action = "would remove" if args.dry_run else "removed"
        print(f"\n{action.capitalize()} {count} file(s).")
        if not args.dirt_samples:
            return

    if not args.dirt_samples:
        parser.error("--dirt-samples is required (unless using --list-mapping or --clean only)")

    dirt_root = args.dirt_samples.resolve()
    if not dirt_root.is_dir():
        print(f"ERROR: Dirt-Samples directory not found at {dirt_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Dirt-Samples directory: {dirt_root}")
    mode = "DRY RUN" if args.dry_run else "COPYING"
    print(f"\n--- {mode} ---\n")

    stats = copy_samples(dirt_root, snd_root, dry_run=args.dry_run)

    print(f"\n--- Summary ---")
    print(f"Folders mapped: {stats['folders']}")
    print(f"Files copied:   {stats['files']}")
    print(f"Folders skipped (no WAVs): {stats['skipped']}")
    if stats["errors"]:
        print(f"Errors: {len(stats['errors'])}")
        for err in stats["errors"]:
            print(f"  {err}")

    if args.dry_run:
        print("\n(Dry run — no files were actually copied)")


if __name__ == "__main__":
    main()
