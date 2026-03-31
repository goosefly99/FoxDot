"""
External SynthDef wrappers for third-party Quark synths.

These wrap SynthDefs provided by the SCLOrkSynths Quark
(https://github.com/SCLOrkHub/SCLOrkSynths). The Quark must be
installed in SuperCollider for these synths to produce sound:

    Quarks.install("SCLOrkSynths");

Each entry registers the synth name in FoxDot's SynthDefs dict so
that players can reference it (e.g. ``d1 >> cheappiano([0,2,4])``).
Because the SynthDefs are compiled by SC's class library at boot,
no .scsyndef file needs to be loaded from disk.
"""

from .SynthDef import SynthDefBaseClass, SynthDefs


class QuarkSynthDef(SynthDefBaseClass):
    """A SynthDef loaded via a SuperCollider Quark (no file on disk)."""

    def write(self):
        return

    def load(self):
        # Quark SynthDefs are compiled by SC's class library at boot.
        return

    def __str__(self):
        return repr(self)


# ---------------------------------------------------------------------------
# SCLOrkSynths wrappers
#
# Selection criteria for inclusion:
#   - Accepts freq, amp, pan (FoxDot convention)
#   - Has a finite envelope (doneAction: 2)
#   - Musically useful and distinct from built-in FoxDot synths
#
# Defaults mirror the SCLOrkSynths source where possible. FoxDot's
# SynthDefBaseClass.__init__ already provides sensible fallbacks for
# standard parameters (amp, sus, pan, freq, bus, etc.), so we only
# override values that differ from those defaults.
# ---------------------------------------------------------------------------

# -- Keys / Piano --

cheappiano = QuarkSynthDef("cheappiano")
cheappiano.defaults.update(
    vel=0.8,
    decay=0.3,
)

rhodey = QuarkSynthDef("rhodey")
rhodey.defaults.update(
    lfoSpeed=0.4,
    lfoDepth=0.1,
)

harpsichord = QuarkSynthDef("harpsichord")

kalimba = QuarkSynthDef("kalimba")
kalimba.defaults.update(
    clickrel=0.01,
)

# -- Pads / Strings --

everythingrhodes = QuarkSynthDef("everythingrhodes")
everythingrhodes.defaults.update(
    vel=0.8,
    modIndex=0.2,
    mix=0.2,
    lfoSpeed=0.4,
    lfoDepth=0.1,
)

dreamyrhodes = QuarkSynthDef("dreamyrhodes")
dreamyrhodes.defaults.update(
    vel=0.6,
    modIndex=0.2,
    mix=0.2,
    lfoSpeed=0.4,
    lfoDepth=0.1,
)

# -- Plucked / Struck --

plucking = QuarkSynthDef("plucking")
plucking.defaults.update(
    coef=0.2,
)

marimbasynth = QuarkSynthDef("marimbasynth")

xylophone = QuarkSynthDef("xylophone")

# -- Bass --

hoover = QuarkSynthDef("hoover")
hoover.defaults.update(
    glide=0.5,
)

# -- Leads / Synth --

organdonor = QuarkSynthDef("organdonor")

moogbass = QuarkSynthDef("moogbass")
moogbass.defaults.update(
    cutoff=1000,
    gain=2.0,
)

sqrgrn = QuarkSynthDef("sqrgrn")
sqrgrn.defaults.update(
    detune=2,
    grainFreq=10,
)

# -- Textural / Experimental --

henontri = QuarkSynthDef("henontri")
henontri.defaults.update(
    a=1.3,
    b=0.3,
    mFreq=2,
)

ring1 = QuarkSynthDef("ring1")
ring1.defaults.update(
    spread=0.5,
)
