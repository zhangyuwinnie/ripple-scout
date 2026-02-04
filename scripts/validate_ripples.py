import pandas as pd
import json
from pathlib import Path
from src.scanner import VCPScanner

def validate_ripples():
    # 1. Load Config & Core Signals
    config_path = Path("config/neighbors.json")
    with open(config_path, "r") as f:
        config = json.load(f)
        
    signals_path = Path("data/core_signals.csv")
    if not signals_path.exists():
        print("Run generate_core_signals.py first!")
        return

    core_signals = pd.read_csv(signals_path)
    core_signals['date'] = pd.to_datetime(core_signals['date'])
    
    print(f"Loaded {len(core_signals)} core signals.")

    # 2. Pre-load and Pre-process All Neighbor Data
    # Get unique list of neighbors
    all_neighbors = set()
    for info in config.values():
        all_neighbors.update(info.get("neighbors", []))
    
    print(f"Loading data for {len(all_neighbors)} neighbors...")
    
    neighbor_data = {}
    scanner = VCPScanner()
    data_dir = Path("data/historical")

    for ticker in all_neighbors:
        file_path = data_dir / f"{ticker}.parquet"
        if not file_path.exists():
            continue
            
        df = pd.read_parquet(file_path)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = df.columns.str.strip()
        df = df.sort_index()
        
        # Calculate Indicators & Signals for Neighbor
        df = scanner.calculate_technical_indicators(df)
        
        # Vectorized Signal Detection (Same as before)
        df['std_10'] = df['Close'].rolling(10).std()
        df['tightness'] = df['std_10'] / df['Close']
        df['is_vcp'] = (df['Close'] > df['SMA_200']) & (df['tightness'] < 0.035)
        df['is_spark'] = (df['RSI'] > 50) & (df['Volume'] > 1.5 * df['Vol_SMA_10']) & (df['Close'] > df['SMA_50'])
        
        neighbor_data[ticker] = df

    # 3. Correlate
    results = []
    
    for idx, row in core_signals.iterrows():
        core_ticker = row['ticker']
        signal_date = row['date']
        signal_type = row['signal']
        
        # Who are the neighbors?
        # Note: config is keyed by Core Ticker
        if core_ticker not in config:
            continue
            
        target_neighbors = config[core_ticker]["neighbors"]
        
        for nb in target_neighbors:
            if nb not in neighbor_data:
                continue
                
            df = neighbor_data[nb]
            
            # Find the row for signal_date
            if signal_date not in df.index:
                continue
                
            # Get integer location of signal_date
            try:
                # searchsorted is faster but requires unique monotonic index
                # get_loc is standard
                loc_idx = df.index.get_loc(signal_date)
            except KeyError:
                continue
            
            # We need forward looking data
            # Check if we have enough days remaining
            max_days = 20
            if loc_idx + max_days >= len(df):
                continue
            
            # Base price (Close on signal day)
            base_close = df.iloc[loc_idx]['Close']
            
            # Future prices
            future_5 = df.iloc[loc_idx + 5]
            future_10 = df.iloc[loc_idx + 10]
            future_20 = df.iloc[loc_idx + 20]
            
            # Max Return in next 20 days (High)
            future_window = df.iloc[loc_idx+1 : loc_idx+21]
            max_price = future_window['High'].max()
            
            # Check for Neighbor Signals in the window [T+1, T+5]
            # Did the neighbor catch the spark?
            ripple_window = df.iloc[loc_idx+1 : loc_idx+6]
            has_ripple_signal = ripple_window['is_spark'].any() or ripple_window['is_vcp'].any()
            
            res = {
                "core_date": signal_date,
                "core_ticker": core_ticker,
                "core_signal": signal_type,
                "neighbor": nb,
                "return_5d": (future_5['Close'] - base_close) / base_close,
                "return_10d": (future_10['Close'] - base_close) / base_close,
                "return_20d": (future_20['Close'] - base_close) / base_close,
                "max_return_20d": (max_price - base_close) / base_close,
                "neighbor_triggered_signal": has_ripple_signal
            }
            results.append(res)

    # 4. Save and Summarize
    if results:
        res_df = pd.DataFrame(results)
        out_path = Path("data/ripple_backtest_results.csv")
        res_df.to_csv(out_path, index=False)
        
        print(f"\nAnalysis Complete. {len(res_df)} correlation events processed.")
        
        # Quick Stats
        avg_ret_5 = res_df['return_5d'].mean() * 100
        avg_ret_20 = res_df['return_20d'].mean() * 100
        win_rate = (res_df['return_20d'] > 0).mean() * 100
        
        print("\n--- Summary Stats ---")
        print(f"Avg 5-Day Return: {avg_ret_5:.2f}%")
        print(f"Avg 20-Day Return: {avg_ret_20:.2f}%")
        print(f"20-Day Win Rate: {win_rate:.2f}%")
        
        print("\n--- Top Performing Pairs (Avg 20d Return) ---")
        pair_stats = res_df.groupby(['core_ticker', 'neighbor'])['return_20d'].mean().sort_values(ascending=False)
        print(pair_stats.head(10))
        
    else:
        print("No results generated.")

if __name__ == "__main__":
    validate_ripples()
