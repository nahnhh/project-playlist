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
    
   def __init__(self, folder: str | None = None) -> None:
      """Initialize music library with optional folder path."""
      self.folder = self._validate_directory(folder)
      self.music_files: list = []
      self.valid_paths: list[Path] = []
      self.mdb: dict = {}
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

      # Process files and extract metadata
      for i, file_path in enumerate(path_list):
         try:
            m = music_tag.load_file(file_path)
            self.music_files.append(m)
            self.valid_paths.append(file_path)
         except Exception as e:
            print(f"{str(e)}: Can't retrieve data from {file_path}")

      # Initialize metadata lists
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

      # Process each music file
      for m in self.music_files:
         md_lists['uid'].append(
            self.id_generator.uid(m['artist'].value, m['album'].value, int(m['tracknumber'].value | 1)))
         md_lists['artist'].append(m['artist'].value)
         md_lists['title'].append(m['title'].value)
         md_lists['album'].append(m['album'].value)
         md_lists['inst'].append(None)
         md_lists['beat'].append(None)
         md_lists['lang'].append(None)
         md_lists['path'].append(self.valid_paths[self.music_files.index(m)])

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

   def create_playlist(self, tracks: list[str], output_path: str) -> None:
      """Create an M3U playlist"""
      with open(output_path, 'w', encoding='utf-8') as f:
         f.write('#EXTM3U\n')
         for track in tracks:
               track_data = self.library.mdb[track]
               f.write(f'#EXTINF:-1,{track_data["artist"]} - {track_data["title"]}\n')
               f.write(f'{str(track_data["path"])}\n')

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

class MetadataEditor:
   """Class to handle metadata editing operations."""
   
   def __init__(self, music_library: MusicLibrary, ui):
      self.library = music_library
      self.ui = ui
      self.editable_fields = ['inst', 'beat', 'lang', 'artist', 'title', 'album']

   def edit_track(self, track_key: str) -> None:
      """
      Edit metadata for selected track.
      
      Args:
         track_key: The search key for the track to edit
      """
      track_data = self.library.mdb[track_key]
      
      print(f"\nEditing: {track_data['artist']} - {track_data['title']}")
      
      while True:
         # Get all new values first
         new_values = {}
         for field in self.editable_fields:
            current = track_data[field]
            new_value = input(f"{field.capitalize()} [{current or 'None'}]: ").strip()
            if new_value == 'q':  # Allow quitting at any time
               print("Edit cancelled.")
               return 0
            # Only add to new_values if there's actual input
            if new_value:
               new_values[field] = new_value
         
         # Display the changes
         print("\nProposed changes:")

         for field in self.editable_fields:
            old_val = track_data[field] or 'None'
            new_val = new_values.get(field, old_val)  # Use get() with default value
            print(f"{field.capitalize()}: {old_val} -> {new_val}")
         
         # Confirm changes with options to apply, redo, or quit
         choice = self.ui.prompt_choose(
            "Apply these changes",
            ["Yes", "Redo", "Quit"],
            ["y", "r", "q"],
            use_letters=True  # Enable letter input mode
         )
         
         if choice == "y":
            for field, value in new_values.items():
               track_data[field] = value
            print("Changes applied.")
            break
         elif choice == "r":
            print("\nRedoing edit...")
            continue
         else:  # choice == "q"
            print("Changes discarded.")
            break
      
      # Update both entries in mdb (the text key and UID key versions)
      self.library.mdb[track_key] = track_data

