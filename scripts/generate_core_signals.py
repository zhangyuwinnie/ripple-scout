import pandas as pd
import json
from pathlib import Path
from src.scanner import VCPScanner

def generate_signals():
    # 1. Load config
    config_path = Path("config/neighbors.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    core_tickers = list(config.keys())
    print(f"Core Tickers to scan: {core_tickers}")

    # 2. Scanner helper
    # We use VCPScanner only for calculate_technical_indicators if possible, 
    # but that method modifies DF in place which is what we want.
    scanner = VCPScanner()
    
    all_signals = []

    data_dir = Path("data/historical")
    
    for ticker in core_tickers:
        file_path = data_dir / f"{ticker}.parquet"
        if not file_path.exists():
            print(f"[!] No data for {ticker}, skipping.")
            continue
            
        print(f"Scanning {ticker}...")
        df = pd.read_parquet(file_path)
        
        # Ensure data is sorted
        df = df.sort_index()
        
        # Calculate indicators
        # Note: We need to handle yfinance MultiIndex columns if present
        # (Though our downloader tried to flatten them, parquet might preserve structure if not careful)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Clean up column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        # Calculate Technicals
        df = scanner.calculate_technical_indicators(df)
        
        # --- Vectorized Detection ---
        
        # VCP Logic
        # tightness: StdDev of last 10 closes / Current Price
        # We use shifting to avoid lookahead bias? rolling(10) includes current row.
        # Yes, standard VCP is "tightness leading up to today".
        df['std_10'] = df['Close'].rolling(window=10).std()
        df['tightness'] = df['std_10'] / df['Close']
        
        # Condition 1: Price > SMA 200 (Uptrend)
        cond_uptrend = df['Close'] > df['SMA_200']
        # Condition 2: Tightness < 3.5%
        cond_tight = df['tightness'] < 0.035
        
        df['is_vcp'] = cond_uptrend & cond_tight
        
        # Spark Logic
        # Condition 1: RSI > 50
        cond_rsi = df['RSI'] > 50
        # Condition 2: Volume > 1.5 * 10-day Vol MA
        cond_vol = df['Volume'] > (1.5 * df['Vol_SMA_10'])
        # Condition 3: Price > SMA 50
        cond_breakout = df['Close'] > df['SMA_50']
        
        df['is_spark'] = cond_rsi & cond_vol & cond_breakout
        
        # Extract Signals
        # We only care about days where at least one signal is True
        signals = df[df['is_vcp'] | df['is_spark']].copy()
        
        if signals.empty:
            continue
            
        for date, row in signals.iterrows():
            signal_types = []
            if row['is_vcp']: signal_types.append("VCP")
            if row['is_spark']: signal_types.append("Spark")
            
            all_signals.append({
                "date": date,
                "ticker": ticker,
                "signal": "+".join(signal_types),
                "close": row['Close'],
                "tightness": row['tightness'] if row['is_vcp'] else None,
                "rsi": row['RSI'] if row['is_spark'] else None
            })

    # 3. Save Results
    if all_signals:
        results_df = pd.DataFrame(all_signals)
        out_path = Path("data/core_signals.csv")
        results_df.to_csv(out_path, index=False)
        print(f"\nSaved {len(results_df)} signals to {out_path}")
        print(results_df.head())
    else:
        print("No signals found.")

if __name__ == "__main__":
    generate_signals()
