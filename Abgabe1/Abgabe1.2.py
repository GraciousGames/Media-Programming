
from pathlib import Path         #Dateipfade
import sounddevice as sd         #Mikrofonaufnahme
import numpy as np               #Berechnungen
import matplotlib.pyplot as plt  #Diagramme
from scipy.io import wavfile     #WAV-Dateien

ordner = Path(__file__).resolve().parent  #Speicherordner

samplerate = 44100  #44100 Abtastwerte pro Sekunde
dauer = 5           #5 Sekunden Aufnahme

#Sprachsignal aufnehmen
aufnahme = sd.rec(
    int(dauer * samplerate),  #5 * 44100 = 220500 Werte
    samplerate=samplerate,    #44100 Hz
    channels=1,               #Mono
    dtype="int16"             #16 Bit = 2 Byte
)

sd.wait()                      #Aufnahme abwarten, da sonst die Aufnahme 
                               #nicht vollständig ist (hoher Piepton zu Beginn, danach Stille)

#WAV-Datei speichern
wavfile.write(ordner / "aufnahme_original.wav", samplerate, aufnahme)

#WAV-Datei einlesen
samplerate, signal = wavfile.read(ordner / "aufnahme_original.wav")

#Erste 20 Millisekunden plotten
anzahl = int(0.02 * samplerate)                 #20 ms = 882 Werte
zeit = np.arange(anzahl) / samplerate * 1000    #Zeit in ms

plt.plot(zeit, signal[:anzahl])         #Erste 882 Werte
plt.xlabel("Zeit (ms)")                 #X-Achse
plt.ylabel("Amplitude")                 #Y-Achse
plt.title("Erste 20 ms")                #Titel
plt.grid()                              #Gitternetz
plt.savefig(ordner / "plot_0ms.png")    #Bild speichern
plt.show()                              #Diagramm anzeigen

#20 Millisekunden ab Sekunde 1 plotten
start = samplerate                            #Sekunde 1 = Abtastwert 44100
zeit = np.arange(anzahl) / samplerate * 1000  #Zeit in ms

plt.figure()                                  #Neues Diagramm
plt.plot(zeit, signal[start:start + anzahl])  #882 Werte ab Sekunde 1
plt.xlabel("Zeit ab Sekunde 1 (ms)")          #X-Achse
plt.ylabel("Amplitude")                       #Y-Achse
plt.title("20 ms ab Sekunde 1")               #Titel
plt.grid()                                    #Gitternetz
plt.savefig(ordner / "plot_1s.png")           #Bild speichern
plt.show()                                    #Diagramm anzeigen

# Zweite WAV-Datei mit anderer Samplerate
neue_samplerate = 94000                       # Neue Abtastrate: 94000 Hz
wavfile.write(ordner / "aufnahme_94000.wav", neue_samplerate, signal)

