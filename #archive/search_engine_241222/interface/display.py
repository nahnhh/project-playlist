from tabulate import tabulate

def trunc(s: str, length: int) -> str:
    """Truncate string to specified length."""
    s = str(s)
    return (s[:length-2] + '..') if len(s) > length+2 else s

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
        
        print(f'{line_break}\n{f'\n{line_break}\n'.join(read_results)}\n{line_break}')

    @staticmethod
    def format_track_list(results: dict) -> str:
        rows = [
            (i+1, 
             trunc(track["artist"], 16),
             trunc(track["title"], 17),
             trunc(track["album"], 10))
            for i, track in enumerate(results.values())
        ]
        print(tabulate(rows, headers=['','Artist','Title','Album'], 
                       maxcolwidths=[None, 27, 27, 27]))