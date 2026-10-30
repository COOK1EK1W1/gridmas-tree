"""Audio offset calibration: a click on every beat and a one-frame flash on the same beat.

Run main.py with --audio-device, stand by the tree, and adjust the offset live with
POST /audio/offset/<ms> until the flashes and clicks land together. Then put that
value in --audio-offset-ms. The first beat of every bar is higher pitched and flashes red.
"""

import numpy as np
from gridmas import *

name = "Calibrate"
author = "Ciaran"

BPM = 120
BEATS_PER_BAR = 4
LENGTH_S = 180
SAMPLERATE = 44100
CLICK_S = 0.01

# 40fps puts exactly 20 frames on each 120bpm beat
set_fps(40)


def _click_track() -> np.ndarray:
    track = np.zeros(LENGTH_S * SAMPLERATE, dtype=np.float32)
    beat_samples = SAMPLERATE * 60 // BPM
    t = np.arange(int(CLICK_S * SAMPLERATE)) / SAMPLERATE
    envelope = np.linspace(1, 0, len(t))
    for beat, start in enumerate(range(0, len(track) - len(t), beat_samples)):
        freq = 1500 if beat % BEATS_PER_BAR == 0 else 1000
        track[start:start + len(t)] = 0.8 * envelope * np.sin(2 * np.pi * freq * t)
    return track


set_music(_click_track(), samplerate=SAMPLERATE)


def draw():
    beat_ms = 60_000 // BPM
    beat, into_beat = divmod(millis(), beat_ms)
    if into_beat < 1000 / 40:
        fill(Color.red() if beat % BEATS_PER_BAR == 0 else Color.white())
    else:
        fill(Color.black())
