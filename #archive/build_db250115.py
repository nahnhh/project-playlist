from pathlib import Path
import time
import music_tag
from ..uid import TrackIDGenerator
from ..md_edit import CustomMetadata
import unicodedata
import re
import pandas as pd
from tqdm import tqdm
from baselines.features import Features
import numpy as np
import os
from ..md_extract import MetadataExtractor

def clean_text(text: str) -> str:
  """
  Clean text while preserving international characters:
  - Normalize Unicode characters
  - Remove control characters
  - Normalize whitespace
  - Strip leading/trailing whitespace
  """
  if not text:
    return ""
  
  # Normalize Unicode characters (e.g., convert ｈｅｌｌｏ to hello)
  text = unicodedata.normalize('NFKC', text)
  
  # Remove control characters but preserve newlines
  text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t')
  
  # Replace multiple whitespace with single space
  text = re.sub(r'\s+', ' ', text)
  
  return text.strip()

def analyze_text(text: str) -> None:
  """Debug helper to show Unicode categories of characters in text."""
  for char in text:
    print(f"{char!r}: {unicodedata.name(char, 'unknown')} ({unicodedata.category(char)})")

class MusicDatabase:
  """Class to manage music library operations and metadata."""
  def __init__(self, copy_folder: str | Path = None) -> None:
    self.copy_folder = self._validate_directory(copy_folder)
    self.music_files = []
    self.valid_paths = []
    self.mdb = {}
    self.index = {}
    self.id_generator = TrackIDGenerator()
    self.metadata_extractor = MetadataExtractor(self.id_generator)
    self.keys = MetadataExtractor.METADATA_KEYS  # Use keys from MetadataExtractor
    self.features = Features()
    self.scan_library()

  def _validate_directory(self, folder: str | None) -> Path:
    """
    Ask for and validate a music directory path.
    Future expansion: Could add support for direct modification of original music folder.
    """
    while True:
      folder = input("Enter music folder path: ").replace('"', '') if folder is None else folder
      fpath = Path(folder)
        
      if not fpath.exists() or not fpath.is_dir():
        folder = None
        raise FileNotFoundError("Path is not valid.")
      return fpath

  def scan_library(self):
    """Scan directory and build music database with features."""
    print(f"Retrieving files from {self.copy_folder}...")
    
    path_list = []
    for root, _, files in os.walk(self.copy_folder):
      for file in files:
        if file.endswith('.mp3'):
          # Use absolute path as string
          full_path = str(Path(root) / file)
          path_list.append(full_path)
      
    if not path_list:
      print("No music files found in this folder.")
      self.copy_folder = self._validate_directory(None)
      return self.scan_library()

    # Initialize DataFrame with proper multi-index columns
    features_df = pd.DataFrame(columns=self.features.columns())
      
    # Process files and build metadata lists
    md_lists = self.metadata_extractor.create_empty_lists()

    for file_path in tqdm(path_list, desc="Processing files"):
      try:
        # Extract metadata
        metadata, music_file = self.metadata_extractor.extract_metadata(file_path)
        
        # Append all metadata
        for key in self.keys:
          md_lists[key].append(metadata[key])
        
        # Store music file if needed later
        self.music_files.append(music_file)
        self.valid_paths.append(file_path)
        
        # Compute features
        t0 = time.time()
        track_info = str(metadata['artist'] + ' - ' + metadata['title'] + ' (' + metadata['album'] + ')')
        feature_series = self.features.compute_features(file_path)
        t1 = time.time()
        print(f"Computed features for {track_info} in {t1-t0:.2f}s")
        if feature_series is not None:
            # Convert series to DataFrame
            feature_series_df = pd.DataFrame(feature_series).T
            # Add track_info as a separate column
            feature_series_df['track_info'] = track_info
            # Convert numeric values
            numeric_cols = feature_series_df.select_dtypes(include=[np.number]).columns
            feature_series_df[numeric_cols] = feature_series_df[numeric_cols].round(4).astype(np.float32)
            # Append to features_df
            features_df = pd.concat([features_df, feature_series_df])
      except Exception as e:
        print(f"Can't process {file_path} ({repr(e)})")

    # Save features to CSV with float32 precision
    features_df.to_csv('music_features.csv', float_format='%.4f')
    print(f"Saved features for {len(features_df)} files in music_features.csv")

    # Build metadata dictionary with both string keys and UIDs
    for values in zip(*md_lists.values(), strict=True):
        track_key = f'{values[1].lower()} - {values[2].lower()} ({values[3].lower()})'
        track_data = dict(zip(self.keys, values))
        uid = values[0]
        self.mdb[track_key] = track_data
        self.index[track_key] = uid

    print(f"Good paths: {len(self.valid_paths)}, Good files: {len(md_lists['artist'])}")

  def search_tracks(self, search_key: str) -> dict:
      """Search tracks in the library by various patterns."""
      search_key = search_key.strip()
      
      # 1. UID prefix search with alias support (e.g., "TEL-", "TEL-2-")
      if len(search_key) >= 4 and search_key[:3].isupper() and search_key[3] == '-':
          prefix = search_key[:3]
          alias_index = None
          if len(search_key) > 5 and search_key[4].isdigit():
              alias_index = int(search_key[4])
          
          return dict(
              (key, data) for key, data in self.mdb.items()
              if (data['uid'].startswith(prefix) and 
                  (alias_index is None or data['uid'].startswith(f"{prefix}-{alias_index}-")))
          )
      
      # 2. Field-specific search with custom metadata support
      if ':' in search_key:
          field, value = search_key.split(':', 1)
          field = field.lower()
          value = value.lower()
          
          # Special handling for custom metadata fields
          if field in ['inst', 'beat', 'lang']:
              return dict(
                  (key, data) for key, data in self.mdb.items()
                  if data.get(field) and value in data[field].lower()
              )
          # Regular metadata fields
          elif field in self.keys:
              return dict(
                  (key, data) for key, data in self.mdb.items()
                  if value in str(data.get(field, '')).lower()
              )
      
      # 3. Default text search
      return dict(
          (key, data) for key, data in self.mdb.items()
          if search_key.lower() in key.lower()
      )

  def update_metadata(self, track_key: str, new_values: dict) -> None:
      """Update both in-memory and file metadata."""
      # Update in-memory dictionary
      self.mdb[track_key].update(new_values)
      
      # Update file metadata
      music_file = music_tag.load_file(self.mdb[track_key]['path'])
      
      # Get existing custom fields
      current_fields = CustomMetadata.unpack_fields(music_file['comment'].value)
      
      # Update with new values
      current_fields.update(new_values)
      
      # Pack back into comment
      packed = CustomMetadata.pack_fields(**current_fields)
      print(f"Saving metadata: {packed}")  # Debug print
      music_file['comment'] = packed
      music_file.save()