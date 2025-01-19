from interface.display import trunc
from audio_extract.md_edit import CustomMetadata
from .databases.track_history import TrackHistory
from .databases.playlist_history import PlaylistHistory

class SearchEngine:
  """Handles all search-related operations"""
  def __init__(self, library, input_handler, display_formatter):
    self.library = library
    self.input_handler = input_handler
    self.display = display_formatter
    self.track_history = TrackHistory(library)
    self.playlist_history = PlaylistHistory(library)
    # Cache commonly used values
    self._mdb = library.mdb
    self._library_keys = library.keys
    self._search_cache = {}  # Cache recent search results

  def show_recent_tracks(self) -> list[str]:
    """Display recent tracks and return them"""
    recent_tracks = self.track_history.get_recent()
    if recent_tracks:
      print("\nRecent tracks:")
      for i, track in enumerate(recent_tracks, 1):
        print(f"{i}: {trunc(track, 60)}")
    return recent_tracks
  
  def show_recent_playlists(self) -> list[str]:
    """Display recent playlists and return them"""
    recent_playlists = self.playlist_history.get_recent()
    if recent_playlists:
      print("\nRecent playlists:")
      for i, playlist in enumerate(recent_playlists, 1):
        print(f"{i}: {trunc(playlist, 60)}")
    return recent_playlists

  def search(self, mode: str | None = None) -> dict:
    """Main search interface with history support"""
    recent_items = []
    if mode == "Create playlist":
      recent_items = self.playlist_history.get_recent()
      if recent_items:
        print("\nRecent playlists:")
        for i, (display_str, tracks) in enumerate(recent_items, 1):
          print(f"{i}: {display_str}")
    elif mode == "Edit metadata":
      recent_items = self.track_history.get_recent()
      if recent_items:
        print("\nRecent tracks:")
        for i, track in enumerate(recent_items, 1):
          print(f"{i}: {trunc(track, 60)}")
  
    while True:
      query = self.input_handler.prompt_choose(
          "Enter a number to select from history, or type to search:"
      )
      
      # Handle history selection or direct search
      if query.isdigit() and recent_items and 0 < int(query) <= len(recent_items):
        if mode == "Create playlist":
          # Return tracks directly from history
          _, tracks = recent_items[int(query) - 1]
          return {track: self.library.mdb[track] for track in tracks}
        else:
          results = self._search_tracks(recent_items[int(query) - 1])
      else:
        results = self._search_tracks(query)
      
      if results:
        return results
      print("No tracks found. Try again sweetie!")

  def _search_tracks(self, search_key: str) -> dict:
    """Search tracks by various patterns"""
    search_key = search_key.strip()
    # 1. UID prefix search with alias support (e.g., "TEL-", "TEL-2-")
    if len(search_key) >= 3 and search_key[:3].isupper():
      return self._search_by_uid_prefix(search_key)
    # 2. Field-specific search with custom metadata support
    elif ':' in search_key:
      return self._search_by_field(search_key)
    # 3. Default text search
    else:
      return self._search_by_text(search_key)

  def _search_by_uid_prefix(self, search_key: str) -> dict:
    """
    Search by UID prefix with support for multiple artists.
    Format: AAA-N[-BBB-M]  where BBB-M are optional collaborator prefixes
    """
    search_key = search_key.upper()
    prefixes = [p.strip() for p in search_key.split('-') if p.strip()]
    
    results = {}
    for key, data in self._mdb.items():
      uid = data['uid'].upper()
      # Check if all searched prefixes exist in the UID
      if all(p in uid.split('-') for p in prefixes):
        results[key] = data
        
    return results

  def _search_by_field(self, search_key: str) -> dict:
    """Search by specific field including custom metadata from comments."""
    field, value = search_key.split(':', 1)
    field = field.lower()
    value = value.lower()
    
    # Use set lookup for better performance
    if field in {'inst', 'beat', 'lang'}:
      return {
        key: data for key, data in self._mdb.items()
        if (custom_fields := CustomMetadata.unpack_fields(data.get('comment'))) 
        and custom_fields.get(field) 
        and value in custom_fields[field].lower()
      }
    
    if field in self._library_keys:
      return {
        key: data for key, data in self._mdb.items()
        if value in str(data.get(field, '')).lower()
      }
    
    return {}

  def _search_by_text(self, search_key: str) -> dict:
    """Default text search in track key"""
    search_key = search_key.lower()  # Convert once instead of multiple times
    return {
      key: data for key, data in self._mdb.items()
      if search_key in key.lower()
    } 