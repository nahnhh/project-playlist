from ..libraries.build_lib import MusicLibrary
from ..playlist import PlaylistMaker
from ..libraries.track_history import TrackHistory
from .prompt_input import InputHandler
from .display import DisplayFormatter
from .editor import EditorInterface, MetadataEditor

class UserInterface:
    """Main user interface coordinator"""
    def __init__(self, library: MusicLibrary) -> None:
        self.library = library
        self.playlist_maker = PlaylistMaker(library)
        self.md_editor = MetadataEditor(library)
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
                print(f"{i}: {track}")
        
        while True:
            # Get search input
            search_input = self.input_handler.prompt_choose(
                "Enter a number to select from history, or type to search:"
            )
            
            # Handle history selection
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

    def _handle_edit(self, results: dict) -> None:
        if len(results) == 1:
            selected = list(results.keys())[0]
        else:
            # Format tracks with proper capitalization
            track_list = [
                f"{track_data.get('artist', 'Unknown')} - {track_data.get('title', 'Unknown')} ({track_data.get('album', 'Unknown')})"
                for track_data in results.values()
            ]
            selected = self.input_handler.prompt_choose(
                "Select a track to edit:",
                displayed_options=track_list
            )
            # Map back to the original key
            if selected:
                selected = list(results.keys())[track_list.index(selected)]
        
        if selected:
            selected_track = {selected: self.library.mdb[selected]}
            self.display.format_track_metadata(selected_track)
            self.editor.edit_track(selected)

    def _handle_playlist(self, results: dict) -> None:
        selected_tracks = self.input_handler.prompt_choose(
            "Select tracks to make a playlist:",
            displayed_options=list(results.keys()),
            allow_multiple=True
        )
        while True:
            output_path = input("Enter playlist file path (.m3u): ").strip()
            if output_path.endswith('.m3u'):
                break
            print("Please provide a valid .m3u file path.")
        self.playlist_maker.create_playlist(selected_tracks, output_path)