from datetime import datetime
from pathlib import Path

class TrackHistory:
    """Manages track editing history and logs."""
    def __init__(self, library, 
                 recent_file: str | Path = "recent_edited_tracks.txt",
                 log_file: str | Path = "edit_details.log"):
        self.library = library
        # Use parent directory of this file for storing history files
        base_dir = Path(__file__).parent
        self.recent_file = base_dir / recent_file
        self.log_file = base_dir / log_file
        self.recent_tracks = []
        self._load_history()

    def add_track(self, track_data: dict, changes: dict) -> None:
        """Add track to history and optionally log changes."""
        track_str = f"{track_data.get('artist', 'Unknown')} - {track_data.get('title', 'Unknown')} ({track_data.get('album', 'Unknown')})"
        
        # Update recent tracks list
        if track_str in self.recent_tracks:
            self.recent_tracks.remove(track_str)
        self.recent_tracks.insert(0, track_str)
        
        # Keep only 5 most recent tracks
        self.recent_tracks = self.recent_tracks[:5]
        self._save_history()
        
        # Log changes if any were made
        if changes:
            self._log_changes(track_data, changes)

    def _log_changes(self, track_data: dict, changes: dict) -> None:
        """Log changes to file, newest first, only if there are actual changes."""
        # Get original values before changes were applied
        original_data = {k: track_data[k] for k in changes.keys()}
        
        # Build list of actual changes
        change_entries = []
        for field in sorted(changes.keys()):
            old_val = original_data[field] or 'None'  # Use 'None' for empty values
            new_val = changes[field]
            if old_val != new_val:  # Only log actual changes
                change_entries.append(f"  {field.capitalize()}: {old_val} -> {new_val}")
        
        # Only log if there were actual changes
        if change_entries:
            timestamp = datetime.now().strftime(r"%y-%m-%d %H:%M:%S")
            track_str = f"{track_data.get('artist', 'Unknown')} - {track_data.get('title', 'Unknown')} ({track_data.get('album', 'Unknown')})"
            
            try:
                # Read existing content
                content = []
                if self.log_file.exists():
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        content = f.readlines()
                
                # Prepare new entry
                new_entry = [
                    f"[{timestamp}] {track_str}\n",
                    *[f"{change}\n" for change in change_entries],
                    "\n\n"  # Blank line between entries
                ]
                
                # Write new content with new entry at the top
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.writelines(new_entry + content)
            except Exception as e:
                print(f"Could not save to log: {e}")

    def get_recent(self) -> list[str]:
        """Get list of recent tracks (max 5)."""
        return self.recent_tracks

    def _load_history(self) -> None:
        if self.recent_file.exists():
            try:
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    self.recent_tracks = [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"Could not load history: {e}")
                self.recent_tracks = []

    def _save_history(self) -> None:
        try:
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.recent_tracks))
        except Exception as e:
            print(f"Could not save history: {e}")