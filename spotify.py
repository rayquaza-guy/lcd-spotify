import asyncio, threading, time
import numpy as np
import serial
import soundcard as sc
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
)

PORT = "COM4"        # check Arduino IDE > Tools > Port
ser = serial.Serial(PORT, 57600)
time.sleep(2)        # Uno resets when serial opens

BANDS, RATE, BLOCK = 16, 48000, 1024
edges = np.logspace(np.log10(40), np.log10(14000), BANDS + 1)
freqs = np.fft.rfftfreq(BLOCK, 1 / RATE)
window = np.hanning(BLOCK)
peak = 1e-6

def send(line):
    ser.write((line + "\n").encode("ascii", "replace"))

# ---- now playing ----
async def get_track():
    mgr = await MediaManager.request_async()
    s = mgr.get_current_session()
    if not s:
        return None
    p = await s.try_get_media_properties_async()
    return f"{p.artist} - {p.title}"

def track_loop():
    last = None
    while True:
        t = asyncio.run(get_track())
        if t and t != last:
            send("T" + t)
            last = t
        time.sleep(1)

threading.Thread(target=track_loop, daemon=True).start()

# ---- visualizer ----
speaker = sc.default_speaker()
loop_mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)

with loop_mic.recorder(samplerate=RATE, channels=2) as rec:
    while True:
        data = rec.record(numframes=BLOCK).mean(axis=1)
        spec = np.abs(np.fft.rfft(data * window))
        levels = []
        for i in range(BANDS):
            m = (freqs >= edges[i]) & (freqs < edges[i + 1])
            levels.append(spec[m].mean() if m.any() else 0)
        levels = np.array(levels)
        peak = max(peak * 0.995, levels.max())      # slow auto-gain
        scaled = np.sqrt(levels / peak)             # compress dynamic range
        out = "".join(str(int(round(v * 8))) for v in scaled)
        send("B" + out)