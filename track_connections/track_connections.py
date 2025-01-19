import sqlite3
import sklearn
import librosa
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from audio_extract.build_db import MusicDatabase
from audio_extract.instgroups import InstrumentGroups
from search_engine.playlist import PlaylistMaker



class TrackAnalyzer:
    """Handles audio analysis and feature extraction"""
    def __init__(self):
        self.supported_instruments = InstrumentGroups.all_instruments()
        self.instrument_groups = InstrumentGroups

    def analyze_track(self, audio_path):
        """Basic audio analysis to detect instruments and beat density"""
        try:
            # Load audio file
            y, sr = librosa.load(audio_path)
            
            # Beat detection
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            beat_density = len(beats) / (len(y) / sr)  # beats per second
            
            # Normalize beat density to your 0-3 scale
            beat_score = min(3, (beat_density / 4))  # adjust divisor as needed
            
            # For instruments, you might need a pre-trained model
            # For now, let's assume manual input or basic detection
            detected_instruments = self._detect_instruments(y, sr)
            
            return {
                'beat': beat_score,
                'instruments': detected_instruments
            }
            
        except Exception as e:
            print(f"Error analyzing {audio_path}: {e}")
            return None

    def _create_feature_vector(self, features: dict) -> np.ndarray:
        """Create a vector that considers both individual instruments and their groups"""
        # One-hot encoding for instruments
        instrument_vector = [1 if inst in features['instruments'] else 0 
                           for inst in self.supported_instruments]
        
        # Combine beat density with instruments (with weighting)
        beat_weight = 2.0  # Adjust this weight to change importance of beat density
        return np.concatenate([[features['beat'] * beat_weight], instrument_vector])

class SimilarityCalculator:
    """Handles similarity calculations and caching"""
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """Calculate cosine similarity between two feature vectors"""
        return cosine_similarity([vector1], [vector2])[0][0]

    def get_cached_similarities(self, track_id: str, min_similarity: float, limit: int) -> List[Tuple[str, float]]:
        """Get pre-calculated similarities from database"""
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("""
                SELECT track2_id, similarity_score 
                FROM track_similarities 
                WHERE track1_id = ? AND similarity_score >= ?
                ORDER BY similarity_score DESC LIMIT ?
            """, (track_id, min_similarity, limit)).fetchall()

    def store_similarity(self, track1_id: str, track2_id: str, similarity: float) -> None:
        """Store calculated similarity in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO track_similarities 
                (track1_id, track2_id, similarity_score)
                VALUES (?, ?, ?)
            """, (track1_id, track2_id, similarity))

class TrackConnections:
    """Main class coordinating track similarity features"""
    def __init__(self, database: MusicDatabase, db_path: str | Path = "track_connections.db"):
        self.database = database
        self.db_path = Path(db_path)
        self.analyzer = TrackAnalyzer()
        self.similarity_calculator = SimilarityCalculator(self.db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database with updated schema for track features."""
        with sqlite3.connect(self.db_path) as conn:
            # Store track features
            conn.execute("""
                CREATE TABLE IF NOT EXISTS track_features (
                    track_id TEXT PRIMARY KEY,
                    beat_density REAL,
                    instruments TEXT,
                    last_analyzed DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Store calculated similarities
            conn.execute("""
                CREATE TABLE IF NOT EXISTS track_similarities (
                    track1_id TEXT,
                    track2_id TEXT,
                    similarity_score REAL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (track1_id, track2_id)
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_track1 ON track_similarities(track1_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_track2 ON track_similarities(track2_id)")

    def get_similar_tracks(self, track: str, 
                          min_similarity: float = 0.5,
                          limit: int = 10) -> List[Tuple[dict, float]]:
        """Get similar tracks based on feature similarity."""
        source_uid = self._get_uid_from_track(track)
        if not source_uid:
            return []

        # Get or calculate similarities
        similar_tracks = self.similarity_calculator.get_cached_similarities(source_uid, min_similarity, limit)
        if not similar_tracks:
            similar_tracks = self._calculate_similarities(source_uid, min_similarity, limit)

        # Convert UIDs to track info
        return [(self._get_track_from_uid(uid), score) 
                for uid, score in similar_tracks]

    def _calculate_similarities(self, source_id: str, min_similarity: float, limit: int) -> List[Tuple[str, float]]:
        """Calculate similarities for a track against all others."""
        source_features = self._get_track_features(source_id)
        if not source_features:
            return []

        source_vector = self.analyzer._create_feature_vector(source_features)
        similar_tracks = []

        for track_id in self.database.tracks:
            if track_id != source_id:
                target_features = self._get_track_features(track_id)
                if target_features:
                    target_vector = self.analyzer._create_feature_vector(target_features)
                    similarity = self.similarity_calculator.calculate_similarity(
                        source_vector, target_vector
                    )
                    if similarity >= min_similarity:
                        similar_tracks.append((track_id, similarity))
                        self.similarity_calculator.store_similarity(
                            source_id, track_id, similarity
                        )

        similar_tracks.sort(key=lambda x: x[1], reverse=True)
        return similar_tracks[:limit]

    def create_similarity_playlist(self, 
                                 start_track: str,
                                 playlist_name: str = "similar_tracks.m3u",
                                 min_similarity: float = 0.5,
                                 max_tracks: int = 20) -> None:
        """Create a playlist of similar tracks using feature-based similarity."""
        similar_tracks = self.get_similar_tracks(
            start_track, 
            min_similarity=min_similarity,
            limit=max_tracks
        )
        
        if not similar_tracks:
            print("No similar tracks found.")
            return

        # Convert track info to list of track keys
        track_keys = []
        for track_info, similarity in similar_tracks:
            # Find the track key in database that matches this track info
            for key, lib_track in self.database.mdb.items():
                if (lib_track['artist'] == track_info['artist'] and 
                    lib_track['title'] == track_info['title'] and 
                    lib_track.get('album') == track_info.get('album')):
                    track_keys.append(key)
                    break

        # Use PlaylistMaker to create the playlist
        playlist_maker = PlaylistMaker(self.database)
        playlist_maker.handle_playlist_creation(
            track_keys,
            input_handler=None,  # Since we're not in interactive mode
            default_name=playlist_name
        )
        print(f"Created playlist {playlist_name} with {len(track_keys)} similar tracks")

    def _get_uid_from_track(self, track_info: str) -> Optional[str]:
        """Convert track string to UID from database."""
        try:
            artist, rest = [part.strip() for part in track_info.split('-', 1)]
            
            if '(' in rest and ')' in rest:
                title = rest[:rest.rfind('(')].strip()
                album = rest[rest.rfind('(')+1:rest.rfind(')')].strip()
            else:
                title = rest.strip()
                album = None

            for uid, track in self.database.tracks.items():
                if track['artist'].lower() == artist.lower() and track['title'].lower() == title.lower():
                    if album is None or track.get('album', '').lower() == album.lower():
                        return uid
        except ValueError:
            print(f"Invalid track format: {track_info}. Expected 'artist - title (album)'")
        return None

    def _get_track_from_uid(self, uid: str) -> Optional[dict]:
        """Retrieve track information from database using UID."""
        return self.database.tracks.get(uid)