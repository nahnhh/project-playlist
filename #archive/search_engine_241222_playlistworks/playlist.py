from pathlib import Path

class PlaylistMaker:
   """Class to handle playlist operations."""
   DEFAULT_PLAYLIST = "playlist.m3u"

   def __init__(self, music_library):
      """Initialize PlaylistMaker with a music library."""
      self.library = music_library

   def create_playlist(self, tracks: list[str],
                      filename: str | Path = None) -> None:
      """Create an M3U playlist"""
      filename = Path(filename if filename is not None else self.DEFAULT_PLAYLIST)
      
      if not filename.suffix == '.m3u':
         filename = filename.with_suffix('.m3u')
      
      with filename.open('w', encoding='utf-8') as f:
         f.write('#EXTM3U\n')
         for track in tracks:
            track_data = self.library.mdb[track]
            f.write(f'#EXTINF:-1,{track_data["artist"]} - {track_data["title"]}\n')
            f.write(f'{track_data["path"]}\n')

   def append_to_playlist(self, tracks: list[str], filename: str | Path = None) -> None:
      """Append tracks to an existing playlist"""
      filename = Path(filename if filename is not None else self.DEFAULT_PLAYLIST)
      
      if not filename.suffix == '.m3u':
         filename = filename.with_suffix('.m3u')
      
      # If playlist doesn't exist, create it
      if not filename.exists():
         return self.create_playlist(tracks, filename)
            
      # If it exists, append to it
      with filename.open('a', encoding='utf-8') as f:
         for track in tracks:
            track_data = self.library.mdb[track]
            f.write(f'#EXTINF:-1,{track_data["artist"]} - {track_data["title"]}\n')
            f.write(f'{str(track_data["path"])}\n')

   def handle_playlist_creation(self, selected_tracks: list[str], input_handler) -> None:
      """Handle the playlist creation workflow including file selection and overwrite checks"""
      while True:
         filename = input(f"Enter name/path of the playlist file (default: {self.DEFAULT_PLAYLIST}): ").strip()
         if not filename:  # If empty input, use default
            filename = self.DEFAULT_PLAYLIST
         # Add .m3u extension if not provided
         if not filename.endswith('.m3u'):
            filename = f"{filename}.m3u"
         
         # Ensure parent directory exists
         playlist_path = Path(filename)
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
            print(f"Overwriting playlist at {playlist_path}")
            self.create_playlist(selected_tracks, playlist_path)
         elif cre_app == "Append":
            print(f"Appending to playlist at {playlist_path}")
            self.append_to_playlist(selected_tracks, playlist_path)
      else:
         print(f"Creating new playlist at {playlist_path}")
         self.create_playlist(selected_tracks, playlist_path)