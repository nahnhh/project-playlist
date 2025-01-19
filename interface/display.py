import re
import unicodedata
import wcwidth
from tabulate import tabulate

def trunc(s, length: int) -> str:
    """Truncate string to specified length, accounting for wide characters."""
    s = str(s)
    current_length = 0
    for i, char in enumerate(s):
        current_length += wcwidth.wcswidth(char)
        if current_length > length - 2:
            return s[:i-1] + '..' if i > 1 else s[:i]
    return s

def clean_text(text: str) -> str:
    """
    Clean text while preserving international characters:
    - Normalize Unicode characters
    - Remove control characters
    - Normalize whitespace
    - Strip leading/trailing whitespace
    """
    if not text:
        text = ""
    
    text = unicodedata.normalize('NFKC', text)
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def analyze_text(text: str) -> None:
    """Debug helper to show Unicode categories of characters in text."""
    for char in text:
        print(f"{char!r}: {unicodedata.name(char, 'unknown')} ({unicodedata.category(char)})")

class DisplayFormatter:
    """Handles all display formatting logic"""
    @staticmethod
    def format_track_metadata(tracks: dict) -> str:
        line_break = '\n===================================\n'
        read_results = []
        
        for track in tracks.values():
            result = (
                f'Inst: {track.get("inst", "None")} | '
                f'Beat: {track.get("beat", "None")} | '
                f'Lang: {track.get("lang", "None")}\n'
                f'Title: {track.get("title")}\n'
                f'Artist: {track.get("artist")}\n'
                f'Album: {track.get("album")}\n'
                f'UID: {track.get("uid")}'
            )
            read_results.append(result)
        
        # Simplified string formatting
        output = line_break + '\n' + line_break.join(read_results) + '\n' + line_break
        print(output)

    @staticmethod
    def format_track_list(results: dict) -> str:
        col_widths = {
            'artist': 20,
            'title': 25,
            'album': 20
        }
        
        rows = [
            (i+1, 
             trunc(track["artist"], col_widths['artist']),
             trunc(track["title"], col_widths['title']),
             trunc(track["album"], col_widths['album']))
            for i, track in enumerate(results.values())
        ]
        
        print(tabulate(
            rows,
            headers=['#', 'Artist', 'Title', 'Album'],
            tablefmt='pipe',
            maxcolwidths=[4, col_widths['artist'], col_widths['title'], col_widths['album']]
        ))