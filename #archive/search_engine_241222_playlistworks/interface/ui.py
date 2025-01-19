from ..libraries.build_lib import MusicLibrary
from ..playlist import PlaylistMaker
from ..libraries.track_history import TrackHistory
from .prompt_input import InputHandler
from .display import DisplayFormatter, trunc
from .editor import EditorInterface, MetadataEditable

class UserInterface:
    """Main user interface coordinator"""
    def __init__(self, library: MusicLibrary) -> None:
        self.library = library
        self.playlist_maker = PlaylistMaker(library)
        self.md_editor = MetadataEditable(library)
        self.input_handler = InputHandler()
        self.display = DisplayFormatter()
        self.editor = EditorInterface(library, self.md_editor, self.input_handler)
        self.edit_history = TrackHistory(library)

    def run_search(self):
        """Main search interface"""
        choice = self.input_handler.prompt_choose(
            "What would you like to do",
            ["Read metadata", "Edit metadata", "Create playlist"]
        )

        # Show recent tracks and get search results
        results = self._handle_search()
        
        if choice == "Read metadata":
            self._handle_read(results)
        elif choice == "Edit metadata":
            self._handle_edit(results)
        elif choice == "Create playlist":
            self._handle_playlist(results)

    def _handle_search(self) -> dict:
        """Handle search workflow including history"""
        # Show recent tracks
        recent_tracks = self.edit_history.get_recent()
        if recent_tracks:
            print("\nRecent tracks:")
            for i, track in enumerate(recent_tracks, 1):
                print(f"{i}: {trunc(track, 60)}")
        
        while True:
            search_input = self.input_handler.prompt_choose(
                "Enter a number to select from history, or type to search:"
            )
            
            # Handle history selection - use full track name for search
            if search_input.isdigit() and 0 < int(search_input) <= len(recent_tracks):
                results = self.library.search_tracks(recent_tracks[int(search_input) - 1])
            else:
                results = self.library.search_tracks(search_input)
            
            # Check if we got any results
            if results:
                return results
            print("No tracks found. Try again sweetie!")

    def _handle_read(self, results: dict) -> None:
        self.display.format_track_metadata(results)
        if len(results) == 1:
            print("READ mode. Above is the song found.")
        else:
            print("READ mode. Above are the songs found.")

    def _handle_selection(self, results: dict, prompt: str, allow_multiple: bool = False):
        """Handle track selection for edit and playlist modes."""
        if len(results) == 1:
            selected = [list(results.keys())[0]] if allow_multiple else list(results.keys())[0]
        else:
            # Format tracks with proper capitalization
            track_list = [
                f"{trunc(track_data.get('artist', 'Unknown'), 27)} - {trunc(track_data.get('title', 'Unknown'), 27)} ({trunc(track_data.get('album', 'Unknown'), 27)})"
                for track_data in results.values()
            ]
            selected = self.input_handler.prompt_choose(
                prompt,
                displayed_options=track_list,
                allow_multiple=allow_multiple
            )
            # Map back to the original keys
            if selected:
                if allow_multiple:
                    selected = [list(results.keys())[track_list.index(track)] for track in selected]
                else:
                    selected = list(results.keys())[track_list.index(selected)]
        return selected

    def _handle_edit(self, results: dict) -> None:
        selected = self._handle_selection(results, "Select a track to edit:")
        if selected:
            selected_track = {selected: self.library.mdb[selected]}
            self.display.format_track_metadata(selected_track)
            self.editor.edit_track(selected)

    def _handle_playlist(self, results: dict) -> None:
        selected_tracks = self._handle_selection(results, "Select tracks to make a playlist:", allow_multiple=True)
        if selected_tracks:
            self.playlist_maker.handle_playlist_creation(selected_tracks, self.input_handler)