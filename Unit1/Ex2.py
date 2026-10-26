import numpy as np
from scipy.io.wavfile import write, read
sr = 44100
dauer = 1.0
t = np.linspace(0, dauer, int(sr * dauer), endpoint=False)
links = 0.5 * np.sin(2 * np.pi * 440 * t)
rechts = 0.5 * np.sin(2 * np.pi * 660 * t)
stereo = np.column_stack((links, rechts))
write("Unit1/stereo.wav", sr, (stereo * 32767).astype(np.int16))
sr2, stereo_data = read("stereo.wav")
mono = stereo_data.mean(axis=1).astype(np.int16)
write("Unit1/mono_aus_stereo.wav", sr2, mono)
print("Stereo-Shape:", stereo_data.shape)
print("Mono-Shape:", mono.shape)