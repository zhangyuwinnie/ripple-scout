import argparse
import pandas as pd
from src.scanner import AlphaScout
from src.graph import KnowledgeGraph
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Ripple Scout v1.0")
    parser.add_argument("--target_date", type=str, help="YYYY-MM-DD for backtesting", default=None)
    args = parser.parse_args()

    target_date = args.target_date
    print(f"--- Starting Ripple Scout (Target: {target_date if target_date else 'Today'}) ---")

    # Initialize
    scout = AlphaScout()
    kg = KnowledgeGraph()
    
    # 1. Get Core List
    core_tickers = kg.get_core_tickers()
    if not core_tickers:
        print("No core tickers found in config.")
        return

    # 2. Scan Core Tickers
    print(f"Scanning {len(core_tickers)} Core Tickers...")
    core_results = scout.scan_list(core_tickers, target_date=target_date)
    
    if core_results.empty:
        print("No data for core tickers.")
        return

    # Filter for "Actionable" Core Stocks (Source of Ripple)
    # Actionable = VCP or Spark
    active_cores = core_results[core_results['actionable'] == True]
    
    print("\n=== Core Alerts (Ripple Sources) ===")
    if active_cores.empty:
        print("No active signals in Core List.")
    else:
        print(f"Found {len(active_cores)} active core stocks.")
        for _, row in active_cores.iterrows():
            print(f"  > {row['ticker']} (${row['current_price']}) - VCP: {row['vcp_score']['is_vcp']}, Spark: {row['spark_score']['is_spark']}")

    # 3. Scan Neighbors for Active Cores (The Ripple)
    # If a core is active, we scan its neighbors
    # For v1, let's also allow a mode where we scan ALL neighbors if user wants, 
    # but strictly following the graph logic: "Ripple" implies causal link.
    
    ripple_candidates = set()
    for _, row in active_cores.iterrows():
        t = row['ticker']
        neighbors = kg.get_neighbors(t)
        print(f"\n[Ripple Effect] Scanning {len(neighbors)} neighbors of {t} ({kg.get_ripple_logic(t)})...")
        ripple_candidates.update(neighbors)
        
    if not ripple_candidates:
        print("\nNo ripple candidates to scan (no active core or no neighbors).")
        return

    # Scan unique candidates
    candidates_list = list(ripple_candidates)
    ripple_results = scout.scan_list(candidates_list, target_date=target_date)
    
    if ripple_results.empty:
         print("No data for candidates.")
         return

    # Filter Actionable Ripples
    active_ripples = ripple_results[ripple_results['actionable'] == True]
    
    print("\n=== Ripple Opportunities (Actionable Neighbors) ===")
    if active_ripples.empty:
        print("No actionable signals in candidate pool.")
    else:
        for _, row in active_ripples.iterrows():
            # Find which core triggered this? (Could be multiple, simplified here)
            print(f"  >> {row['ticker']} (${row['current_price']})")
            print(f"     VCP Tightness: {row['vcp_score']['tightness']}")
            print(f"     Spark Info: {row['spark_score']}")

if __name__ == "__main__":
    main()
