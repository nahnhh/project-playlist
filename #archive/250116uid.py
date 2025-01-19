from hashlib import md5
from .interface.display import clean_text

class ArtistGroup:
    """Manages a group of artists, aliases and their shared prefix."""
    def __init__(self, primary_name: str, prefix: str):
        self.primary_name = primary_name.lower()
        self.prefix = prefix.upper()
        self.aliases = {self.primary_name}
    
    def add_alias(self, alias: str) -> None:
        """Add an alias to the group."""
        self.aliases.add(alias.lower())
    
    def contains(self, name: str) -> bool:
        """Check if a name belongs to this group."""
        return name.lower() in self.aliases
    
    def get_all_names(self) -> set[str]:
        """Get all names in the group."""
        return self.aliases.copy()

class TrackIDGenerator:
    """Class to handle unique track ID generation."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._discography = {}
            cls._instance._custom_prefixes = {}
            cls._instance._aliases = {}
            cls._instance._primary_names = {}
            cls._instance._alias_indices = {}  # Maps alias to its index number
        return cls._instance

    def set_custom_prefix(self, artist: str, prefix: str, aliases: list[str] | None = None) -> None:
        """Set a custom 3-character prefix for an artist and their aliases."""
        if not prefix or len(prefix) != 3:
            raise ValueError("Prefix must be exactly 3 characters")
            
        # Set prefix for main artist (index 1)
        artist_lower = artist.lower()
        self._custom_prefixes[artist_lower] = prefix.upper()
        self._alias_indices[artist_lower] = 1
        
        # Initialize primary name's alias set
        if artist_lower not in self._primary_names:
            self._primary_names[artist_lower] = {artist_lower}
        
        # Set same prefix for aliases with incrementing indices
        if aliases:
            for i, alias in enumerate(aliases, 2):  # Start from 2 for aliases
                alias_lower = alias.lower()
                self._custom_prefixes[alias_lower] = prefix.upper()
                self._aliases[alias_lower] = artist_lower
                self._primary_names[artist_lower].add(alias_lower)
                self._alias_indices[alias_lower] = i

    def get_related_names(self, artist: str) -> set[str]:
        """Returns all related names (including aliases) for an artist."""
        artist_lower = artist.lower()
        primary = self._aliases.get(artist_lower, artist_lower)
        return self._primary_names.get(primary, {artist_lower})
    
    def get_primary_name(self, artist: str) -> str:
        """Get the primary name for an artist or alias."""
        return self._aliases.get(artist.lower(), artist.lower())
    
    def uid(self, artist: str, album: str, track_number: int) -> str:
        """
        Generate a unique track ID in format: AAA-N-XXXX-TT
        where AAA = Artist prefix (3 chars)
              N = Alias index (1 for primary, 2+ for aliases)
              XXXX = Album hash (4 chars)
              TT = Track number (2 digits)
        """
        artist_lower = artist.lower()
        primary_artist = self._aliases.get(artist_lower, artist_lower)
        artist_prefix = self._custom_prefixes.get(primary_artist, artist[:3].upper())
        alias_index = self._alias_indices.get(artist_lower, 1)
        album_hash = md5(album.lower().encode()).hexdigest()[:4].upper()
        return f"{artist_prefix}-{alias_index}-{album_hash}-{track_number:02d}"
    
    def get_artist_tracks(self, prefix: str, alias_index: int | None = None) -> set[str]:
        """
        Get all UIDs for an artist prefix, optionally filtered by alias index.
        
        Args:
            prefix: The 3-character artist prefix
            alias_index: Optional specific alias index to filter by
        """
        # Implementation would depend on how you store/index the UIDs
        pass
    
    def merge_groups(self, artist1: str, artist2: str) -> None:
        """Merge two artist groups together."""
        group1 = self._artist_groups.get(artist1.lower())
        group2 = self._artist_groups.get(artist2.lower())
        
        if not group1 or not group2 or group1 is group2:
            return
        
        # Use group1's prefix and primary name
        for name in group2.get_all_names():
            group1.add_alias(name)
            self._artist_groups[name.lower()] = group1