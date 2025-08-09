import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# --- Step 1: Define Tickers and Parameters ---
#tickers = ['SPY', 'AGG', 'GLD', 'QQQ', 'EFA', 'AAPL', 'MSFT']
public_tickers = ['TQQQ']
# We need a reference index for our custom funds, so we'll grab it from AGG.
reference_index = None
end_date = datetime.today()
start_date = end_date - timedelta(days=30 * 365)
interval = '1d'
output_dir = 'stockData'

# --- Step 2: Create Directory ---
try:
    os.makedirs(output_dir, exist_ok=True)
    print(f"Directory '{output_dir}' created or already exists.")
except Exception as e:
    print(f"Error creating directory: {e}")
    exit()

# --- Step 3: Download Data with the Explicit Fix ---
print("\nStarting data download...")

for ticker in public_tickers:
    print(f"Processing {ticker}...")
    try:
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(start=start_date, end=end_date, interval=interval, auto_adjust=True)
        
        # <<< FIX #1: REMOVE TIMEZONE INFORMATION >>>
        # This makes the index 'timezone-naive' so it can match our generated files.
        data.index = data.index.tz_localize(None)

        if not data.empty:
            if reference_index is None:
                reference_index = data.index # Save the clean index from the first successful download
            
            columns_to_drop = ['Dividends', 'Stock Splits', 'Capital Gains']
            data = data.drop(columns=[col for col in columns_to_drop if col in data.columns], errors='ignore')
            file_path = os.path.join(output_dir, f"{ticker}_{interval}.csv")
            data.to_csv(file_path)
        print(f"\nSuccessfully saved data for {ticker} to {file_path}")

    except Exception as e:
        print(f"An error occurred while processing {ticker}: {e}")

print("\n------------------------------------")
print("All downloads complete.")
print("------------------------------------")