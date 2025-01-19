class EditorInterface:
    """Handles the UI for track editing"""
    def __init__(self, library, md_editor, input_handler, track_history):
        self.library = library
        self.md_editor = md_editor
        self.input_handler = input_handler
        self.track_history = track_history

    def edit_track(self, track_key: str) -> None:
        """Handle the UI portion of track editing"""
        track_data = self.library.mdb[track_key].copy()  # Make a copy of original data
        uid = self.library.index[track_key]
        print(f"\nEditing: {track_data['artist']} - {track_data['title']} ({track_data['album']})")
        print(f"UID: {uid}")
        
        while True:
            new_values = self._collect_new_values(track_data)
            if not new_values:  # Empty dict - no changes made
                print("No changes were made.")
                return
            
            self._display_changes(track_data, new_values)
            choice = self.input_handler.prompt_choose(
                "Apply these changes?",
                options=["Yes", "Redo", "Quit"],
                inputs=["y", "r", "q"],
            )

            if choice == "Yes":
                # Update both in-memory and file metadata
                self.md_editor.update_metadata(track_key, new_values)
                
                # Log changes with original track data
                self.track_history.add_track(track_data, new_values)
                print("Changes applied.")
                break
            elif choice == "Redo":
                print("\nRedoing edit...")
                continue
            elif choice == "Quit":
                print("Changes discarded.")
                break

    def _collect_new_values(self, track_data: dict) -> dict:
        """Collect new values for each editable field"""
        new_values = {}
        for field in self.md_editor.EDITABLE_FIELDS:
            current = track_data[field]
            new_value = input(f"{field.capitalize()} [{current or 'None'}]: ").strip()
            if new_value == 'q':
                return {}
            if new_value == 's':
                break
            if new_value:
                new_values[field] = new_value
        return new_values

    def _display_changes(self, track_data: dict, new_values: dict) -> None:
        """Display proposed changes"""
        print("\nProposed changes:")
        for field in self.md_editor.EDITABLE_FIELDS:
            old_val = track_data[field]
            new_val = new_values.get(field, old_val)
            print(f"{field.capitalize()}: {old_val} -> {new_val}")