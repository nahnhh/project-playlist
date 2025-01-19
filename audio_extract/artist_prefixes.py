from interface.display import clean_text

def clean_name(name: str) -> str:
  """Clean artist name by removing extra whitespace and normalizing text"""
  name = name.replace(' ', '')  # First join all characters
  name = clean_text(name)       # Then clean the text
  return name.lower()           # Finally lowercase

class ArtistGroup:
  """Manages a group of artists and their aliases"""
  def __init__(self, primary_name: str):
    self.primary_name = primary_name.lower()
    self.aliases = {self.primary_name}
  
  def add_alias(self, alias: str) -> None:
    self.aliases.add(alias.lower())
  
  def get_all_names(self) -> set[str]:
    return self.aliases.copy()

class ArtistPrefixes:
  """Manages artist prefixes and their relationships"""
  def __init__(self):
      self._groups = {}  # primary_name -> ArtistGroup
      self._prefixes = {}  # artist_name -> prefix
      self._primary_names = {}  # alias -> primary_name
      self._unk_counter = 0  # Track number of UNK prefixes
      self._set_default_prefixes()
    
  def _set_default_prefixes(self):
    """Set up default prefixes for common artists"""
    # Set default prefixes
    defaults = {
      'ネザーnether': 'NZA',
      '記憶消去': 'KIO',
      'from tokyo to honolulu': 'FTH',
      'm e m o r y メモリー': 'MEM',
      'memorykeeper7': 'MK7',
      'E U P H O R I A 永遠の': 'EUP',
      'F i b o n a c c i': 'FIB',
      'ℍUM♥ℕIGHTM♥RE': 'HUM',
      'THIRDWORLD DREAMPLACE': 'TWD',
      'Nhớ Nhà': 'NHA',
      '德羅斯': 'DRO',
      '定常 w a n d e r e r': 'WAN',
      '恋人の夢': 'KOI',
      '猫 シ Corp.': 'CAT',
      'دل': 'DEL',
      '𝓁𝓊𝓍𝓊𝓇𝓎 ボールペン': 'LUX',
      'Glass Maiden': 'GLM'
    }
    for artist, prefix in defaults.items():
      self.set_prefix(artist, prefix)

    # Set artists with aliases
    aliases = {
      't e l e p a t h テレパシー能力者': ('TEL', ['トリニティー無限大', '泰合志恒']),
      '仮想夢プラザ': ('VDP', ['虛擬夢想廣場']),
      'desert sand feels warm at night': ('DES', ['ծիածանի հիբիսկուս', 'Sand!']),
      'days of blue skies': ('BLU', ['days of blue', 'කොළ අතර හිරු එළිය']),
      'Illusionary ドリーミング': ('ILL', ['夢研究センター']),
      'G a t e w a y ゲートウェイ': ('GTE', ['m a k e b e l i e v e']),
      'Glaciology': ('GLA', ['私の物語の断片']),
      'M y s t e r yミステリー': ('MYS', ['目的地']),
      'Mystical Composer': ('MCO', ['Mystical Composer 光霊']),
      '絡み合った運命': ('MEI', ['交织的命运']), 
      'S O A R E R': ('SOA', ['ابدی']),
      '818181': ('818', ['Your Bestest Friend :)']),
      'MindSpring Memories': ('MSM', ['softer', 'softest']),
      'TRANSMITTER「送信機」': ('TSM', ['送信機']),
    }
    for artist, (prefix, aliases) in aliases.items():
      self.set_prefix(artist, prefix, aliases)
  
  def set_prefix(self, artist: str, prefix: str = None, aliases: list[str] = None) -> str:
    """Set prefix for artist and their aliases. Returns the prefix."""
    if not artist:
        self._unk_counter += 1
        return f'UNK'  # Will be combined with counter in get_alias_index
        
    try:
        main_artist = clean_name(artist)
        
        # Check if artist already has a prefix
        if main_artist in self._prefixes:
            return self._prefixes[main_artist]
            
        if prefix:
            prefix = prefix.upper()
        else:
            # Find first 3 roman characters
            roman_chars = [c for c in main_artist if c.isascii() and c.isalpha()]
            if len(roman_chars) >= 3:
                prefix = ''.join(roman_chars[:3]).upper()
            else:
                self._unk_counter += 1
                prefix = 'UNK'
        
        # Create or get artist group
        if main_artist not in self._groups:
            self._groups[main_artist] = ArtistGroup(main_artist)
        
        # Set prefix
        self._prefixes[main_artist] = prefix
        self._primary_names[main_artist] = main_artist
        
        # Handle aliases
        if aliases:
            for alias in aliases:
                alias = clean_name(alias)
                self._groups[main_artist].add_alias(alias)
                self._prefixes[alias] = prefix
                self._primary_names[alias] = main_artist
                
        return prefix
        
    except (TypeError, AttributeError):
        self._unk_counter += 1
        return 'UNK'
  
  def get_prefix(self, artist: str) -> str:
      """Get prefix for artist or their alias"""
      try:
          artist = clean_name(artist)
          return self._prefixes.get(artist, None)
      except (TypeError, AttributeError):
          return None
  
  def get_primary_name(self, artist: str) -> str:
      """Get primary name for any artist or alias"""
      artist = clean_name(artist)
      return self._primary_names.get(artist, artist)
  
  def get_alias_index(self, artist: str) -> int:
      """
      Get alias index for an artist name
      Returns: 1 for primary artist, 2+ for aliases in order they were added,
      or unique counter for UNK prefixes
      """
      artist = clean_name(artist)
      prefix = self.get_prefix(artist)
      
      if prefix == 'UNK':
          return self._unk_counter
          
      primary = self.get_primary_name(artist)
      
      if artist == primary:
          return 1
          
      # Get all aliases for this primary artist
      group = self._groups.get(primary)
      if not group:
          return 1
          
      # Convert to list to maintain order and find index
      aliases = sorted(list(group.aliases - {primary}))
      try:
          return aliases.index(artist) + 2  # +2 because primary is 1
      except ValueError:
          return 1 
  
  def print_all_prefixes(self):
    """Print all artist prefixes and their aliases in debug format"""
    result = {}
    
    # Group by prefix
    for artist_name, prefix in sorted(self._prefixes.items()):
      primary_name = self._primary_names.get(artist_name, artist_name)  # Handle UNK cases
      if primary_name not in result:
        # Get aliases except primary name
        group = self._groups.get(primary_name)
        aliases = sorted(list(group.aliases - {primary_name})) if group else []
        result[primary_name] = (prefix, aliases)
      
    # Print in sorted order by prefix
    for name, (prefix, aliases) in sorted(result.items()):
      if aliases:  # Show entries with aliases
        print(f"'{name}': ('{prefix}', {aliases}),")
      else:  # Show entries without aliases
        print(f"'{name}': '{prefix}',") 