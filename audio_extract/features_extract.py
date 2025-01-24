import pandas as pd
import time
from tqdm import tqdm
from .features_compute import FeaturesCompute

class FeatureExtractor:
    def __init__(self, split, in_out_sec):
        self.features = FeaturesCompute(split, in_out_sec)
    
    def extract_features_single(self, uid, audio_path):
        """Extract features from a single audio file."""
        print(f"\n========================================\nComputing features for {uid} ({audio_path})")
        t1 = time.time()
        features_part = self.features.compute_features(uid=uid, audio_path=audio_path)
        t2 = time.time()
        print(f"Computed features for {uid} in {t2-t1:.2f}s\n========================================")
        return features_part

    def extract_features(self, uids, path_list, output_file):
        """Extract features from audio files and save to CSV"""
        t0 = time.time()
        features_by_part = {}  # Dictionary to store features for each part
        bad_files = []

        # Extract features for each file
        uids_paths_zip = list(zip(uids, path_list))
        for uid, file_path in tqdm(uids_paths_zip, desc="Extracting features"):
            try:
                # Compute features
                features_parts = self.extract_features_single(uid, file_path)
                
                # Initialize lists in dictionary for each part if not exists
                for i in range(len(features_parts)):
                    if i not in features_by_part:
                        features_by_part[i] = []
                
                # Add features to respective parts
                for i, part_features in enumerate(features_parts):
                    features_by_part[i].append(part_features)
                    
            except Exception as e:
                print(f"Can't process features for {file_path} ({repr(e)})")
                bad_files.append(file_path)

        # Check if we have any features
        if not features_by_part:
            print("No features were extracted")
            return None

        # Process each part's features and save to separate CSV files
        for part_num, features_list in features_by_part.items():
            if not features_list:
                continue
                
            # Create and save dataframe for this part
            df = pd.concat(features_list, axis=1).T.set_index('uid')
            save_path = str(output_file).replace('.csv', f'_{part_num+1}_{self.features.split[part_num]}.csv')
            df.to_csv(save_path, float_format='%.4f')
            print(f"Saved part {part_num+1} ({self.features.split[part_num]}%) features of {len(df)} files")

        print(f"Total processing time: {time.time()-t0:.2f}s")

        # Print bad files once at the end
        if bad_files:
            print("==========BAD FILES==========")
            print('\n'.join(bad_files))
            print("==========BAD FILES==========")