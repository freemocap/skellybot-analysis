import numpy as np
import pandas as pd
from plotly import graph_objects as go

import logging
logger = logging.getLogger(__name__)


def create_histogram_subplot(fig: go.Figure,
                             data: pd.Series,
                             subplot_row: int,
                             subplot_col: int,
                             x_label: str,
                             color: str,
                             number_of_bins: int = 30,
                             max_bin: int = None,
                             min_bin: int = None,
                             units: str = "units",
                             allow_fractional_bins: bool = False,  #if False, binning will ensure all bins are whole numbers
                             subplot_title: str = None,
                             ):
    # Calculate statistics
    mean_val = data.mean()
    median_val = data.median()
    min_val = data.min()
    max_val = data.max()
    data_range = max_val - min_val

    # Calculate mode (most frequent value)
    try:
        mode_val = data.mode()[0]  # Get the first mode if there are multiple
    except:
        mode_val = None

    # Use bin_edges if provided, otherwise calculate bins based on max_bin
    bin_min = min_bin if min_bin is not None else min_val
    bin_max = max_bin if max_bin is not None else max_val

    # Handle non-fractional binning
    if not allow_fractional_bins:
        # Round bin edges to integers
        bin_min = int(np.floor(bin_min))
        bin_max = int(np.ceil(bin_max))

        # Calculate bin size based on the range and number of bins
        bin_size = max(1, (bin_max - bin_min) // number_of_bins)

        # Recalculate number of bins to ensure whole number bin sizes
        number_of_bins = (bin_max - bin_min) // bin_size

        # Adjust bin_max to ensure exact division into whole number bins
        bin_max = bin_min + (number_of_bins * bin_size)
    bin_edges = np.linspace(bin_min, bin_max, number_of_bins + 1)
    hist_values, bin_edges = np.histogram(data, bins=bin_edges)
    max_freq = hist_values.max()
    bin_size = (bin_edges[1] - bin_edges[0])

    logger.info(
        f"Creating histogram for {x_label} (row {subplot_row}, col {subplot_col}), data size: {len(data)}, "
        f"max_freq: {max_freq}, mean: {mean_val}, median: {median_val}, mode: {mode_val}, "
        f"range: {min_val}-{max_val}, bin_size: {bin_size:.2f}")
    histogram_args = {
        "x": data,
        "marker_color": color,
        "name": x_label
    }

    if bin_edges is not None:
        histogram_args["xbins"] = dict(start=bin_edges[0], end=bin_edges[-1], size=bin_size)
    else:
        histogram_args["nbinsx"] = 30

    fig.add_trace(
        go.Histogram(**histogram_args),
        row=subplot_row,
        col=subplot_col
        )

    # Create a darkened version of the histogram color for the line
    # Parse the color to determine if it's hex, rgb, or rgba
    darkened_color = color
    if color.startswith('#'):
        # Convert hex to rgb and darken
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        # Darken by multiplying by 0.7
        r, g, b = int(r * 0.7), int(g * 0.7), int(b * 0.7)
        darkened_color = f"rgb({r},{g},{b})"
    elif color.startswith('rgb'):
        # Extract rgb values and darken
        rgb_values = color.strip('rgb()').split(',')
        r, g, b = [int(val.strip()) for val in rgb_values]
        # Darken by multiplying by 0.7
        r, g, b = int(r * 0.7), int(g * 0.7), int(b * 0.7)
        darkened_color = f"rgb({r},{g},{b})"

    # Add a blocky line along the top of the histogram bins
    x_line = []
    y_line = []

    # Start at zero height at the first bin edge
    x_line.append(bin_edges[0])
    y_line.append(0)

    # For each bin, create the step pattern
    for i in range(len(hist_values)-1):
        # Bottom-left corner of the bin
        x_line.append(bin_edges[i])
        y_line.append(hist_values[i])

        # Top-right corner of the bin
        x_line.append(bin_edges[i + 1])
        y_line.append(hist_values[i])

        # If this is the last bin, add a point at zero height
        if i == len(hist_values) - 1:
            x_line.append(bin_edges[i + 1])
            y_line.append(0)

    fig.add_trace(
        go.Scatter(
            x=x_line,
            y=y_line,
            mode='lines',
            line=dict(
                width=2.5,
                color=darkened_color,
            ),
            showlegend=False,
            hoverinfo='none'
        ),
        row=subplot_row,
        col=subplot_col
    )

    # Define statistical markers with their colors
    stat_markers = [
        {"value": mean_val, "color": "red", "name": "Mean"},
        {"value": median_val, "color": "green", "name": "Median"},
    ]

    if mode_val is not None:
        stat_markers.append({"value": mode_val, "color": "blue", "name": "Mode"})

    # Find the height of each bin for the statistical markers
    def get_bin_height(value):
        # Find which bin the value falls into
        for i in range(len(bin_edges) - 1):
            if bin_edges[i] <= value < bin_edges[i + 1]:
                return hist_values[i]
        # If value is exactly at the last edge
        if value == bin_edges[-1]:
            return hist_values[-1]
        return 0  # Default if not found

    def get_bin_midpoint(value):
        # Find which bin the value falls into
        for i in range(len(bin_edges) - 1):
            if bin_edges[i] <= value < bin_edges[i + 1]:
                return (bin_edges[i] + bin_edges[i + 1]) / 2
        # If value is exactly at the last edge
        if value == bin_edges[-1]:
            return (bin_edges[-2] + bin_edges[-1]) / 2
        return 0
    # Add triangle markers for statistics right above their respective bins
    for marker in stat_markers:


        fig.add_trace(
            go.Scatter(
                x=[get_bin_midpoint(marker["value"])]*2,  # Midpoint of the bin
                y=[get_bin_height(marker['value']), max_freq* 1.1],  # Position above the histogram
                mode="lines",
                line=dict(
                    width=1,
                    color="grey",
                    dash="dot"

                ),
                showlegend=False,
                hoverinfo="text",
                hovertext=f"{marker['name']}: {marker['value']:.1f} {units}"
            ),
            row=subplot_row,
            col=subplot_col
        )
        fig.add_trace(
            go.Scatter(
                x=[get_bin_midpoint(marker["value"])],  # Midpoint of the bin
                y=[max_freq* 1.1],  # Position above the histogram
                mode="markers",
                marker=dict(
                    symbol="triangle-down",
                    size=8,
                    color=marker["color"],
                    line=dict(width=1, color="black")
                ),
                showlegend=False,
                hoverinfo="text",
                hovertext=f"{marker['name']}: {marker['value']:.1f} {units}"
            ),
            row=subplot_row,
            col=subplot_col
        )

    # Create stats text for upper right corner with colored markers
    stats_text = (
        f"<span>Mean: {mean_val:.1f} <span style='color:red'>▼</span></span><br>"
        f"<span>Median: {median_val:.1f} <span style='color:green'>▼</span></span><br>"
    )

    if mode_val is not None:
        stats_text += f"<span>Mode: {mode_val:.1f} <span style='color:blue'>▼</span></span><br>"
    else:
        stats_text += f"Mode: N/A<br>"

    stats_text += (
        f"Range: {int(min_val)} - {int(max_val)}<br>"
        f"Bin size: {bin_size:.1f}"
    )

    # Add annotation in the upper right corner
    fig.add_annotation(
        x=0.95, y=0.95,
        xref="x domain", yref="y domain",
        text=stats_text,
        showarrow=False,
        align="right",
        bgcolor="rgba(255, 255, 255, 0.7)",
        bordercolor="black",
        borderwidth=1,
        borderpad=4,
        font=dict(size=10),
        row=subplot_row, col=subplot_col
    )

    # Axis labels
    fig.update_xaxes(title_text=x_label,
                     title_standoff=2,  # Reduce standoff to move label closer to axis
                     row=subplot_row, col=subplot_col)
    fig.update_yaxes(
        title_text="Frequency",
        title_standoff=2,  # Reduce standoff to move label closer to axis
        row=subplot_row,
        col=subplot_col
    )
    # Ensure y-axis extends high enough to show the markers
    fig.update_yaxes(range=[0, max_freq * 1.15], row=subplot_row, col=subplot_col)
