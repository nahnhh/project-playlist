from datetime import datetime
from pathlib import Path

class TrackHistory:
    """Manages track editing history and logs."""
    def __init__(self, library, 
                 recent_file: str | Path = "recent_edited_tracks.txt",
                 log_file: str | Path = "edit_details.log"):
        self.library = library
        self.recent_file = Path(recent_file)
        self.log_file = Path(log_file)
        self.recent_tracks = []
        self._load_history()

    def add_track(self, track_data: dict, changes: dict) -> None:
        # Add to recent tracks
        track_str = f"{track_data.get('artist', 'Unknown')} - {track_data.get('title', 'Unknown')} ({track_data.get('album', 'Unknown')})"
        if track_str not in self.recent_tracks:
            self.recent_tracks.insert(0, track_str)
            self._save_history()
        
        # Log the changes
        self._log_changes(track_data, changes)

    def _log_changes(self, track_data: dict, changes: dict) -> None:
        timestamp = datetime.now().strftime(r"%y-%m-%d %H:%M:%S")
        log_entry = [
            f"\n[{timestamp}]",
            f"Track: {track_data.get('artist', 'Unknown')} - {track_data.get('title', 'Unknown')} ({track_data.get('album', 'Unknown')})",
            "Changes:"
        ]
        
        # Get original values before changes were applied
        original_data = {k: track_data[k] for k in changes.keys()}
        
        for field in sorted(changes.keys()):
            old_val = original_data[field] or 'None'  # Use 'None' for empty values
            new_val = changes[field]
            if old_val != new_val:  # Only log actual changes
                log_entry.append(f"  {field.capitalize()}: {old_val} -> {new_val}")
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write('\n'.join(log_entry) + '\n')
        except Exception as e:
            print(f"Could not save to log: {e}")

    def get_recent(self, limit: int = 5) -> list[str]:
        return self.recent_tracks[:limit]

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