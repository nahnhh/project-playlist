from pathlib import Path

class PlaylistMaker:
   """Class to handle playlist operations."""
   def __init__(self, music_library):
      self.library = music_library

   def create_playlist(self, tracks: list[str], filename: str | Path) -> None:
      """Create an M3U playlist"""
      filename = Path(filename)
      
      # Ensure parent directory exists
      filename.parent.mkdir(parents=True, exist_ok=True)
      
      with filename.open('w', encoding='utf-8') as f:
         f.write('#EXTM3U\n')
         for track in tracks:
            track_data = self.library.mdb[track]
            f.write(f'#EXTINF:-1,{track_data["artist"]} - {track_data["title"]}\n')
            f.write(f'{track_data["path"]}\n')

   def append_to_playlist(self, tracks: list[str], filename: str) -> None:
      """Append tracks to an existing playlist"""
      # If playlist doesn't exist, create it
      if not Path(filename).exists():
         return self.create_playlist(tracks, filename)
            
      # If it exists, append to it
      with open(filename, 'a', encoding='utf-8') as f:
         for track in tracks:
            track_data = self.library.mdb[track]
            f.write(f'#EXTINF:-1,{track_data["artist"]} - {track_data["title"]}\n')
            f.write(f'{str(track_data["path"])}\n')