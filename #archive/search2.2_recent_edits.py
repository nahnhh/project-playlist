from tabulate import tabulate
import music_tag
from pathlib import Path
from hashlib import md5

class TrackIDGenerator:
   """Class to handle unique track ID generation."""
   def __init__(self):
      self._discography: dict[str, list] = {}  # {artist: [album1, album2, ...]}
      self._custom_prefixes: dict[str, str] = {}  # {artist: prefix}
   
   def set_custom_prefix(self, artist: str, prefix: str) -> None:
      """Set a custom 2-character prefix for an artist."""
      if not prefix or len(prefix) != 2:
         raise ValueError("Prefix must be exactly 2 characters")
      self._custom_prefixes[artist.lower()] = prefix.upper()
   
   def uid(self, artist: str, album: str, track_number: int) -> str:
      """
      Generate a unique track ID in the format: AA-NN-TT
      where AA = Artist prefix (2 chars)
            XXXX = Album hash (0000-FFFF)
            TT = Track number (01-99)
      """
      # Check for custom prefix first
      artist_prefix = self._custom_prefixes.get(artist.lower())
      
      # Fall back to default prefix if no custom prefix exists
      if not artist_prefix:
         artist_prefix = artist[:2].upper()
      
      # Generate a consistent album number using hash
      album_hash = md5(album.lower().encode()).hexdigest()[:4]
      
      return f"{artist_prefix}-{album_hash}-{track_number:02d}"

class MusicLibrary:
   """Class to manage music library operations and metadata."""
    
   def __init__(self, folder: str | Path | None = None) -> None:
      """Initialize music library with optional folder path."""
      self.folder: Path = self._validate_directory(folder)
      self.music_files: list[music_tag.File] = []
      self.valid_paths: list[Path] = []
      self.mdb: dict[str, dict] = {}
      self.keys: list[str] = ['uid', 'artist', 'title', 'album', 'inst', 'beat', 'lang', 'path']
      self.id_generator = TrackIDGenerator()  # Add ID generator instance
      self.scan_library()

   def _validate_directory(self, folder: str | None) -> Path:
      """
      Ask for a music directory path and validate it.
        
      Args:
         folder: Path to music directory
            
      Returns:
         Path object of validated directory
      """
      while True:
         folder = input("Enter music folder path: ").replace('"', '') if folder is None else folder
         fpath = Path(folder)
         
         if not fpath.exists() or not fpath.is_dir():
            folder = None
            raise FileNotFoundError("Path is not valid.")
         return fpath

   def scan_library(self):
      """Scan directory and build music database"""
      print(f"Retrieving files from {self.folder}...")
      path_list = list(self.folder.rglob("*.mp3"))
      
      if not path_list:
         print("No music files found in this folder.")
         self.folder = self._validate_directory(None)
         return self.scan_library()

      # Process files and build metadata lists
      md_lists = {
         'uid': [],
         'artist': [],
         'title': [], 
         'album': [],
         'inst': [],
         'beat': [],
         'lang': [],
         'path': []
      }

      for file_path in path_list:
         try:
            m = music_tag.load_file(file_path)
            # Extract values once to avoid repeated property access
            artist = m['artist'].value
            album = m['album'].value
            title = m['title'].value
            track_num = int(m['tracknumber'].value or 1)
            
            # Generate UID and append all metadata at once
            md_lists['uid'].append(self.id_generator.uid(artist, album, track_num))
            md_lists['artist'].append(m['artist'].value)
            md_lists['title'].append(m['title'].value)
            md_lists['album'].append(m['album'].value)
            md_lists['inst'].append(None)
            md_lists['beat'].append(None)
            md_lists['lang'].append(None)
            md_lists['path'].append(file_path)
            
            # Only store music file if needed later
            self.music_files.append(m)
            self.valid_paths.append(file_path)
            
         except Exception as e:
            print(f"Can't retrieve data from {file_path} ({str(e)})")

      # Build metadata dictionary with both string keys and UIDs
      for values in zip(*md_lists.values(), strict=True):
         uid = values[0]
         track_key = f'{values[1].lower()} - {values[2].lower()} ({values[3].lower()})'
         track_data = dict(zip(self.keys, values))
         self.mdb[track_key] = track_data  # Keep text for searching
         self.mdb[uid] = track_data        # Keep UID for internal reference

      print(f"Good paths: {len(self.valid_paths)}, Good files: {len(md_lists['artist'])}")

   def search_tracks(self, search_key: str) -> dict:
      """Search tracks in the library by user-friendly string"""
      return dict(
         (key, data) for key, data in self.mdb.items() 
         if search_key.lower() in key.lower() and not key.startswith('AA-')  # Exclude UID keys from search results
      )

