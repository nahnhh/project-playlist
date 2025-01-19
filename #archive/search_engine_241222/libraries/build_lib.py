from pathlib import Path
import music_tag
from ..uid import TrackIDGenerator
from ..md_editable import CustomMetadata

class MusicLibrary:
    """Class to manage music library operations and metadata."""
    def __init__(self, folder: str | Path | None = None) -> None:
        self.folder: Path = self._validate_directory(folder)
        self.music_files: list[music_tag.File] = []
        self.valid_paths: list[Path] = []
        self.mdb: dict[str, dict] = {}
        self.index: dict[str, str] = {}
        self.keys: list[str] = ['uid', 'artist', 'title', 'album', 'inst', 'beat', 'lang', 'path']
        self.id_generator = TrackIDGenerator()
        self.scan_library()

    def _validate_directory(self, folder: str | None) -> Path:
        """Ask for a music directory path and validate it."""
        while True:
            folder = input("Enter music folder path: ").replace('"', '') if folder is None else folder
            fpath = Path(folder)
            
            if not fpath.exists() or not fpath.is_dir():
                folder = None
                raise FileNotFoundError("Path is not valid.")
            return fpath

    def scan_library(self):
        """Scan directory and build music database"""
        print(f"Retrieving files from {self.folder}...")
        path_list = list(self.folder.rglob("*.mp3"))
        
        if not path_list:
            print("No music files found in this folder.")
            self.folder = self._validate_directory(None)
            return self.scan_library()

        # Process files and build metadata lists
        md_lists = {
            'uid': [],
            'artist': [],
            'title': [], 
            'album': [],
            'inst': [],
            'beat': [],
            'lang': [],
            'path': []
        }

        for file_path in path_list:
            try:
                m = music_tag.load_file(file_path)
                # Extract custom fields from comments
                custom_fields = CustomMetadata.unpack_fields(m['comment'].value)
                
                # Extract values
                artist = m['artist'].value
                album = m['album'].value
                title = m['title'].value
                track_num = int(m['tracknumber'].value or 1)
                uid = self.id_generator.uid(artist, album, track_num)

                # Generate UID and append all metadata
                md_lists['uid'].append(uid)
                md_lists['artist'].append(m['artist'].value)
                md_lists['title'].append(m['title'].value)
                md_lists['album'].append(m['album'].value)
                md_lists['inst'].append(custom_fields['inst'])
                md_lists['beat'].append(custom_fields['beat'])
                md_lists['lang'].append(custom_fields['lang'])
                md_lists['path'].append(file_path)
                
                # Only store music file if needed later
                self.music_files.append(m)
                self.valid_paths.append(file_path)
                
            except Exception as e:
                print(f"Can't retrieve data from {file_path} ({str(e)})")

        # Build metadata dictionary with both string keys and UIDs
        for values in zip(*md_lists.values(), strict=True):
            track_key = f'{values[1].lower()} - {values[2].lower()} ({values[3].lower()})'
            track_data = dict(zip(self.keys, values))
            uid = values[0]
            self.mdb[track_key] = track_data
            self.index[track_key] = uid

        print(f"Good paths: {len(self.valid_paths)}, Good files: {len(md_lists['artist'])}")

    def search_tracks(self, search_key: str) -> dict:
        """Search tracks in the library by user-friendly string"""
        return dict(
            (key, data) for key, data in self.mdb.items() 
            if search_key.lower() in key.lower() and not key.startswith('AA-')  # Exclude UID keys from search results
        )

    def update_metadata(self, track_key: str, new_values: dict) -> None:
        """Update both in-memory and file metadata."""
        # Update in-memory dictionary
        self.mdb[track_key].update(new_values)
        
        # Update file metadata
        music_file = music_tag.load_file(self.mdb[track_key]['path'])
        
        # Get existing custom fields
        current_fields = CustomMetadata.unpack_fields(music_file['comment'].value)
        
        # Update with new values
        current_fields.update(new_values)
        
        # Pack back into comment
        music_file['comment'] = CustomMetadata.pack_fields(**current_fields)
        music_file.save()