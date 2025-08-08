import pandas as pd
import pandas_ta as ta
import os
import glob
import numpy as np

# --- Configuration Parameters ---
STOCK_DATA_DIR = 'stockData'
REPORTS_DIR = 'reports'
MA_PERIOD = 365
INITIAL_CAPITAL_PORTFOLIO = 100000 
INITIAL_CAPITAL_INDIVIDUAL = 100000 
COMMISSION_PCT = 0.0005
# NOTE: Position size is now set dynamically depending on the simulation tier
# For Tier 2 (Portfolio), it will be 0.10. For Tier 1 (Individual), it will be 1.0.

# <<< Optimization Parameters >>>
TRAILING_STOPS_PCT = [10, 15, 20, 25, 30]
PROFIT_TARGETS_PCT = [None, 50, 100, 150, 200]

def prepare_data(file_path, ma_period):
    """Loads data, ensures index is a timezone-naive datetime, and calculates indicators."""
    try:
        df = pd.read_csv(file_path, index_col='Date')
        df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
        df.ta.sma(length=ma_period, append=True, col_names=(f'SMA_{ma_period}',))
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"  [Error] Could not process {file_path}. Reason: {e}")
        return None

def calculate_benchmark_stats(df, start_capital):
    """Calculates performance for a Buy and Hold strategy."""
    if df.empty or start_capital <= 0:
        return {"P&L ($)": 0, "CAGR (%)": 0, "Max Drawdown (%)": 0, "Calmar Ratio": 0}
    start_price = df['Open'].iloc[0]
    if start_price <= 0: return {"P&L ($)": 0, "CAGR (%)": 0, "Max Drawdown (%)": 0, "Calmar Ratio": 0}
    end_price = df['Close'].iloc[-1]
    num_shares = start_capital / start_price
    final_equity = num_shares * end_price
    equity_curve = (start_capital / start_price) * df['Close']
    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak
    max_drawdown = abs(drawdown.min()) * 100
    num_years = len(df) / 252 
    cagr = ((final_equity / start_capital) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0
    return { "P&L ($)": final_equity - start_capital, "CAGR (%)": cagr, "Max Drawdown (%)": max_drawdown, "Calmar Ratio": calmar }

def run_backtest(df, trailing_stop_pct, profit_target_pct, initial_capital, position_size_pct, commission_pct, sma_col):
    """The unified backtest engine, now accepting position size as a parameter."""
    in_position = False
    entry_price = 0
    peak_price_since_entry = 0
    position_size_dollars = initial_capital * position_size_pct
    num_shares = 0
    cash = initial_capital
    equity_curve = [initial_capital]
    trades = []
    
    for i in range(1, len(df)):
        current_position_value = num_shares * df['Close'].iloc[i-1] if in_position else 0
        current_equity = cash + current_position_value
        equity_curve.append(current_equity)

        if in_position:
            peak_price_since_entry = max(peak_price_since_entry, df['High'].iloc[i])
            exit_price = -1
            trailing_stop_price = peak_price_since_entry * (1 - trailing_stop_pct / 100)
            if df['Low'].iloc[i] <= trailing_stop_price: exit_price = trailing_stop_price
            if exit_price == -1 and profit_target_pct is not None:
                profit_target_price = entry_price * (1 + profit_target_pct / 100)
                if df['High'].iloc[i] >= profit_target_price: exit_price = profit_target_price
            if exit_price != -1:
                exit_value = num_shares * exit_price
                cash += exit_value * (1 - commission_pct)
                trades.append({"pnl": (exit_price - entry_price) / entry_price})
                in_position = False; num_shares = 0
        
        if not in_position and i > 1:
            prev_close, prev_sma = df['Close'].iloc[i-1], df[sma_col].iloc[i-1]
            prev_prev_close, prev_prev_sma = df['Close'].iloc[i-2], df[sma_col].iloc[i-2]
            if prev_prev_close <= prev_prev_sma and prev_close > prev_sma:
                entry_price_candidate = df['Open'].iloc[i]
                if entry_price_candidate > 0:
                    entry_price = entry_price_candidate
                    peak_price_since_entry = entry_price
                    # Use the dynamically set position size
                    position_size_dollars = current_equity * position_size_pct
                    num_shares = position_size_dollars / entry_price
                    position_cost = num_shares * entry_price
                    cash -= position_cost * (1 + commission_pct)
                    in_position = True

    final_equity = equity_curve[-1]
    final_pnl = final_equity - initial_capital
    num_years = len(df) / 252
    cagr = ((final_equity / initial_capital) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0
    eq_series = pd.Series(equity_curve)
    peak = eq_series.expanding(min_periods=1).max()
    drawdown = (eq_series - peak) / peak
    max_drawdown = abs(drawdown.min()) * 100
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0

    return {
        "Trailing Stop (%)": trailing_stop_pct,
        "Profit Target (%)": "None" if profit_target_pct is None else profit_target_pct,
        "P&L ($)": final_pnl, "CAGR (%)": cagr, 
        "Max Drawdown (%)": max_drawdown, "Calmar Ratio": calmar,
        "Total Trades": len(trades),
        "% Profitable": (sum(1 for t in trades if t['pnl'] > 0) / len(trades) * 100) if trades else 0,
    }

def generate_individual_report(ticker, results_df, sweet_spot, bh_stats, report_dir, ma_period, num_years, start_date, end_date):
    """Generates a detailed individual report assuming 100% capital allocation to this asset."""
    display_df = results_df.copy()
    for col in ['P&L ($)', 'CAGR (%)', 'Max Drawdown (%)', '% Profitable', 'Calmar Ratio']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}")
    
    md_content = f"# Backtest Report (Individual Asset Focus) for {ticker.upper()}\n\n"
    md_content += "## Backtest Configuration\n"
    md_content += f"- **Universe:** This asset ONLY.\n"
    md_content += f"- **Starting Capital:** `${INITIAL_CAPITAL_INDIVIDUAL:,.2f}`\n"
    md_content += f"- **Position Sizing:** Each trade uses **100%** of available equity.\n"
    md_content += f"- **Strategy:** Buy on Close crossing above the **{ma_period}-period SMA**.\n"
    md_content += f"- **Analysis Period:** {start_date} to {end_date} ({num_years:.1f} years)\n\n"
    
    md_content += "## Performance Summary\n"
    md_content += "_This table provides an 'apples-to-apples' comparison of the strategy against a Buy & Hold benchmark for this single asset. Use the **Calmar Ratio** to determine the best risk-adjusted performance._\n\n"
    md_content += "| Metric                  | Strategy (Optimal) | Buy & Hold |\n"
    md_content += "|:------------------------|:-------------------|:-----------|\n"
    md_content += f"| **Optimal Combination**     | T-Stop: `{sweet_spot['Trailing Stop (%)']}%`, P-Target: `{sweet_spot['Profit Target (%)']}` | N/A        |\n"
    md_content += f"| **Final P&L ($)**           | `${sweet_spot['P&L ($)']:,.2f}`         | `${bh_stats['P&L ($)']:,.2f}`  |\n"
    md_content += f"| **CAGR (%)**              | `{sweet_spot['CAGR (%)']:.2f}`%                | `{bh_stats['CAGR (%)']:.2f}`%     |\n"
    md_content += f"| **Max Drawdown (%)**      | `{sweet_spot['Max Drawdown (%)']:.2f}`%           | `{bh_stats['Max Drawdown (%)']:.2f}`%|\n"
    md_content += f"| **Calmar Ratio**          | `{sweet_spot['Calmar Ratio']:.2f}`                  | `{bh_stats['Calmar Ratio']:.2f}`     |\n\n"
    
    md_content += f"## Full Optimization Grid\n"
    md_content += display_df.to_markdown(index=False)
    
    report_path = os.path.join(report_dir, f"{ticker}_{ma_period}.md")
    with open(report_path, 'w') as f: f.write(md_content)
    print(f"  Individual report for {ticker} saved.")

def generate_summary_report(summary_data, group_sweet_spot, start_date, end_date, ma_period, report_dir):
    """Generates a summary report for the portfolio-level simulation."""
    if not summary_data: return
    summary_df = pd.DataFrame(summary_data)
    summary_df.rename(columns={"Trailing Stop (%)": "T-Stop (%)", "Profit Target (%)": "P-Target (%)"}, inplace=True)
    group_df = pd.DataFrame([group_sweet_spot])
    final_df = pd.concat([summary_df, group_df], ignore_index=True)
    cols_order = ["Symbol", "T-Stop (%)", "P-Target (%)", "P&L ($)", "Calmar Ratio", "Total Trades"]
    final_df = final_df[cols_order]
    for col in ['P&L ($)', 'Calmar Ratio']:
        final_df[col] = final_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)
    md_content = f"# Portfolio-Level Summary Report\n\n"
    md_content += "## Backtest Configuration\n"
    md_content += f"- **Universe:** All tested assets, sharing a single capital pool.\n"
    md_content += f"- **Starting Capital:** `${INITIAL_CAPITAL_PORTFOLIO:,.2f}`\n"
    md_content += f"- **Position Sizing:** Each trade allocates **10%** of the shared capital.\n"
    md_content += f"- **Strategy:** Buy on Close crossing above the **{ma_period}-period SMA**.\n"
    md_content += f"- **Analysis Date Range:** {start_date} to {end_date}\n\n"
    md_content += "## Portfolio Optimal Result\n"
    md_content += "The following combination was found by summing the P&L of every parameter set across all stocks.\n\n"
    md_content += f"- **Optimal Group T-Stop:** `{group_sweet_spot['T-Stop (%)']}%`\n"
    md_content += f"- **Optimal Group P-Target:** `{group_sweet_spot['P-Target (%)']}`\n"
    md_content += f"- **Aggregate Portfolio P&L:** `${group_sweet_spot['P&L ($)']:,.2f}`\n\n"
    md_content += "## Individual Asset Sweet Spots (Portfolio Context)\n"
    md_content += "The table shows the best parameter combination for each asset within the portfolio simulation.\n\n"
    md_content += final_df.to_markdown(index=False)
    report_path = os.path.join(report_dir, f'summary_report_{ma_period}.md')
    with open(report_path, 'w') as f: f.write(md_content)
    print(f"\nPortfolio summary report saved to: {report_path}")

