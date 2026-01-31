import pandas as pd
import numpy as np
from src.data_loader import DataLoader

class VCPScanner:
    def __init__(self):
        pass

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds SMA, RSI, Volume MA to dataframe.
        """
        if df.empty:
            return df
        
        # Simple Moving Averages
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # Volume MA
        df['Vol_SMA_10'] = df['Volume'].rolling(window=10).mean()
        
        # RSI (14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df

    def detect_vcp(self, df: pd.DataFrame) -> dict:
        """
        Detects Volatility Contraction Pattern characteristics.
        Returns a score and details.
        """
        if len(df) < 50:
            return {"is_vcp": False, "reason": "Not enough data"}

        # Logic for VCP is often: High -> Low -> Lower High -> Higher Low (narrowing range)
        # Simplified VCP for v1:
        # 1. Price is in an uptrend (Close > SMA200)
        # 2. Volatility is contracting (Standard Deviation of last 10 days is low relative to price)
        
        current_price = df.iloc[-1]['Close']
        sma_200 = df.iloc[-1]['SMA_200']
        
        if current_price < sma_200:
             return {"is_vcp": False, "reason": "Below SMA 200 (Downtrend)"}

        # Tightness: StdDev of last 10 closes / Current Price
        last_10 = df.iloc[-10:]
        std_dev = last_10['Close'].std()
        tightness = std_dev / current_price
        
        # Contraction check: If tightness < 0.03 (3%), considering it "tight"
        is_tight = tightness < 0.035 
        
        return {
            "is_vcp": is_tight,
            "tightness": round(tightness, 4),
            "sma_200_ok": True
        }

    def detect_spark(self, df: pd.DataFrame) -> dict:
        """
        Detects 'Spark' (Breakout/Momentum) signals.
        """
        if len(df) < 20: 
             return {"is_spark": False}
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. RSI > 50 and rising (Momentum)
        rsi_ok = curr['RSI'] > 50
        
        # 2. Volume Spike (Today's Volume > 1.5x 10-day Average)
        vol_spike = curr['Volume'] > (1.5 * curr['Vol_SMA_10'])
        
        # 3. Price Breakout (Price > SMA50)
        price_breakout = curr['Close'] > curr['SMA_50']
        
        # Comprehensive Trigger
        is_spark = rsi_ok and vol_spike and price_breakout
        
        return {
            "is_spark": is_spark,
            "rsi": round(curr['RSI'], 2),
            "vol_ratio": round(curr['Volume'] / curr['Vol_SMA_10'], 2) if curr['Vol_SMA_10'] > 0 else 0
        }

    def scan_ticker(self, ticker: str, df: pd.DataFrame) -> dict:
        """
        Analyzes a single ticker dataframe.
        """
        if df.empty or len(df) < 200:
             return {"ticker": ticker, "valid": False, "reason": "Insufficient Data"}

        df = self.calculate_technical_indicators(df)
        
        vcp_res = self.detect_vcp(df)
        spark_res = self.detect_spark(df)
        
        return {
            "ticker": ticker,
            "valid": True,
            "current_price": round(df.iloc[-1]['Close'], 2),
            "vcp_score": vcp_res,
            "spark_score": spark_res,
            "actionable": vcp_res['is_vcp'] or spark_res['is_spark']
        }

class AlphaScout:
    def __init__(self):
        self.loader = DataLoader()
        self.scanner = VCPScanner()

    def scan_list(self, tickers: list, target_date: str = None) -> pd.DataFrame:
        results = []
        print(f"Scanning {len(tickers)} tickers for target_date={target_date}...")
        
        for t in tickers:
            df = self.loader.get_price_history(t, target_date=target_date)
            res = self.scanner.scan_ticker(t, df)
            if res['valid']:
                results.append(res)
        
        return pd.DataFrame(results)

if __name__ == "__main__":
    # Test on a few tickers
    scout = AlphaScout()
    # Adding some known names and some random ones
    test_tickers = ["NVDA", "AMD", "INTC", "SMCI"] 
    
    # Test 1: Today
    print("\n--- Scan Result (Today) ---")
    df_res = scout.scan_list(test_tickers)
    print(df_res[['ticker', 'current_price', 'actionable']])
    
    # Test 2: Backtest (e.g. catch SMCI breakout early 2024?)
    # Let's try 2024-01-18 (Random date when SMCI started moving)
    print("\n--- Scan Result (Backtest: 2024-01-18) ---")
    df_res_back = scout.scan_list(test_tickers, target_date="2024-01-18")
    if not df_res_back.empty:
        print(df_res_back[['ticker', 'current_price', 'actionable', 'spark_score']])
