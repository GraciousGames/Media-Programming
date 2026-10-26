import numpy as np
from scipy.io.wavfile import write
sr = 96000 # Samples pro Sekunde
dauer = 1 # Sekunden
frequenz = 880 # Hz
t = np.linspace(0, dauer, int(sr * dauer), endpoint=False)
signal = 0.5 * np.sin(2 * np.pi * frequenz * t)
audio_int16 = (signal * 32767).astype(np.int16)
write("sinus_880Hz_96000samp.wav", sr, audio_int16)