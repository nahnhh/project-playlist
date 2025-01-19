from colorsys import hsv_to_rgb
import plotly.express as px
import plotly.graph_objects as go

# HSV (Hue, Saturation, Value) color space works best for this
INSTRUMENT_COLORS = {
    'keys':    (0,    1, 1),  # Red      (0°)
    'strings': (240,  1, 1),  # Blue     (240°)
    'winds':   (120,  1, 1),  # Green    (120°)
    'vocals':  (300,  1, 1)   # Purple   (300°)
}

# Conceptual implementation
def calculate_color(primary_inst, primary_weight, 
                   secondary_inst, secondary_weight, 
                   beat_score):
    """
    primary_inst: main instrument group
    primary_weight: intensity of primary (0-1)
    secondary_inst: secondary instrument group
    secondary_weight: intensity of secondary (0-1)
    beat_score: 0-3 score for beat intensity
    """
    # Normalize weights to sum to 1
    total = primary_weight + secondary_weight
    p_weight = primary_weight / total
    s_weight = secondary_weight / total

    # Get base colors
    p_color = INSTRUMENT_COLORS[primary_inst]
    s_color = INSTRUMENT_COLORS[secondary_inst]

    # Blend hues
    blended_hue = (p_color[0] * p_weight + 
                   s_color[0] * s_weight)

    # Use beat score for saturation (normalized to 0-1)
    saturation = min(1.0, beat_score / 3.0)

    return hsv_to_rgb(blended_hue/360, saturation, 1.0)

def calculate_color_multi(instrument_weights: dict, beat_score: float):
    """
    instrument_weights: {
        'instrument_group': weight,
        ...
    }
    Example: {
        'keys': 0.5,
        'strings': 0.3,
        'winds': 0.2
    }
    """
    # Normalize weights to sum to 1
    total_weight = sum(instrument_weights.values())
    normalized_weights = {
        inst: weight/total_weight 
        for inst, weight in instrument_weights.items()
    }

    # Weighted average of hues
    blended_hue = sum(
        INSTRUMENT_COLORS[inst][0] * weight
        for inst, weight in normalized_weights.items()
    )

    # Could also consider using the top 2-3 strongest instruments only
    top_instruments = dict(
        sorted(normalized_weights.items(), 
              key=lambda x: x[1], 
              reverse=True)[:2]
    )

    # Normalize top instruments
    top_total = sum(top_instruments.values())
    top_normalized = {k: v/top_total for k, v in top_instruments.items()}

    # Use beat score for saturation
    saturation = min(0.2, beat_score / 3.0)

    return hsv_to_rgb(blended_hue/360, saturation, 1.0)

def create_3d_plot(pca_results, feature_data):
    """
    pca_results: PCA transformed coordinates
    feature_data: Original feature information
    """
    colors = [
        calculate_color(
            row['primary_inst'], row['primary_weight'],
            row['secondary_inst'], row['secondary_weight'],
            row['beat_score']
        ) for row in feature_data
    ]

    fig = go.Figure(data=[go.Scatter3d(
        x=pca_results[:, 0],
        y=pca_results[:, 1],
        z=pca_results[:, 2],
        mode='markers',
        marker=dict(
            size=6,
            color=colors,
            opacity=0.8
        ),
        hovertext=[f"""
            Track: {row['title']}
            Primary: {row['primary_inst']} ({row['primary_weight']:.2f})
            Secondary: {row['secondary_inst']} ({row['secondary_weight']:.2f})
            Beat: {row['beat_score']:.1f}
        """ for row in feature_data]
    )])

    fig.update_layout(
        scene=dict(
            xaxis_title='PC1',
            yaxis_title='PC2',
            zaxis_title='PC3'
        ),
        title='Music Feature Space'
    )

    return fig