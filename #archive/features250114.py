import warnings
import numpy as np
from scipy import stats
import pandas as pd
import librosa

class Features:
  """
  Compute features for a given audio file. Saves to CSV format.
  """
  def columns(self):
    """Defines the structure of features and their column names"""
    feature_sizes = dict(
        chroma_stft=12, 
        chroma_cqt=12, 
        chroma_cens=12,
        tonnetz=6, 
        mfcc=12, 
        rmse=1, 
        zcr=1,
        spectral_centroid=1, 
        spectral_bandwidth=1,
        spectral_contrast=7, 
        spectral_rolloff=1
    )
    # Descriptive stats
    stats = ('mean', 'std', 'skew', 'kurtosis', 'median', 'min', 'max')

    # Column names
    columns = []
    for feat, size in feature_sizes.items():
      for stat in stats:
        for i in range(size):
          # Need to understand multi-index dataframe for this
          # it = (mfcc, mean, 01)
          it = ((feat, stat, '{:02d}'.format(i+1)) for i in range(size))
          columns.extend(it)

    names = ('feature', 'statistics', 'number')
    columns = pd.MultiIndex.from_tuples(columns, names=names)

    return columns.sort_values()

  def compute_features(self, audio_path, date_added=None, track_index=None):
    """Compute the features."""
    columns = self.columns()
    features = pd.Series(index=columns, dtype=np.float32)
    warnings.filterwarnings('error', module='librosa') 

    # if date_added:
    #   features["date_added"] = date_added
    # elif track_index:
    #   features["track_index"] = track_index

    def feature_stats(feature, values):
      """Calculates descriptive statistics for each feature."""
      values = values.T
      features[feature, 'mean'] = np.mean(values, axis=0)
      features[feature, 'std'] = np.std(values, axis=0)
      features[feature, 'skew'] = stats.skew(values, axis=0)
      features[feature, 'kurtosis'] = stats.kurtosis(values, axis=0)
      features[feature, 'median'] = np.median(values, axis=0)
      features[feature, 'min'] = np.min(values, axis=0)
      features[feature, 'max'] = np.max(values, axis=0)

    try:
      # Load audio file
      y, sr = librosa.load(audio_path, sr=None, mono=True)
      # Zero-Crossing Rate
      f = librosa.feature.zero_crossing_rate(y, frame_length=2048, hop_length=512)
      feature_stats('zcr', f)
      # Tonnetz
      f = librosa.feature.tonnetz(chroma=f)
      feature_stats('tonnetz', f)

      # Compute Constant-Q Spectrogram for Chroma features
      cqt = np.abs(librosa.cqt(y, sr=sr, hop_length=512, bins_per_octave=12,
                              n_bins=7*12, tuning=None))
      assert cqt.shape[0] == 7 * 12
      assert np.ceil(len(y)/512) <= cqt.shape[1] <= np.ceil(len(y)/512)+1

      # Chroma Features
      f = librosa.feature.chroma_cqt(C=cqt, n_chroma=12, n_octaves=7)
      feature_stats('chroma_cqt', f)
      f = librosa.feature.chroma_cens(C=cqt, n_chroma=12, n_octaves=7)
      feature_stats('chroma_cens', f)

      # Compute STFT for Spectral features
      del cqt
      stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
      assert stft.shape[0] == 1 + 2048 // 2
      assert np.ceil(len(y)/512) <= stft.shape[1] <= np.ceil(len(y)/512)+1
      del y

      # Chroma STFT
      f = librosa.feature.chroma_stft(S=stft**2, n_chroma=12)
      feature_stats('chroma_stft', f)
      # Root Mean Square Energy
      f = librosa.feature.rms(S=stft)
      feature_stats('rmse', f)
      # Spectral features
      f = librosa.feature.spectral_centroid(S=stft)
      feature_stats('spectral_centroid', f)
      f = librosa.feature.spectral_bandwidth(S=stft)
      feature_stats('spectral_bandwidth', f)
      f = librosa.feature.spectral_contrast(S=stft, n_bands=6)
      feature_stats('spectral_contrast', f)
      f = librosa.feature.spectral_rolloff(S=stft)
      feature_stats('spectral_rolloff', f)

      # Compute Mel-scaled Spectrogram for MFCC
      mel = librosa.feature.melspectrogram(sr=sr, S=stft**2)
      del stft
      # MFCC
      f = librosa.feature.mfcc(S=librosa.power_to_db(mel), n_mfcc=20)
      feature_stats('mfcc', f)

    except Exception as e:
      print('{}: {}'.format(audio_path, repr(e)))

    return features