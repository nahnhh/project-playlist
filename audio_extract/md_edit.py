import music_tag
import json

class CustomMetadata:
    """Handles custom metadata fields stored in MP3 comments."""
    
    @staticmethod
    def pack_fields(inst: str | None = None, 
                   beat: str | None = None, 
                   lang: str | None = None) -> str:
        """Pack custom fields into a JSON string."""
        custom_fields = {
            'inst': inst,
            'beat': beat,
            'lang': lang
        }
        return json.dumps(custom_fields)
    
    @staticmethod
    def unpack_fields(comment: str | None) -> dict:
        """Extract custom fields from comment string."""
        if not comment:
            return {'inst': None, 'beat': None, 'lang': None}
            
        try:
            fields = json.loads(comment)
            return {
                'inst': fields.get('inst'),
                'beat': fields.get('beat'),
                'lang': fields.get('lang')
            }
        except json.JSONDecodeError:
            return {'inst': None, 'beat': None, 'lang': None}

class MetadataEditable:
    """Defines which fields can be edited and handles metadata updates."""
    EDITABLE_FIELDS = ['inst', 'beat', 'lang']

    def __init__(self, database):
        self.database = database

    def update_metadata(self, track_key: str, new_values: dict) -> None:
        """Update both in-memory and file metadata."""
        # Update in-memory dictionary
        self.database.mdb[track_key].update(new_values)
        
        # Update file metadata
        music_file = music_tag.load_file(self.database.mdb[track_key]['path'])
        # Get existing custom fields
        current_fields = CustomMetadata.unpack_fields(music_file['comment'].value)
        # Update with new values
        current_fields.update(new_values)
        # Pack back into comment
        packed = CustomMetadata.pack_fields(**current_fields)
        print(f"Saving metadata: {packed}")  # Debug print
        music_file['comment'] = packed
        music_file.save()