class UserInterface:
   """Class to handle user interaction and display."""
   
   def __init__(self, library: MusicLibrary) -> None:
      """
      Initialize user interface.
      
      Args:
         library: MusicLibrary instance to interact with
      """
      self.library = library
      self.playlist_maker = PlaylistMaker(library)
      self.md_editor = MetadataEditor(library, self)  # Add editor instance
      self.lines: list[str] = []

   def prompt_yn(self, question: str, default: str | None = None) -> bool:
      """Yes/No prompt with optional default."""
      choices = ("", "y", "n") if default in ("yes", "no") else ("y", "n")
      hint = "Y/n" if default == "yes" else "y/n"
      hint = "y/N" if default == "no" else hint
      reply = None
      while reply not in choices:
         reply = input(f"{question}? [{hint}] ").lower()
      return (reply == "y") if default != "yes" else (reply in ("", "y"))

   def prompt_choose(
      self, 
      question: str, 
      displayed_options: list, 
      actions: list | None = None, 
      allow_multiple: bool = False,
      use_letters: bool = False
   ) -> str | list[str]:
      """
      Enhanced choice prompt supporting multiple selections and letter inputs.
      
      Args:
         question: Question to display
         displayed_options: List of options to show
         actions: List of corresponding actions
         allow_multiple: Whether multiple selections are allowed
         use_letters: Whether to accept single-letter inputs instead of numbers
         
      Returns:
         Selected action(s)
      """
      if actions is None:
         actions = displayed_options
      if displayed_options is not None:
         try:
            list(zip(displayed_options, actions))  # Validate lengths match
            print(f"\n{question}?")
            for i, option in enumerate(displayed_options, 1):
               if use_letters:
                  print(f"{actions[i-1]}: {option}")
               else:
                  print(f"{i}: {option}")
         except Exception as e:
            print(f"[options] and [actions] must have same length ({e})")
            return []

      while True:
         try:
            if allow_multiple and not use_letters:
               print("Enter numbers separated by spaces (e.g., '1 3 4')")
               nums = input().split()
               response = [actions[int(n)-1] for n in nums if 0 < int(n) <= len(actions)]
               if response:  # If at least one valid selection
                  return response
            else:
               response = input().lower()
               if use_letters:
                  if response in actions:
                     return response
               else:
                  idx = int(response)
                  if 0 < idx <= len(actions):
                     return actions[idx-1]
            print("Please enter valid input")
         except (ValueError, IndexError):
            print("Invalid input. Please try again.")

   def print_read(self, results: dict):
      """Display track metadata"""
      read_results = []
      for track in results.values():
         read_template = (
               f'Inst: {track["inst"]} | Beat: {track["beat"]} | Lang: {track["lang"]}\n'
               f'Title: {track["title"]}\n'
               f'Artist: {track["artist"]}\n'
               f'Album: {track["album"]}'
         )
         read_results.append(read_template)
      line_break = '\n\n===================================\n\n'
      print(line_break + f'{line_break}'.join(read_results) + line_break)

   def print_edit(self, results: dict):
      """Display editable track list"""
      self.lines = []
      rows = []
      for i, track in enumerate(results.values()):
         line = f'{track["artist"].lower()} - {track["title"].lower()} ({track["album"].lower()})'
         self.lines.append(line)
         row = (i+1, self.trunc(track["artist"], 16), 
               self.trunc(track["title"], 17), 
               self.trunc(track["album"], 10))
         rows.append(row)
      print("\n" + tabulate(rows, headers=['','Artist','Title','Album'], 
                            maxcolwidths=[None, 27, 27, 27]))
      print("\nEDIT mode. Above are the songs found.")

   @staticmethod
   def trunc(s: str, length: int) -> str:
      """
      Truncate string to specified length.
      
      Args:
         text: String to truncate
         length: Maximum length
         
      Returns:
         Truncated string
      """
      s = str(s)
      return (s[:length-2] + '..') if len(s) > length+2 else s

   def run_search(self):
      """Main search interface"""
      while True:
         search_key = input("Search for a track: ")
         results = self.library.search_tracks(search_key)
         if results:
               break
         print("No track found. Try again sweetie!")

      choice = self.prompt_choose("What would you like to do",
                                  ["Read metadata", "Edit metadata", "Create playlist"])
      
      if choice == "Read metadata":
         self.print_read(results)
         
      elif choice == "Edit metadata":
         self.print_edit(results)
         selected_tracks = self.prompt_choose(
            "Select tracks to edit", None, self.lines)
         self.md_editor.edit_track(selected_tracks)
         
      elif choice == "Create playlist":
         selected_tracks = self.prompt_choose(
            "Select tracks to make a playlist", None, self.lines, allow_multiple=True)
         while True:
            output_path = input("Enter playlist file path (.m3u): ").strip()
            if output_path.endswith('.m3u'):
               break
            print("Please provide a valid .m3u file path")
         self.playlist_maker.create_playlist(selected_tracks, output_path)