import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from audio_extract.build_db import MusicDatabase
from audio_extract.uid_gen import TrackIDGenerator

def get_features(base_path, split=[15, 70, 15]):
  folder_list = []

  # Get all subfolders
  for root, dirs, files in os.walk(base_path):
      folder_path = Path(root)
      
      # Check if current folder has MP3 files directly
      has_mp3 = any(file.endswith('.mp3') for file in files)
      has_csv = any(file.endswith('.csv') for file in files)
      
      if not has_mp3:
          print(f"Skipping empty folder: {folder_path}")
      elif has_csv:
          print(f"Skipping folder with CSV: {folder_path}")
      else:
          folder_list.append(str(folder_path))

  # Process each folder
  id_gen = TrackIDGenerator()
  for folder in folder_list:
      first_track = next(Path(folder).glob('*.mp3'), None)
      if first_track:
          # Create database for this folder
          print(f"Getting metadata of {folder}...")
          database = MusicDatabase(copy_folder=folder, depth=False)
          base_uid = '#' + database.df.iloc[0].name[:-3]
          print(f"Processing {folder} --> {base_uid}_[1,2,..].csv")
          database._scan_library(depth=False, extract_features=True, output_file=f'{base_uid}.csv', split=split)
          print(f"Processed {folder} --> {base_uid}_[1,2,..].csv")

if __name__ == "__main__":
  base_path = r'D:\#ALLMYMUSIC - Copy'
  get_features(base_path, split=[20, 20, 20, 20, 20])