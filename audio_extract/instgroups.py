class InstrumentGroups:
    """Organize instruments into logical groups for better categorization"""
    
    KEYS = [
        'piano',      # Acoustic/grand piano
        'synth',      # Synthesizer
        'keys',       # Other keyboards (electric piano, organ)
        'chimes',     # Bell-like sounds, music box
    ]
    
    GUITARS = [
        'aguitar',     # Acoustic guitar
        'eguitar',     # Electric guitar
    ]
    
    STRINGS = [
        'violin',     # Violin/fiddle
        'strings',    # Orchestral strings ensemble
        'acc',        # Accordion
    ]
    
    WINDS = [
        'sax',        # Saxophone
        'flute',      # Flute/woodwinds
        'brass',      # Trumpet and other brass
        'whistle',    # Whistles/recorders
    ]
    
    VOCALS = [
        'voc',        # Main vocals
        'choir',      # Choral/group vocals
        'ooh',        # Background vocals/harmonies
    ]

    @classmethod
    def all_inst_groups(cls) -> list:
        """Return flat list of all instruments"""
        return (cls.KEYS + cls.STRINGS + cls.WINDS + cls.VOCALS)

    @classmethod
    def get_inst_group(cls, instrument: str) -> str:
        """Return the group name for a given instrument"""
        if instrument in cls.KEYS:
            return 'keys'
        elif instrument in cls.STRINGS:
            return 'strings'
        elif instrument in cls.WINDS:
            return 'winds'
        elif instrument in cls.VOCALS:
            return 'vocals'
        return 'unknown'

class LanguageGroups:
    """Organize languages into logical groups for better categorization"""
    WESTERN = [
        'en',
        'ru',
        'sw'
    ]
    EASTERN = [
        'jp',
        'cn',
        'vn'
    ]

    @classmethod
    def all_lang_groups(cls) -> list:
        """Return flat list of all languages"""
        return (cls.WESTERN + cls.EASTERN)