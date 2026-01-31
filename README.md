# Ripple Scout v1.0

Monitoring system that captures "Ripple Effects" in the supply chain. It tracks "Core" stocks (e.g., NVDA) and scans their downstream "Neighbors" (e.g., SMCI, VRT) for technical breakouts (VCP, Spark).

## 📂 Project Structure
- `src/`: Source code (Scanner, Graph, Main Orchestrator).
- `config/`: Configuration files (e.g., `neighbors.json`).
- `doc/`: Design docs and plans.

## 🚀 Setup

1. **Install Dependencies:**
   ```bash
   # Ensure you have uv installed (https://github.com/astral-sh/uv)
   uv sync
   ```

## 🛠 Usage

### 1. Run the Dashboard (UI)
The easiest way to use the system.
```bash
uv run streamlit run src/app.py
```

### 2. Run the CLI Scanner
Scan for current signals based on the latest market data directly in terminal.
```bash
uv run python -m src.main
```

### 2. Backtest (Historical Scan)
Test the logic on a specific past date to see if it would have caught a move (e.g., checking Jan 2024).
```bash
uv run python -m src.main --target_date 2024-01-18
```
*Note: Format is YYYY-MM-DD.*

## 📊 Modules
- **Scanner:** Implements VCP (Volatility Contraction) and Spark (Momentum) detection.
- **Linkage:** Maps Core stocks to Neighbors using `config/neighbors.json`.
- **Data:** Uses `yfinance`.
