import numpy as np
from scipy import stats
from pathlib import Path
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
    tuples = []
    for feat, size in feature_sizes.items():
      for stat in stats:
        # (chroma_cens, kurtosis, 01..12)
        it = ((feat, stat, '{:02d}'.format(i+1)) for i in range(size))
        tuples.extend(it)

    # Create MultiIndex with explicit names
    columns = pd.MultiIndex.from_tuples(
        tuples,
        names=['feature', 'statistic', 'compo#']
    )

    return columns.sort_values()
  
  def compute_features(self, audio_path):
    """Compute the features."""
    
    features = pd.Series(index=self.columns(), dtype=np.float32)
    
    def feature_stats(name, values):
        values = np.asarray(values, dtype=np.float32)
        values = values.T
        """Calculates descriptive statistics for each feature."""
        features[name, 'mean'] = np.mean(values, axis=0)
        features[name, 'std'] = np.std(values, axis=0)
        features[name, 'skew'] = stats.skew(values, axis=0)
        features[name, 'kurtosis'] = stats.kurtosis(values, axis=0)
        features[name, 'median'] = np.median(values, axis=0)
        features[name, 'min'] = np.min(values, axis=0)
        features[name, 'max'] = np.max(values, axis=0)
        
        print(f"Finished {name}: added {len(values)} components")

    file = audio_path
    print(f"Processing file: {file}")
    # Load audio file
    try:
        # Get duration first
        duration = librosa.get_duration(path=file)
        
        # Calculate middle %
        middle_percent = 0.6
        start_percent = (1 - middle_percent) / 2  # = 0.2 for middle 60%
        
        offset = duration * start_percent
        clip_duration = duration * middle_percent
        
        # Load just the middle portion for CQT
        y, sr = librosa.load(file, 
                           offset=offset, 
                           duration=clip_duration,
                           sr=None)
        
        # Stream audio file for STFT
        stream = librosa.stream(file,
                               block_length=1024,
                               frame_length=2048,
                               hop_length=512)

        print(f"Loaded {clip_duration:.2f}s starting at {offset:.2f}s")
        # Rest of your feature computation...
    except Exception as e:
        print(f"Failed to load audio: {e}")
        return None

    # Compute CQT for Chroma features
    cqt = np.abs(librosa.cqt(y, sr=sr, 
                             hop_length=512, 
                             bins_per_octave=12,
                             n_bins=7*12, 
                             tuning=None))
    assert cqt.shape[0] == 7 * 12
    assert np.ceil(len(y)/512) <= cqt.shape[1] <= np.ceil(len(y)/512)+1

    # Chroma Features - rely on resampling, so will take a while
    f = librosa.feature.chroma_cqt(C=cqt, n_chroma=12, n_octaves=7)
    feature_stats('chroma_cqt', f)
    f = librosa.feature.chroma_cens(C=cqt, n_chroma=12, n_octaves=7)
    feature_stats('chroma_cens', f)

    # Arrays to store values computed for each block
    zcr_blocks = []
    chroma_stft_blocks = []
    tonnetz_blocks = []
    rmse_blocks = []
    spectral_centroid_blocks = []
    spectral_bandwidth_blocks = []
    spectral_contrast_blocks = []
    spectral_rolloff_blocks = []
    mfcc_blocks = []

    # STFT-based analysis: Compute STFT for Spectral features
    del cqt
    for y_block in stream:
      D_block = np.abs(librosa.stft(y_block, 
                                 n_fft=2048,
                                 hop_length=512,
                                 center=False))
      # assert D_block.shape[0] == 1 + 2048 // 2
      # assert np.ceil(len(y_block)/512) <= D_block.shape[1] <= np.ceil(len(y_block)/512)+1

      # Zero-Crossing Rate
      f = librosa.feature.zero_crossing_rate(y_block, frame_length=2048, hop_length=512)
      zcr_blocks.extend(f)

      # Chroma STFT
      f = librosa.feature.chroma_stft(S=D_block**2, n_chroma=12)
      chroma_stft_blocks.extend(f)

      # Tonnetz
      f = librosa.feature.tonnetz(chroma=f)
      tonnetz_blocks.extend(f)

      # Root Mean Square Energy
      f = librosa.feature.rms(S=D_block)
      rmse_blocks.extend(f)

      # Spectral features
      f = librosa.feature.spectral_centroid(S=D_block)
      spectral_centroid_blocks.extend(f)

      f = librosa.feature.spectral_bandwidth(S=D_block)
      spectral_bandwidth_blocks.extend(f)

      f = librosa.feature.spectral_contrast(S=D_block, n_bands=6)
      spectral_contrast_blocks.extend(f)

      f = librosa.feature.spectral_rolloff(S=D_block)
      spectral_rolloff_blocks.extend(f)

      # Compute Mel-scaled Spectrogram from STFT
      mel_block = librosa.feature.melspectrogram(y=y_block, 
                                                 sr=sr, 
                                                 S=D_block**2, 
                                                 n_fft=2048,
                                                 hop_length=512,
                                                 center=False
                                                 )
      # MFCC from mel spectrogram
      f = librosa.feature.mfcc(S=librosa.power_to_db(mel_block), n_mfcc=20)
      mfcc_blocks.extend(f)

      del D_block, mel_block  # Clean up memory
    
    # Cast to a numpy array for use downstream
    zcr_blocks = np.concatenate(zcr_blocks, dtype=np.float32  )
    chroma_stft_blocks = np.concatenate(chroma_stft_blocks, dtype=np.float32)
    tonnetz_blocks = np.concatenate(tonnetz_blocks, dtype=np.float32)
    rmse_blocks = np.concatenate(rmse_blocks, dtype=np.float32)
    spectral_centroid_blocks = np.concatenate(spectral_centroid_blocks, dtype=np.float32)
    spectral_bandwidth_blocks = np.concatenate(spectral_bandwidth_blocks, dtype=np.float32)
    spectral_contrast_blocks = np.concatenate(spectral_contrast_blocks, dtype=np.float32)
    spectral_rolloff_blocks = np.concatenate(spectral_rolloff_blocks, dtype=np.float32)
    mfcc_blocks = np.concatenate(mfcc_blocks, dtype=np.float32)

    # Compute stats for each feature
    feature_stats('zcr', zcr_blocks)
    feature_stats('chroma_stft', chroma_stft_blocks)
    feature_stats('tonnetz', tonnetz_blocks)
    feature_stats('rmse', rmse_blocks)
    feature_stats('spectral_centroid', spectral_centroid_blocks)
    feature_stats('spectral_bandwidth', spectral_bandwidth_blocks)
    feature_stats('spectral_contrast', spectral_contrast_blocks)
    feature_stats('spectral_rolloff', spectral_rolloff_blocks)
    feature_stats('mfcc', mfcc_blocks)

    print(f"Total features computed: {len(features)}")  # Debug print
    return features