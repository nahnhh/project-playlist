from ..uid import TrackIDGenerator

class ArtistPrefixes:
    """Manages custom artist prefixes for track ID generation"""
    
    def __init__(self):
        self.id_gen = TrackIDGenerator()
        self.prefixes = {  # dict[str, str]
            'ネザーnether': 'NZA',
            '記憶消去': 'KIO',
            'from tokyo to honolulu': 'FTH',
            'M y s t e r yミステリー': 'MYS',
            'E U P H O R I A 永遠の': 'EUP',
            'F i b o n a c c i': 'FIB',
            'ℍUM♥ℕIGHTM♥RE': 'HUM',
            'Mystical Composer': 'MCO',
            'Your Bestest Friend :)': 'YBF',
            'THIRDWORLD DREAMPLACE': 'TWD',
            'TRANSMITTER「送信機」': 'TSM',
            'Nhớ Nhà': 'NHA',
            '德羅斯': 'DRO',
            '定常 w a n d e r e r': 'WAN',
            '恋人の夢': 'KOI',
            '猫 シ Corp.': 'CAT',
            'دل': 'DEL',
        }
        
        # Artists with aliases: dict[str, tuple[str, list[str]]]
        self.artists_with_aliases = {
            't e l e p a t h テレパシー能力者': ('TEL', ['トリニティー無限大', '泰合志恒']),
            '仮想夢プラザ': ('VDP', ['虛擬夢想廣場']),
            'desert sand feels warm at night': ('DES', ['ծիածանի հիբիսկուս']),
            'days of blue skies': ('BLU', ['days of blue', 'කොළ අතර හිරු එළිය']),
            'Illusionary ドリーミング': ('ILL', ['夢研究センター']),
            'G a t e w a y ゲートウェイ': ('GTE', ['m a k e b e l i e v e']),
            '絡み合った運命': ('MEI', ['交织的命运']),
            'S O A R E R': ('SRR', ['ابدی']),
            '818181': ('818', ['Your Bestest Friend :)']),
        }

    def initialize_prefixes(self):
        """Set up all artist prefixes"""
        # Set regular prefixes
        for artist, prefix in self.prefixes.items():
            self.id_gen.set_custom_prefix(artist, prefix)
        
        # Set prefixes with aliases
        for artist, (prefix, aliases) in self.artists_with_aliases.items():
            self.id_gen.set_custom_prefix(artist, prefix, aliases)

    def set_custom_prefix(self, artist: str, prefix: str, aliases=None): #aliases: list[str]
        """Set a custom prefix for an artist"""
        self.id_gen.set_custom_prefix(artist, prefix, aliases) 