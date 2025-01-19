from pathlib import Path
import os
import numpy as np
import matplotlib.pyplot as plt
import librosa, librosa.display
import pyloudnorm as pyln
import soundfile as sf
from tqdm import tqdm


class FUCK:
  def compute_features(self, audio_path):
    print(f"Processing file: {audio_path}")
    try:
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        print(f"Audio loaded successfully! Length: {len(y)}, Sample rate: {sr}")
        return y, sr
    except Exception as e:
        print(f"Failed to load audio: {e}")
        return None

# audio_path = r'D:\#ALLMYMUSIC - Copy\00. Future Funk\The Stars Through Your Eyes - Android Apartment\08. Blue My Blues.mp3'

# y, sr = FUCK().compute_features(audio_path)


class FOLDER:
  def __init__(self, folder):
    self.folder = folder

  def scan_library(self):
    path_list = []
    for root, _, files in os.walk(self.folder):
      for file in files:
        if file.endswith('.mp3'):
          # Use absolute path as string
          full_path = str(Path(root) / file)
          path_list.append(full_path)
    for fuck_path in tqdm(path_list, desc="Processing files"):
      features_series = FUCK().compute_features(fuck_path)

folder = FOLDER(r'D:/#ALLMYMUSIC - Copy/00. Future Funk')
folder.scan_library()



# print(sr)
# print(y.shape)

# D = librosa.stft(y)
# S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

# print(librosa.feature.tempo(y=y, sr=sr))

# plt.figure(figsize=(14, 5))
# librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='log')
# plt.colorbar(format='%+2.0f dB')
# plt.title('Log-frequency power spectrogram')
# plt.tight_layout()
# plt.show()

# #print(librosa.get_duration(y=x, sr=sr))


# librosa.display.waveshow(y=y, sr=sr)

# peak normalize audio to -1 dB
# peak_normalized_audio = pyln.normalize.peak(data, -1.0)

# # measure the loudness first 
# meter = pyln.Meter(rate) # create BS.1770 meter
# loudness = meter.integrated_loudness(data)

# # loudness normalize audio to -12 dB LUFS
# loudness_normalized_audio = pyln.normalize.loudness(data, loudness, -12.0)


