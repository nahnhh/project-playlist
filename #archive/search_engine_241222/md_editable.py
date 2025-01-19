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
    """Defines which fields can be edited"""
    EDITABLE_FIELDS = ['inst', 'beat', 'lang']

    def __init__(self, library):
        self.library = library 