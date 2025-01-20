import numpy as np
from scipy import stats
import pandas as pd
import librosa

class FeaturesCompute:
  """
  Compute features for a given audio file. Saves to CSV format.
  """
  def columns(self):
    """Defines the structure of features and their column names"""
    feature_sizes = dict(
        chroma_cens=12, # for chord progression
        mfcc=13, # for melody
        zcr=1, # for percussive or harmonic
        rmse=1, # for loudness
        spectral_contrast=7, # for clear vs muddy
        spectral_flatness=1, # for noise fade in/out or phaser style
        spectral_centroid=1, # for brightness, skewness & kurtosis
        spectral_bandwidth=1, # for frequency spread
    )
    # Different stats for different features
    single_value_stats = ('mean', 'std')
    multi_value_stats = ('mean', 'std', 'skewness', 'kurtosis')
    
    tuples = []
    for feat, size in feature_sizes.items():
      stats = single_value_stats if size == 1 else multi_value_stats
      for stat in stats:
        # (chroma_cens, kurtosis, 01..12)
        it = ((feat, stat, '{:02d}'.format(i+1)) for i in range(size))
        tuples.extend(it)
    
    # Create MultiIndex with explicit names and sort it
    columns = pd.MultiIndex.from_tuples(tuples,
                                     names=['feature', 'statistics', 'compo#'])

    return columns.sort_values()  # Sort the index and return sorted version
  
  def compute_features(self, audio_path, uid=None, mid_split: float = 0.6, in_out_sec: int = 30):
    """Compute the features."""
    
    features = pd.Series(index=self.columns(), dtype=np.float32)
    features.sort_index()
    
    features[('path', '', '')] = audio_path
    if uid:
      features[('uid', '', '')] = uid

    def feature_stats(name, values):
      """Calculates descriptive statistics for each feature."""
      try:
          values = np.asarray(values, dtype=np.float32)
          values = values.T
          # For single-value features (zcr, rmse)
          if values.shape[1] == 1:
              features[name, 'mean'] = np.around(np.mean(values, axis=0), decimals=4)
              features[name, 'std'] = np.around(np.std(values, axis=0), decimals=4)
          # For multi-value features (chroma_cens, mfcc, spectral features)
          else:
              features[name, 'mean'] = np.around(np.mean(values, axis=0), decimals=4)
              features[name, 'std'] = np.around(np.std(values, axis=0), decimals=4)
              features[name, 'skewness'] = np.around(stats.skew(values, axis=0), decimals=4)
              features[name, 'kurtosis'] = np.around(stats.kurtosis(values, axis=0), decimals=4)
      except Exception as e:
          print(f"Warning: Could not compute stats for {name}: {e}")

    file = audio_path
    # Load audio file
    try:
      # Get duration first
      duration = librosa.get_duration(path=file)
      
      # Calculate middle %
      start_percent = (1 - mid_split) / 2 # = 0.2 for middle 60%
      offset = duration * start_percent
      mid_duration = duration * mid_split
      in_out = np.min([duration * start_percent, in_out_sec])
      
      #Load middle part
      y, sr = librosa.load(file, 
                          offset=offset, 
                          duration=mid_duration,
                          sr=None)
      y_sr = [(y, sr)]

      if mid_split < 1:
        # Load beginning part
        y_start, sr_start = librosa.load(file, 
                            duration=in_out,
                            sr=None)
        y_sr.append((y_start, sr_start))
        # Load end part
        y_end, sr_end = librosa.load(file, 
                            offset=duration-in_out, 
                            duration=in_out,
                            sr=None)
        y_sr.append((y_end, sr_end))

    except Exception as e:
      print(f"Failed to load audio: {e}")
      return None


    # Compute features for each part
    features_part = []
    for i, (y, sr) in enumerate(y_sr):
      if i == 0:
        print("[[[PROCESSING MIDDLE PART: {:.2f}s]]]".format(mid_duration))
      elif i == 1:
        print("[[[PROCESSING START PART: {:.2f}s]]]".format(in_out))
      else:
        print("[[[PROCESSING END PART: {:.2f}s]]]".format(in_out))

      # Create new features Series for each part
      features = pd.Series(index=self.columns(), dtype=np.float32)
      features.sort_index()
      features[('path', '', '')] = audio_path
      if uid:
        features[('uid', '', '')] = uid

      # Compute tempo
      try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr, start_bpm=50)
        features[('tempo', 'mean', '01')] = np.around(tempo[0], decimals=3)
      except Exception as e:
        print("Failed to compute tempo, set to NaN")
        features[('tempo', 'mean', '01')] = np.nan

      # Compute CQT for Chroma features
      cqt = np.abs(librosa.cqt(y, sr=sr, 
                              hop_length=512, 
                              bins_per_octave=12,
                              n_bins=7*12, 
                              tuning=None))
      assert cqt.shape[0] == 7 * 12
      assert np.ceil(len(y)/512) <= cqt.shape[1] <= np.ceil(len(y)/512)+1

      # Chroma Features - rely on resampling, so will take a while
      f = librosa.feature.chroma_cens(C=cqt, n_chroma=12, n_octaves=7)
      f = f[:, ::10]
      feature_stats('chroma_cens', f)
      del cqt

      # STFT-based analysis: Compute STFT for Spectral features
      D = np.abs(librosa.stft(y, 
                              n_fft=2048,
                              hop_length=512))
      # Compute Mel-scaled Spectrogram from STFT
      mel = librosa.feature.melspectrogram(sr=sr, S=D**2)
      # MFCC from mel spectrogram
      f = librosa.feature.mfcc(S=librosa.power_to_db(mel), n_mfcc=13)
      feature_stats('mfcc', f)
      del mel

      # Zero-Crossing Rate
      f = librosa.feature.zero_crossing_rate(y, frame_length=2048, hop_length=512)
      feature_stats('zcr', f)
      del y, sr

      # Root Mean Square Energy
      f = librosa.feature.rms(S=D)
      feature_stats('rmse', f)

      # Spectral features
      f = librosa.feature.spectral_centroid(S=D)
      feature_stats('spectral_centroid', f)

      f = librosa.feature.spectral_bandwidth(S=D)
      feature_stats('spectral_bandwidth', f)

      f = librosa.feature.spectral_contrast(S=D, n_bands=6)
      feature_stats('spectral_contrast', f)

      f = librosa.feature.spectral_flatness(S=D)
      feature_stats('spectral_flatness', f)

      del D

      features_part.append(features)
    return features_part