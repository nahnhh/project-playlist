from .interface.display import trunc
from .libraries.track_history import TrackHistory
from .md_edit import CustomMetadata

class SearchEngine:
    """Handles all search-related operations"""
    def __init__(self, library, input_handler, display_formatter):
        self.library = library
        self.input_handler = input_handler
        self.display = display_formatter
        self.track_history = TrackHistory(library)

    def show_recent_tracks(self) -> list[str]:
        """Display recent tracks and return them"""
        recent_tracks = self.track_history.get_recent()
        if recent_tracks:
            print("\nRecent tracks:")
            for i, track in enumerate(recent_tracks, 1):
                print(f"{i}: {trunc(track, 60)}")
        return recent_tracks

    def search(self, query: str | None = None) -> dict:
        """Main search interface with history support"""
        recent_tracks = self.show_recent_tracks()
        
        while True:
            if query is None:
                query = self.input_handler.prompt_choose(
                    "Enter a number to select from history, or type to search:"
                )
            
            # Handle history selection
            if query.isdigit() and recent_tracks and 0 < int(query) <= len(recent_tracks):
                results = self._search_tracks(recent_tracks[int(query) - 1])
            else:
                results = self._search_tracks(query)
            
            if results:
                return results
            print("No tracks found. Try again sweetie!")
            query = None  # Reset query for next iteration

    def _search_tracks(self, search_key: str) -> dict:
        """Search tracks by various patterns"""
        search_key = search_key.strip()
        
        # 1. UID prefix search with alias support (e.g., "TEL-", "TEL-2-")
        if len(search_key) >= 4 and search_key[:3].isupper() and search_key[3] == '-':
            return self._search_by_uid_prefix(search_key)
        
        # 2. Field-specific search with custom metadata support
        if ':' in search_key:
            return self._search_by_field(search_key)
        
        # 3. Default text search
        return self._search_by_text(search_key)

    def _search_by_uid_prefix(self, search_key: str) -> dict:
        """
        Search by UID prefix with optional alias index.
        Handles UIDs in format: AAA-N-XXXX-TT
        where:
            AAA = Artist prefix (3 chars)
            N = Alias index (1 for primary, 2+ for aliases)
            XXXX = Album hash (4 chars)
            TT = Track number (2 digits)
        """
        # Get the artist prefix (first 3 characters)
        prefix = search_key[:3].upper()
        
        # Check for alias index (the N in AAA-N-XXXX-TT)
        alias_index = None
        if len(search_key) >= 5 and search_key[3] == '-':
            try:
                alias_index = int(search_key[4])
            except ValueError:
                pass
        
        # Check for album hash prefix (the XXXX in AAA-N-XXXX-TT)
        album_hash = None
        if len(search_key) >= 11 and search_key[5] == '-':
            album_hash = search_key[6:10]
        
        return dict(
            (key, data) for key, data in self.library.mdb.items()
            if (data['uid'].startswith(prefix) and 
                (alias_index is None or data['uid'].startswith(f"{prefix}-{alias_index}-")) and
                (album_hash is None or data['uid'][6:10] == album_hash))
        )

    def _search_by_field(self, search_key: str) -> dict:
        """Search by specific field including custom metadata from comments."""
        field, value = search_key.split(':', 1)
        field = field.lower()
        value = value.lower()
        
        if field in ['inst', 'beat', 'lang']:
            return dict(
                (key, data) for key, data in self.library.mdb.items()
                if (custom_fields := CustomMetadata.unpack_fields(data.get('comment'))) 
                and custom_fields.get(field) 
                and value in custom_fields[field].lower()
            )
        elif field in self.library.keys:
            return dict(
                (key, data) for key, data in self.library.mdb.items()
                if value in str(data.get(field, '')).lower()
            )
        return {}

    def _search_by_text(self, search_key: str) -> dict:
        """Default text search in track key"""
        return dict(
            (key, data) for key, data in self.library.mdb.items()
            if search_key.lower() in key.lower()
        ) 