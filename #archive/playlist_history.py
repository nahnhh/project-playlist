from datetime import datetime
from pathlib import Path

class PlaylistHistory:
    """Manages playlist creation history."""
    def __init__(self, library, 
                 recent_file: str | Path = "recent_playlists.txt",
                 log_file: str | Path = "playlist_details.log"):
        self.library = library
        base_dir = Path(__file__).parent
        self.recent_file = base_dir / recent_file
        self.log_file = base_dir / log_file
        self.recent_playlists = []
        self._load_history()

    def add_playlist(self, tracks: list[str], playlist_path: Path) -> None:
        """Add playlist to history and log details."""
        # Create playlist entry with track count
        playlist_str = f"{playlist_path.name} ({len(tracks)} tracks)"
        
        # Update recent playlists list
        if playlist_str in self.recent_playlists:
            self.recent_playlists.remove(playlist_str)
        self.recent_playlists.insert(0, playlist_str)
        
        # Keep only 5 most recent playlists
        self.recent_playlists = self.recent_playlists[:5]
        self._save_history()
        
        # Log playlist details
        self._log_playlist(tracks, playlist_path)

    def _log_playlist(self, tracks: list[str], playlist_path: Path) -> None:
        """Log detailed playlist information."""
        timestamp = datetime.now().strftime(r"%y-%m-%d %H:%M:%S")
        
        try:
            # Prepare new entry
            new_entry = [
                f"\n[{timestamp}] {playlist_path.name}",
                f"Location: {playlist_path}",
                f"Tracks ({len(tracks)}):"
            ]
            
            # Add track details
            for track in tracks:
                track_data = self.library.mdb[track]
                new_entry.append(
                    f"  • {track_data['artist']} - {track_data['title']} "
                    f"({track_data['album']})"
                )
            
            new_entry.append("\n")  # Blank line between entries
            
            # Read existing content
            content = []
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    content = f.readlines()
            
            # Write new content with new entry at the top
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_entry + [line.rstrip() for line in content]))
                
        except Exception as e:
            print(f"Could not save to playlist log: {e}")

    def get_recent(self) -> list[str]:
        """Get list of recent playlists (max 5)."""
        return self.recent_playlists

    def _load_history(self) -> None:
        if self.recent_file.exists():
            try:
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    self.recent_playlists = [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"Could not load playlist history: {e}")
                self.recent_playlists = []

    def _save_history(self) -> None:
        try:
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.recent_playlists))
        except Exception as e:
            print(f"Could not save playlist history: {e}") 