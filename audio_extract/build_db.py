import os
from pathlib import Path
from .md_extract import MetadataExtractor
from .uid_gen import TrackIDGenerator
from .features_compute import FeaturesCompute
from .artist_prefixes import ArtistPrefixes
from .features_extract import FeatureExtractor

class MusicDatabase:
  """Class to manage music library operations and metadata."""
  def __init__(self, copy_folder: str | Path = None, depth: bool = True) -> None:
    self.copy_folder = self._validate_directory(copy_folder)
    self.depth = depth
    self.mdb = {}
    self.index = {}
    
    # Initialize prefixes right away
    self.prefixes = ArtistPrefixes()  # Save reference to prefixes
    self.id_generator = TrackIDGenerator()
    self.metadata_extractor = MetadataExtractor(self.id_generator)
    # Get metadata keys from extractor
    self.keys = self.metadata_extractor.METADATA_KEYS
    self._scan_library()
    

  def _print_prefixes(self):
    # Print all prefixes after scanning
    print("\nAll Artist Prefixes:")
    self.prefixes.print_all_prefixes()

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

  def _scan_library(self, depth: bool = True, extract_features: bool = False, 
               output_file: str = 'music_features.csv'):
    """Scan directory and build music database with features."""
    self.extract_features = extract_features
    self.output_file = output_file
    if extract_features is True:
      self.features = FeaturesCompute()
    #print(f"Retrieving files from {self.copy_folder}...")
    
    self.depth = 1 if self.depth is False else 1 if depth is False else 100
    copy_folder = os.path.abspath(self.copy_folder)

    path_list = []
    for root, _, files in os.walk(copy_folder):
      if root[len(copy_folder):].count(os.sep) < self.depth:
        for file in files:
          if file.endswith('.mp3'):
            # Use absolute path as string
            full_path = str(Path(root) / file)
            path_list.append(full_path)
      
    if not path_list:
      print("No music files found in this folder.")
      self.copy_folder = self._validate_directory(None)
      return self._scan_library()
    
    # Process files and build metadata lists
    self.mdb, self.index, self.df = self.metadata_extractor.extract_metadata(path_list)
    # Extract features if needed
    if self.extract_features:
        output_dir = Path(self.copy_folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / self.output_file
        FeatureExtractor.extract_features(path_list=path_list, uids=self.df.index, output_file=output_file)