def main():
    """Main function to run the two-tiered analysis."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    stock_files = glob.glob(os.path.join(STOCK_DATA_DIR, '*.csv'))
    if not stock_files: print("Error: No CSV files found."); return

    print(f"Starting Two-Tiered Analysis. This will run two simulations.\n")
    
    # --- Tier 1: Individual Asset Analysis (Dedicated Capital, 100% Position Size) ---
    print("--- Running Tier 1: Individual Asset Backtests ---")
    for file_path in stock_files:
        ticker = os.path.basename(file_path).split('_')[0]
        print(f"  Processing {ticker.upper()}...")
        df = prepare_data(file_path, MA_PERIOD)
        if df is None or df.empty:
            print("    DataFrame is empty. Skipping.")
            continue
        
        start_date_str = df.index.min().strftime('%Y-%m-%d')
        end_date_str = df.index.max().strftime('%Y-%m-%d')
        num_years = len(df) / 252.0
        buy_and_hold_stats = calculate_benchmark_stats(df, INITIAL_CAPITAL_INDIVIDUAL)
        sma_col = f'SMA_{MA_PERIOD}'
        results_this_stock = []
        
        for ts_pct in TRAILING_STOPS_PCT:
            for pt_pct in PROFIT_TARGETS_PCT:
                # Use dedicated capital and 100% position size for this tier
                result = run_backtest(df, ts_pct, pt_pct, INITIAL_CAPITAL_INDIVIDUAL, 1.0, COMMISSION_PCT, sma_col)
                results_this_stock.append(result)
        
        if not results_this_stock: continue
        results_df = pd.DataFrame(results_this_stock)
        sweet_spot = results_df.loc[results_df['Calmar Ratio'].idxmax()].to_dict()
        generate_individual_report(ticker, results_df, sweet_spot, buy_and_hold_stats, REPORTS_DIR, MA_PERIOD, num_years, start_date_str, end_date_str)

    # --- Tier 2: Portfolio Analysis (Shared Capital, 10% Position Size) ---
    print("\n--- Running Tier 2: Portfolio-Level Backtest ---")
    all_results_matrix = []
    individual_sweet_spots_portfolio = []
    min_start_date, max_end_date = pd.Timestamp.max, pd.Timestamp.min

    for file_path in stock_files:
        ticker = os.path.basename(file_path).split('_')[0]
        df = prepare_data(file_path, MA_PERIOD)
        if df is None or df.empty: continue
        min_start_date = min(min_start_date, df.index.min())
        max_end_date = max(max_end_date, df.index.max())
        sma_col = f'SMA_{MA_PERIOD}'
        results_this_stock_portfolio = []
        for ts_pct in TRAILING_STOPS_PCT:
            for pt_pct in PROFIT_TARGETS_PCT:
                # Use shared portfolio capital and 10% position size for this tier
                result = run_backtest(df, ts_pct, pt_pct, INITIAL_CAPITAL_PORTFOLIO, 0.10, COMMISSION_PCT, sma_col)
                all_results_matrix.append({'ticker': ticker, 'ts_pct': ts_pct, 'pt_pct': pt_pct, 'pnl': result['P&L ($)']})
                results_this_stock_portfolio.append(result)
        
        if not results_this_stock_portfolio: continue
        results_df_portfolio = pd.DataFrame(results_this_stock_portfolio)
        sweet_spot_portfolio = results_df_portfolio.loc[results_df_portfolio['Calmar Ratio'].idxmax()].to_dict()
        sweet_spot_portfolio['Symbol'] = ticker.upper()
        individual_sweet_spots_portfolio.append(sweet_spot_portfolio)

    if not all_results_matrix:
        print("\nNo portfolio trades were executed. Cannot generate summary report.")
        return

    matrix_df = pd.DataFrame(all_results_matrix)
    group_pnl = matrix_df.groupby(['ts_pct', 'pt_pct'])['pnl'].sum()
    portfolio_optimal_params = group_pnl.idxmax()
    optimal_ts, optimal_pt = portfolio_optimal_params
    total_trades_portfolio = 0
    for file_path in stock_files:
        df = prepare_data(file_path, MA_PERIOD)
        if df is None or df.empty: continue
        sma_col = f'SMA_{MA_PERIOD}'
        result = run_backtest(df, optimal_ts, optimal_pt if not pd.isna(optimal_pt) else None, INITIAL_CAPITAL_PORTFOLIO, 0.10, COMMISSION_PCT, sma_col)
        total_trades_portfolio += result['Total Trades']

    group_sweet_spot = {
        'Symbol': '**PORTFOLIO OPTIMAL**',
        'T-Stop (%)': optimal_ts,
        'P-Target (%)': 'None' if pd.isna(optimal_pt) else int(optimal_pt),
        'P&L ($)': group_pnl.max(),
        'Calmar Ratio': 'N/A',
        'Total Trades': total_trades_portfolio
    }
    
    generate_summary_report(
        individual_sweet_spots_portfolio, 
        group_sweet_spot,
        min_start_date.strftime('%Y-%m-%d'), 
        max_end_date.strftime('%Y-%m-%d'), 
        MA_PERIOD,
        REPORTS_DIR
    )
    
    print("\n--- All backtests complete! ---")

if __name__ == "__main__":
    main()