import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from audio_extract.build_db import MusicDatabase
from audio_extract.uid_gen import TrackIDGenerator
from audio_extract.artist_prefixes import ArtistPrefixes

prefixes = ArtistPrefixes()
prefixes.print_all_prefixes()

folder = r'D:/#ALLMYMUSIC - Copy'

id_gen = TrackIDGenerator()
first_track = next(Path(folder).glob('*.mp3'), None)
if first_track:
    # Create database for this folder
    database = MusicDatabase(copy_folder=folder)
    database._scan_library()
    database._print_prefixes()
    base_uid = database.df.iloc[0].name[:-3]
    print(f"Processing {folder} --> {base_uid}.csv")
    database._scan_library(extract_features=True, output_file=f'{base_uid}.csv')
    print(f"Processed {folder} --> {base_uid}.csv")