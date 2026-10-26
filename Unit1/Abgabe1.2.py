
import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
import threading

from scipy.io import wavfile
from scipy.signal import resample_poly


# ============================================================
# 1. EINSTELLUNGEN
# ============================================================

samplerate = 44100       # 44.100 Samples pro Sekunde
dauer = 5                # Aufnahmedauer in Sekunden
blocksize = 1024         # Samples pro Audio-Block

# Anzahl der Samples für die gesamte Aufnahme:
# 44.100 * 5 = 220.500 Samples
gesamt_samples = samplerate * dauer


# ============================================================
# 2. AUFNAHMEGERÄT AUSWÄHLEN
# ============================================================

# Alle verfügbaren Audiogeräte abfragen
geraete = sd.query_devices()

# Nur Geräte anzeigen, die Audio aufnehmen können
eingabegeraete = []

print("\nVerfügbare Aufnahmegeräte:\n")

for index, geraet in enumerate(geraete):

    # max_input_channels > 0 bedeutet:
    # Das Gerät besitzt mindestens einen Eingangskanal.
    if geraet["max_input_channels"] > 0:

        eingabegeraete.append(index)

        print(
            f"Geräteindex: {index} | "
            f"Name: {geraet['name']} | "
            f"Eingangskanäle: {geraet['max_input_channels']}"
        )

# Prüfen, ob überhaupt ein Aufnahmegerät gefunden wurde
if len(eingabegeraete) == 0:
    raise RuntimeError("Kein Aufnahmegerät gefunden!")


# Benutzer wählt ein Gerät anhand seines Geräteindex aus
while True:

    try:
        geraet_index = int(
            input("\nBitte Geräteindex eingeben: ")
        )

        if geraet_index in eingabegeraete:
            break

        print("Bitte einen gültigen Geräteindex eingeben.")

    except ValueError:
        print("Bitte eine ganze Zahl eingeben.")


# Gewähltes Gerät anzeigen
print("\nAusgewähltes Gerät:")
print(sd.query_devices(geraet_index)["name"])


# Prüfen, ob das Gerät die gewünschten Einstellungen unterstützt
# So erkennen wir beispielsweise, wenn 44.100 Hz nicht möglich sind.
sd.check_input_settings(
    device=geraet_index,
    samplerate=samplerate,
    channels=1,
    dtype="int16"
)


# ============================================================
# 3. VARIABLEN FÜR DIE AUFNAHME
# ============================================================

# Hier werden die Audio-Blöcke gesammelt.
audio_bloecke = []

# Zählt die aufgenommenen Samples.
samples_aufgenommen = 0

# Merkt sich den ADC-Zeitstempel des ersten Audio-Blocks.
# Dieser Zeitstempel stammt aus dem Audiotreiber.
start_adc_time = None

# Event zur Mitteilung, dass die Aufnahme beendet ist.
# Damit brauchen wir kein sd.wait().
aufnahme_fertig = threading.Event()


# ============================================================
# 4. CALLBACK-FUNKTION
# ============================================================

def callback(indata, frames, time, status):

    global samples_aufgenommen
    global start_adc_time

    # Statusmeldungen des Audiotreibers anzeigen.
    # Beispielsweise kann es zu einem Buffer-Überlauf kommen.
    if status:
        print("Audio-Status:", status)

    # Zeitstempel des ersten aufgenommenen Audio-Blocks speichern.
    # inputBufferAdcTime bezeichnet den Aufnahmezeitpunkt
    # des ersten Samples dieses Blocks laut Audiotreiber.
    if start_adc_time is None:
        start_adc_time = time.inputBufferAdcTime

    # Den Block SOFORT kopieren und sichern.
    # Die Daten in indata dürfen nach dem Callback
    # nicht als dauerhaft verfügbar betrachtet werden.
    audio_bloecke.append(indata.copy())

    # Anzahl der Samples dieses Blocks addieren.
    samples_aufgenommen += frames

    # Sobald mindestens 5 Sekunden aufgenommen wurden,
    # den Audiostream kontrolliert beenden.
    if samples_aufgenommen >= gesamt_samples:
        raise sd.CallbackStop


# ============================================================
# 5. CALLBACK NACH ENDE DES STREAMS
# ============================================================

def fertig_callback():

    # Signalisiert dem Hauptprogramm:
    # Der Audiostream ist vollständig beendet.
    aufnahme_fertig.set()


