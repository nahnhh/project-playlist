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
        self.recent_playlists = []  # Will store tuples of (display_str, tracks)
        self._load_history()

    def add_playlist(self, tracks: list[str], playlist_path: Path) -> None:
        """Add playlist to history and log details."""
        timestamp = datetime.now().strftime(r"%H:%M:%S")
        display_str = f"[{timestamp}] {playlist_path.name} ({len(tracks)} tracks)"
        
        # Update recent playlists list with both display string and tracks
        playlist_entry = (display_str, tracks)
        if playlist_entry in self.recent_playlists:
            self.recent_playlists.remove(playlist_entry)
        self.recent_playlists.insert(0, playlist_entry)
        
        # Keep only 5 most recent playlists
        self.recent_playlists = self.recent_playlists[:5]
        self._save_history()
        
        # Log playlist details
        self._log_playlist(tracks, playlist_path)

    def _log_playlist(self, tracks: list[str], playlist_path: Path) -> None:
        """Log detailed playlist information."""
        timestamp = datetime.now().strftime(r"%y-%m-%d %H:%M:%S")
        artists = len({self.library.mdb[track]['artist'] for track in tracks})
        
        new_entry = [
            f"\n[{timestamp}] {playlist_path.name}",
            f"Location: {playlist_path}",
            f"Summary: {len(tracks)} tracks by {artists} artists",
            "Tracks:"
        ]
        
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

    def get_recent(self) -> list[tuple[str, list[str]]]:
        """Get list of recent playlists with their tracks."""
        return self.recent_playlists

    def _load_history(self) -> None:
        if self.recent_file.exists():
            try:
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    i = 0
                    while i < len(lines):
                        display_str = lines[i].strip()
                        if i + 1 < len(lines) and lines[i + 1].startswith("TRACKS:"):
                            tracks = lines[i + 1].strip()[7:].split("|")
                            self.recent_playlists.append((display_str, tracks))
                        i += 2
            except Exception as e:
                print(f"Could not load playlist history: {e}")
                self.recent_playlists = []

    def _save_history(self) -> None:
        try:
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                for display_str, tracks in self.recent_playlists:
                    f.write(f"{display_str}\n")
                    f.write("TRACKS:" + "|".join(tracks) + "\n")
        except Exception as e:
            print(f"Could not save playlist history: {e}")

    def show_playlist_contents(self, playlist_name: str) -> None:
        """Display the contents of a specific playlist from history."""
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find and print the specific playlist section
                if playlist_name in content:
                    section = content.split(f"{playlist_name}\n")[1].split("\n\n")[0]
                    print(section) 