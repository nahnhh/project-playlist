import pandas as pd
import time
from tqdm import tqdm
from .features_compute import FeaturesCompute

class FeatureExtractor:
    features = FeaturesCompute()
    
    @staticmethod
    def extract_features_single(uid, audio_path):
        """Extract features from a single audio file."""
        print(f"\n========================================\nComputing features for {uid} ({audio_path})")
        t1 = time.time()
        features_part = FeatureExtractor.features.compute_features(uid=uid, audio_path=audio_path)
        t2 = time.time()
        print(f"Computed features for {uid} in {t2-t1:.2f}s\n========================================")
        return features_part

    @staticmethod
    def extract_features(uids, path_list, output_file):
        """Extract features from audio files and save to CSV"""
        t0 = time.time()
        fs_mid_list = []
        fs_start_list = []
        fs_end_list = []
        bad_files = []
        # Extract features for each file
        for uid, file_path in tqdm(list(zip(uids, path_list)), desc="Extracting features"):
            try:
                # Compute features
                features_part = FeatureExtractor.extract_features_single(uid, file_path)
                fs_mid_list = features_part[0]
                if features_part[1] is not None:
                    fs_start_list = features_part[1]
                    #fs_end_list = features_part[2]
            except Exception as e:
                print(f"Can't process features for {file_path} ({repr(e)})")
                bad_files.append(file_path)
        # Check if we have any features before creating dataframe
        if not fs_mid_list or fs_mid_list.empty:
            print("No features were extracted???")
            return None
            
        # Process each feature dataframe (mid, start, end)
        for i, fs_df in enumerate([fs_mid_list, fs_start_list, fs_end_list]):
            if fs_df.empty:
                continue
                
            # Create and save dataframe
            df = pd.concat(fs_df, axis=1).T.set_index('uid')
            save_path = str(output_file).replace('.csv', f'_{i+1}.csv') if fs_start_list else output_file
            df.to_csv(save_path, float_format='%.4f')
            print(f"Saved features of {len(df)} files in {time.time()-t0:.2f}s")

        # Print bad files once at the end
        if bad_files:
            print("==========BAD FILES==========")
            print('\n'.join(bad_files))
            print("==========BAD FILES==========")