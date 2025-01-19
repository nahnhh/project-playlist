from audio_extract.build_db import MusicDatabase
from audio_extract.md_edit import MetadataEditable
from search_engine.playlist import PlaylistMaker
from search_engine.search import SearchEngine
from .prompt_input import InputHandler
from .display import DisplayFormatter, trunc
from .editor import EditorInterface

class UserInterface:
    """Main user interface coordinator"""
    def __init__(self, database: MusicDatabase) -> None:
        self.database = database
        self.playlist_maker = PlaylistMaker(database)
        self.md_editor = MetadataEditable(database)
        self.input_handler = InputHandler()
        self.display = DisplayFormatter()
        self.search_engine = SearchEngine(database, self.input_handler, self.display)
        self.editor = EditorInterface(
            database, 
            self.md_editor, 
            self.input_handler,
            self.search_engine.track_history
        )

    def run_search(self):
        """Main search interface"""
        choice = self.input_handler.prompt_choose(
            "What would you like to do?",
            ["Read metadata", "Edit metadata", "Create playlist"]
        )

        # Use search engine's search method - it handles everything!
        results = self.search_engine.search(choice)
        
        if choice == "Read metadata":
            self._handle_read(results)
        elif choice == "Edit metadata":
            self._handle_edit(results)
        elif choice == "Create playlist":
            self._handle_playlist(results)

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
            self.display.format_track_list(results)
            track_list = [
                f"{trunc(track_data.get('artist', 'Unknown'), 27)} - {trunc(track_data.get('title', 'Unknown'), 27)} ({trunc(track_data.get('album', 'Unknown'), 27)})"
                for track_data in results.values()
            ]
            selected = self.input_handler.prompt_choose(
                prompt,
                options=track_list,
                allow_multiple=allow_multiple,
                hide_options=True
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
            selected_track = {selected: self.database.mdb[selected]}
            self.display.format_track_metadata(selected_track)
            self.search_engine.track_history.add_track(selected_track[selected], {})
            self.editor.edit_track(selected)

    def _handle_playlist(self, results: dict) -> None:
        """Handle playlist creation workflow."""
        selected_tracks = self._handle_selection(
            results, 
            "Select tracks to make a playlist:", 
            allow_multiple=True
        )
        if selected_tracks:
            self.playlist_maker.handle_playlist_creation(selected_tracks, self.input_handler)