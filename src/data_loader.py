import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class DataLoader:
    def __init__(self, cache_dir="data"):
        self.cache_dir = cache_dir

    def fetch_data(self, ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Fetches historical data for a ticker. 
        If end_date is provided, it simulates 'today' being end_date by only returning data up to that point.
        """
        # Set default start date to 1 year ago if not specified, to ensure enough data for VCP (200 days)
        if not start_date:
            # If end_date is set, go back 1 year from there. Otherwise 1 year from actual today.
            if end_date:
                base_date = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                base_date = datetime.now()
            start_date = (base_date - timedelta(days=400)).strftime("%Y-%m-%d")

        # Fetch data
        print(f"Fetching {ticker} from {start_date} to {end_date if end_date else 'Now'}...")
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, multi_level_index=False)
            
            if df.empty:
                print(f"Warning: No data found for {ticker}")
                return df
            
            # Ensure columns are flat (yfinance sometimes returns multi-index if multiple tickers)
            if isinstance(df.columns, pd.MultiIndex):
                 df.columns = df.columns.get_level_values(0)

            return df
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return pd.DataFrame()

    def get_price_history(self, ticker: str, target_date: str = None, lookback_days: int = 365) -> pd.DataFrame:
        """
        Get price history ending at target_date (inclusive).
        target_date: "YYYY-MM-DD". If None, uses today.
        """
        if target_date:
            # yfinance end_date is exclusive, so we need target_date + 1 day
            end_dt = datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)
            end_str = end_dt.strftime("%Y-%m-%d")
            
            start_dt = end_dt - timedelta(days=lookback_days)
            start_str = start_dt.strftime("%Y-%m-%d")
            
            return self.fetch_data(ticker, start_date=start_str, end_date=end_str)
        else:
            return self.fetch_data(ticker, start_date=(datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"))

if __name__ == "__main__":
    # fast test
    loader = DataLoader()
    df = loader.get_price_history("NVDA", target_date="2024-01-01")
    print("NVDA 2024-01-01 Last Close:", df.iloc[-1]['Close'])
