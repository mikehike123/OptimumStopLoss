import pandas as pd
import os
import glob
import numpy as np

# --- Configuration Parameters ---
STOCK_DATA_DIR = 'stockData'
REPORTS_DIR = 'reports'
INITIAL_PORTFOLIO_CAPITAL = 100000

def prepare_all_data(stock_files):
    """Loads and aligns data for all tickers in the universe."""
    all_dfs = {}
    for file_path in stock_files:
        ticker = os.path.basename(file_path).split('_')[0]
        try:
            df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
            df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
            df.ffill(inplace=True)
            all_dfs[ticker] = df['Close']
        except Exception as e:
            print(f"  [Error] Could not process {file_path}. Reason: {e}")
            
    portfolio_df = pd.DataFrame(all_dfs)
    first_valid_date = portfolio_df.dropna().index.min()
    portfolio_df = portfolio_df.loc[first_valid_date:]
    portfolio_df.ffill(inplace=True)
    return portfolio_df

def run_rebalanced_benchmark(df, initial_capital):
    """
    Runs a backtest for an Annually Rebalanced, Equal-Weighted Buy & Hold portfolio.
    """
    print("--- Running Annually Rebalanced B&H Benchmark ---")
    num_assets = len(df.columns)
    equity_curve = []
    rebalance_year = -1
    positions = {ticker: 0 for ticker in df.columns} # Stores shares of each asset

    for i in range(len(df)):
        current_date = df.index[i]
        
        # Calculate current portfolio value (sum of all holdings)
        current_value = sum(positions[ticker] * df[ticker].iloc[i] for ticker in df.columns)
        if i == 0: current_value = initial_capital
        
        equity_curve.append(current_value)

        if current_date.year != rebalance_year:
            print(f"  Rebalancing for year {current_date.year}...")
            rebalance_year = current_date.year
            allocation_per_asset = current_value / num_assets
            
            for ticker in df.columns:
                price = df[ticker].iloc[i]
                if price > 0:
                    positions[ticker] = allocation_per_asset / price

    return calculate_performance_metrics(equity_curve, initial_capital, len(df))

def run_buy_and_forget_benchmark(df, initial_capital):
    """
    Runs a backtest for a "Buy and Forget" Equal-Weighted portfolio with NO rebalancing.
    """
    print("\n--- Running Buy and Forget B&H Benchmark (No Rebalancing) ---")
    num_assets = len(df.columns)
    equity_curve = []
    
    # --- Initial Investment on Day 1 ---
    allocation_per_asset = initial_capital / num_assets
    positions = {} # Stores shares of each asset, set only once
    for ticker in df.columns:
        price = df[ticker].iloc[0]
        if price > 0:
            positions[ticker] = allocation_per_asset / price
    
    print("  Initial investment made. Now holding until the end.")

    # --- Hold Phase ---
    for i in range(len(df)):
        current_value = sum(positions[ticker] * df[ticker].iloc[i] for ticker in df.columns)
        equity_curve.append(current_value)

    return calculate_performance_metrics(equity_curve, initial_capital, len(df))

def calculate_performance_metrics(equity_curve, initial_capital, num_days):
    """Calculates final performance metrics from an equity curve."""
    final_equity = equity_curve[-1]
    final_pnl = final_equity - initial_capital
    num_years = num_days / 252.0
    
    cagr = ((final_equity / initial_capital) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0

    eq_series = pd.Series(equity_curve)
    peak = eq_series.expanding(min_periods=1).max()
    drawdown = (eq_series - peak) / peak
    max_drawdown = abs(drawdown.min()) * 100
    
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0

    return { "Final Value": final_equity, "P&L": final_pnl, "CAGR": cagr, "Max Drawdown": max_drawdown, "Calmar": calmar }

def main():
    """Main function to run and compare both benchmark simulations."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    stock_files = glob.glob(os.path.join(STOCK_DATA_DIR, '*.csv'))
    if not stock_files:
        print("Error: No CSV files found."); return

    print(f"Found {len(stock_files)} assets. Preparing portfolio data...\n")
    
    portfolio_df = prepare_all_data(stock_files)
    if portfolio_df.empty:
        print("Could not create portfolio DataFrame. Check data files.")
        return
        
    # --- Run Simulations ---
    rebalanced_results = run_rebalanced_benchmark(portfolio_df, INITIAL_PORTFOLIO_CAPITAL)
    buy_and_forget_results = run_buy_and_forget_benchmark(portfolio_df, INITIAL_PORTFOLIO_CAPITAL)
    
    # --- Print Final Comparison Report ---
    num_years = len(portfolio_df) / 252.0
    print("\n\n--- FINAL BENCHMARK COMPARISON ---")
    print(f"Analysis Period: {portfolio_df.index.min().strftime('%Y-%m-%d')} to {portfolio_df.index.max().strftime('%Y-%m-%d')} ({num_years:.1f} years)")
    print(f"Initial Portfolio Value: ${INITIAL_PORTFOLIO_CAPITAL:,.2f}\n")

    print(f"{'Metric':<20} | {'Rebalanced Portfolio':<25} | {'Buy & Forget Portfolio':<25}")
    print("-" * 75)
    print(f"{'Final Value':<20} | ${rebalanced_results['Final Value']:<24,.2f} | ${buy_and_forget_results['Final Value']:<24,.2f}")
    print(f"{'Total P&L':<20} | ${rebalanced_results['P&L']:<24,.2f} | ${buy_and_forget_results['P&L']:<24,.2f}")
    print(f"{'CAGR (%)':<20} | {rebalanced_results['CAGR']:<24.2f} | {buy_and_forget_results['CAGR']:<24.2f}")
    print(f"{'Max Drawdown (%)':<20} | {rebalanced_results['Max Drawdown']:<24.2f} | {buy_and_forget_results['Max Drawdown']:<24.2f}")
    print(f"{'Calmar Ratio':<20} | {rebalanced_results['Calmar']:<24.2f} | {buy_and_forget_results['Calmar']:<24.2f}")


if __name__ == "__main__":
    main()