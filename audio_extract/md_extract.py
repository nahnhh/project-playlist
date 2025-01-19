import music_tag
from .uid_gen import TrackIDGenerator
from .md_edit import CustomMetadata
import pandas as pd

class MetadataExtractor:
    # Define keys as class attribute
    METADATA_KEYS = [
        'uid',
        'artist',
        'title', 
        'album',
        'inst',
        'beat',
        'lang',
        'path'
    ]

    def __init__(self, id_generator: TrackIDGenerator):
        self.id_generator = id_generator

    def extract_metadata_single(self, file_path):
      """Extract metadata from a music file."""
      m = music_tag.load_file(file_path)
      
      # Extract and clean values, ensure None becomes empty string
      artist = m['artist'].value or ''
      album = m['album'].value or ''
      title = m['title'].value or ''
      track_num = int(m['tracknumber'].value or 1)
      
      # Generate UID using the id_generator
      uid = self.id_generator.uid(artist=artist, album=album, track_number=track_num)
      
      # Safely handle comment field
      try:
          custom_fields = CustomMetadata.unpack_fields(m['comment'].value)
      except:
          # If comment reading fails, use empty defaults
          custom_fields = {'inst': '', 'beat': '', 'lang': ''}
      
      # Build metadata dictionary
      metadata = {
          'uid': uid,
          'artist': artist,
          'title': title,
          'album': album,
          'inst': custom_fields['inst'],
          'beat': custom_fields['beat'],
          'lang': custom_fields['lang'],
          'path': str(file_path)
      }
      
      return metadata, m
    
    def extract_metadata(self, path_list):
      self.bad_files = []
      self.music_files = []
      self.valid_paths = []
      """Extract metadata from a list of music files."""
      md_lists = self.create_empty_lists()
      for file_path in path_list:
        try:
          metadata, m = self.extract_metadata_single(file_path)
          # Append all metadata
          for key in self.METADATA_KEYS:
            md_lists[key].append(metadata[key])
          # Store music file if needed later
          self.music_files.append(m)
          self.valid_paths.append(file_path)
        except Exception as e:
          print(f"Can't process metadata for {file_path} ({repr(e)})")
          self.bad_files.append(file_path)
      
      #print(f"Good paths: {len(self.valid_paths)}, Good files: {len(self.music_files)}")
      if self.bad_files:
        print(f"==========BAD FILES==========")
        for bad_file in self.bad_files:
          print(bad_file)
        print(f"==========BAD FILES==========")
      
      # Build dictionaries and DataFrame
      mdb, index, metadata_df = self.build_metadata_dict(md_lists)

      return mdb, index, metadata_df

    @classmethod
    def create_empty_lists(cls) -> dict:
        """Create empty metadata lists dictionary"""
        return {key: [] for key in cls.METADATA_KEYS} 

    def build_metadata_dict(self, md_lists):
        """Convert metadata lists to dictionary and DataFrame"""
        # Create dictionary with string keys and UIDs
        mdb = {}
        index = {}
        
        for values in zip(*md_lists.values(), strict=True):
          track_key = f'{values[1].lower()} - {values[2].lower()} ({values[3].lower()})'
          track_data = dict(zip(self.METADATA_KEYS, values))
          uid = values[0]
          mdb[track_key] = track_data
          index[track_key] = uid
            
        # Create DataFrame
        metadata_df = pd.DataFrame.from_dict(md_lists)
        metadata_df = metadata_df.set_index('uid')

        return mdb, index, metadata_df