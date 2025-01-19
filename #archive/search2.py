from tabulate import tabulate
import music_tag
import os
from pathlib import Path
from glob import glob

#Check if path is valid
def directoryinput(folder=None) -> Path:
   """
   Check whether path to music folder is valid or not.

   Args:
      folder (str, optional): Path to music folder (default=None).
   
   Returns:
      Path: Valid path to music folder.
   """
   while True:
      try:
         folder = input("Enter music folder path: ").replace('"','') if folder is None else folder
         fpath = Path(folder)
         
         if not fpath.exists() or not fpath.is_dir():
            raise FileNotFoundError("Path is not valid.")
         
         return fpath #if dir typed in code, must manually change \ to /
      except FileNotFoundError as e:
         print(f"Error: {e}")
         folder = None

def create_uid(index: int, file_path: str) -> str:
    """Create a unique identifier for a song using index and path hash"""
    path_hash = md5(str(file_path).encode()).hexdigest()[:6]  # First 6 chars of hash
    return f"{index:04d}_{path_hash}"  # Format: 0001_a1b2c3

def goodfiles(folder) -> dict:
   """
   Process music files and extract their metadata.
   
   Args:
      folder (Path): Path to music folder
       
   Returns:
      dict: Database of music files with their metadata
   """
   print(f"Retrieving files from {folder}...")
   # Get all MP3 files recursively
   path_list = list(folder.rglob("*.mp3"))
   if not path_list:
      print("There are no music files in this folder.")
      return goodfiles(directoryinput())

   #music metadata viewed vertically (as lists of keys)
   music_files = []
   valid_paths = []
   for i, file_path in enumerate(path_list):
      try:
         m = music_tag.load_file(file_path)
         music_files.append(m)
         valid_paths.append(file_path)
      except Exception as e:
         print(f"{str(e)}: Can't retrieve data from {file_path}")
         path_list.pop(i)

   # Create lists for required metadata
   md_lists = {
      'uid': [create_uid(i, path) for i, path in enumerate(valid_paths)],
      'artist': [m['artist'].value for m in music_files],
      'title': [m['title'].value for m in music_files],
      'album': [m['album'].value for m in music_files],
      'inst': [None] * len(music_files),  # placeholder
      'beat': [None] * len(music_files),  # placeholder
      'lang': [None] * len(music_files),  # placeholder
      'path': valid_paths
   }

   print(f"Good paths: {len(valid_paths)}, Good files: {len(md_lists['artist'])}")

   # Create metadata dictionary
   global keys, mdb
   keys = list(md_lists.keys())
   mdb = {}
   
   # Zip all metadata values together and create entries
   for values in zip(*md_lists.values(), strict=True):
       track_key = f'{values[0].lower()} - {values[1].lower()} ({values[2].lower()})'
       mdb[track_key] = dict(zip(keys, values))

#Yes/No prompt, stolen from willbelr
def prompt_yn(question: str, default=None) -> bool:
   """Yes/No prompt, stolen from willbelr."""
   choices = ("", "y", "n") if default in ("yes", "no") else ("y", "n")
   hint = "Y/n" if default == "yes" else "y/n"
   hint = "y/N" if default == "no" else hint
   reply = None
   while reply not in choices:
      reply = input(f"{question}? [{hint}] ").lower()
   return (reply == "y") if default != "yes" else (reply in ("", "y"))

#Prompt to choose: select one number as choice
def prompt_choose(question: str, displayed_options: list, actions: list) -> str:
   """Prompt to choose: select index of options, return action.
   [options] and [actions] must have the same length."""
   # same length test
   if displayed_options != None:
      try:
         zip(displayed_options, actions)
         for i, option in enumerate(displayed_options):
            print(f"{i+1}. {option}")
      except Exception:
         print("[options] and [actions] does not have the same length.")
   # valid number test
   chosen = None
   while chosen not in range(1,len(actions)+1):
      try:
         i = int(input(f"{question}? "))
         chosen = actions[i-1]
         return chosen
      except (KeyError, IndexError):
         print("Index number is beyond the list.")
      except ValueError:
         print("That's not a number, silly!")

#a quick way to convert track to values for dict mdb[track][key]
def trackinfo(result: dict) -> list[tuple]: #[(a1, t2, a3, i4, b5, l6, p7), (...)]
   """"Convert mdb[track][key] and track[key] to [(keys1), (keys2), ...]"""
   result_key = []
   try:
      for track in result.values(): #track = {'artist': '...', ...}
         track_values = track.values()
         result_key.append(tuple(track_values))
   except AttributeError: #1 result: str
      track_values = mdb[result].values()
      result_key.append(tuple(track_values))
   return result_key

#Function to query metadata
def print_read(results: dict) -> str:
   """Function to query metadata."""
   read_results = []
   for a1, t2, a3, i4, b5, l6, _ in trackinfo(results):
      read_template = f'Inst: {i4} | Beat: {b5} | Lang: {l6}\nTitle: {t2}\nArtist: {a1}\nAlbum: {a3}'
      read_results.append(read_template)
   line_break = '\n===================================\n'
   print(line_break)
   print(f'\n{line_break}\n'.join(read_results))
   print(line_break)
         # Inst: | Beat: | Lang: 
         # Title:
         # Artist
         # Album:

#Function to query songs to edit
def trunc(s: str, length: int) -> str:
   s = u'{}'.format(s)
   return (s[:length-2] + '..') if len(s) > length+2 else s

def print_edit(results: dict) -> str:
   """Function to query songs to edit."""
   global lines
   lines = []  #['Artist - Title (Album)', '...']
   rows = []
   for i, (artist, title, album, inst, beat, lang, _) in enumerate(trackinfo(results)):
      #track == mdb_track filtered after search
      line = f'{artist.lower()} - {title.lower()} ({album.lower()})'
      lines.append(line)
      #row == row in table of results
      row = (i+1, trunc(artist, 16), trunc(title, 17), trunc(album, 10))
      rows.append(row)
   print("") #print the table of results
   print(tabulate(rows, headers=['','Artist','Title','Album'], maxcolwidths=[None, 27, 27, 27]))
   print("\nEDIT mode. Above are the songs found.")

#Query: get user input to read or edit metadata of songs
def search(folder=None) -> str:
   """Final function. Check # of music files from folder, get user input to read or edit metadata of specific file."""
   goodfiles(directoryinput(folder))
   while True:
      search_key = input("Search for a track: ").lower()
      results = dict(filter(lambda item: search_key in item[0], mdb.items()))
      if results == {}:
         print("No track found. Try again sweetie!")
      else: break
   print('Got it!')
   match prompt_yn("Search to read[Y] or edit[N]", default='no'):
      case True: #read mode
         print_read(results)
         print("READ mode. Above are the songs found.")
      case False:#edit mode
         if len(results) > 1:
            print_edit(results)
            song_edit = prompt_choose("Which track do you want to edit", displayed_options=None, actions=lines)
            print_read(song_edit)
         else: #1 result
            print_read(results)
            print("EDIT mode. Above is the song found.")
         element_edit = prompt_choose("Which element do you want to edit", displayed_options=keys, actions=keys)
         print(element_edit)