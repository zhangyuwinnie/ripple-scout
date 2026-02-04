import os
import json
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta

def download_data():
    # 1. Load all unique tickers from config
    # Assuming running from project root (ripple-scout/)
    config_path = Path("config/neighbors.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    all_tickers = set(config.keys())
    for core, info in config.items():
        all_tickers.update(info.get("neighbors", []))
    
    print(f"Total unique tickers to download: {len(all_tickers)}")

    # 2. Setup storage
    data_dir = Path("data/historical")
    data_dir.mkdir(parents=True, exist_ok=True)

    # 3. Define time range (2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)
    
    # 4. Download and save
    failed = []
    for ticker in sorted(all_tickers):
        print(f"Downloading {ticker}...")
        try:
            # We use a buffer of 300 days extra to ensure technical indicators (like 200MA) 
            # have enough data even at the start of our 2-year backtest period.
            df = yf.download(ticker, start=start_date - timedelta(days=300), end=end_date, progress=False)
            if df.empty:
                print(f"  [!] No data found for {ticker}")
                failed.append(ticker)
                continue
            
            # Save to parquet (efficient for time-series)
            file_path = data_dir / f"{ticker}.parquet"
            df.to_parquet(file_path)
            print(f"  [+] Saved to {file_path}")
        except Exception as e:
            print(f"  [!] Error downloading {ticker}: {e}")
            failed.append(ticker)

    print("\n--- Download Complete ---")
    if failed:
        print(f"Failed tickers: {', '.join(failed)}")
    else:
        print("All tickers downloaded successfully.")

if __name__ == "__main__":
    download_data()
