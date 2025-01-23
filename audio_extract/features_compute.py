import numpy as np
from scipy import stats
import pandas as pd
import librosa

class FeaturesCompute:
  """
  Compute features for a given audio file. Saves to CSV format.
  """
  def __init__(self, split: list = [15, 70, 15], in_out_sec: int = 30):
    self.split = split  # Store split as instance variable
    self.in_out_sec = in_out_sec
    
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
  
  def split_audio(self, audio_path):
    """Split audio into parts using self.split configuration"""
    file = audio_path
    # Load audio file
    try:
      duration = librosa.get_duration(path=file)
      y_sr = []
      
      if len(self.split) % 2 == 1:  # ODD SPLITS
        mid_idx = len(self.split) // 2
        mid_split = self.split[mid_idx] / 100
        
        # Load middle part first
        offset = duration * sum(self.split[:mid_idx]) / 100
        mid_duration = duration * mid_split
        y, sr = librosa.load(file, offset=offset, duration=mid_duration, sr=None)
        y_sr.append((y, sr, f'middle ({mid_split}%)', mid_duration))
        
        # Load remaining parts
        current_offset = offset
        for i, p in enumerate(self.split[:mid_idx]):  # Before middle
          # Compare first part with in_out_sec
          part_dur = min(duration * p/100, self.in_out_sec) if i == 0 else duration * p/100
          y, sr = librosa.load(file, offset=current_offset-part_dur, duration=part_dur, sr=None)
          y_sr.insert(i, (y, sr, f'part {i+1} ({p}%)', part_dur))
          current_offset -= part_dur
        
        current_offset = offset + mid_duration
        for i, p in enumerate(self.split[mid_idx+1:]):  # After middle
          # Compare last part with in_out_sec
          part_dur = min(duration * p/100, self.in_out_sec) if i == len(self.split[mid_idx+1:])-1 else duration * p/100
          y, sr = librosa.load(file, offset=current_offset, duration=part_dur, sr=None)
          y_sr.append((y, sr, f'part {len(self.split)-i} ({p}%)', part_dur))
          current_offset += part_dur
              
      else:  # EVEN SPLITS
        mid_point = duration / 2
        left_splits = self.split[:len(self.split)//2]
        right_splits = self.split[len(self.split)//2:]
        
        # Load parts before middle
        current_offset = mid_point
        for i, p in enumerate(reversed(left_splits)):
          # Compare first part with in_out_sec
          part_dur = min(duration * p/100, self.in_out_sec) if i == len(left_splits)-1 else duration * p/100
          y, sr = librosa.load(file, offset=current_offset-part_dur, duration=part_dur, sr=None)
          # Fix: use i directly for part numbering
          part_num = len(left_splits) - i
          y_sr.insert(0, (y, sr, f'part {part_num} ({p}%)', part_dur))
          current_offset -= part_dur
            
        # Load parts after middle
        current_offset = mid_point
        for i, p in enumerate(right_splits):
          # Compare last part with in_out_sec
          part_dur = min(duration * p/100, self.in_out_sec) if i == len(right_splits)-1 else duration * p/100
          y, sr = librosa.load(file, offset=current_offset, duration=part_dur, sr=None)
          # Fix: continue numbering from where left splits ended
          part_num = len(left_splits) + i + 1
          y_sr.append((y, sr, f'part {part_num} ({p}%)', part_dur))
          current_offset += part_dur

    except Exception as e:
      print(f"Failed to load audio: {e}")
      return None
    
    return y_sr

  def compute_features(self, audio_path, uid=None):
    """Compute features from audio parts."""
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

    y_sr = self.split_audio(audio_path)
    features_part = []
    for y, sr, label, part_dur in y_sr:
      print(f"[[[PROCESSING {label.upper()}: {part_dur:.2f}s]]]")
      
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