class PlaylistMaker:
   """Class to handle playlist operations."""
   def __init__(self, music_library: MusicLibrary):
      self.library = music_library

   def create_playlist(self, tracks: list[str], output_path: str | Path) -> None:
      """Create an M3U playlist"""
      output_path = Path(output_path)
      
      # Ensure parent directory exists
      output_path.parent.mkdir(parents=True, exist_ok=True)
      
      with output_path.open('w', encoding='utf-8') as f:
         f.write('#EXTM3U\n')
         for track in tracks:
            track_data = self.library.mdb[track]
            f.write(f'#EXTINF:-1,{track_data["artist"]} - {track_data["title"]}\n')
            f.write(f'{track_data["path"]}\n')

   def append_to_playlist(self, tracks: list[str], playlist_path: str) -> None:
      """Append tracks to an existing playlist"""
      # If playlist doesn't exist, create it
      if not Path(playlist_path).exists():
         return self.create_playlist(tracks, playlist_path)
            
      # If it exists, append to it
      with open(playlist_path, 'a', encoding='utf-8') as f:
         for track in tracks:
            track_data = self.library.mdb[track]
            f.write(f'#EXTINF:-1,{track_data["artist"]} - {track_data["title"]}\n')
            f.write(f'{str(track_data["path"])}\n')

