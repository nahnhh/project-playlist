from hashlib import md5
from .artist_prefixes import ArtistPrefixes

class TrackIDGenerator:
    """Generates unique track IDs"""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._prefixes = ArtistPrefixes()
        return cls._instance

    def uid(self, artist: str, album: str, track_number: int) -> str:
        """
        Generate a unique track ID in format: AAA-N-XXXX-TT[-BBB-M]
        where AAA = Primary artist prefix
              N = Primary artist alias index
              XXXX = Album hash
              TT = Track number
              BBB-M = Additional artist prefixes and their alias indexes
        """
        # Split artists by common separators
        separators = [", ",
                      " ; ",
                      " / ",
                      " | ",
                      " & ",
                      " and ",
                      " ft. ",
                      " feat. ",
                      " with "]
        for sep in separators:
            artist = artist.replace(sep, "||")  # Convert all to common separator
        artists = [a.strip() for a in artist.split("||") if a.strip()]
        
        # Generate primary artist part
        primary = artists[0]
        primary = primary.strip()
        prefix = self._prefixes.get_prefix(primary)
        if not prefix:
            prefix = self._prefixes.set_prefix(primary)
        prefix = prefix.upper()
        
        # Get alias index for primary
        alias_index = self._prefixes.get_alias_index(primary)
        
        # Generate album hash
        album_hash = md5(album.lower().encode()).hexdigest()[:4].upper()
        
        # Start with primary artist UID
        uid = f"{prefix}-{alias_index}-{album_hash}-{track_number:02d}"
        
        # Add additional artists
        for collab in artists[1:]:
            collab = collab.strip()
            c_prefix = self._prefixes.get_prefix(collab)
            if not c_prefix:
                c_prefix = self._prefixes.set_prefix(collab)
            c_index = self._prefixes.get_alias_index(collab)
            uid += f"-{c_prefix}-{c_index}"
            
        return uid