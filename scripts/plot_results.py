import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def generate_plot():
    data_path = Path("ripple-scout/data/ripple_backtest_results.csv")
    if not data_path.exists():
        print("No data found.")
        return

    df = pd.read_csv(data_path)
    
    # Group by Pair
    pair_stats = df.groupby(['core_ticker', 'neighbor']).agg(
        events=('date', 'count'),
        avg_return=('return_20d', 'mean'),
        win_rate=('return_20d', lambda x: (x > 0).mean())
    ).reset_index()

    # Filter for min events
    min_events = 10
    subset = pair_stats[pair_stats['events'] >= min_events].copy()
    
    # Convert to %
    subset['avg_return'] *= 100
    subset['win_rate'] *= 100

    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")
    
    # Plot
    scatter = sns.scatterplot(
        data=subset, 
        x="win_rate", 
        y="avg_return", 
        size="events", 
        hue="core_ticker",
        sizes=(50, 400),
        alpha=0.7,
        palette="tab10"
    )

    # Add labels for top performers (High Return OR High Win Rate)
    for i in range(subset.shape[0]):
        row = subset.iloc[i]
        if row['avg_return'] > 5 or row['win_rate'] > 60:
            plt.text(
                row['win_rate']+0.5, 
                row['avg_return'], 
                f"{row['core_ticker']}->{row['neighbor']}", 
                horizontalalignment='left', 
                size='small', 
                color='black', 
                weight='semibold'
            )

    plt.title(f"Ripple Strategy: Risk vs Reward (Min {min_events} Signals)", fontsize=16)
    plt.xlabel("Win Rate (%)", fontsize=12)
    plt.ylabel("Avg 20-Day Return (%)", fontsize=12)
    plt.axhline(0, color='red', linestyle='--')
    plt.axvline(50, color='gray', linestyle='--')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Core Source")
    
    out_path = Path("ripple-scout/data/backtest_summary.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    print(f"MEDIA: {out_path.absolute()}")

if __name__ == "__main__":
    generate_plot()