class EditHistory:
    """Class to manage history of edited and selected tracks."""
    MAX_HISTORY = 5  # Make this a class constant
    
    def __init__(self, history_file: str = "edit_history.txt"):  # Remove max_history parameter
        self.history_file = Path(history_file)
        self.tracks = self._load_history()

    def _load_history(self) -> list[str]:
        """Load track history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    # Strip whitespace and filter out empty lines
                    return [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                print(f"Couldn't load history: {e}")
        return []

    def add_track(self, track: str) -> None:
        """Add a track to history and save to file."""
        if not track.strip():  # Skip empty strings
            return
            
        # Remove if already exists to avoid duplicates
        if track in self.tracks:
            self.tracks.remove(track)
        
        # Add to end of list (most recent)
        self.tracks.append(track)
        
        # Keep only last N items
        self.tracks = self.tracks[-self.MAX_HISTORY:]
        
        # Save to file
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                for t in self.tracks:
                    f.write(f"{t.strip()}\n")  # Ensure clean lines
        except Exception as e:
            print(f"Couldn't save to history: {e}")

    def get_recent(self) -> list[str]:
        """Get list of recent tracks."""
        return self.tracks.copy()

class InputPrompts:
    """Class for handling generic user input prompts."""
    def __init__(self):
        self.edit_history = EditHistory()

    @staticmethod
    def prompt_yn(question: str, default: str | None = None) -> bool:
        """Yes/No prompt with optional default."""
        choices = ("", "y", "n") if default in ("yes", "no") else ("y", "n")
        hint = "Y/n" if default == "yes" else "y/n"
        hint = "y/N" if default == "no" else hint
        reply = None
        while reply not in choices:
            reply = input(f"{question}? [{hint}] ").lower()
        return (reply == "y") if default != "yes" else (reply in ("", "y"))

    def prompt_choose(self,
        question: str, 
        displayed_options: list | None = None, 
        inputs: list | None = None,
        allow_multiple: bool = False,
        use_letters: bool = False,
        search_history: EditHistory | None = None
    ) -> str | list[str]:
        """Enhanced choice prompt supporting multiple selections and letter inputs."""
        self.question = question
        self.displayed_options = displayed_options
        self.inputs = inputs if inputs is not None else displayed_options
        self.allow_multiple = allow_multiple
        self.use_letters = use_letters

        # Always display the question
        print(f"\n{self.question}?")

        if self.displayed_options is not None:
            try:
                list(zip(self.displayed_options, self.inputs))  # Validate lengths match
                for i, option in enumerate(self.displayed_options, 1):
                    if self.use_letters:
                        print(f"{self.inputs[i-1]}: {option}")
                    else:
                        print(f"{i}: {option}")
            except Exception as e:
                print(f"[options] and [actions] must have same length ({e})")
                return []

        while True:
            try:
                if self.allow_multiple and not self.use_letters:
                    print("Enter numbers separated by spaces: ")
                    nums = input().split()
                    response = [self.inputs[int(n)-1] for n in nums if 0 < int(n) <= len(self.inputs)]
                    if response:  # If at least one valid selection
                        return response
                else:
                    response = input().lower()
                    if self.use_letters:
                        if response in self.inputs:
                            return response
                    else:
                        idx = int(response)
                        if 0 < idx <= len(self.inputs):
                            return self.inputs[idx-1]
                print("Invalid input. Please try again.")
            except (ValueError, IndexError):
                print("Invalid input. Please try again.")

    def save_edited_track(self, track: str) -> None:
        """Save a track to edit history"""
        self.edit_history.add_track(track)

class MetadataEditor:
    """Class to handle metadata editing operations."""
    
    def __init__(self, music_library: MusicLibrary):
        self.library = music_library
        self.editable_fields = ['inst', 'beat', 'lang', 'artist', 'title', 'album']

    def apply_changes(self, track_key: str, new_values: dict) -> None:
        """Apply metadata changes to a track"""
        track_data = self.library.mdb[track_key]
        for field, value in new_values.items():
            track_data[field] = value
        self.library.mdb[track_key] = track_data

class UserInterface:
   """Class to handle user interaction and display."""
   
   def __init__(self, library: MusicLibrary) -> None:
      self.library = library
      self.playlist_maker = PlaylistMaker(library)
      self.md_editor = MetadataEditor(library)
      self.lines: list[str] = []
      self.prompts = InputPrompts()
      self.search_history = EditHistory()

   def print_read(self, results: dict):
      """Display track metadata"""
      # More readable: use consistent f-strings and join for better performance
      line_break = '\n===================================\n'
      read_results = [
         f'Inst: {track["inst"]} | Beat: {track["beat"]} | Lang: {track["lang"]}\n'
         f'Title: {track["title"]}\n'
         f'Artist: {track["artist"]}\n'
         f'Album: {track["album"]}'
         for track in results.values()
      ]
      
      print(f'{line_break}\n{line_break.join(read_results)}\n{line_break}')

   def print_edit(self, results: dict):
      """Display editable track list"""
      lines = [
         f'{track["artist"].lower()} - {track["title"].lower()} ({track["album"].lower()})'
         for track in results.values()
      ]
      rows = [
         (i+1, 
          self.trunc(track["artist"], 16),
          self.trunc(track["title"], 17),
          self.trunc(track["album"], 10))
         for i, track in enumerate(results.values())
      ]
      
      print("\n" + tabulate(rows, headers=['','Artist','Title','Album'], 
                           maxcolwidths=[None, 27, 27, 27]) + "\n")
      print("EDIT mode. Above are the songs found.")
      return lines  # Return instead of storing as instance variable

   @staticmethod
   def trunc(s: str, length: int) -> str:
      """Truncate string to specified length."""
      s = str(s)
      return (s[:length-2] + '..') if len(s) > length+2 else s

   def run_search(self):
      """Main search interface"""
      # Main menu choice
      choice = self.prompts.prompt_choose("What would you like to do",
                                 ["Read metadata", "Edit metadata", "Create playlist"])
   
   # Show recent tracks
      recent_tracks = self.search_history.get_recent()
      if recent_tracks:
         print("\nRecent tracks:")
         for i, track in enumerate(recent_tracks, 1):
            print(f"{i}: {track}")
   
   # Search for keyword or select from history
      while True:
         search_input = input("Enter a number to select from history, or type to search: ")
         if search_input.isdigit() and 0 < int(search_input) <= len(recent_tracks):
            results = self.library.search_tracks(recent_tracks[int(search_input) - 1])
         else:
            results = self.library.search_tracks(search_input)
         if results:
            break
         print("No track found. Try again sweetie!")

      if choice == "Read metadata":
         self.print_read(results)
         if len(results) == 1:
            print("READ mode. Above is the song found.")
         else:
            print("READ mode. Above are the songs found.")
         
      elif choice == "Edit metadata":
         if len(results) == 1:
            self.print_read(results)
            selected_track = list(results.keys())[0]
            print("EDIT mode. Above is the song found.")
         else:
            self.print_edit(results)
            selected_track = self.prompts.prompt_choose("Select a track to edit", displayed_options=None, inputs=self.lines)
         self.edit_track(selected_track)
         self.search_history.add_track(selected_track)
      
      elif choice == "Create playlist":
         selected_tracks = self.prompts.prompt_choose(
               "Select tracks to make a playlist", None, self.lines, allow_multiple=True)
         while True:
               output_path = input("Enter playlist file path (.m3u): ").strip()
               if output_path.endswith('.m3u'):
                  break
               print("Please provide a valid .m3u file path")
         self.playlist_maker.create_playlist(selected_tracks, output_path)

   def edit_track(self, track_key: str) -> None:
      """Handle the UI portion of track editing"""
      track_data = self.library.mdb[track_key]
      print(f"\nEditing: {track_data['artist']} - {track_data['title']}")
      
      while True:
         # Get all new values first
         new_values = {}
         for field in self.md_editor.editable_fields:
               current = track_data[field]
               new_value = input(f"{field.capitalize()} [{current or 'None'}]: ").strip()
               if new_value == 'q':
                  print("Edit cancelled.")
                  return
               if new_value:
                  new_values[field] = new_value
         
         # Display the changes
         print("\nProposed changes:")
         for field in self.md_editor.editable_fields:
               old_val = track_data[field] or 'None'
               new_val = new_values.get(field, old_val)
               print(f"{field.capitalize()}: {old_val} -> {new_val}")
         
         # Confirm changes
         choice = self.prompts.prompt_choose(
               "Apply these changes",
               ["Yes", "Redo", "Quit"],
               ["y", "r", "q"],
               use_letters=True
         )
         
         if choice == "y":
               self.md_editor.apply_changes(track_key, new_values)
               self.prompts.save_edited_track(track_key)
               print("Changes applied.")
               break
         elif choice == "r":
               print("\nRedoing edit...")
               continue
         else:  # choice == "q"
               print("Changes discarded.")
               break