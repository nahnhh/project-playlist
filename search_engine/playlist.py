from pathlib import Path
from .databases.playlist_history import PlaylistHistory

class PlaylistMaker:
   """Class to handle playlist operations."""
   DEFAULT_PLAYLIST = "playlist.m3u"
   
   def __init__(self, music_library):
      """Initialize PlaylistMaker with a music library."""
      self.library = music_library
      self.playlist_history = PlaylistHistory(music_library)
   
   def write_to_playlist(self, tracks: list[str], filename: str | Path = None, append: bool = False) -> None:
      """Write tracks to an M3U playlist
      
      Args:
          tracks: List of track IDs to write
          filename: Target playlist file path
          append: If True, append to existing playlist; if False, create/overwrite
      """
      
      # If appending to non-existent file, create it instead
      if append and not filename.exists():
         return self.write_to_playlist(tracks, filename, append=False)
            
      mode = 'a' if append else 'w'
      with filename.open(mode, encoding='utf-8') as f:
         # Write header only for new playlists
         if not append:
            f.write('#EXTM3U\n')
         
         for track in tracks:
            track = self.library.mdb[track]
            relative_path = str(track["path"]).replace("\\","/")
            relative_path = relative_path.replace(str(self.library.copy_folder).replace("\\","/"), "..")
            f.write(f'#EXTINF:-1,{track["artist"]} - {track["title"]}\n')
            f.write(f'{relative_path}\n')

   def create_playlist(self, tracks: list[str], filename: str | Path = None) -> None:
      """Create a new M3U playlist"""
      return self.write_to_playlist(tracks, filename, append=False)

   def append_to_playlist(self, tracks: list[str], filename: str | Path = None) -> None:
      """Append tracks to an existing playlist"""
      return self.write_to_playlist(tracks, filename, append=True)

   def handle_playlist_creation(self, selected_tracks: list[str], input_handler) -> None:
      """Handle the playlist creation workflow including file selection and overwrite checks"""
      while True:
         filename = input(f"Enter name/path of the playlist file (default: {self.DEFAULT_PLAYLIST}): ").strip()
         # Convert to Path object and handle default case
         playlist_path = Path(filename if filename else self.DEFAULT_PLAYLIST)
         
         # Add .m3u extension if not present
         if not playlist_path.suffix == '.m3u':
            playlist_path = playlist_path.with_suffix('.m3u')
         
         # Ensure parent directory exists
         try:
            playlist_path.parent.mkdir(parents=True, exist_ok=True)
            break
         except PermissionError:
            print("Cannot create directory - permission denied. Please choose a different location.")
            continue
      
      if playlist_path.exists():
         cre_app = input_handler.prompt_choose(
            "File already exists. Overwrite or append to the playlist?",
            ["Overwrite", "Append"], 
            inputs="num"
         )
         if cre_app == "Overwrite":
            print(f"Overwriting playlist at {playlist_path}...")
            self.create_playlist(selected_tracks, playlist_path)
            self.playlist_history.add_playlist(selected_tracks, playlist_path)
         elif cre_app == "Append":
            print(f"Appending to playlist at {playlist_path}...")
            self.append_to_playlist(selected_tracks, playlist_path)
            self.playlist_history.add_playlist(selected_tracks, playlist_path)
      else:
         print(f"Creating new playlist at {playlist_path}...")
         self.create_playlist(selected_tracks, playlist_path)
         self.playlist_history.add_playlist(selected_tracks, playlist_path)