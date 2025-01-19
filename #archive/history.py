from pathlib import Path

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