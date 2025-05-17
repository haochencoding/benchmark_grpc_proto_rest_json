import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def generate_desc_stats(df, col):
    summary_records = []
    grouped = df.groupby(['protocol', 'size'])

    for (protocol, size), group in grouped:
        data = group[col].dropna()
        mean = data.mean()
        std = data.std()
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        min_val = data.min()
        max_val = data.max()
        count = data.count()

        summary_records.append({
            'protocol': protocol,
            'size': size,
            'variable': col,
            'mean': mean,
            'std': std,
            'IQR': iqr,
            'min': min_val,
            'max': max_val,
            'count': count
        })

    # Create a DataFrame for the summary
    summary_df = pd.DataFrame(summary_records)

    return summary_df


def boxplots_by_size(df, col, protocols=['grpc', 'rest_proto', 'rest_json'], n_col_plot=4, figsize=(12, 6)):
    """
    For a given numeric column `col` in df (with 'protocol' & 'size'):
        - Builds a list of N sublists (one per size) of 3 arrays (grpc, rest_proto, rest_json).
        - Draws a grid of boxplots: n_rows × n_col_plot subplots, each for one size.
    """
    # 1) Define order of sizes & protocols
    sizes = sorted(df['size'].unique())

    # 2) Prepare the nested data list
    data = [
        [
            df.loc[(df['size']==size) & (df['protocol']==protocol), col]
                .dropna().values
            for protocol in protocols
        ]
        for size in sizes
    ]

    # 3) Plot setup
    plt.style.use("default")
    n_rows = math.ceil(len(sizes) / n_col_plot)
    fig, axes = plt.subplots(
        n_rows,
        n_col_plot,
        figsize=figsize,
        sharey=False
    )
    axes = np.array(axes).flatten()     # ensure a 1D array of Axes

    # 4) Draw each boxplot
    for ax, size, dat in zip(axes, sizes, data):
        ax.boxplot(dat)
        ax.set_title(f"{size} items per request")
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(protocols, rotation=0, ha='center')

    # 5) Hide any extra subplots
    for ax in axes[len(sizes):]:
        ax.axis('off')

    fig.suptitle(f"Boxplots of `{col}` by Protocol for Different Numbers of Items Per Request", y=1.02)
    plt.tight_layout()
    plt.show()