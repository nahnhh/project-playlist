from typing import List
import numpy as np
import pandas as pd
from .track_connections import InstrumentGroups
from .color_map import *
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def prepare_pca_visualization(feature_vectors: np.ndarray, 
                            track_metadata: List[dict],
                            n_components: int = 3):
    """
    feature_vectors: Array of instrument and beat features
    track_metadata: List of track information
    n_components: Number of PCA components (default 3 for 3D viz)
    """
    # 1. Standardize features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(feature_vectors)

    # 2. Apply PCA
    pca = PCA(n_components=n_components)
    pca_result = pca.fit_transform(scaled_features)

    # 3. Analyze feature importance
    feature_importance = pd.DataFrame(
        pca.components_.T,
        columns=[f'PC{i+1}' for i in range(n_components)],
        index=['beat'] + InstrumentGroups.all_instruments()
    )

    # 4. Prepare visualization data
    viz_data = []
    for i, (coords, metadata) in enumerate(zip(pca_result, track_metadata)):
        # Get top instruments
        inst_values = feature_vectors[i][1:]  # Skip beat score
        top_insts = get_top_instruments(inst_values, 
                                      InstrumentGroups.all_instruments())
        
        viz_data.append({
            'pca_coords': coords,
            'track_info': metadata,
            'instrument_weights': top_insts,
            'beat_score': feature_vectors[i][0]
        })

    return viz_data, feature_importance

def get_top_instruments(inst_values: np.ndarray, 
                       inst_names: List[str], 
                       threshold: float = 0.1) -> dict:
    """
    Get instruments with significant presence
    threshold: minimum value to consider instrument significant
    """
    significant_insts = {}
    for value, name in zip(inst_values, inst_names):
        if value >= threshold:
            significant_insts[name] = value
    
    return dict(sorted(significant_insts.items(), 
                      key=lambda x: x[1], 
                      reverse=True))

# Usage example:
def create_visualization(feature_vectors, track_metadata):
    # Prepare data
    viz_data, importance = prepare_pca_visualization(
        feature_vectors, 
        track_metadata
    )
    
    # Create colors for each point
    colors = [
        calculate_color_multi(
            data['instrument_weights'],
            data['beat_score']
        ) for data in viz_data
    ]
    
    # Create plot
    fig = create_3d_plot(
        np.vstack([d['pca_coords'] for d in viz_data]),
        viz_data
    )
    
    return fig, importance