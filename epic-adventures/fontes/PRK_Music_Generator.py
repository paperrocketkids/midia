"""Original, royalty-free cheerful instrumental for the PaperRocket Kids Reels (synthesized from scratch)."""
import numpy as np, wave, sys

SR = 44100
BPM = 112
BEAT = 60 / BPM


def note_freq(n):  # MIDI note -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


def pluck(freq, dur, bright=0.5):
    """Karplus-Strong plucked string (ukulele-like)."""
    n = int(SR * dur)
    period = max(2, int(SR / freq))
    buf = np.random.uniform(-1, 1, period)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % period]
        buf[i % period] = 0.996 * (bright * buf[i % period] + (1 - bright) * buf[(i + 1) % period]) if True else 0
    return out * np.exp(-np.linspace(0, 3, n))


def marimba(freq, dur):
    t = np.arange(int(SR * dur)) / SR
    env = np.exp(-t * 7)
    s = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t * 20)
    att = np.minimum(1, t / 0.004)
    return s * env * att


def bass(freq, dur):
    t = np.arange(int(SR * dur)) / SR
    env = np.exp(-t * 3) * np.minimum(1, t / 0.01)
    return (np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(4 * np.pi * freq * t)) * env


def shaker(dur):
    n = int(SR * dur)
    x = np.random.uniform(-1, 1, n)
    x = np.diff(np.concatenate([[0], x]))  # crude high-pass
    return x * np.exp(-np.linspace(0, 12, n))


def add(track, sig, start, gain):
    i = int(start * SR)
    j = min(len(track), i + len(sig))
    track[i:j] += gain * sig[: j - i]


# C – G – Am – F, one bar (4 beats) each
CHORDS = [[60, 64, 67], [55, 59, 62, 67], [57, 60, 64], [53, 57, 60, 65]]
ROOTS = [36, 43, 45, 41]
# playful melody (MIDI, beats) per 4-bar phrase; two phrases
MEL_A = [(72, .5), (76, .5), (79, 1), (76, .5), (74, .5), (71, .5), (74, .5), (76, .5), (72, .5), (69, 1), (72, .5), (77, .5), (76, .5), (74, .5), (72, 1), (None, 1)]
MEL_B = [(79, .5), (81, .5), (79, .5), (76, .5), (74, 1), (79, .5), (74, .5), (76, .5), (72, .5), (69, .5), (72, .5), (74, .5), (77, .5), (76, .5), (74, .5), (72, 1.5), (None, .5)]


def compose(seconds, seed=7):
    np.random.seed(seed)
    track = np.zeros(int(SR * (seconds + 2)))
    bar = 4 * BEAT
    nbars = int(np.ceil(seconds / bar))
    for b in range(nbars):
        t0 = b * bar
        ci = b % 4
        # strum pattern: down on 1, 2&, 3, 4
        for k, off in enumerate([0, 1.5, 2, 3]):
            for j, n in enumerate(CHORDS[ci]):
                add(track, pluck(note_freq(n), 0.9, 0.5), t0 + off * BEAT + j * 0.012, 0.18 if k == 0 else 0.12)
        add(track, bass(note_freq(ROOTS[ci]), 1.6), t0, 0.5)
        add(track, bass(note_freq(ROOTS[ci] + 7), 1.0), t0 + 2 * BEAT, 0.35)
        for s in range(8):
            add(track, shaker(0.12), t0 + s * BEAT / 2, 0.025 if s % 2 else 0.04)
    # melody after a 1-bar intro
    t = bar
    phrase = 0
    while t < seconds:
        for n, d in (MEL_A if phrase % 2 == 0 else MEL_B):
            if n is not None and t < seconds:
                add(track, marimba(note_freq(n), d * BEAT + 0.4), t, 0.32)
            t += d * BEAT
        phrase += 1
    track = track[: int(SR * seconds)]
    # fade in/out and normalise to -1 dBFS
    fi, fo = int(SR * 0.3), int(SR * 1.5)
    track[:fi] *= np.linspace(0, 1, fi)
    track[-fo:] *= np.linspace(1, 0, fo)
    track = np.tanh(track * 1.2)
    track /= np.max(np.abs(track)) / 0.89
    return track


def save(path, x):
    st = np.stack([x, np.roll(x, 90) * 0.97], 1)  # tiny stereo widening
    data = (st * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


if __name__ == "__main__":
    secs = float(sys.argv[1]); out = sys.argv[2]
    save(out, compose(secs))
    print("wrote", out, secs)