# ============================================================
# 6. AUFNAHME STARTEN
# ============================================================

print("\nAufnahme startet ...")
print("Bitte jetzt das gewünschte Tonsignal erzeugen!")

# InputStream startet die Aufnahme.
# Ab dem ersten Callback werden die Audio-Daten gespeichert.
with sd.InputStream(
    device=geraet_index,             # ausgewähltes Mikrofon
    samplerate=samplerate,           # 44.100 Hz
    channels=1,                      # Mono
    dtype="int16",                   # 16-Bit-Samples
    blocksize=blocksize,             # Blockgröße
    callback=callback,               # Funktion für neue Daten
    finished_callback=fertig_callback
):

    # Auf das Ende der Aufnahme warten, aber NICHT sd.wait()
    # verwenden. Die Schleife prüft das Event alle 20 ms.
    while not aufnahme_fertig.is_set():
        sd.sleep(20)

print("Aufnahme beendet!")


# ============================================================
# 7. AUDIO-BLÖCKE ZUSAMMENFÜGEN
# ============================================================

# Alle aufgenommenen Blöcke zu einem Array verbinden.
# Jeder Block enthält eine Folge aufeinanderfolgender Samples.
audio = np.concatenate(audio_bloecke, axis=0)

# Der letzte Block kann über die benötigte Sample-Anzahl
# hinausgehen. Deshalb schneiden wir exakt auf 220.500 Samples.
audio = audio[:gesamt_samples]

print("Anzahl der Samples:", len(audio))
print("Dauer der gespeicherten Aufnahme:",
      len(audio) / samplerate, "Sekunden")

if start_adc_time is not None:
    print("ADC-Zeitstempel des ersten Blocks:", start_adc_time)


# ============================================================
# 8. ORIGINALAUFNAHME SPEICHERN
# ============================================================

# Speichert die Aufnahme im aktuellen Arbeitsverzeichnis.
wavfile.write(
    "aufnahme_original.wav",
    samplerate,
    audio
)

print("Gespeichert: aufnahme_original.wav")


# ============================================================
# 9. AUF 22.050 Hz RESAMPLEN
# ============================================================

# WICHTIG:
# Nur den WAV-Header auf 22.050 Hz zu setzen wäre falsch.
# Die Samples müssen tatsächlich umgerechnet werden.
#
# resample_poly(audio, 1, 2) halbiert die Sample-Anzahl
# und wandelt 44.100 Hz in 22.050 Hz um.

audio_22050 = resample_poly(
    audio[:, 0],   # Mono-Signal als eindimensionales Array
    up=1,
    down=2
)

wavfile.write(
    "aufnahme_22050.wav",
    22050,
    audio_22050.astype(np.int16)
)

print("Gespeichert: aufnahme_22050.wav")


# ============================================================
# 10. ERSTE 20 MILLISEKUNDEN AUSWÄHLEN
# ============================================================

# 20 ms entsprechen 0,020 Sekunden.
zeitdauer_ms = 20

# Benötigte Sample-Anzahl berechnen:
# 44.100 * 0,020 = 882 Samples
anzahl = int(samplerate * zeitdauer_ms / 1000)

# Nur die ersten 882 Samples auswählen.
# [:, 0] wählt den einzigen Mono-Kanal aus.
ausschnitt = audio[:anzahl, 0]

# Zeitachse berechnen.
# Sample 0 liegt bei 0 ms, Sample 1 bei ca. 0,0227 ms usw.
zeit = np.arange(anzahl) / samplerate * 1000


# ============================================================
# 11. SIGNAL PLOTTEN
# ============================================================

plt.figure(figsize=(12, 5))

# Aufgenommenes Signal darstellen
plt.plot(
    zeit,
    ausschnitt,
    color="blue",
    linewidth=1,
    label="Audiosignal"
)

# Nulllinie bei Amplitude 0 einzeichnen
plt.axhline(
    y=0,
    color="red",
    linestyle="--",
    linewidth=1,
    label="Nulllinie (Amplitude = 0)"
)

# Achsenbeschriftungen
plt.xlabel("Zeit (ms)")
plt.ylabel("Amplitude")

# Diagrammtitel
plt.title("Audiosignal – erste 20 ms")

# X-Achse von 0 bis 20 ms
plt.xlim(0, 20)

# Gitternetz und Legende
plt.grid(True)
plt.legend()

# Abstände automatisch anpassen
plt.tight_layout()

# Diagramm anzeigen
plt.show()
