import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from audio_extract.folder_features import get_features_from_folder

if __name__ == "__main__":
  base_path = r'D:\#ALLMYMUSIC - Copy'
  get_features_from_folder(base_path, split=5)